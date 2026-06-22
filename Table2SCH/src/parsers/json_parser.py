import re
import csv
import json
import os

def parse_value(val_str):
    """提取数值和原始字符串"""
    match = re.match(r"([-+]?\d*\.?\d+)([a-zA-Z]+)", val_str.strip())
    if not match: return 0.0, val_str
    
    val, unit = float(match.group(1)), match.group(2)
    multiplier = 1.0
    if unit in ['mV', 'mA', 'ms']: multiplier = 1e-3
    elif unit in ['uA', 'us']: multiplier = 1e-6
    elif unit in ['nA', 'ns']: multiplier = 1e-9
    
    return abs(val * multiplier), val_str

def get_part_type(val_str):
    """根据单位特征推断被动元器件类型"""
    val_upper = val_str.upper()
    if 'F' in val_upper: return 'C'
    if 'OHM' in val_upper or 'R' in val_upper: return 'R'
    if 'H' in val_upper: return 'L'
    return 'Unknown'

def extract_pin_specs_to_csv(json_data, output_path):
    """提取数据并使用 CSV 流式写入混合结构"""
    pin_order_str = json_data.get("pin_order", "")
    valid_pins = []
    if pin_order_str:
        for p in pin_order_str.split(','):
            parts = p.strip().split()
            if len(parts) >= 2:
                valid_pins.append(parts[1].strip())
    
    pin_dict = {}
    global_mt_pairs = set()
    global_passives = set()

    def init_pin(pin):
        if pin not in pin_dict:
            pin_dict[pin] = {
                'Force_V_Max': 0.0, 'Force_V_Str': '-',
                'Force_I_Max': 0.0, 'Force_I_Str': '-',
                'Is_Float': False
            }

    # 1. 数据解析阶段
    for item in json_data.get("records", []):
        if len(item) < 4: continue
        code = item[3]
        
        # 提取 FV / FI
        for f_type in ['FV', 'FI']:
            for f_block in re.findall(rf'{f_type}\[(.*?)\]', code):
                for expr in f_block.split(','):
                    if '=' in expr:
                        pin, val_str = expr.split('=', 1)
                        pin = pin.strip()
                        if pin in valid_pins:
                            val_num, val_orig = parse_value(val_str)
                            init_pin(pin)
                            if f_type == 'FV' and val_num > pin_dict[pin]['Force_V_Max']:
                                pin_dict[pin]['Force_V_Max'] = val_num
                                pin_dict[pin]['Force_V_Str'] = val_orig
                            elif f_type == 'FI' and val_num > pin_dict[pin]['Force_I_Max']:
                                pin_dict[pin]['Force_I_Max'] = val_num
                                pin_dict[pin]['Force_I_Str'] = val_orig

        # 提取 Is_Float
        for flt_block in re.findall(r'Float\[(.*?)\]', code):
            for pin in flt_block.split(','):
                pin = pin.strip()
                if pin in valid_pins:
                    init_pin(pin)
                    pin_dict[pin]['Is_Float'] = True

        # 提取 MT 测量管脚对
        for mt_block in re.findall(r'MT\[(.*?)\]', code):
            pins_in_mt = re.findall(r'\(([a-zA-Z0-9_]+)=', mt_block)
            pins_in_mt = [p.strip() for p in pins_in_mt if p.strip() in valid_pins]
            if len(pins_in_mt) >= 2:
                p1, p2 = pins_in_mt[0], pins_in_mt[1]
                global_mt_pairs.add(f"{p1}-{p2}")

        # 提取 Connect 阻容网络挂载
        for c_block in re.findall(r'Connect\[(.*?)\]', code):
            for expr in c_block.split(','):
                if '=' in expr:
                    pins_part, val_part = expr.split('=', 1)
                    val_part = val_part.strip()
                    if '-' in pins_part:
                        try:
                            p1, p2 = [p.strip() for p in pins_part.split('-')]
                            if p1 in valid_pins and p2 in valid_pins:
                                part_type = get_part_type(val_part)
                                device_str = f"{{part:'{part_type}', value:'{val_part}', pins:['{p1}', '{p2}']}}"
                                global_passives.add(device_str)
                        except ValueError:
                            pass

    # 2. 文件写入阶段 (打破 DataFrame 限制)
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        
        # Block 1: 物理管脚区
        writer.writerow(['Pin', 'Force_V_Max', 'Force_I_Max', 'Is_Float'])
        for pin in valid_pins:
            if pin in pin_dict:
                d = pin_dict[pin]
                writer.writerow([
                    pin,
                    d['Force_V_Str'],
                    d['Force_I_Str'],
                    'Yes' if d['Is_Float'] else '-'
                ])
            else:
                writer.writerow([pin, '-', '-', '-'])
                
        # 空两行作为分隔
        writer.writerow([])
        writer.writerow([])
        
        # Block 2: MT_Pair 区 (横向扩展)
        mt_row = ['MT_Pair'] + sorted(list(global_mt_pairs))
        writer.writerow(mt_row)
        
        # 空两行作为分隔
        writer.writerow([])
        writer.writerow([])
        
        # Block 3: Passive_Comp 区 (横向扩展，csv 模块会自动处理内部双引号)
        passive_row = ['Passive_Comp'] + sorted(list(global_passives))
        writer.writerow(passive_row)

if __name__ == "__main__":
    base_dir = r"C:\Users\11271\Desktop\Table2SCH"
    json_file_path = os.path.join(base_dir, "FT_Test_Plan_JSON_2.json")
    output_csv_path = os.path.join(base_dir, "Final_Pin_Specs_v4.csv")
    
    with open(json_file_path, "r", encoding="utf-8") as f:
        raw_json_data = json.load(f)
        
    extract_pin_specs_to_csv(raw_json_data, output_csv_path)
    print("✅ 混合格式 CSV 写入完成！MT_Pair 和 Passive_Comp 已完美横向展开。")