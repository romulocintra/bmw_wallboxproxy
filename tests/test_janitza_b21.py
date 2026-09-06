import math

import register_map


def _u32(regs, addr):
    return (regs[addr] << 16) | regs[addr + 1]


def _s32(regs, addr):
    raw=_u32(regs,addr)
    return raw-0x100000000 if raw & 0x80000000 else raw


def test_b21_is_single_phase_with_documented_scaling(monkeypatch):
    monkeypatch.setattr(register_map,"get_meter_model",lambda:"janitza_b21")
    monkeypatch.setattr(register_map,"get_test_mode",lambda:False)
    monkeypatch.setattr(register_map,"latest_values",{
        "u1":230.0,"u2":231.0,"u3":232.0,"i1":16.21,"i2":2.0,"i3":3.0,
        "p_total":3728.5,"p1":3728.5,"p2":0.0,"p3":0.0,"freq":50.0,
        "e_import_total":100.0,"e_export_total":0.0,"power_offset":0.0,
    })
    monkeypatch.setattr(register_map,"get_power_offset_override",lambda:None)
    regs=register_map.get_register_map()
    assert _u32(regs,0x5B00)==2300
    assert _u32(regs,0x5B0C)==1621
    assert _s32(regs,0x5B14)==372850
    assert _s32(regs,0x5B16)==372850
    assert _u32(regs,0x5B02)==0
    assert _u32(regs,0x5B04)==0
    assert _u32(regs,0x5B0E)==0
    assert _u32(regs,0x5B10)==0


def test_b21_test_mode_matches_b_series_vectors(monkeypatch):
    monkeypatch.setattr(register_map,"get_meter_model",lambda:"janitza_b21")
    monkeypatch.setattr(register_map,"get_test_mode",lambda:True)
    from test_mode import reset_test_sequence
    reset_test_sequence(); regs=register_map.get_register_map()
    assert _u32(regs,0x5B00)==2300
    assert _u32(regs,0x5B0C)==0
    assert _s32(regs,0x5B14)==0


def test_b21_frequency_is_uint32_with_0_01_resolution(monkeypatch):
    monkeypatch.setattr(register_map,"get_meter_model",lambda:"janitza_b21")
    monkeypatch.setattr(register_map,"get_test_mode",lambda:False)
    monkeypatch.setattr(register_map,"latest_values",{"u1":230.0,"u2":0.0,"u3":0.0,"i1":1.0,"i2":0.0,"i3":0.0,"p_total":230.0,"p1":230.0,"p2":0.0,"p3":0.0,"freq":50.0,"e_import_total":0.0,"e_export_total":0.0,"power_offset":0.0})
    monkeypatch.setattr(register_map,"get_power_offset_override",lambda:None)
    regs=register_map.get_register_map()
    assert _u32(regs,0x5B2C)==5000
