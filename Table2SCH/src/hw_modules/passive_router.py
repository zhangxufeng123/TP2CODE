# filepath: src/hw_modules/passive_router.py
import json

class PassiveRouter:
    @staticmethod
    def process(pin_context, res_manager, grouped_modules):
        """
        解析 Testplan 中定义的无源器件规则，并注入到对应的渲染组中。
        支持单一电阻、电容，以及针对部分放电测试等高频场景的 RC Snubber 网络。
        """
        # 从 pin_mapping 的当前行中提取 Passives 配置
        # 期望格式为 JSON 字符串，例如: 
        # '[{"type": "R", "val": "100k", "net_pos": "PIN_VIN", "net_neg": "FL_S1"}]'
        passives_str = pin_context.pin_row.get("Passives", "").strip()
        if not passives_str:
            return

        try:
            passive_items = json.loads(passives_str)
            if isinstance(passive_items, dict):
                passive_items = [passive_items] # 兼容单体字典
        except json.JSONDecodeError:
            print(f"⚠️ 解析引脚 {pin_context.logical_net} 的 Passives 字段失败: {passives_str}")
            return

        for item in passive_items:
            comp_type = item.get("type", "").upper()
            val = item.get("val", "DNP")
            
            # 默认连接策略：正端接当前逻辑网络，负端接当前 Site 的仪器地
            pos_pin = item.get("net_pos", pin_context.logical_net)
            neg_pin = item.get("net_neg", f"FL_{pin_context.sheet_id}")

            if comp_type == "R":
                r_ref = res_manager.comp.get_next("R")
                grouped_modules["Resistor"].append({
                    "@R1@": r_ref,               # 替换器件编号
                    "@10k@": val,                # 替换器件阻值 (匹配模板的 Value)
                    "@Pos_Pin@": pos_pin,        # 替换正端网络
                    "@Neg_Pin@": neg_pin         # 替换负端网络
                })

            elif comp_type == "C":
                c_ref = res_manager.comp.get_next("C")
                grouped_modules["Capacitor"].append({
                    "@C1@": c_ref,
                    "@4.7uF@": val,              # 替换电容容值
                    "@Pos_Pin@": pos_pin,
                    "@Neg_Pin@": neg_pin
                })
                
            # 高级应用：RC Snubber 或 RC 滤波网络
            elif comp_type == "RC_SNUBBER":
                r_val = item.get("r_val", "10R")
                c_val = item.get("c_val", "1nF")
                mid_net = f"SNUBBER_MID_{pin_context.logical_net}"
                
                # 分配 R 和 C
                r_ref = res_manager.comp.get_next("R")
                c_ref = res_manager.comp.get_next("C")
                
                # R 连接 目标网络 和 中间节点
                grouped_modules["Resistor"].append({
                    "@R1@": r_ref, "@10k@": r_val, 
                    "@Pos_Pin@": pos_pin, "@Neg_Pin@": mid_net
                })
                # C 连接 中间节点 和 地
                grouped_modules["Capacitor"].append({
                    "@C1@": c_ref, "@4.7uF@": c_val, 
                    "@Pos_Pin@": mid_net, "@Neg_Pin@": neg_pin
                })