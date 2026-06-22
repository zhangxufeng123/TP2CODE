import os
import sys
import json
import csv
import ast
from typing import Dict, List

# ==========================================
# 动态加入 Python 环境变量
# ==========================================
src_dir = os.path.dirname(os.path.abspath(__file__))
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from models.schema import Table2SchConfig
from exporters.sch_generator import SchGenerator

def parse_passives(passive_str: str) -> List[Dict]:
    """安全解析被动元件数据"""
    if not passive_str or passive_str.strip() in ("", "{}", '"{}"'):
        return []

    try:
        # 清理JSON字符串中的双重引号
        cleaned = passive_str.replace('""', '"')

        # 有些被动元件已经是有效JSON格式的列表
        if cleaned.startswith('[') and cleaned.endswith(']'):
            # 示例: [{"part": "C", "value": "1nF", "pins": ["LO", "VSS"]}]
            return json.loads(cleaned)
        else:
            # 示例: {"PASSIVES": [...]}
            data = json.loads(cleaned)
            return data.get("PASSIVES", [])
    except Exception as e:
        print(f"⚠️ 被动元件解析失败: {e}")
        print(f"   原始数据: {passive_str}")
        return []

def load_csv_as_dict(csv_path: str) -> Dict:
    print(f"🔄 检测到 CSV 文件，正在重组为 Pydantic 兼容的数据结构...")
    
    config_dict = {
        "project_info": {},
        "hardware_config": "",
        "pin_template_mapping": []
    }
    
    # 新版字段映射（完全匹配 schema.PinMappingRow）
    HEADER_MAP = {
        "Display Pin": "display_pin",
        "Hidden F/S Mapping": "socket_pins_map", 
        "Logical Net": "logical_net",
        "Resource Types": "resource_type",
        "Channel Allocations": "channel_allocations",
        "Connect Type": "connect_type",
        "Active Circuits": "active_circuits",
        "Passive Circuits (Parsed)": "passive_circuits",
        "Params": "parameters"  # 关键修改点：改为 parameters
    }

    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.reader(f)
        current_block = None
        headers = []
        
        for row in reader:
            if not row or not row[0].strip():
                continue

            first_cell = row[0].strip()
            
            if first_cell.startswith("# ====== PROJECT SETUP METADATA"):
                current_block = "METADATA"
                continue
            elif first_cell.startswith("# ====== PIN MAPPING"):
                current_block = "PIN_MAPPING"
                headers = []
                continue

            if current_block == "METADATA":
                if len(row) >= 2:
                    key, val = row[0].strip(), row[1].strip()
                    if key == "Hardware Config":
                        config_dict["hardware_config"] = val
                    # 解析所有METADATA字段
                    elif key in ("project_name", "site_num", "schema_version", "default_package",
                              "default_voltage", "default_tolerance", "ate_platform"):
                        config_dict["project_info"][key] = int(val) if key == "site_num" else val
                    elif key == "component_overrides":
                        try:
                            config_dict["project_info"][key] = eval(val)
                        except:
                            config_dict["project_info"][key] = {}

            elif current_block == "PIN_MAPPING":
                if not headers:
                    headers = [col.strip() for col in row]
                else:
                    # 跳过空行和模板标题行
                    if not row or not row[0].strip() or row[0].startswith('Module_Category'):
                        continue

                    # 跳过CSV结束标记
                    if row[0].startswith('# ======'):
                        current_block = None
                        continue

                    row_dict = {}
                    for i, header in enumerate(headers):
                        if i >= len(row):
                            continue
                            
                        val = row[i].strip()
                        mapped_key = HEADER_MAP.get(header, header)
                        
                        # 简化的字段处理
                        if val.strip() in ("", "{}"):
                            if mapped_key in ["socket_pins_map", "parameters"]:
                                row_dict[mapped_key] = {}
                            elif mapped_key in ["active_circuits", "passive_circuits"]:
                                row_dict[mapped_key] = []
                            else:
                                row_dict[mapped_key] = ""
                        elif mapped_key == "socket_pins_map":
                            # 安全解析字典
                            try:
                                row_dict[mapped_key] = eval(val)
                            except:
                                row_dict[mapped_key] = {}
                        elif mapped_key == "active_circuits":
                            row_dict[mapped_key] = [c.strip() for c in val.split(",")]
                        elif mapped_key == "passive_circuits":
                            row_dict[mapped_key] = parse_passives(val)
                        elif mapped_key == "parameters":
                            try:
                                row_dict[mapped_key] = json.loads(val.replace('""', '"'))
                            except:
                                row_dict[mapped_key] = {}
                        else:
                            row_dict[mapped_key] = val
                    
                    if row_dict:
                        config_dict["pin_template_mapping"].append(row_dict)

    return config_dict

def generate_from_config_file(file_path: str):
    print(f"📥 正在加载配置: {file_path}")

    try:
        data = load_csv_as_dict(file_path) if file_path.endswith('.csv') else json.load(open(file_path))
        print(f"🔍 解析后数据: project_info={data.get('project_info', {})}")
        print(f"🔍 引脚映射数量: {len(data.get('pin_template_mapping', []))}")

        config = Table2SchConfig(**data)
        print("✅ 数据验证成功！")

        out_path = SchGenerator.generate_from_config(config)
        print(f"✅ 生成成功！\n📁 原理图路径: {out_path}")
    except Exception as e:
        print(f"❌ 错误:\n{type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # target_file = sys.argv[1] if len(sys.argv) > 1 else None
    target_file = r"E:\Base-Data\AI_Prj\sch_creater\AI_Prj\t-default\Table2SCH\STS8300_LB_RevA.csv"
    if not target_file:
        target_file = next((f for f in ["STS8300_LB_RevA.json", "STS8300_LB_RevA.csv"] 
                          if os.path.exists(f)), None)
    
    if not target_file:
        print("❌ 找不到配置文件")
        sys.exit(1)
        
    generate_from_config_file(target_file)