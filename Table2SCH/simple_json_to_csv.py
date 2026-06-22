#!/usr/bin/env python3
"""
简化版本：从JSON生成CSV配置，然后使用现有debug_gen.py
"""

import json
import csv
import re
from pathlib import Path

def extract_pins_and_passives(json_file: str) -> dict:
    """从JSON中提取引脚和被动元件信息"""

    with open(json_file, 'r', encoding='utf-8') as f:
        json_data = json.load(f)

    # 提取引脚顺序
    pin_order_str = json_data.get("pin_order", "")
    valid_pins = []
    if pin_order_str:
        for p in pin_order_str.split(','):
            parts = p.strip().split()
            if len(parts) >= 2:
                valid_pins.append(parts[1].strip())

    pin_dict = {}
    passives_list = []

    def parse_value(val_str: str):
        """解析数值"""
        match = re.match(r"([-+]?\d*\.?\d+)([a-zA-Z]+)", val_str.strip())
        if not match:
            return 0.0, val_str
        val, unit = float(match.group(1)), match.group(2)
        return val, val_str

    # 解析测试记录
    for item in json_data.get("records", []):
        if len(item) < 4:
            continue
        code = item[3]

        # 提取浮动引脚
        for flt_block in re.findall(r'Float\[(.*?)\]', code):
            for pin in flt_block.split(','):
                pin = pin.strip()
                if pin in valid_pins:
                    if pin not in pin_dict:
                        pin_dict[pin] = {'Is_Float': False}
                    pin_dict[pin]['Is_Float'] = True

        # 提取被动元件
        for c_block in re.findall(r'Connect\[(.*?)\]', code):
            for expr in c_block.split(','):
                if '=' in expr:
                    pins_part, val_part = expr.split('=', 1)
                    pins_part, val_part = pins_part.strip(), val_part.strip()
                    if '-' in pins_part:
                        try:
                            p1, p2 = [p.strip() for p in pins_part.split('-')]
                            if p1 in valid_pins and p2 in valid_pins:
                                part_type = 'C' if 'F' in val_part.upper() else 'R'
                                passives_list.append({
                                    'part': part_type,
                                    'value': val_part,
                                    'pins': [p1, p2]
                                })
                        except ValueError:
                            pass

    return {
        'pins': valid_pins,
        'pin_specs': pin_dict,
        'passives': passives_list
    }

def generate_csv_config(json_file: str, output_csv: str):
    """生成CSV配置文件"""

    print("🔍 解析JSON测试计划...")
    json_data = extract_pins_and_passives(json_file)

    # 生成CSV配置
    with open(output_csv, 'w', encoding='utf-8') as f:
        writer = csv.writer(f)

        # 项目元数据
        writer.writerow(['# ====== PROJECT SETUP METADATA ======'])
        writer.writerow(['project_name', 'STS8300_LB_from_JSON'])
        writer.writerow(['site_num', '4'])
        writer.writerow(['schema_version', '1.0'])
        writer.writerow(['default_package', '0603'])
        writer.writerow(['default_voltage', '50V'])
        writer.writerow(['default_tolerance', '1%'])
        writer.writerow(['ate_platform', 'STS8300_A28D4'])
        writer.writerow(['component_overrides', "{'SOCKET_PATH': 'Sch_lib/sockets/JW_Contator.kicad_sym', 'SOCKET_NAME': 'FTD_PP_25C_DFN4X4X0.75-10'}"])
        writer.writerow(['Hardware Config', 'Sch_lib/platforms/sts8300_slot.xlsx'])

        # 引脚映射表头
        writer.writerow([])
        writer.writerow(['# ====== PIN MAPPING ======'])
        writer.writerow(['Display Pin', 'Hidden F/S Mapping', 'Logical Net', 'Resource Types',
                        'Channel Allocations', 'Connect Type', 'Active Circuits',
                        'Passive Circuits (Parsed)', 'Params'])

        # 引脚数据
        print(f"处理引脚数据: {len(json_data['pins'])} 个引脚")
        for i, pin in enumerate(json_data['pins'], 1):
            pin_spec = json_data['pin_specs'].get(pin, {})

            # 确定连接类型
            if pin_spec.get('Is_Float', False):
                connect_type = "NC"
                active_circuits = ""
            else:
                connect_type = "Kelvin"  # 默认用Kelvin连接
                active_circuits = "ChargeRelease"

            # 资源分配
            resource_type = "ACM200" if i <= 2 else "FXVIe"

            # 查找该引脚的被动元件
            pin_passives = []
            for p in json_data['passives']:
                if pin in p['pins']:
                    pin_passives.append(p)

            # 处理被动元件格式
            passive_str = "{PASSIVES:[]}"
            if pin_passives:
                passive_items = []
                for p in pin_passives:
                    passive_items.append(f"{{'part':'{p['part']}','value':'{p['value']}','pins':{p['pins']}}}")
                passive_str = f"{{PASSIVES:[{','.join(passive_items)}]}}"

            writer.writerow([
                f"{i}F/S ({pin})",
                f"{{'F':'{i}F','S':'{i}S'}}",
                pin,
                resource_type,
                f"Site1({resource_type}[S{i}_CH0]) | Site2({resource_type}[S{i+4}_CH0]) | Site3({resource_type}[S{i+8}_CH0]) | Site4({resource_type}[S{i+12}_CH0])",
                connect_type,
                active_circuits,
                passive_str,
                f"{{\"{resource_type}\":{{\"GROUP_ID\":\"{resource_type}_G{i}\"}},\"{active_circuits}\":{{\"GROUP_ID\":\"CR_Group{i}\",\"VCC_NET\":\"+5V_VDD\"}}}}"
            ])

        # 参数模板
        writer.writerow([])
        writer.writerow(['# ====== PARAM DICTIONARY TEMPLATE ======'])
        writer.writerow(['Module_Category', 'Module_Name', 'Parameter_Key', 'Input_Type',
                        'Description', 'Example_Placeholder'])

    print(f"✅ CSV配置文件已生成: {output_csv}")
    print(f"📊 统计信息:")
    print(f"   - 引脚数量: {len(json_data['pins'])}")
    print(f"   - 被动元件: {len(json_data['passives'])}")

def main():
    """主函数"""
    json_file = Path("FT_Test_Plan_JSON_2.json")
    output_csv = Path("STS8300_LB_from_JSON.csv")

    if not json_file.exists():
        print(f"❌ JSON文件不存在: {json_file}")
        return

    try:
        # 生成CSV配置
        generate_csv_config(str(json_file), str(output_csv))

        print(f"\n✅ 生成完成！")
        print(f"📁 CSV文件: {output_csv}")
        print(f"💡 现在可以使用以下命令生成原理图:")
        print(f"   python src/debug_gen.py {output_csv}")

    except Exception as e:
        print(f"❌ 生成失败: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if output_csv.exists():
            print(f"✅ CSV文件已创建: {output_csv}")
        else:
            print(f"❌ CSV文件未创建")

if __name__ == "__main__":
    main()