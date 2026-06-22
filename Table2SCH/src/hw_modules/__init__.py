# 导入你的各个硬件模块

from .direct import DirectModule
from .active_circuits import (
    OPA145Buffer, 
    OPA235Amp, 
    INA141InstAmp, 
    SN74HC273Latch, 
    RelaySwitch
)

# 注册中心：将 GUI 上显示的字符串，映射到对应的 Python 类
ACTIVE_CIRCUIT_REGISTRY = {
    "OPA145_Buffer": OPA145Buffer,
    "OPA235_Amp": OPA235Amp,
    "INA141_InstAmp": INA141InstAmp,
    "SN74HC273_Latch": SN74HC273Latch,
    "Relay_Switch": RelaySwitch
}

def get_available_active_circuits():
    return list(ACTIVE_CIRCUIT_REGISTRY.keys())

def get_active_circuit_class(circuit_name):
    return ACTIVE_CIRCUIT_REGISTRY.get(circuit_name)