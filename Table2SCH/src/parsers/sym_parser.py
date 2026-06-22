# src/parsers/sym_parser.py
import re

class KiCadSymParser:
    @staticmethod
    def parse_file(filepath, target_symbol_name):
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        # 1. 准确定位目标 symbol 的起始位置
        start_str = f'(symbol "{target_symbol_name}"'
        start_idx = content.find(start_str)
        
        if start_idx == -1:
            raise ValueError(f"在文件中找不到名为 '{target_symbol_name}' 的器件。")

        # 2. 括号匹配算法提取块
        bracket_count = 0
        end_idx = -1
        for i in range(start_idx, len(content)):
            if content[i] == '(':
                bracket_count += 1
            elif content[i] == ')':
                bracket_count -= 1
                if bracket_count == 0:
                    end_idx = i + 1
                    break
        
        if end_idx == -1:
            raise ValueError("KiCad 文件格式损坏，括号不匹配，解析失败。")
            
        sym_block = content[start_idx:end_idx]

        # 3. 提取所有的引脚 (Pin)
        pin_pattern = r'\(pin.*?\(name\s+"([^"]*)".*?\(number\s+"([^"]+)"'
        pins = re.findall(pin_pattern, sym_block, re.DOTALL | re.IGNORECASE)

        if not pins:
            raise ValueError(f"No pins found inside symbol '{target_symbol_name}'.")

        # 4. 智能 Kelvin 对匹配算法 (处理 1F/1S, VDD_F/VDD_S 等)
        pin_dict = {name.strip(): num for name, num in pins}
        logical_pads = {}
        processed_names = set()

        for name, num in pins:
            name = name.strip()
            if not name or name == "~":
                name = f"PIN_{num}"
                
            if name in processed_names:
                continue

            name_upper = name.upper()
            is_kelvin = False

            # 判断是否为 Kelvin 匹配
            if name_upper.endswith('F') or name_upper.endswith('S'):
                suffix = name_upper[-1]
                other_suffix = 'S' if suffix == 'F' else 'F'
                
                if name_upper.endswith('_F') or name_upper.endswith('_S'):
                    base_net = name[:-2]
                    other_name = base_net + '_' + other_suffix
                else:
                    base_net = name[:-1]
                    other_name = base_net + other_suffix

                matching_pin_name = next((n for n in pin_dict.keys() if n.upper() == other_name.upper()), None)

                if matching_pin_name:
                    logical_pads[base_net] = {"pins": {suffix: num, other_suffix: pin_dict[matching_pin_name]}}
                    processed_names.add(name)
                    processed_names.add(matching_pin_name)
                    is_kelvin = True
                    
            if not is_kelvin:
                logical_pads[name] = {"pins": {"Single": num}}
                processed_names.add(name)

        # ==========================================
        # 🌟 新增：对解析出的结果进行“自然升序排列”
        # ==========================================
        def natural_keys(text):
            """
            将字符串拆分成数字和字母，实现完美的数字升序 (例如 1, 2, 10, VDD)
            """
            return [int(c) if c.isdigit() else c.lower() for c in re.split(r'(\d+)', text)]

        # 根据字典的 key 进行排序，并重新构建一个有序的字典
        sorted_pads = {k: logical_pads[k] for k in sorted(logical_pads.keys(), key=natural_keys)}

        return sorted_pads