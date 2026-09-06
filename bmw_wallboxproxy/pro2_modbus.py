"""Modbus write handling for the Inepro PRO2-Mod writable register block."""

import struct
from typing import Optional

from pro2_state import write_fc06, write_fc10


def _exception(function_code: int, code: int) -> bytes:
    return bytes((function_code | 0x80, code))


def handle_fc06_pdu(pdu: bytes) -> bytes:
    """Handle FC06 PDU and return the normal/exception PDU."""
    if len(pdu) != 5 or pdu[0] != 6:
        return _exception(6, 3)
    addr, value = struct.unpack(">HH", pdu[1:5])
    try:
        write_fc06(addr, value)
    except KeyError:
        return _exception(6, 2)
    except ValueError:
        return _exception(6, 3)
    return pdu


def handle_fc10_pdu(pdu: bytes) -> bytes:
    """Handle FC16/0x10 PDU and return the normal/exception PDU."""
    if len(pdu) < 6 or pdu[0] != 0x10:
        return _exception(0x10, 3)
    addr, quantity, byte_count = struct.unpack(">HHB", pdu[1:6])
    if quantity < 1 or quantity > 123 or byte_count != quantity * 2 or len(pdu) != 6 + byte_count:
        return _exception(0x10, 3)
    # PRO2 FC16 writable registers are documented as two-register values.
    # A wrong quantity is a malformed/illegal-value request, not an unknown
    # register address, so report exception 03.
    if quantity != 2:
        return _exception(0x10, 3)
    words = struct.unpack(">HH", pdu[6:10])
    try:
        write_fc10(addr, words)
    except KeyError:
        return _exception(0x10, 2)
    except ValueError:
        return _exception(0x10, 3)
    return struct.pack(">BHH", 0x10, addr, quantity)


def handle_write_pdu(pdu: bytes) -> Optional[bytes]:
    if not pdu:
        return None
    if pdu[0] == 6:
        return handle_fc06_pdu(pdu)
    if pdu[0] == 0x10:
        return handle_fc10_pdu(pdu)
    return None
