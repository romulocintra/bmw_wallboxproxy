import struct

import pytest


def _f32_from_words(hi: int, lo: int) -> float:
    return struct.unpack(">f", struct.pack(">HH", hi, lo))[0]


def test_latest_capture_is_only_l1_current_polling():
    """Regression fixture from the 2026-09-16 BMW Wallbox TCP capture."""
    request = bytes.fromhex("01 03 50 0C 00 02")
    responses = (
        bytes.fromhex("01 03 04 41 97 33 33 0b 06"),
        bytes.fromhex("01 03 04 41 98 e1 48 27 86"),
        bytes.fromhex("01 03 04 41 9a 66 66 65 aa"),
        bytes.fromhex("01 03 04 41 9a 51 ec f2 3d"),
    )
    assert request[2:4] == bytes.fromhex("50 0c")
    observed = []
    for response in responses:
        assert response[:3] == bytes.fromhex("01 03 04")
        observed.append(_f32_from_words(
            int.from_bytes(response[3:5], "big"),
            int.from_bytes(response[5:7], "big"),
        ))
    assert observed == pytest.approx([
        18.899999618530273,
        19.110000610351562,
        19.299997329711914,
        19.290000915527344,
    ], abs=5e-6)


def test_latest_capture_has_no_identity_poll():
    """The supplied steady-state capture contains no 0x4000 identity request."""
    captured_requests = [bytes.fromhex("01 03 50 0C 00 02")] * 4
    assert all(req[2:4] == bytes.fromhex("50 0c") for req in captured_requests)
    assert not any(req[2:4] == bytes.fromhex("40 00") for req in captured_requests)
