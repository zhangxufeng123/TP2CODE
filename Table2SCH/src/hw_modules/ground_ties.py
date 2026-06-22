# filepath: src/hw_modules/ground_ties.py
from .base_template_module import TemplateHWModule

class GroundTiesModule(TemplateHWModule):
    @classmethod
    def get_module_name(cls):
        return "Ground_Ties"

    @classmethod
    def process(cls, ctx, res_manager, grouped_modules):
        """
        这个模块在遍历 Pin 时不做任何操作，
        它的主要逻辑在 generate_all 方法中，在所有 Pin 处理完后统一调用。
        """
        pass

    @staticmethod
    def generate_all(used_instruments, grouped_modules):
        """
        根据收集到的所有使用过的仪器，生成需要连接到悬浮地的 FL/SL 列表。
        """
        FL_SL_SUFFIXES = {
            "ACM200": ["FL(0-11)", "FL(12-23)", "SL(0-5)", "SL(6-11)", "SL(12-17)", "SL(18-23)"],
            "FPVIE":  ["FL0", "FL1", "SL0", "SL1"],
            "FXVIE":  ["FL(0-5)", "FL(6-11)", "SL(0-5)", "SL(6-11)"]
        }
        
        ground_ties_to_add = set()
        for inst in used_instruments:  
            parts = inst.split('_')
            if len(parts) >= 2:
                inst_type = parts[1].upper()
                if inst_type in FL_SL_SUFFIXES:
                    for suffix in FL_SL_SUFFIXES[inst_type]:
                        ground_ties_to_add.add(f"{parts[0]}_{parts[1]}_{suffix}")
                        
        for net in sorted(ground_ties_to_add):
            grouped_modules["Ground_Ties"].append({"NET": net})