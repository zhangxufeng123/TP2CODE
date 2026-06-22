import re

class SmartPinMapper:
    @staticmethod
    def apply_rules(logical_pads: dict, tp_pins: list) -> list:
        """
        将 Symbol 的引脚与 TP 的引脚名对齐，并自动应用 ATE 硬件规则。
        """
        mapped_rows = []
        
        for i, (net_name, data) in enumerate(logical_pads.items()):
            pins_dict = data["pins"]
            is_kelvin_symbol = "F" in pins_dict and "S" in pins_dict
            primary_num = pins_dict.get("F", pins_dict.get("Single", "NC"))
            
            # 修复双 F 问题：剥离末尾自带的 F
            clean_num = str(primary_num)
            if is_kelvin_symbol and clean_num.upper().endswith('F'):
                clean_num = clean_num[:-1]
            
            # 从 TP 获取清洗后的名字
            tp_name = tp_pins[i] if i < len(tp_pins) else f"NC_{i}"
            tp_name_up = tp_name.upper()
            
            display_str = f"{clean_num} ({tp_name})" if not is_kelvin_symbol else f"{clean_num}F/S ({tp_name})"
            
            # ==========================================
            # 🧠 智能业务规则引擎 (V4 终极版)
            # ==========================================
            res_defaults = ["ACM200"] # 默认模拟通道
            conn_type = "Direct"      # 默认 Direct 连线
            active_circuits = []      # 默认无有源电路
            
            # 1. 特征识别
            is_power = bool(re.search(r'(VDD|VCC|PWR|VSYS|VBAT|VD\d+)', tp_name_up))
            is_gnd = "GND" in tp_name_up or "VSS" in tp_name_up
            is_i2c = "SDA" in tp_name_up or "SCL" in tp_name_up
            
            # 2. 规则应用
            if is_power or is_gnd:
                # 🌟 修复：无论是电源还是 GND，统统视为大电流 Power Pin
                # 统一分配 FPVIe 资源，走 Kelvin 连线，挂载 ChargeRelease 放电
                conn_type = "Kelvin"
                active_circuits = ["ChargeRelease"]
                res_defaults = ["FPVIe"] 
                    
            elif is_i2c:
                # I2C 引脚 (SDA/SCL) 需要数字通道读写，保留 ACM200
                res_defaults = ["ACM200", "DCM"]

            mapped_rows.append({
                "display_pin": display_str,
                "hidden_pin_dict": pins_dict,
                "logical_net": tp_name,
                "res_defaults": res_defaults,
                "conn_type": conn_type,
                "active_circuits": active_circuits,
                "params": "{}"
            })
            
        return mapped_rows