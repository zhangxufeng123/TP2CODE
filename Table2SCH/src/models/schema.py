import json  # 新增导入
from pydantic import BaseModel, Field
from typing import List, Dict, Optional

# 简化被动元件模型 - 仅保留必需字段
class PassiveComponent(BaseModel):
    part: str = Field("C", description="器件类型")
    value: str = Field(..., description="器件值")
    pins: List[str] = Field(..., description="连接脚位")

# 简化映射行模型 - 移除所有alias设置
class PinMappingRow(BaseModel):
    display_pin: str
    socket_pins_map: Dict[str, str] = {}
    logical_net: str
    resource_type: str
    channel_allocations: str = ""
    connect_type: str
    active_circuits: List[str] = []
    passive_circuits: List[PassiveComponent] = []
    parameters: Dict = {}

class ProjectInfo(BaseModel):
    project_name: str
    site_num: int
    schema_version: str = "1.0"
    default_package: str = "0603"
    default_voltage: str = "50V"
    default_tolerance: str = "1%"
    ate_platform: str
    component_overrides: Dict[str, str] = Field(default_factory=dict)

class Table2SchConfig(BaseModel):
    """整个项目的全局数据结构 (对应导出的 JSON)"""
    project_info: ProjectInfo
    hardware_config: str = ""  # 改为可选
    pin_template_mapping: List[PinMappingRow]
    
