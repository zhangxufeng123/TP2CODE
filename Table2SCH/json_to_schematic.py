#!/usr/bin/env python3
"""
集成脚本：从FT_Test_Plan_JSON文件直接生成KiCad原理图
整合了JSON解析、资源分配和原理图生成功能
"""

import json
import csv
import re
import os
import sys
import pandas as pd
from pathlib import Path
from typing import Dict, List, Set, Tuple

# 动态添加Python路径
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

from models.schema import Table2SchConfig
from exporters.sch_generator import SchGenerator
from src.parsers.ate_resource_allocator import MultisiteTesterPool


def parse_test_plan_json(json_file: str) -> Dict:
    """解析FT_Test_Plan_JSON文件，提取引脚规格和被动元件"""

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
    mt_pairs = set()
    passives_dict = {}

    def parse_value(val_str: str) -> Tuple[float, str]:
        """解析数值和单位"""
        match = re.match(r"([-+]?\d*\.?\d+)([a-zA-Z]+)", val_str.strip())
        if not match:
            return 0.0, val_str

        val, unit = float(match.group(1)), match.group(2)
        multiplier = 1.0
        if unit in ['mV', 'mA', 'ms']: multiplier = 1e-3
        elif unit in ['uA', 'us']: multiplier = 1e-6
        elif unit in ['nA', 'ns']: multiplier = 1e-9

        return abs(val * multiplier), val_str

    def init_pin(pin: str):
        """初始化引脚数据"""
        if pin not in pin_dict:
            pin_dict[pin] = {
                'Force_V_Max': 0.0, 'Force_V_Str': '-',
                'Force_I_Max': 0.0, 'Force_I_Str': '-',
                'Is_Float': False
            }

    # 解析测试记录
    for item in json_data.get("records", []):
        if len(item) < 4:
            continue
        code = item[3]

        # 提取电压/电流设置
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

        # 提取浮动引脚
        for flt_block in re.findall(r'Float\[(.*?)\]', code):
            for pin in flt_block.split(','):
                pin = pin.strip()
                if pin in valid_pins:
                    init_pin(pin)
                    pin_dict[pin]['Is_Float'] = True

        # 提取测量管脚对
        for mt_block in re.findall(r'MT\[(.*?)\]', code):
            pins_in_mt = re.findall(r'\(([a-zA-Z0-9_]+)=', mt_block)
            pins_in_mt = [p.strip() for p in pins_in_mt if p.strip() in valid_pins]
            if len(pins_in_mt) >= 2:
                p1, p2 = pins_in_mt[0], pins_in_mt[1]
                mt_pairs.add(f"{p1}-{p2}")

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
                                # 判断元件类型
                                part_type = 'C' if 'F' in val_part.upper() else 'R'
                                key = f"{p1}-{p2}"
                                passives_dict[key] = {
                                    'part': part_type,
                                    'value': val_part,
                                    'pins': [p1, p2]
                                }
                        except ValueError:
                            pass

    return {
        'pins': valid_pins,
        'pin_specs': pin_dict,
        'mt_pairs': list(mt_pairs),
        'passives': list(passives_dict.values())
    }


def generate_schematic_config(json_file: str, ate_platform: str = "STS8300_A28D4") -> Dict:
    """生成原理图配置数据"""

    print("🔍 解析JSON测试计划...")
    json_data = parse_test_plan_json(json_file)

    print("🔧 分配ATE资源...")
    # 使用现有的资源分配器
    tester = MultisiteTesterPool(
        ate_platform_str=ate_platform,
        config_dir=None,
        site_count=4
    )

    # 默认配置模板
    config = {
        "project_info": {
            "project_name": "STS8300_LB_from_JSON",
            "site_num": 4,
            "schema_version": "1.0",
            "default_package": "0603",
            "default_voltage": "50V",
            "default_tolerance": "1%",
            "ate_platform": ate_platform,
            "component_overrides": {
                "SOCKET_PATH": "Sch_lib/sockets/JW_Contator.kicad_sym",
                "SOCKET_NAME": "FTD_PP_25C_DFN4X4X0.75-10"
            }
        },
        "hardware_config": "",
        "pin_template_mapping": []
    }

    # 基于JSON数据构建引脚映射
    for i, pin in enumerate(json_data['pins'], 1):
        pin_spec = json_data['pin_specs'].get(pin, {})

        # 确定连接类型（根据电压范围）
        if pin_spec.get('Force_V_Max', 0) > 10:
            connect_type = "Kelvin"
        elif pin_spec.get('Is_Float', False):
            connect_type = "NC"
        else:
            connect_type = "Relay"

        # 简单资源分配策略
        resources = ["ACM200"] if i <= 2 else ["FXVIe"]  # 简化逻辑

        pin_mapping = {
            "display_pin": f"{i}F/S ({pin})",
            "socket_pins_map": {"F": f"{i}F", "S": f"{i}S"},
            "logical_net": pin,
            "resource_type": resources[0] if resources else "ACM200",
            "channel_allocations": f"Site1({resources[0]}[S{i}_CH0]) | Site2({resources[0]}[S{i+4}_CH0]) | " +
                                  f"Site3({resources[0]}[S{i+8}_CH0]) | Site4({resources[0]}[S{i+12}_CH0])",
            "connect_type": connect_type,
            "active_circuits": ["ChargeRelease"] if connect_type == "Kelvin" else [],
            "passive_circuits": [],
            "parameters": {}
        }

        config["pin_template_mapping"].append(pin_mapping)

    # 添加被动元件到相应的引脚
    for passive in json_data['passives']:
        pins = passive.get('pins', [])
        if len(pins) >= 2:
            # 找到包含这些引脚的映射条目
            for pin_map in config["pin_template_mapping"]:
                if pin_map["logical_net"] in pins:
                    if "passive_circuits" not in pin_map:
                        pin_map["passive_circuits"] = []
                    pin_map["passive_circuits"].append(passive)

    print(f"✅ 配置生成完成: {len(config['pin_template_mapping'])} 个引脚映射")
    return config


def main():
    """主函数：执行完整流程"""

    json_file = Path("FT_Test_Plan_JSON_2.json")
    if not json_file.exists():
        print(f"❌ JSON文件不存在: {json_file}")
        return

    try:
        # 1. 生成配置
        config_data = generate_schematic_config(str(json_file))

        # 2. 验证配置
        config = Table2SchConfig(**config_data)
        print("✅ 配置验证通过")

        # 3. 生成原理图
        print("🚀 开始生成原理图...")
        out_path = SchGenerator.generate_from_config(config)

        print(f"\n🎉 生成成功！")
        print(f"📁 原理图路径: {out_path}")
        print(f"📊 包含内容:")
        print(f"   - {len(config.pin_template_mapping)} 个引脚映射")
        print(f"   - 被动元件: {sum(len(p.passive_circuits) for p in config.pin_template_mapping)} 个")

    except Exception as e:
        print(f"❌ 生成失败: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()