import select
import socket
import struct
import time
import threading
from typing import Optional, Tuple

from config import (
    MODBUS_IDLE_DISCONNECT_SECONDS,
    MODBUS_INITIAL_CONNECT_IDLE_SECONDS,
    MODBUS_LISTEN_HOST,
    MODBUS_LISTEN_PORT,
    MODBUS_TCP_KEEPALIVE_COUNT,
    MODBUS_TCP_KEEPALIVE_IDLE,
    MODBUS_TCP_KEEPALIVE_INTERVAL,
    SOCKET_TIMEOUT,
    SLAVE_ID,
)
from state import (
    get_transport_mode,
    get_transport_mode_generation,
    log_modbus,
    log_net,
    log_tcp_raw,
    stats,
    stats_lock,
    stop_event,
)
from modbus_codec import append_crc, modbus_crc
from register_map import get_register_map


connection_lock = threading.Lock()
active_server_socket: Optional[socket.socket] = None
active_client_socket: Optional[socket.socket] = None

# Poll intervals for the select-based loops. They must stay well below the
# charger's 200 ms request interval so idle checks and new connections are
# noticed without delaying request handling.
ACCEPT_POLL_SECONDS = 0.5
CLIENT_POLL_SECONDS = 0.25


def _looks_like_rtu_request(frame: bytes) -> bool:
    if len(frame) != 8:
        return False

    if frame[1] not in (3, 4):
        return False

    return modbus_crc(frame[:-2]) == struct.unpack("<H", frame[-2:])[0]


def _rtu_crc_valid(frame: bytes) -> bool:
    return len(frame) >= 4 and modbus_crc(frame[:-2]) == struct.unpack("<H", frame[-2:])[0]


# Total RTU request length (slave id + PDU + CRC) per function code. Read and
# single-write requests are 8 bytes, which is what the charger sends in normal
# operation, but a master may also probe with other function codes. Assuming
# every request is 8 bytes long shreds those frames in the resync path and the
# master gets no answer at all — masters retry a few times on silence and then
# drop the link, whereas a Modbus exception reply is handled cleanly.
_RTU_FIXED_REQUEST_LENGTHS = {
    1: 8,   # read coils
    2: 8,   # read discrete inputs
    3: 8,   # read holding registers
    4: 8,   # read input registers
    5: 8,   # write single coil
    6: 8,   # write single register
    8: 8,   # diagnostics
    7: 4,   # read exception status
    11: 4,  # get comm event counter
    12: 4,  # get comm event log
    17: 4,  # report slave id
}
# Function codes whose length is carried in a byte-count field, mapped to the
# index of that field within the frame.
_RTU_BYTE_COUNT_INDEX = {
    15: 6,  # write multiple coils
    16: 6,  # write multiple registers
    20: 2,  # read file record
    21: 2,  # write file record
}
MAX_RTU_FRAME = 256
MIN_RTU_FRAME = 4


def _rtu_expected_length(buffer: bytearray) -> Optional[int]:
    """Total length of the RTU request at the head of the buffer.

    Returns None when the length cannot be determined yet, either because too
    few bytes have arrived or because the function code is not one we know.
    """
    if len(buffer) < 2:
        return None

    function_code = buffer[1]

    fixed = _RTU_FIXED_REQUEST_LENGTHS.get(function_code)
    if fixed is not None:
        return fixed

    count_index = _RTU_BYTE_COUNT_INDEX.get(function_code)
    if count_index is not None:
        if len(buffer) <= count_index:
            return None
        return count_index + 1 + buffer[count_index] + 2

    if function_code == 43:  # encapsulated interface transport
        if len(buffer) < 3:
            return None
        if buffer[2] == 14:  # read device identification
            return 7

    return None


def _take_rtu_frame(buffer: bytearray) -> Tuple[Optional[bytes], bool]:
    """Pop the next complete RTU request off the buffer.

    Returns (frame, need_more_data). A (None, False) result means the head of
    the buffer is not the start of any valid frame and the caller must resync.
    """
    expected = _rtu_expected_length(buffer)
    if expected is not None:
        if expected > MAX_RTU_FRAME:
            return None, False
        if len(buffer) < expected:
            return None, True
        candidate = bytes(buffer[:expected])
        if _rtu_crc_valid(candidate):
            del buffer[:expected]
            return candidate, False

    # Unknown function code, or the declared length did not check out. Fall back
    # to looking for any prefix that passes CRC before discarding bytes.
    for length in range(MIN_RTU_FRAME, min(len(buffer), MAX_RTU_FRAME) + 1):
        candidate = bytes(buffer[:length])
        if _rtu_crc_valid(candidate):
            del buffer[:length]
            return candidate, False

    if expected is None and len(buffer) < 8:
        # Too little to judge: an unrecognised frame may still be in flight.
        return None, True

    return None, False


def _resync_rtu_buffer(buffer: bytearray) -> int:
    """Drop one leading byte so the caller can retry frame extraction.

    Wireless serial bridges can inject or lose single bytes; recovering
    in-stream keeps the session alive instead of disconnecting the charger,
    which only tolerates a few missed 200 ms polls before it errors out.
    """
    if len(buffer) > MAX_RTU_FRAME:
        dropped = len(buffer) - MAX_RTU_FRAME
        del buffer[:dropped]
        return dropped

    if not buffer:
        return 0

    del buffer[0]
    return 1


def _looks_like_mbap_frame(data: bytes) -> bool:
    if len(data) < 6:
        return False
    protocol_id = struct.unpack(">H", data[2:4])[0]
    length = struct.unpack(">H", data[4:6])[0]
    return protocol_id == 0 and 2 <= length <= 260


def build_read_payload(slave_id: int, function_code: int, start_addr: int, quantity: int) -> bytes:
    reg_map = get_register_map()
    words = [reg_map.get(addr, 0) for addr in range(start_addr, start_addr + quantity)]
    payload = bytearray([function_code, quantity * 2])
    for word in words:
        payload += struct.pack(">H", word)
    log_modbus(
        f"MAP slave={slave_id} fc={function_code} addr=0x{start_addr:04X}-0x{start_addr + quantity - 1:04X} words="
        f"{' '.join(f'{word:04X}' for word in words)}"
    )
    return bytes(payload)


def build_exception_payload(slave_id: int, function_code: int, exc_code: int, reason: str) -> bytes:
    with stats_lock:
        stats["last_exception"] = f"fc={function_code} code={exc_code} {reason}"
    log_modbus(f"EXC slave={slave_id} fc={function_code} code={exc_code} reason={reason}")
    return bytes([function_code | 0x80, exc_code])


def _finalize_rtu_response(slave_id: int, payload: bytes) -> bytes:
    return append_crc(bytes([slave_id]) + payload)


def _finalize_tcp_response(transaction_id: int, unit_id: int, payload: bytes) -> bytes:
    header = struct.pack(">HHHB", transaction_id, 0, len(payload) + 1, unit_id)
    return header + payload


def _handle_decoded_request(
    slave_id: int,
    function_code: int,
    start_addr: int,
    quantity: int,
    transport: str,
) -> Optional[bytes]:
    with stats_lock:
        stats["last_fc"] = function_code
        stats["last_start_addr"] = f"0x{start_addr:04X}"
        stats["last_quantity"] = quantity
        stats["last_exception"] = "-"

    log_modbus(f"DEC mode={transport} slave={slave_id} fc={function_code} start=0x{start_addr:04X} qty={quantity}")

    if slave_id != SLAVE_ID:
        with stats_lock:
            stats["wrong_slave"] += 1
        log_modbus(f"IGN wrong slave id {slave_id}")
        return None

    if function_code not in (3, 4):
        # Answer with an exception rather than staying silent. A master retries
        # on silence and drops the link after a few timeouts; it accepts an
        # exception reply and moves on.
        with stats_lock:
            stats["unsupported_fc"] += 1
        return build_exception_payload(slave_id, function_code, 1, "unsupported function code")

    if quantity < 1 or quantity > 125:
        with stats_lock:
            stats["illegal_quantity"] += 1
        return build_exception_payload(slave_id, function_code, 3, f"illegal quantity {quantity}")

    try:
        return build_read_payload(slave_id, function_code, start_addr, quantity)
    except Exception as exc:
        # A single unrepresentable live value must not tear down the session.
        return build_exception_payload(slave_id, function_code, 4, f"register build failed: {exc}")


def handle_rtu_request(frame: bytes) -> Optional[bytes]:
    log_modbus(f"RX RTU {frame.hex(' ')}")

    with stats_lock:
        stats["rx_frames"] += 1
        stats["bytes_rx"] += len(frame)
        stats["last_rx"] = time.strftime("%H:%M:%S")

    if len(frame) < MIN_RTU_FRAME:
        with stats_lock:
            stats["short_frames"] += 1
        log_modbus("ERR frame too short")
        return None

    body = frame[:-2]
    recv_crc = struct.unpack("<H", frame[-2:])[0]
    expected_crc = modbus_crc(body)
    with stats_lock:
        stats["last_crc_received"] = f"0x{recv_crc:04X}"
        stats["last_crc_expected"] = f"0x{expected_crc:04X}"
        stats["last_transaction_id"] = "-"

    if recv_crc != expected_crc:
        with stats_lock:
            stats["crc_fail"] += 1
        log_modbus(f"ERR CRC fail recv=0x{recv_crc:04X} expected=0x{expected_crc:04X} — frame dropped")
        return None

    slave_id = frame[0]
    function_code = frame[1]
    if len(frame) >= 8:
        start_addr = struct.unpack(">H", frame[2:4])[0]
        quantity = struct.unpack(">H", frame[4:6])[0]
    else:
        # Short requests (report slave id, read exception status, ...) carry no
        # address or quantity; they are answered with an exception anyway.
        start_addr = 0
        quantity = 0

    log_modbus(f"CRC mode=rtu_over_tcp recv=0x{recv_crc:04X} expected=0x{expected_crc:04X}")

    payload = _handle_decoded_request(slave_id, function_code, start_addr, quantity, "rtu_over_tcp")
    if payload is None:
        return None
    return _finalize_rtu_response(slave_id, payload)


def handle_modbus_tcp_request(frame: bytes) -> Optional[bytes]:
    log_modbus(f"RX TCP {frame.hex(' ')}")

    with stats_lock:
        stats["rx_frames"] += 1
        stats["bytes_rx"] += len(frame)
        stats["last_rx"] = time.strftime("%H:%M:%S")
        stats["last_crc_received"] = "-"
        stats["last_crc_expected"] = "-"

    if len(frame) < 12:
        with stats_lock:
            stats["short_frames"] += 1
        log_modbus("ERR Modbus TCP frame too short")
        return None

    transaction_id, protocol_id, length = struct.unpack(">HHH", frame[:6])
    unit_id = frame[6]

    with stats_lock:
        stats["last_transaction_id"] = f"0x{transaction_id:04X}"

    if protocol_id != 0:
        log_modbus(f"ERR invalid MBAP protocol id {protocol_id}")
        return None

    expected_length = len(frame) - 6
    if length != expected_length:
        log_modbus(f"ERR MBAP length mismatch recv={length} actual={expected_length}")
        return None

    pdu = frame[7:]
    if len(pdu) < 5:
        with stats_lock:
            stats["short_frames"] += 1
        log_modbus("ERR Modbus TCP PDU too short")
        return None

    function_code = pdu[0]
    start_addr = struct.unpack(">H", pdu[1:3])[0]
    quantity = struct.unpack(">H", pdu[3:5])[0]
    log_modbus(
        f"MBAP txid=0x{transaction_id:04X} proto={protocol_id} len={length} unit={unit_id}"
    )

    payload = _handle_decoded_request(unit_id, function_code, start_addr, quantity, "modbus_tcp")
    if payload is None:
        return None
    return _finalize_tcp_response(transaction_id, unit_id, payload)


def _next_tcp_frame_length(buffer: bytearray) -> Optional[int]:
    """Length of the next MBAP frame, None if incomplete, -1 on a framing mismatch."""
    if len(buffer) >= 8 and _looks_like_rtu_request(bytes(buffer[:8])):
        log_modbus("ERR framing mismatch: received RTU-over-TCP request while mode=modbus_tcp")
        return -1
    if len(buffer) < 7:
        return None
    length = struct.unpack(">H", buffer[4:6])[0]
    if length < 2 or length > 260:
        log_modbus(f"ERR invalid MBAP length {length}; likely wrong transport mode")
        return -1
    return 6 + length


def handle_request(frame: bytes, transport_mode: str) -> Optional[bytes]:
    if transport_mode == "modbus_tcp":
        return handle_modbus_tcp_request(frame)
    return handle_rtu_request(frame)


def _session_summary(
    started_at: float,
    requests_served: int,
    responses_sent: int,
    last_response_at: Optional[float],
) -> str:
    """Describe a finished session so a disconnect line says why it mattered.

    "client disconnected" on its own is unactionable: it does not say whether
    the session was healthy up to the last poll or had already stopped being
    answered.
    """
    now = time.monotonic()
    duration = now - started_at
    if last_response_at is None:
        last_reply = "never answered"
    else:
        last_reply = f"last reply {now - last_response_at:.1f}s ago"
    unanswered = requests_served - responses_sent
    detail = (
        f" (session {duration:.1f}s, {requests_served} requests, "
        f"{responses_sent} replies, {last_reply}"
    )
    if unanswered:
        detail += f", {unanswered} unanswered"
    return detail + ")"


def _set_socket_linger_abort(sock: socket.socket) -> None:
    try:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, struct.pack("ii", 1, 0))
    except OSError:
        pass


def _register_server_socket(sock: socket.socket) -> None:
    global active_server_socket
    with connection_lock:
        active_server_socket = sock


def _register_client_socket(sock: Optional[socket.socket]) -> None:
    global active_client_socket
    with connection_lock:
        active_client_socket = sock


def force_disconnect_dr(reason: str) -> None:
    with connection_lock:
        client = active_client_socket
        server = active_server_socket

    if client is not None:
        try:
            _set_socket_linger_abort(client)
            client.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
        try:
            client.close()
        except OSError:
            pass
        _register_client_socket(None)
        log_net(f"Forced DR disconnect: {reason}")

    if server is not None:
        try:
            server.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass


def _configure_client_socket(conn: socket.socket) -> None:
    conn.settimeout(SOCKET_TIMEOUT)

    try:
        # Disable Nagle: responses are tiny and the charger expects them well
        # within its 200 ms poll interval, so they must never be coalesced.
        conn.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    except OSError as exc:
        log_net(f"TCP_NODELAY configuration skipped: {exc}")

    try:
        conn.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)

        idle_opt = getattr(socket, "TCP_KEEPIDLE", None)
        if idle_opt is None:
            idle_opt = getattr(socket, "TCP_KEEPALIVE", None)
        if idle_opt is not None:
            conn.setsockopt(socket.IPPROTO_TCP, idle_opt, MODBUS_TCP_KEEPALIVE_IDLE)

        interval_opt = getattr(socket, "TCP_KEEPINTVL", None)
        if interval_opt is not None:
            conn.setsockopt(socket.IPPROTO_TCP, interval_opt, MODBUS_TCP_KEEPALIVE_INTERVAL)

        count_opt = getattr(socket, "TCP_KEEPCNT", None)
        if count_opt is not None:
            conn.setsockopt(socket.IPPROTO_TCP, count_opt, MODBUS_TCP_KEEPALIVE_COUNT)
    except OSError as exc:
        log_net(f"TCP keepalive configuration skipped: {exc}")


def tcp_server_loop() -> None:
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    _register_server_socket(server)
    try:
        server.bind((MODBUS_LISTEN_HOST, MODBUS_LISTEN_PORT))
        server.listen(1)
        active_mode = get_transport_mode()
        log_net(
            f"Listening on {MODBUS_LISTEN_HOST}:{MODBUS_LISTEN_PORT} mode={active_mode}"
        )

        pending_conn: Optional[Tuple[socket.socket, Tuple[str, int]]] = None

        while not stop_event.is_set():
            conn = None
            had_connection = False
            abort_on_close = False
            mode_generation = get_transport_mode_generation()
            try:
                if pending_conn is not None:
                    conn, addr = pending_conn
                    pending_conn = None
                else:
                    readable, _, _ = select.select([server], [], [], ACCEPT_POLL_SECONDS)
                    if not readable:
                        continue
                    conn, addr = server.accept()
                had_connection = True
                _register_client_socket(conn)
                _configure_client_socket(conn)
                active_mode = get_transport_mode()
                mode_generation = get_transport_mode_generation()
                last_payload_at = time.monotonic()

                with stats_lock:
                    stats["tcp_connects"] += 1
                    stats["tcp_connected"] = True
                    stats["last_connect"] = time.strftime("%H:%M:%S")
                    stats["last_buffer_len"] = 0
                    stats["transport_mode"] = active_mode

                log_net(f"Modbus client connected from {addr[0]}:{addr[1]} mode={active_mode}")
                buffer = bytearray()
                got_first_payload = False
                framing_checked = False
                session_started_at = time.monotonic()
                requests_served = 0
                responses_sent = 0
                last_response_at: Optional[float] = None
                abort_on_close = False

                while not stop_event.is_set():
                    try:
                        current_generation = get_transport_mode_generation()
                        if current_generation != mode_generation:
                            log_net(
                                "Closing client connection to apply new transport mode"
                                + _session_summary(session_started_at, requests_served, responses_sent, last_response_at)
                            )
                            break

                        readable, _, _ = select.select([conn, server], [], [], CLIENT_POLL_SECONDS)

                        if server in readable and conn not in readable:
                            new_conn, new_addr = server.accept()
                            pending_conn = (new_conn, new_addr)
                            abort_on_close = True
                            log_net(
                                f"New Modbus client from {new_addr[0]}:{new_addr[1]} — "
                                "replacing existing connection so a reconnecting charger or bridge is served immediately"
                            )
                            raise ConnectionError("replaced by new client connection")

                        if conn not in readable:
                            elapsed = time.monotonic() - last_payload_at
                            if got_first_payload:
                                idle_limit = MODBUS_IDLE_DISCONNECT_SECONDS
                                label = "established session idle"
                            else:
                                idle_limit = MODBUS_INITIAL_CONNECT_IDLE_SECONDS
                                label = "no initial payload"
                            if idle_limit > 0 and elapsed >= idle_limit:
                                log_net(
                                    f"Closing idle client connection after {elapsed:.1f}s ({label})"
                                )
                                raise ConnectionError(f"idle timeout: {label}")
                            continue

                        data = conn.recv(256)
                        if not data:
                            raise ConnectionError("client disconnected")

                        last_payload_at = time.monotonic()
                        got_first_payload = True

                        log_tcp_raw(f"TCP RX {len(data)} bytes {data.hex(' ')}")
                        buffer.extend(data)
                        with stats_lock:
                            stats["last_buffer_len"] = len(buffer)

                        if not framing_checked and len(buffer) >= 6:
                            framing_checked = True
                            if active_mode == "rtu_over_tcp" and _looks_like_mbap_frame(bytes(buffer)):
                                raise ConnectionError(
                                    "framing mismatch: charger is sending Modbus TCP (MBAP) frames"
                                    " but Transport Mode is set to rtu_over_tcp"
                                    " — change Transport Mode to modbus_tcp"
                                )
                            if active_mode == "modbus_tcp" and len(buffer) >= 8 and _looks_like_rtu_request(bytes(buffer[:8])):
                                raise ConnectionError(
                                    "framing mismatch: charger is sending RTU-over-TCP frames"
                                    " but Transport Mode is set to modbus_tcp"
                                    " — change Transport Mode to rtu_over_tcp"
                                )

                        log_modbus(f"BUF mode={active_mode} len={len(buffer)}")

                        while True:
                            if active_mode == "rtu_over_tcp":
                                frame, need_more = _take_rtu_frame(buffer)
                                if frame is None:
                                    if need_more:
                                        log_modbus("BUF waiting for complete rtu_over_tcp frame")
                                        break
                                    dropped = _resync_rtu_buffer(buffer)
                                    if dropped:
                                        with stats_lock:
                                            stats["crc_fail"] += 1
                                            stats["last_buffer_len"] = len(buffer)
                                        log_modbus(
                                            f"RESYNC dropped {dropped} garbage byte(s) to realign RTU stream"
                                        )
                                        continue
                                    break
                            else:
                                next_frame_len = _next_tcp_frame_length(buffer)
                                if next_frame_len == -1:
                                    log_net("Closing client connection because incoming traffic does not match selected transport mode")
                                    raise ConnectionError("transport mode mismatch")
                                if next_frame_len is None or len(buffer) < next_frame_len:
                                    log_modbus("BUF waiting for complete modbus_tcp frame")
                                    break
                                frame = bytes(buffer[:next_frame_len])
                                del buffer[:next_frame_len]

                            with stats_lock:
                                stats["last_buffer_len"] = len(buffer)

                            if len(buffer):
                                log_modbus(f"BUF trailing={len(buffer)} bytes after frame extraction")

                            requests_served += 1
                            response = handle_request(frame, active_mode)
                            if response:
                                conn.sendall(response)
                                responses_sent += 1
                                last_response_at = time.monotonic()
                                with stats_lock:
                                    stats["tx_frames"] += 1
                                    stats["bytes_tx"] += len(response)
                                    stats["last_tx"] = time.strftime("%H:%M:%S")
                                log_modbus(f"TX {active_mode} {response.hex(' ')}")
                                log_tcp_raw(f"TCP TX {len(response)} bytes {response.hex(' ')}")

                    except socket.timeout:
                        continue
                    except ConnectionError as e:
                        log_net(f"Connection closed: {e}{_session_summary(session_started_at, requests_served, responses_sent, last_response_at)}")
                        break
                    except Exception as e:
                        log_net(f"Connection error: {e}{_session_summary(session_started_at, requests_served, responses_sent, last_response_at)}")
                        break

            except Exception as e:
                with stats_lock:
                    stats["tcp_accept_errors"] += 1
                log_net(f"TCP error: {e}")

            finally:
                if conn:
                    try:
                        # Only abort with RST when replacing a stale connection.
                        # A linger-0 close discards anything still unacked, which
                        # on a normal close can throw away the reply the charger
                        # is waiting for instead of letting TCP retransmit it.
                        if abort_on_close:
                            _set_socket_linger_abort(conn)
                        conn.close()
                    except Exception:
                        pass
                _register_client_socket(None)
                with stats_lock:
                    if had_connection:
                        stats["tcp_disconnects"] += 1
                        stats["last_disconnect"] = time.strftime("%H:%M:%S")
                    stats["tcp_connected"] = False
                    stats["last_buffer_len"] = 0
    finally:
        _register_server_socket(None)
        server.close()