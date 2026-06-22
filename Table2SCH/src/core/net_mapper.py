# filepath: src/core/net_mapper.py
import re
from types import SimpleNamespace
from .net_naming import NetNamingManager
from .resource_manager import ComponentAllocator, RelayPacker
from .net_mapper_context import PinContext

# --- 导入所有独立的硬件模块 (插件注册表) ---
from hw_modules.instrument_router import InstrumentRouter
from hw_modules.ground_ties import GroundTiesModule
from hw_modules.charge_release import ChargeReleaseModule
from hw_modules.opa189 import OPA189Module
# from hw_modules.opa145 import OPA145Module       # 示例：如果你已经拆分了 OPA145, 就取消这行注释
# from hw_modules.buf634 import BUF634Module     # 示例
# from hw_modules.sn74 import SN74Module          # 示例
# from hw_modules.tps_ldo import TPSLDOModule       # 示例


class NetMapper:
    
    # 🌟 核心修复: 在这里注册所有你需要用到的插件！
    # 执行顺序很重要：先路由仪器，再挂载电路。
    REGISTERED_PLUGINS = [
        InstrumentRouter,
        ChargeReleaseModule,
        OPA189Module,
        # OPA145Module, # 示例：取消注释以启用
        # BUF634Module, # 示例
        # SN74Module,   # 示例
        # TPSLDOModule, # 示例
    ]

    @staticmethod
    def build_site_modules(pin_mapping, site_idx, sheet_id, cbit_counters, mux_eng_exists):
        
        # --- 初始化 ---
        grouped_modules = {
            "Kelvin": [], "ChargeRelease": [], "Relay_Direct": [], "Relay_MUX_Shared": [], 
            "FH_SH_Shorts": [], "Hardwire": [], "BUF634A_SOP8": [], "OPA145_INA141": [], 
            "OPA189": [], "SN74LVC2G17DBVR": [], "TPS78401DRVR_3.3V": [],
            "Relay_Coils": [], "Ground_Ties": [],
            # 👇 新增初始化
            "Resistor": [], "Capacitor": []
        }
        
        res_manager = SimpleNamespace(
            comp = ComponentAllocator(sheet_id),
            relay = RelayPacker(sheet_id)
        )
        
        global_state = {
            'placed_shared_groups': set(),
            'placed_qtmu_buses': set(),
            'used_instruments': set(),
            'mux_eng_exists': mux_eng_exists,
            'sys_5v': f"S{'34' if site_idx in [1, 2] else '36'}_J+5V"
        }

        # --- 遍历Pin，分发任务给插件，同时收集被动元件 ---
        for pin in pin_mapping:
            pin_context = PinContext(pin, site_idx, sheet_id, global_state)

            # 收集用到的仪器
            for net_val in pin_context.chan_map.values():
                m = re.match(r'^(S\d+_[A-Za-z0-9]+)_', str(net_val))
                if m: global_state['used_instruments'].add(m.group(1))

            # 收集属于当前站点的被动元件
            allocations = pin.channel_allocations
            passives = pin.passive_circuits
            if f"Site{site_idx}" in allocations and passives:
                for passive in passives:
                    if passive.part == "C":  # 电容B
                        # 生成正确的电容位号
                        # c_counter = len([p for p in grouped_modules.get("Capacitor", []) if p.get("part") == "C"]) + 1
                        # cap_ref = res_manager.comp.get_next("C"),
                        # 使用与系统中ChargeRelease等模块相同的模板格式
                        cap_dict = {
                            # 模板替换字段 - 使用@...@格式（与现有模块一致）
                            "@C1@": res_manager.comp.get_next("C"),  # 电容位号
                            "@VALUE@": passive.value or "100nF",  # 电容值
                            # 根据引脚连接设置网络标签
                            "@Pos_Pin@": passive.pins[0] if len(passive.pins) > 0 else "GND",
                            "@Neg_Pin@": passive.pins[1] if len(passive.pins) > 1 else "GND",
                            "@INTERSHEET_REFS@": "",  # 系统将处理的占位符
                            # 基础信息
                            "part": "C",
                            "value": passive.value or "100nF",
                            "pins": passive.pins or [],
                            "pin_net": pin.logical_net,
                            "site": site_idx
                        }

                        grouped_modules["Capacitor"].append(cap_dict)
                        # print(f"  🎯 生成电容 {cap_ref}: 值={passive.value}, 引脚={passive.pins}")

            for plugin in NetMapper.REGISTERED_PLUGINS:
                plugin.process(pin_context, res_manager, grouped_modules)

        # --- 循环结束，统一结算 ---
        GroundTiesModule.generate_all(global_state['used_instruments'], grouped_modules)
        
        # 生成继电器线圈
        cbit_slot = "34" if site_idx in [1, 2] else "36"
        start_cbit_idx = 0 if site_idx % 2 != 0 else 64  
        for i in range(1, res_manager.relay.k_idx):
            grouped_modules["Relay_Coils"].append({
                "@K1@": f"K{i}_{sheet_id}A", 
                "@D1@": f"D{i}_Coil_{sheet_id}",
                "@R1@": f"R{i}_Coil_{sheet_id}", "@C1@": f"C{i}_Coil_{sheet_id}",   
                "@CBIT1@": f"S{cbit_slot}_CBit{start_cbit_idx + i - 1}", 
                "@5V@": global_state['sys_5v'], "@FL@": f"FL_{sheet_id}",
                '"AGND"': f'"FL_{sheet_id}"', '"GND"': f'"FL_{sheet_id}"',
            "Resistor": [], "Capacitor": [] # 👈 别忘了在这里初始化这两个空列表
            })
            
        cbit_counters[cbit_slot] = start_cbit_idx + (res_manager.relay.k_idx - 1)
        return grouped_modules