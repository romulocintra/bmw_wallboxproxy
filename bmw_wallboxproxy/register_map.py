from typing import Dict

from config import get_meter_model, get_test_mode
from meter_models import build_register_map as build_model_register_map
from state import get_float_word_order, get_phase_order, get_power_offset_override, latest_values, state_lock
from test_mode import next_test_values


def _apply_phase_order(order: str, a: float, b: float, c: float) -> tuple:
    idx=[int(x)-1 for x in order.split(",")]; src=(a,b,c); return src[idx[0]],src[idx[1]],src[idx[2]]


def _snapshot_output_values() -> dict:
    with state_lock: snap=latest_values.copy()
    def get(name,default=0.0): return float(snap.get(name,default))
    order=get_phase_order(); u1,u2,u3=_apply_phase_order(order,get("u1"),get("u2"),get("u3")); i1,i2,i3=_apply_phase_order(order,get("i1"),get("i2"),get("i3"))
    override=get_power_offset_override(); offset_kw=(override if override is not None else snap.get("power_offset",0.0))/1000.0
    p_total=get("p_total")/1000.0+offset_kw; p1,p2,p3=_apply_phase_order(order,get("p1")/1000.0+offset_kw/3,get("p2")/1000.0+offset_kw/3,get("p3")/1000.0+offset_kw/3)
    e_import,e_export=get("e_import_total"),get("e_export_total"); s_total=abs(p_total); s1,s2,s3=abs(p1),abs(p2),abs(p3)
    return {"voltage_avg":(u1+u2+u3)/3,"u1":u1,"u2":u2,"u3":u3,"freq":get("freq"),"current_total":i1+i2+i3,"i1":i1,"i2":i2,"i3":i3,"p_total":p_total,"p1":p1,"p2":p2,"p3":p3,"q_total":0.0,"q1":0.0,"q2":0.0,"q3":0.0,"s_total":s_total,"s1":s1,"s2":s2,"s3":s3,"pf_total":p_total/s_total if s_total else 0.0,"pf1":p1/s1 if s1 else 0.0,"pf2":p2/s2 if s2 else 0.0,"pf3":p3/s3 if s3 else 0.0,"e_total":e_import+e_export,"e_import":e_import,"e_export":e_export}


def get_output_values() -> dict: return _snapshot_output_values()


def _build_model_values(values: dict, model: str) -> dict:
    out=dict(values)
    if model in ("janitza_b21","janitza_b23"):
        for key in ("p_total","p1","p2","p3","s_total","s1","s2","s3"): out[key]=values[key]*1000.0
    if model in ("inepro_pro2","janitza_b21"):
        out["voltage_avg"]=values["u1"]; out["u2"]=out["u3"]=0.0; out["current_total"]=values["i1"]; out["i2"]=out["i3"]=0.0
        out["p_total"]=values["p1"]; out["p1"]=values["p1"]; out["p2"]=out["p3"]=0.0
        out["q_total"]=0.0; out["q1"]=out["q2"]=out["q3"]=0.0
        out["s_total"]=abs(values["p1"]); out["s1"]=abs(values["p1"]); out["s2"]=out["s3"]=0.0
        out["pf_total"]=values["pf1"]; out["pf1"]=values["pf1"]; out["pf2"]=out["pf3"]=0.0
    return out


def _apply_legacy_aliases(regs: Dict[int,int], alias_mode: str) -> Dict[int,int]:
    if alias_mode=="exact": return regs
    aliased=dict(regs); addresses=(0x5000,0x5002,0x5004,0x5006,0x5008,0x500A,0x500C,0x500E,0x5010,0x5012,0x5014,0x5016,0x5018,0x501A,0x501C,0x501E,0x5020,0x5022,0x5024,0x5026,0x5028,0x502A,0x502C,0x502E,0x5030,0x6000,0x6002,0x6004,0x6006,0x6008,0x600A,0x600C,0x600E,0x6010,0x6012,0x6014,0x6018,0x601A,0x601C,0x601E,0x6020,0x6022,0x6024,0x6026,0x6028,0x602A,0x602C,0x602E,0x6030,0x6032,0x6034,0x6036,0x6038,0x603A,0x603C,0x603E,0x6040,0x6042,0x6044,0x6046,0x6049)
    for addr in addresses:
        if addr not in regs or addr+1 not in regs: continue
        hi,lo=regs[addr],regs[addr+1]
        if alias_mode in ("alias_minus_1","alias_both"): aliased[addr-1],aliased[addr]=hi,lo
        if alias_mode in ("alias_plus_1","alias_both"): aliased[addr+1],aliased[addr+2]=hi,lo
    return aliased


def get_register_map() -> Dict[int,int]:
    model=get_meter_model(); values=next_test_values() if get_test_mode() else _snapshot_output_values()
    regs=build_model_register_map(model,_build_model_values(values,model),get_float_word_order())
    if model in ("inepro_pro380","inepro_pro2"): regs=_apply_legacy_aliases(regs,get_register_alias_mode())
    return regs
