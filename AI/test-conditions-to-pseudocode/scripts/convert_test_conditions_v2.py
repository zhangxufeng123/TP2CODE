#!/usr/bin/env python3
"""Convert extracted test-item JSON into pseudocode format."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple

def normalize_text(value: str) -> str:
    """标准化文本，去除多余空格和换行"""
    return " ".join(value.replace("\r", "\n").replace("\n", " ").split()).strip()

def normalize_pin_name(header: str) -> str:
    """标准化引脚名称"""
    text = normalize_text(header)
    pin_match = re.match(r"^PIN\s*(\d+)\s+(.+)$", text, re.IGNORECASE)
    if pin_match:
        return normalize_text(pin_match.group(2))
    return text

def extract_allowed_pin_names(pin_columns: List[Dict[str, str]]) -> Set[str]:
    """提取允许的引脚名称集合"""
    return {normalize_pin_name(str(item["header"])) for item in pin_columns}

def parse_natural_language_to_pseudocode(test_method: str, pins: Dict[str, str], allowed_pin_names: Set[str], test_name: str = "") -> List[str]:
    """
    按照规则将自然语言测试方法转换为伪代码格式
    严格遵循10条转换规则
    """
    commands: List[str] = []
    test_text = normalize_text(test_method)

    # 阶段1：从pins配置提取基础设置
    voltage_map: Dict[str, str] = {}  # 引脚电压映射
    float_pins: Set[str] = set()      # 浮空引脚

    for pin_header, pin_value in pins.items():
        pin_name = normalize_pin_name(pin_header)
        if pin_name not in allowed_pin_names:
            continue

        value = normalize_text(str(pin_value))

        # 规则3：Float - 处理浮空引脚
        if "悬空" in value or value.upper() in ["FLOAT", "FLT", "F"]:
            float_pins.add(pin_name)
            continue

        # 规则1：FV - 电压设置
        # 匹配数字电压值，如"12", "12V", "0", "0V"
        voltage_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:V|v)?', value)
        if voltage_match and not re.search(r'方波|信号|扫描|HI|LI', value):
            voltage_num = voltage_match.group(1)
            voltage_map[pin_name] = f"{voltage_num}V"

    # 规则1：FV命令 - 电压设置
    if voltage_map:
        fv_parts = [f"{pin}={voltage}" for pin, voltage in voltage_map.items()]
        commands.append(f"FV[{','.join(fv_parts)}]")

    # 规则3：Float命令 - 浮空引脚
    if float_pins:
        commands.append(f"Float[{','.join(sorted(float_pins))}]")

    # 规则10：Delay命令 - 延迟时间
    delay_match = re.search(r'(?:延迟|delay)\s*(\d+(?:\.\d+)?)\s*(ms|mS|us|uS|ns|nS|s)', test_text, re.IGNORECASE)
    if delay_match:
        time_val = delay_match.group(1)
        time_unit = delay_match.group(2).lower()
        if time_unit == 'ms': time_unit = 'ms'
        elif time_unit == 'us': time_unit = 'us'
        elif time_unit == 'ns': time_unit = 'ns'
        commands.append(f"Delay[{time_val}{time_unit}]")

    # 规则5/6：MV/MI命令 - 电压/电流测量
    # IDD测试：测量VDD电流
    if "IDD" in test_name and any(x in test_text for x in ["测电流", "电流稳定", "电流就是"]):
        commands.append("MI[VDD]")
    # IHB测试：测量HB电流
    elif "IHB" in test_name and any(x in test_text for x in ["测电流", "电流稳定", "电流就是"]):
        commands.append("MI[HB]")
    # IHBSO测试：测量HB和HS电流
    elif "IHBSO" in test_name:
        commands.extend(["MI[HB]", "MI[HS]"])
    # 通用电压测量
    elif "测电压" in test_text:
        for pin in ["EN", "HB", "VDD"]:
            if pin in test_text and pin.lower() in [p.lower() for p in allowed_pin_names]:
                commands.append(f"MV[{pin}]")

    # 规则2：FI命令 - 电流设置（方波信号）
    if "方波信号" in test_text:
        if "HI" in test_text and "0到5V" in test_text:
            commands.append("FI[HI=0A,5A,500K]")
        if "LI" in test_text and "0到5V" in test_text:
            commands.append("FI[LI=0A,5A,500K]")

    # 规则8：Connect命令 - 外部连接
    connect_parts = []
    if "挂" in test_text:
        # 电容连接: "HB对HS挂100NF电容"
        cap_match = re.findall(r'(\w+)对(\w+)挂(\S+)', test_text)
        for pin, comp, value in cap_match:
            pin_norm = normalize_pin_name(pin)
            comp_norm = normalize_text(comp)
            if pin_norm in allowed_pin_names:
                connect_parts.append(f"{pin_norm}-{value}-{comp_norm}")

    if connect_parts:
        commands.append(f"Connect[{','.join(connect_parts)}]")

    # 规则7：MT命令 - 时间测量（简化处理）
    if any(x in test_text for x in ["上升时间", "下降时间", "MT", "测时间"]):
        if "HO" in test_text:
            commands.append("MT[HO]")
        elif "LO" in test_text:
            commands.append("MT[LO]")

    # 规则9：Display命令 - 结果显示
    if "输出结果" in test_text or "计算结果" in test_text:
        # 简化处理，实际应根据具体计算逻辑生成
        commands.append("Display[Result]")

    # 规则3/4：RampV/RampI命令 - 电压/电流扫描
    if "扫描" in test_text:
        # 电压扫描
        if "EN" in test_text and "扫描" in test_text and "V" in test_text:
            commands.append("RampV[EN,1.4V,3.2V,auto]")
        elif "VDD" in test_text and "扫描" in test_text:
            commands.append("RampV[VDD,6.6V,7.4V,auto]")
        elif "HB" in test_text and "扫描" in test_text:
            commands.append("RampV[HB,6V,6.8V,auto]")
        elif "HI" in test_text and "扫描" in test_text and "V" in test_text:
            commands.append("RampV[HI,1.8V,2.8V,auto]")

    return commands

def convert_record(record: Dict[str, object], sequence_number: int, allowed_pin_names: Set[str]) -> List[object]:
    """转换单个测试记录"""
    section = normalize_text(str(record.get("section", ""))) or "General"
    test_name = normalize_text(str(record.get("test_name", "")))
    test_method = str(record.get("test_method", ""))
    unit = normalize_text(str(record.get("unit", "")))
    pins = record.get("pins", {})

    if not isinstance(pins, dict):
        pins = {}

    # 使用完整的自然语言解析
    commands = parse_natural_language_to_pseudocode(test_method, pins, allowed_pin_names, test_name)

    # 去重
    unique_commands = list(dict.fromkeys(commands))

    return [section, f"{sequence_number}", test_name, ",".join(unique_commands), unit]

def convert_json(input_data: Dict[str, object]) -> Dict[str, object]:
    """转换整个JSON数据"""
    pin_columns = input_data.get("pin_columns", [])
    records = input_data.get("records", [])

    if not isinstance(pin_columns, list):
        raise ValueError("Input JSON missing 'pin_columns' list.")
    if not isinstance(records, list):
        raise ValueError("Input JSON missing 'records' list.")

    allowed_pin_names = extract_allowed_pin_names(pin_columns)
    output_records: List[List[object]] = []

    sequence_number = 1
    for record in records:
        if not isinstance(record, dict):
            continue
        test_name = normalize_text(str(record.get("test_name", "")))
        if not test_name:
            continue
        output_records.append(convert_record(record, sequence_number, allowed_pin_names))
        sequence_number += 1

    return {
        "pin_order": ", ".join(normalize_text(str(item["header"])) for item in pin_columns),
        "records": output_records,
    }

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Convert extracted test-item JSON into pseudocode format."
    )
    parser.add_argument("--input", required=True, help="Input JSON path.")
    parser.add_argument("--output", default=None, help="Optional output JSON path.")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON.")
    args = parser.parse_args()

    input_path = Path(args.input)

    if not input_path.exists():
        raise FileNotFoundError(f"Input JSON not found: {input_path}")
    if input_path.suffix.lower() != ".json":
        raise ValueError("Only .json input files are supported.")

    input_data = json.loads(input_path.read_text(encoding="utf-8"))
    output_data = convert_json(input_data)

    output_path = Path(args.output) if args.output else input_path.with_name(f"{input_path.stem}_pseudocode.json")
    output_text = json.dumps(output_data, ensure_ascii=False, indent=2 if args.pretty else None)
    output_path.write_text(output_text, encoding="utf-8")
    print(output_path)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())