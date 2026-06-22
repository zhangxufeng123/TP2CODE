# filepath: src/hw_modules/charge_release.py
from .base_template_module import TemplateHWModule

# 🌟 把旧的 ChargeReleaseMapper 逻辑直接放在这里，作为静态方法工具
class ChargeReleaseMapper:
    @staticmethod
    def build_replace_dict(row_idx, sheet_id, base_net, ate_net, params_str):
        # 这个方法现在是 charge_release.py 内部的一个辅助工具
        # 你可以把之前在 net_mapper.py 里的旧逻辑粘贴到这里
        # 我先为你创建一个基础版本
        return {
            "@Socket_pin@": f"{base_net}_{sheet_id}",
            "@ATE_pin@": ate_net,
        }

class ChargeReleaseModule(TemplateHWModule):
    
    @classmethod
    def get_module_name(cls):
        return "ChargeRelease"
    
    @classmethod
    def process(cls, ctx, res_manager, grouped_modules):
        if cls.get_module_name() not in ctx.active_circuits:
            return
            
        if "GND" in ctx.logical_net.upper():
            return
        
        # 使用本文件内的 ChargeReleaseMapper
        cr_dict = ChargeReleaseMapper.build_replace_dict(
            res_manager.comp.counters['R'], 
            ctx.sheet_id, 
            ctx.base_net, 
            ctx.fallback_ate_f, 
            ctx.pin_data.parameters
        )
        
        cr_dict.update({
            "@Socket_pin@": ctx.primary_socket_net,
            '"AGND"': f'"{ctx.fl_net}"',
            '"GND"': f'"{ctx.fl_net}"',
            '"GND3"': f'"{ctx.fl_net}"',
            '"GNDREF"': f'"{ctx.fl_net}"',
            "@FL@": ctx.fl_net,
            "@K1@": res_manager.relay.get_switch(),
            "@R1@": res_manager.comp.get_next("R"),
            "@C1@": res_manager.comp.get_next("C"),
            "@D1@": res_manager.comp.get_next("D")
        })
        
        grouped_modules[cls.get_module_name()].append(cr_dict)