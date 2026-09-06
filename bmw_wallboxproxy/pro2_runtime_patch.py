"""Install PRO2-specific Modbus behaviour without changing other meter models."""

import struct
import time

import config
import dr_client
import pro2_modbus
from modbus_codec import append_crc, modbus_crc
from pro2_state import get_slave_id

_ORIGINAL_DECODED = dr_client._handle_decoded_request
_ORIGINAL_RTU = dr_client.handle_rtu_request
_ORIGINAL_TCP = dr_client.handle_modbus_tcp_request


def _is_pro2() -> bool:
    return config.get_meter_model() == "inepro_pro2"


def _record_decoded(slave_id, function_code, start_addr, quantity, transport):
    """Keep the PRO2 dispatcher on the same activity/stats path as dr_client."""
    with dr_client.stats_lock:
        dr_client.stats["last_fc"] = function_code
        dr_client.stats["last_start_addr"] = f"0x{start_addr:04X}"
        dr_client.stats["last_quantity"] = quantity
        dr_client.stats["last_exception"] = "-"
    dr_client.log_modbus(
        f"DEC mode={transport} slave={slave_id} fc={function_code} "
        f"start=0x{start_addr:04X} qty={quantity}"
    )


def _pro2_decoded(slave_id, function_code, start_addr, quantity, transport):
    if not _is_pro2():
        return _ORIGINAL_DECODED(slave_id, function_code, start_addr, quantity, transport)

    _record_decoded(slave_id, function_code, start_addr, quantity, transport)

    if slave_id != get_slave_id():
        with dr_client.stats_lock:
            dr_client.stats["wrong_slave"] += 1
        dr_client.log_modbus(f"IGN wrong slave id {slave_id}")
        return None

    if function_code == 6:
        payload = pro2_modbus.handle_fc06_pdu(struct.pack(">BHH", 6, start_addr, quantity))
        dr_client.log_modbus(
            f"WRITE FC06 slave={slave_id} addr=0x{start_addr:04X} value=0x{quantity:04X}"
        )
        return payload

    if function_code == 3:
        reg_map = dr_client.get_register_map()
        if quantity < 1 or quantity > 125:
            with dr_client.stats_lock:
                dr_client.stats["illegal_quantity"] += 1
            return dr_client.build_exception_payload(
                slave_id, function_code, 3, f"illegal quantity {quantity}"
            )
        if any(addr not in reg_map for addr in range(start_addr, start_addr + quantity)):
            return dr_client.build_exception_payload(
                slave_id, function_code, 2, "PRO2 illegal data address"
            )
        try:
            return dr_client.build_read_payload(slave_id, function_code, start_addr, quantity)
        except Exception as exc:
            return dr_client.build_exception_payload(
                slave_id, function_code, 4, f"register build failed: {exc}"
            )

    if function_code == 4:
        return dr_client.build_exception_payload(
            slave_id, function_code, 1, "PRO2 map documents FC03 reads"
        )

    with dr_client.stats_lock:
        dr_client.stats["unsupported_fc"] += 1
    return dr_client.build_exception_payload(
        slave_id, function_code, 1, "unsupported function code"
    )


def _rtu(frame: bytes):
    if not _is_pro2():
        return _ORIGINAL_RTU(frame)

    dr_client.log_modbus(f"RX RTU {frame.hex(' ')}")
    with dr_client.stats_lock:
        dr_client.stats["rx_frames"] += 1
        dr_client.stats["bytes_rx"] += len(frame)
        dr_client.stats["last_rx"] = time.strftime("%H:%M:%S")

    if len(frame) < 4:
        dr_client.stats["short_frames"] += 1
        dr_client.log_modbus("ERR frame too short")
        return None

    recv_crc = struct.unpack("<H", frame[-2:])[0]
    expected_crc = modbus_crc(frame[:-2])
    with dr_client.stats_lock:
        dr_client.stats["last_crc_received"] = f"0x{recv_crc:04X}"
        dr_client.stats["last_crc_expected"] = f"0x{expected_crc:04X}"
        dr_client.stats["last_transaction_id"] = "-"

    if recv_crc != expected_crc:
        with dr_client.stats_lock:
            dr_client.stats["crc_fail"] += 1
        dr_client.log_modbus(
            f"ERR CRC fail recv=0x{recv_crc:04X} expected=0x{expected_crc:04X} — frame dropped"
        )
        return None

    slave_id = frame[0]
    function_code = frame[1]
    if slave_id != get_slave_id():
        with dr_client.stats_lock:
            dr_client.stats["wrong_slave"] += 1
        dr_client.log_modbus(f"IGN wrong slave id {slave_id}")
        return None

    if function_code == 0x10:
        payload = pro2_modbus.handle_fc10_pdu(frame[1:-2])
        dr_client.log_modbus(f"WRITE FC16 slave={slave_id} pdu={frame[1:-2].hex(' ')}")
    elif function_code in (3, 4, 6):
        if len(frame) < 8:
            with dr_client.stats_lock:
                dr_client.stats["short_frames"] += 1
            dr_client.log_modbus("ERR PRO2 request too short")
            return None
        start_addr, quantity = struct.unpack(">HH", frame[2:6])
        payload = _pro2_decoded(slave_id, function_code, start_addr, quantity, "rtu_over_tcp")
    else:
        if len(frame) >= 8:
            start_addr, quantity = struct.unpack(">HH", frame[2:6])
        else:
            start_addr = quantity = 0
        payload = _pro2_decoded(slave_id, function_code, start_addr, quantity, "rtu_over_tcp")

    return append_crc(bytes([slave_id]) + payload)


def _tcp(frame: bytes):
    if not (_is_pro2() and len(frame) >= 12 and frame[6] == get_slave_id()):
        return _ORIGINAL_TCP(frame)

    dr_client.log_modbus(f"RX TCP {frame.hex(' ')}")
    with dr_client.stats_lock:
        dr_client.stats["rx_frames"] += 1
        dr_client.stats["bytes_rx"] += len(frame)
        dr_client.stats["last_rx"] = time.strftime("%H:%M:%S")
        dr_client.stats["last_crc_received"] = "-"
        dr_client.stats["last_crc_expected"] = "-"

    transaction_id, protocol_id, length = struct.unpack(">HHH", frame[:6])
    unit_id = frame[6]
    with dr_client.stats_lock:
        dr_client.stats["last_transaction_id"] = f"0x{transaction_id:04X}"

    if protocol_id != 0 or length != len(frame) - 6:
        return _ORIGINAL_TCP(frame)

    pdu = frame[7:]
    if not pdu:
        return _ORIGINAL_TCP(frame)

    function_code = pdu[0]
    if function_code == 0x10:
        payload = pro2_modbus.handle_fc10_pdu(pdu)
        dr_client.log_modbus(f"WRITE FC16 slave={unit_id} pdu={pdu.hex(' ')}")
    elif function_code in (3, 4, 6):
        if len(pdu) < 5:
            with dr_client.stats_lock:
                dr_client.stats["short_frames"] += 1
            dr_client.log_modbus("ERR PRO2 Modbus TCP PDU too short")
            return None
        start_addr, quantity = struct.unpack(">HH", pdu[1:5])
        payload = _pro2_decoded(unit_id, function_code, start_addr, quantity, "modbus_tcp")
    else:
        start_addr = struct.unpack(">H", pdu[1:3])[0] if len(pdu) >= 3 else 0
        quantity = struct.unpack(">H", pdu[3:5])[0] if len(pdu) >= 5 else 0
        payload = _pro2_decoded(unit_id, function_code, start_addr, quantity, "modbus_tcp")

    return dr_client._finalize_tcp_response(transaction_id, unit_id, payload)


dr_client._handle_decoded_request = _pro2_decoded
dr_client.handle_rtu_request = _rtu
dr_client.handle_modbus_tcp_request = _tcp
