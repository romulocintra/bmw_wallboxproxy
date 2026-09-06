from typing import Callable, Dict
from modbus_codec import float_to_words, to_float32_safe

RegisterEncoder = Callable[[float], tuple[int, ...]]
def _float_encoder(word_order: str) -> RegisterEncoder:
    def encode(value: float) -> tuple[int, ...]: return float_to_words(to_float32_safe(value), word_order)
    return encode
def _scaled_u32(scale: float) -> RegisterEncoder:
    def encode(value: float) -> tuple[int, ...]:
        raw=min(max(0,int(round(float(value)/scale))),0xFFFFFFFF); return ((raw>>16)&0xFFFF,raw&0xFFFF)
    return encode
def _scaled_s32(scale: float) -> RegisterEncoder:
    def encode(value: float) -> tuple[int, ...]:
        raw=max(-0x80000000,min(int(round(float(value)/scale)),0x7FFFFFFF))&0xFFFFFFFF; return ((raw>>16)&0xFFFF,raw&0xFFFF)
    return encode
def _put_float(regs: Dict[int,int], enc: RegisterEncoder, addr:int, value:float)->None:
    hi,lo=enc(value); regs[addr],regs[addr+1]=hi,lo
def _put_u16(regs: Dict[int,int], addr:int, value:int)->None: regs[addr]=int(value)&0xFFFF
def _value(values:dict,name:str,default:float=0.0)->float: return float(values.get(name,default))

def _inepro_energy_values(values:dict)->dict[int,float]:
    return {0x6000:_value(values,"e_total"),0x6002:0.0,0x6004:0.0,0x6006:0.0,0x6008:0.0,0x600A:0.0,0x600C:_value(values,"e_import"),0x600E:0.0,0x6010:0.0,0x6012:0.0,0x6014:0.0,0x6016:0.0,0x6018:_value(values,"e_export"),0x601A:0.0,0x601C:0.0,0x601E:0.0,0x6020:0.0,0x6022:0.0,0x6024:0.0,0x6026:0.0,0x6028:0.0,0x602A:0.0,0x602C:0.0,0x602E:0.0,0x6030:0.0,0x6032:0.0,0x6034:0.0,0x6036:0.0,0x6038:0.0,0x603A:0.0,0x603C:0.0,0x603E:0.0,0x6040:0.0,0x6042:0.0,0x6044:0.0,0x6046:0.0}

def build_inepro_pro380(values:dict,word_order:str)->Dict[int,int]:
    enc=_float_encoder(word_order); regs={}; fields={0x5000:"voltage_avg",0x5002:"u1",0x5004:"u2",0x5006:"u3",0x5008:"freq",0x500A:"current_total",0x500C:"i1",0x500E:"i2",0x5010:"i3",0x5012:"p_total",0x5014:"p1",0x5016:"p2",0x5018:"p3",0x501A:"q_total",0x501C:"q1",0x501E:"q2",0x5020:"q3",0x5022:"s_total",0x5024:"s1",0x5026:"s2",0x5028:"s3",0x502A:"pf_total",0x502C:"pf1",0x502E:"pf2",0x5030:"pf3"}
    for addr,name in fields.items(): _put_float(regs,enc,addr,_value(values,name))
    for addr,value in _inepro_energy_values(values).items(): _put_float(regs,enc,addr,value)
    regs[0x6048]=0; _put_float(regs,enc,0x6049,0.0); return regs

def build_inepro_pro2(values:dict,word_order:str)->Dict[int,int]:
    """Dedicated single-phase Inepro PRO2-Mod map; PRO2 FLOAT32 values are ABCD."""
    enc=_float_encoder("abcd"); regs={}
    for addr,value in ((0x4000,0),(0x4001,0),(0x4002,0),(0x4003,1),(0x4004,9600),(0x400B,100),(0x400F,1),(0x4010,10),(0x4011,1),(0x4012,ord("F")),(0x4015,0),(0x4016,0),(0x4017,1),(0x401B,0),(0x401C,0),(0x401D,0),(0x401E,0)): _put_u16(regs,addr,value)
    for addr in (0x4005,0x4007,0x4009): _put_float(regs,enc,addr,0.0)
    _put_float(regs,enc,0x400D,1000.0)
    for addr,name in ((0x5000,"voltage_avg"),(0x5002,"u1"),(0x5008,"freq"),(0x500A,"current_total"),(0x500C,"i1"),(0x5012,"p_total"),(0x501A,"q_total"),(0x5022,"s_total"),(0x502A,"pf_total")): _put_float(regs,enc,addr,_value(values,name))
    for addr in (0x5004,0x5006,0x500E,0x5010,0x5014,0x5016,0x5018,0x501C,0x501E,0x5020,0x5024,0x5026,0x5028,0x502C,0x502E,0x5030): _put_float(regs,enc,addr,0.0)
    for addr,value in _inepro_energy_values(values).items(): _put_float(regs,enc,addr,value)
    regs[0x6048]=1; _put_float(regs,enc,0x6049,0.0); return regs

def _build_janitza_b_series(values:dict,single_phase:bool)->Dict[int,int]:
    """Janitza B21/B23 0x5Bxx map: UINT32/INT32 values, frequency is one UINT16."""
    regs={}; u32_01,u32_001,s32_001=_scaled_u32(0.1),_scaled_u32(0.01),_scaled_s32(0.01)
    u1,u2,u3=_value(values,"u1"),_value(values,"u2"),_value(values,"u3"); i1,i2,i3=_value(values,"i1"),_value(values,"i2"),_value(values,"i3"); p1,p2,p3=_value(values,"p1"),_value(values,"p2"),_value(values,"p3")
    if single_phase: u2=u3=i2=i3=p2=p3=0.0
    for addr,val in ((0x5B00,u1),(0x5B02,u2),(0x5B04,u3),(0x5B06,0.0),(0x5B08,0.0),(0x5B0A,0.0)):
        hi,lo=u32_01(val); regs[addr],regs[addr+1]=hi,lo
    for addr,val in ((0x5B0C,i1),(0x5B0E,i2),(0x5B10,i3),(0x5B12,0.0)):
        hi,lo=u32_001(val); regs[addr],regs[addr+1]=hi,lo
    for addr,val in ((0x5B14,_value(values,"p_total")*1000),(0x5B16,p1*1000),(0x5B18,p2*1000),(0x5B1A,p3*1000),(0x5B1C,_value(values,"q_total")*1000),(0x5B1E,0.0),(0x5B20,0.0),(0x5B22,0.0),(0x5B24,_value(values,"s_total")*1000),(0x5B26,abs(p1)*1000),(0x5B28,abs(p2)*1000),(0x5B2A,abs(p3)*1000)):
        hi,lo=s32_001(val); regs[addr],regs[addr+1]=hi,lo
    regs[0x5B2C]=int(round(_value(values,"freq")/0.01))&0xFFFF
    return regs

def build_janitza_b23(values:dict,word_order:str="abcd")->Dict[int,int]: return _build_janitza_b_series(values,False)
def build_janitza_b21(values:dict,word_order:str="abcd")->Dict[int,int]: return _build_janitza_b_series(values,True)
METER_BUILDERS={"inepro_pro380":build_inepro_pro380,"inepro_pro2":build_inepro_pro2,"janitza_b23":build_janitza_b23,"janitza_b21":build_janitza_b21}
def build_register_map(model:str,values:dict,word_order:str="abcd")->Dict[int,int]:
    try: return METER_BUILDERS[model](values,word_order)
    except KeyError as exc: raise ValueError(f"Unsupported meter model: {model}") from exc
