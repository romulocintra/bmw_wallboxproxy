import struct
import sys
from pathlib import Path

PACKAGE_DIR = Path(__file__).resolve().parents[1] / "bmw_wallboxproxy"
if str(PACKAGE_DIR) not in sys.path:
    sys.path.insert(0, str(PACKAGE_DIR))

from meter_models import build_inepro_pro2


def _words(regs, addr):
    return regs[addr], regs[addr + 1]


def test_pro2_float_word_order_is_configurable():
    values = {"u1": 230.0, "voltage_avg": 230.0, "freq": 50.0, "i1": 19.25, "current_total": 19.25}
    abcd = build_inepro_pro2(values, "abcd")
    cdab = build_inepro_pro2(values, "cdab")

    assert _words(abcd, 0x500C) == (0x419A, 0x0000)
    assert _words(cdab, 0x500C) == (0x0000, 0x419A)
    assert _words(abcd, 0x500C) != _words(cdab, 0x500C)
