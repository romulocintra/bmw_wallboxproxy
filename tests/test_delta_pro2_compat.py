import struct
import sys
from pathlib import Path

PACKAGE_DIR = Path(__file__).resolve().parents[1] / "bmw_wallboxproxy"
if str(PACKAGE_DIR) not in sys.path:
    sys.path.insert(0, str(PACKAGE_DIR))

import config
import dr_client
from meter_models import build_inepro_pro2
import pro2_runtime_patch  # noqa: F401 - installs the PRO2 dispatcher patch
from modbus_codec import modbus_crc


def _request(start_addr: int, quantity: int) -> bytes:
    body = bytes([1, 3]) + struct.pack(">HH", start_addr, quantity)
    return body + struct.pack("<H", modbus_crc(body))


def _decode_cdab(words):
    return struct.unpack(">f", struct.pack(">HH", words[1], words[0]))[0]


def test_delta_current_poll_expands_500c_to_three_phase_block(monkeypatch):
    monkeypatch.setattr(config, "METER_MODEL", "inepro_pro2")
    regs = build_inepro_pro2(
        {"u1": 230.0, "i1": 19.58, "p_total": 4.5},
        "cdab",
    )
    monkeypatch.setattr(dr_client, "get_register_map", lambda: regs)

    response = dr_client.handle_rtu_request(_request(0x500C, 2))

    assert response is not None
    assert len(response) == 17
    assert response[:3] == bytes.fromhex("01 03 0C")
    assert response[3:7] == bytes.fromhex("A3 D7 41 9C")
    assert response[7:15] == b"\x00" * 8
    assert _decode_cdab((0xA3D7, 0x419C)) == pytest.approx(19.58, abs=1e-5)
    assert response[-2:] == struct.pack("<H", modbus_crc(response[:-2]))


def test_delta_voltage_poll_expands_5000_to_three_phase_block(monkeypatch):
    monkeypatch.setattr(config, "METER_MODEL", "inepro_pro2")
    regs = build_inepro_pro2({"u1": 230.0, "i1": 0.0}, "cdab")
    monkeypatch.setattr(dr_client, "get_register_map", lambda: regs)

    response = dr_client.handle_rtu_request(_request(0x5000, 2))

    assert response is not None
    assert len(response) == 17
    assert response[:3] == bytes.fromhex("01 03 0C")
    assert response[3:7] == bytes.fromhex("00 00 43 66")
    assert response[7:15] == b"\x00" * 8


def test_delta_active_power_remains_single_float(monkeypatch):
    monkeypatch.setattr(config, "METER_MODEL", "inepro_pro2")
    regs = build_inepro_pro2({"p_total": 4.5}, "cdab")
    monkeypatch.setattr(dr_client, "get_register_map", lambda: regs)

    response = dr_client.handle_rtu_request(_request(0x5012, 2))

    assert response is not None
    assert len(response) == 9
    assert response[2] == 4
    assert _decode_cdab((
        struct.unpack(">H", response[3:5])[0],
        struct.unpack(">H", response[5:7])[0],
    )) == pytest.approx(4.5, abs=1e-6)
