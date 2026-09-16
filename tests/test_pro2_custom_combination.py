import pro2_state


def test_custom_combination_code_is_empty_by_default(monkeypatch):
    monkeypatch.delenv("CUSTOM_COMBINATION_CODE", raising=False)
    pro2_state.reset_state()
    assert pro2_state.get_register(0x400F) == 1


def test_custom_combination_code_accepts_decimal(monkeypatch):
    monkeypatch.setenv("CUSTOM_COMBINATION_CODE", "3")
    pro2_state.reset_state()
    assert pro2_state.get_register(0x400F) == 3
    assert pro2_state.snapshot()[0x400F] == 3


def test_custom_combination_code_accepts_hexadecimal(monkeypatch):
    monkeypatch.setenv("CUSTOM_COMBINATION_CODE", "0x0003")
    pro2_state.reset_state()
    assert pro2_state.get_register(0x400F) == 3


def test_custom_combination_code_is_fixed_for_writes(monkeypatch):
    monkeypatch.setenv("CUSTOM_COMBINATION_CODE", "0x0003")
    pro2_state.reset_state()
    pro2_state.write_fc06(0x400F, 3)
    assert pro2_state.get_register(0x400F) == 3

    try:
        pro2_state.write_fc06(0x400F, 1)
    except ValueError as exc:
        assert "fixed" in str(exc)
    else:
        raise AssertionError("expected custom combination code write to remain fixed")


def test_invalid_custom_combination_code_keeps_default(monkeypatch):
    monkeypatch.setenv("CUSTOM_COMBINATION_CODE", "not-a-number")
    pro2_state.reset_state()
    assert pro2_state.get_register(0x400F) == 1
