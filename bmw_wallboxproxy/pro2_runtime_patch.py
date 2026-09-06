"""Install PRO2-specific Modbus behaviour without changing other meter models.

The existing transport code is intentionally shared. This module wraps its
request handlers at import time so PRO2 can implement the documented FC06/FC16
writes and return exception 02 for addresses that are not in the physical
PRO2 map, while PRO380/Janitza retain their existing behaviour.
"""

import struct

import dr_client
from config import get_meter_model
from modbus_codec import append_crc, modbus_crc
from pro2_modbus import handle_fc10_pdu
from pro2_state import get_slave_id

_ORIGINAL_DECODED = dr_client._handle_decoded_request
_ORIGINAL_RTU = dr_client.handle_rtu_request
_ORIGINAL_TCP = dr_client.handle_modbus_tcp_request


def _is_pro2() -> bool:
    return get_meter_model() == "inepro_pro2"


def _pro2_decoded(slave_id, function_code, start_addr, quantity, transport):
    if not _is_pro2():
        return _ORIGINAL_DECODED(slave_id, function_code, start_addr, quantity, transport)

    if slave_id != get_slave_id():
        with dr_client.stats_lock:
            dr_client.stats["wrong_slave"] += 1
        dr_client.log_modbus(f"IGN wrong PRO2 slave id {slave_id}")
        return None

    if function_code == 6:
        pdu = struct.pack(">BHH", 6, start_addr, quantity)
        return dr_client.pro2_modbus.handle_fc06_pdu(pdu)

    if function_code in (3, 4):
        if function_code != 3:
            return dr_client.build_exception_payload(slave_id, function_code, 1, "PRO2 map documents FC03 reads")
        reg_map = dr_client.get_register_map()
        if quantity < 1 or quantity > 125:
            return dr_client.build_exception_payload(slave_id, function_code, 3, f"illegal quantity {quantity}")
        if any(addr not in reg_map for addr in range(start_addr, start_addr + quantity)):
            return dr_client.build_exception_payload(slave_id, function_code, 2, "PRO2 illegal data address")

    return _ORIGINAL_DECODED(slave_id, function_code, start_addr, quantity, transport)


def _rtu(frame: bytes):
    if _is_pro2() and len(frame) >= 8 and frame[1] == 0x10:
        if modbus_crc(frame[:-2]) != struct.unpack("<H", frame[-2:])[0]:
            return _ORIGINAL_RTU(frame)
        slave_id = frame[0]
        if slave_id != get_slave_id():
            return None
        pdu = frame[1:-2]
        payload = handle_fc10_pdu(pdu)
        return append_crc(bytes([slave_id]) + payload)
    return _ORIGINAL_RTU(frame)


def _tcp(frame: bytes):
    if _is_pro2() and len(frame) >= 12 and frame[7] == 0x10:
        transaction_id, protocol_id, length = struct.unpack(">HHH", frame[:6])
        unit_id = frame[6]
        if protocol_id != 0 or length != len(frame) - 6:
            return _ORIGINAL_TCP(frame)
        if unit_id != get_slave_id():
            return None
        payload = handle_fc10_pdu(frame[7:])
        return dr_client._finalize_tcp_response(transaction_id, unit_id, payload)
    return _ORIGINAL_TCP(frame)


dr_client._handle_decoded_request = _pro2_decoded
dr_client.handle_rtu_request = _rtu
dr_client.handle_modbus_tcp_request = _tcp
