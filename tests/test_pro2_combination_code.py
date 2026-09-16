import sys
from pathlib import Path

PACKAGE_DIR = Path(__file__).resolve().parents[1] / "bmw_wallboxproxy"
if str(PACKAGE_DIR) not in sys.path:
    sys.path.insert(0, str(PACKAGE_DIR))

import pro2_state


def test_pro2_default_combination_code_is_single_phase_l1():
    pro2_state.reset_state()
    assert pro2_state.get_register(0x400F) == 3


def test_pro2_combination_code_accepts_supported_values():
    pro2_state.reset_state()
    for value in (1, 2, 3, 4, 5):
        pro2_state.write_fc06(0x400F, value)
        assert pro2_state.get_register(0x400F) == value


def test_pro2_combination_code_rejects_unsupported_value():
    pro2_state.reset_state()
    for value in (0, 6, 9, 10, 65535):
        try:
            pro2_state.write_fc06(0x400F, value)
        except ValueError as exc:
            assert "combination code" in str(exc)
        else:
            raise AssertionError(f"unsupported combination code {value} should fail")
