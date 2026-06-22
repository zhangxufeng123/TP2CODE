#!/usr/bin/env python3
"""Convert extracted test-item JSON into exchange-style pseudocode JSON."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Dict, Iterable, List, Set, Tuple

FLOAT_TOKENS = {"FLOAT", "FLT", "F", "DISC"}
PLACEHOLDER_TOKENS = {"", "NC", "XXX", "N/A", "NA"}
STEP_LINE_PATTERN = re.compile(r"^\s*\d+[、\.\)]\s*")
PIN_HEADER_PATTERN = re.compile(r"^PIN\s*(\d+)\s+(.+)$", re.IGNORECASE)


def normalize_text(value: str) -> str:
    return " ".join(value.replace("\r", "\n").replace("\n", " ").split()).strip()


def clean_multiline(value: str) -> List[str]:
    return [line.strip() for line in value.replace("\r", "\n").split("\n") if line.strip()]


def normalize_units(value: str) -> str:
    return normalize_text(value).replace("次", "Ω")


def normalize_ascii_punctuation(value: str) -> str:
    return (
        value.replace("，", ",")
        .replace("：", ":")
        .replace("；", ";")
        .replace("（", "(")
        .replace("）", ")")
        .replace("。", ".")
    )


def load_input(path: Path) -> Dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def normalize_pin_name(header: str) -> str:
    header_text = normalize_text(header)
    match = PIN_HEADER_PATTERN.match(header_text)
    if match:
        return normalize_text(match.group(2))
    return header_text


def build_pin_order(pin_columns: Iterable[Dict[str, str]]) -> str:
    return ", ".join(normalize_text(str(item["header"])) for item in pin_columns)


def extract_allowed_pin_names(pin_columns: Iterable[Dict[str, str]]) -> Set[str]:
    return {normalize_pin_name(str(item["header"])) for item in pin_columns}


def is_placeholder_value(value: str) -> bool:
    normalized = normalize_text(value).upper()
    return normalized in PLACEHOLDER_TOKENS


def is_float_value(value: str) -> bool:
    return normalize_text(value).upper() in FLOAT_TOKENS


def merge_pin_lines(lines: List[str]) -> List[str]:
    merged: List[str] = []
    i = 0
    while i < len(lines):
        current = normalize_units(lines[i])
        if i + 1 < len(lines):
            next_line = normalize_units(lines[i + 1])
            if current.lower().endswith(" and") and "to gnd" in next_line.lower():
                left = current[:-4].strip()
                right = re.sub(r"(?i)\s+to\s+gnd$", "", next_line).strip()
                merged.append(f"{left} and {right} to gnd")
                i += 2
                continue
            if current.lower() == "change from" and i + 2 < len(lines):
                third_line = normalize_units(lines[i + 2])
                if re.match(r"^[0-9].+\bto\b.+", next_line, re.IGNORECASE) and (
                    third_line.upper().startswith("MV WHEN") or third_line.upper().startswith("MI WHEN")
                ):
                    merged.append(f"{current} {next_line} {third_line}")
                    i += 3
                    continue
        merged.append(current)
        i += 1
    return merged


def parse_voltage_or_current_value(value: str) -> Tuple[str | None, str | None]:
    text = normalize_units(value)
    if not text:
        return None, None

    if re.fullmatch(r"[-+]?[0-9]*\.?[0-9]+(?:V|mV|uV|kV)", text, re.IGNORECASE):
        return "FV", text
    if re.fullmatch(r"[-+]?[0-9]*\.?[0-9]+(?:A|mA|uA|nA)", text, re.IGNORECASE):
        return "FI", text
    return None, None


def parse_connect_components(pin_name: str, text: str) -> List[str]:
    normalized = normalize_units(text)
    lower = normalized.lower()
    commands: List[str] = []

    if " and " in lower:
        for part in re.split(r"\band\b", normalized, flags=re.IGNORECASE):
            part = part.strip()
            if not part:
                continue
            subcommands = parse_connect_components(pin_name, part)
            if subcommands:
                commands.extend(subcommands)
                continue
            component = normalize_text(part).replace(" ", "")
            if component and re.search(r"[0-9]", component):
                commands.append(f"Connect[{pin_name}-{component}]")
        return commands

    for suffix in ("gnd", "5v", "fb"):
        match = re.fullmatch(rf"(.+?)\s+to\s+{suffix}", normalized, re.IGNORECASE)
        if match:
            component = normalize_text(match.group(1)).replace(" ", "")
            if component:
                commands.append(f"Connect[{pin_name}-{component}-{suffix.upper()}]")
            return commands

    if "probe pad" in lower:
        commands.append(f"Connect[{pin_name}-ProbePad]")
    return commands


def parse_pin_condition(pin_name: str, text: str) -> List[str]:
    line = normalize_units(text)
    if not line:
        return []

    if line.upper() == "SPI":
        return []

    if is_float_value(line):
        return [f"Float[{pin_name}]"]

    if line.upper() in {"MI", "MV", "MT"}:
        return [f"{line.upper()}[{pin_name}]"]

    connect_commands = parse_connect_components(pin_name, line)
    if connect_commands:
        return connect_commands

    assign_match = re.fullmatch(rf"{re.escape(pin_name)}\s*=\s*(.+)", line, re.IGNORECASE)
    if assign_match:
        line = normalize_units(assign_match.group(1))

    cmd_type, raw_value = parse_voltage_or_current_value(line)
    if cmd_type and raw_value:
        if cmd_type == "FV":
            return [f"FV[{pin_name}={raw_value}]"]
        elif cmd_type == "FI":
            return [f"FI[{pin_name}={raw_value}]"]

    if " MV when " in f" {line} ":
        left, right = line.split("MV when", 1)
        commands = parse_pin_condition(pin_name, left.strip())
        commands.append(f"MV[{pin_name}]")
        commands.append(f"Monitor[{normalize_text(right)}]")
        return commands

    if " MI when " in f" {line} ":
        left, right = line.split("MI when", 1)
        commands = parse_pin_condition(pin_name, left.strip())
        commands.append(f"MI[{pin_name}]")
        commands.append(f"Monitor[{normalize_text(right)}]")
        return commands

    change_match = re.fullmatch(r"change from\s+(.+?)\s+to\s+(.+)", line, re.IGNORECASE)
    if change_match:
        start, end = change_match.groups()
        return [f"RampV[{pin_name},{normalize_text(start)},{normalize_text(end)},auto]"]

    if line.lower().startswith("source out until"):
        condition = normalize_text(line[len("source out until") :])
        monitor_text = condition
        if "," in condition:
            monitor_text = normalize_text(condition.split(",", 1)[0])
        commands = [f"Monitor[{monitor_text}]"]
        if re.search(rf"\bIV?{re.escape(pin_name)}\b", condition, re.IGNORECASE):
            commands.append(f"MI[{pin_name}]")
        return commands

    if line.lower().startswith("source out "):
        amount = normalize_text(line[len("source out ") :]).rstrip(",")
        if "," in amount:
            amount = amount.split(",", 1)[0].strip()
        return [f"FI[{pin_name}=-{amount}]"]

    if line.lower().startswith("sink in "):
        amount = normalize_text(line[len("sink in ") :])
        return [f"FI[{pin_name}={amount}]"]

    if line.lower().startswith("sink "):
        amount = normalize_text(line[len("sink ") :])
        return [f"FI[{pin_name}={amount}]"]

    if line.lower().startswith("load "):
        payload = normalize_text(line[len("load ") :])
        return [f"Display[Load[{pin_name}:{payload}]]"]

    return [f"Display[{pin_name}:{line}]"]


def split_commands_by_type(commands: Iterable[str]) -> Dict[str, List[str]]:
    buckets = {
        "FV": [],
        "FI": [],
        "Connect": [],
        "Float": [],
        "RampV": [],
        "RampI": [],
        "Delay": [],
        "MI": [],
        "MV": [],
        "MT": [],
        "Monitor": [],
        "Display": [],
        "Other": [],
    }

    for command in commands:
        matched = False
        for prefix in buckets:
            if prefix != "Other" and command.startswith(f"{prefix}["):
                buckets[prefix].append(command)
                matched = True
                break
        if not matched:
            buckets["Other"].append(command)
    return buckets


def merge_same_type_commands(commands: Iterable[str], prefix: str) -> str | None:
    items: List[str] = []
    seen: Set[str] = set()
    for command in commands:
        inner = command[len(prefix) + 1 : -1]
        if inner in seen:
            continue
        seen.add(inner)
        items.append(inner)
    if not items:
        return None
    return f"{prefix}[{','.join(items)}]"


def order_grouped_commands(buckets: Dict[str, List[str]], allowed_pin_names: Set[str] = None) -> List[str]:
    ordered: List[str] = []

    # 按照指定格式：FV将所有电压设置合并，然后是Float命令，Delay命令，最后是测量命令

    # 1. 处理FV命令（将所有电压设置合并到一个FV命令中）
    fv_commands = []
    for command in buckets["FV"]:
        # 提取FV命令中的引脚=值部分
        if command.startswith("FV[") and command.endswith("]"):
            pins_config = command[3:-1]
            if "," in pins_config:
                # 如果是多个引脚的FV命令，直接添加到列表中
                fv_commands.append(pins_config)
            else:
                fv_commands.append(pins_config)

    if fv_commands:
        # 合并所有FV配置
        all_fv_configs = ",".join(fv_commands)
        ordered.append(f"FV[{all_fv_configs}]")

    # 2. 处理FI命令
    if buckets["FI"]:
        for command in dict.fromkeys(buckets["FI"]):
            ordered.append(command)

    # 3. 处理Connect命令
    if buckets["Connect"]:
        for command in dict.fromkeys(buckets["Connect"]):
            ordered.append(command)

    # 4. 处理Float命令
    if buckets["Float"]:
        for command in dict.fromkeys(buckets["Float"]):
            ordered.append(command)

    # 5. 处理Ramp命令
    for prefix in ["RampV", "RampI"]:
        for command in dict.fromkeys(buckets[prefix]):
            ordered.append(command)

    # 6. 处理Delay命令
    for command in dict.fromkeys(buckets["Delay"]):
        ordered.append(command)

    # 7. 处理测量命令（MI, MV, MT）
    for prefix in ["MI", "MV", "MT"]:
        for command in dict.fromkeys(buckets[prefix]):
            ordered.append(command)

    # 8. 处理其他命令
    for prefix in ["Monitor", "Display", "Other"]:
        for command in dict.fromkeys(buckets[prefix]):
            ordered.append(command)

    return ordered


def build_pin_commands(pins: Dict[str, str], allowed_pin_names: Set[str]) -> List[str]:
    """
    按照指定格式生成伪代码：
    设置命令：FV, FI, Float, Connect
    扫描命令：RampV, RampI
    测量命令：MV, MI, MT
    显示命令：Display
    控制命令：Delay, WR

    按照：FV命令、Float命令、Delay命令、测量命令的顺序
    """

    # 收集各类命令
    fv_settings: Dict[str, str] = {}      # FV引脚电压设置
    fi_settings: Dict[str, str] = {}      # FI引脚电流设置
    float_pins: Set[str] = set()          # 浮动引脚
    connect_commands: Set[str] = set()    # 连接命令
    rampv_commands: Set[str] = set()      # 电压扫描
    rampi_commands: Set[str] = set()      # 电流扫描
    mv_commands: Set[str] = set()         # 电压测量
    mi_commands: Set[str] = set()         # 电流测量
    mt_commands: Set[str] = set()         # 时间测量
    delay_commands: Set[str] = set()      # 延迟命令
    display_commands: Set[str] = set()    # 显示命令
    wr_commands: Set[str] = set()         # 寄存器写入

    for header, raw_value in pins.items():
        pin_name = normalize_pin_name(header)
        if pin_name not in allowed_pin_names:
            continue
        value = str(raw_value)
        if is_placeholder_value(value):
            continue

        merged_lines = merge_pin_lines(clean_multiline(value))

        for line in merged_lines:
            line_text = normalize_units(line)

            # 1. 检查浮动引脚
            if is_float_value(line_text):
                float_pins.add(pin_name)
                continue

            # 2. 检查Delay命令
            if "delay" in line_text.lower() or "延迟" in line_text:
                delay_match = re.search(r"(?:延迟|Delay)\s*([0-9]+(?:\.[0-9]+)?\s*(?:ms|us|s|mS|uS|nS))", line_text, re.IGNORECASE)
                if delay_match:
                    delay_commands.add(f"Delay[{delay_match.group(1).replace(' ', '')}]")

            # 3. 检查电压设置 (FV)
            # 匹配纯数字或带V的数字（如 "17" 或 "17V"）
            voltage_match = re.search(r'(^|\s)(\d+(?:\.\d+)?)\s*(V|v)?(\s|$)', line_text)
            if voltage_match:
                voltage_value = voltage_match.group(2)
                voltage_value += 'V' if voltage_match.group(3) is None else voltage_match.group(3).upper()
                fv_settings[pin_name] = voltage_value

            # 4. 检查测量命令
            if 'MI' in line_text.upper() or '测电流' in line_text or ('电流' in line_text and '测' in line_text):
                mi_commands.add(f"MI[{pin_name}]")

            if 'MV' in line_text.upper() or '测电压' in line_text or ('电压' in line_text and '测' in line_text):
                mv_commands.add(f"MV[{pin_name}]")

            if 'MT' in line_text.upper() or '测时间' in line_text or ('时间' in line_text and '测' in line_text):
                mt_commands.add(f"MT[{pin_name}]")

    # 按照指定顺序组织命令
    ordered_commands: List[str] = []

    # 1. FV命令 - 电压设置
    if fv_settings:
        fv_parts = [f"{pin}={voltage}" for pin, voltage in fv_settings.items()]
        ordered_commands.append(f"FV[{','.join(fv_parts)}]")

    # 2. FI命令 - 电流设置
    if fi_settings:
        fi_parts = [f"{pin}={current}" for pin, current in fi_settings.items()]
        ordered_commands.append(f"FI[{','.join(fi_parts)}]")

    # 3. Float命令
    if float_pins:
        ordered_commands.append(f"Float[{','.join(sorted(float_pins))}]")

    # 4. Connect命令
    if connect_commands:
        ordered_commands.append(f"Connect[{','.join(sorted(connect_commands))}]")

    # 5. RampV命令
    if rampv_commands:
        for cmd in sorted(rampv_commands):
            ordered_commands.append(cmd)

    # 6. RampI命令
    if rampi_commands:
        for cmd in sorted(rampi_commands):
            ordered_commands.append(cmd)

    # 7. MV命令
    if mv_commands:
        for cmd in sorted(mv_commands):
            ordered_commands.append(cmd)

    # 8. MI命令
    if mi_commands:
        for cmd in sorted(mi_commands):
            ordered_commands.append(cmd)

    # 9. MT命令
    if mt_commands:
        for cmd in sorted(mt_commands):
            ordered_commands.append(cmd)

    # 10. Delay命令
    if delay_commands:
        for cmd in sorted(delay_commands):
            ordered_commands.append(cmd)

    # 11. WR命令
    if wr_commands:
        ordered_commands.append(f"WR[{','.join(sorted(wr_commands))}]")

    # 12. Display命令（最后）
    if display_commands:
        for cmd in sorted(display_commands):
            ordered_commands.append(cmd)

    return ordered_commands


def build_kelvin_record(record: Dict[str, object]) -> List[str] | None:
    test_name = normalize_text(str(record.get("test_name", "")))
    if not test_name.startswith("Kelvin_") and not test_name.startswith("P_Kelvin_"):
        return None

    pins = record.get("pins", {})
    if not isinstance(pins, dict):
        return None

    target_pin = None
    target_value = None
    for header, raw_value in pins.items():
        value = normalize_text(str(raw_value))
        if value and value.upper() != "DISC":
            target_pin = normalize_pin_name(header)
            target_value = value
            break

    if not target_pin or not target_value:
        return None

    parts = clean_multiline(target_value)
    if len(parts) >= 2 and parts[1].upper().startswith("R="):
        return [f"Display[{parts[1]}]"]
    return [f"Display[{target_pin}:{target_value}]"]


def build_cnt_record(record: Dict[str, object]) -> List[str] | None:
    test_name = normalize_text(str(record.get("test_name", "")))
    if not test_name.startswith("CNT_") and not test_name.startswith("P_CNT_"):
        return None

    pins = record.get("pins", {})
    if not isinstance(pins, dict):
        return None

    target_pin = None
    fv_parts: List[str] = []
    measurement_cmd = None

    for header, raw_value in pins.items():
        pin_name = normalize_pin_name(header)
        value = normalize_text(str(raw_value))
        if not value or value.upper() == "DISC":
            continue
        if "MV" in value.upper():
            target_pin = pin_name
            measurement_cmd = f"MV[{pin_name}]"
            stripped = value.replace("MV", "").strip()
            if stripped:
                cmd_type, parsed = parse_voltage_or_current_value(stripped)
                if cmd_type == "FV" and parsed:
                    fv_parts.append(f"{pin_name}={parsed}")
            continue
        if value.upper() in {"0", "0V", "GND"}:
            if pin_name != "GND":
                fv_parts.append(f"{pin_name}=0V")
            continue
        cmd_type, parsed = parse_voltage_or_current_value(value)
        if cmd_type == "FV" and parsed:
            fv_parts.append(f"{pin_name}={parsed}")

    commands: List[str] = []
    if fv_parts:
        commands.append(f"FV[{','.join(dict.fromkeys(fv_parts))}]")
    if measurement_cmd:
        commands.append(measurement_cmd)
    return commands if commands else None


def extract_target_pin_from_test_name(test_name: str, allowed_pin_names: Set[str]) -> str | None:
    match = re.search(r"(OUT\d+)", test_name, re.IGNORECASE)
    if match:
        candidate = match.group(1).upper()
        for pin_name in allowed_pin_names:
            if pin_name.upper() == candidate:
                return pin_name
    return None


def build_spi_pins(pins: Dict[str, str]) -> List[str]:
    spi_names: List[str] = []
    for header, raw_value in pins.items():
        if normalize_text(str(raw_value)).upper() == "SPI":
            pin_name = normalize_pin_name(header)
            spi_names.append(pin_name)
    return spi_names


def extract_register_writes(text: str) -> List[str]:
    matches = re.findall(r"([0-9A-Fa-f]{2})\s*[-=]\s*([0-9A-Fa-f]{2})", text)
    return [f"{addr}={value}" for addr, value in matches]


def build_board_driver_record(
    record: Dict[str, object],
    allowed_pin_names: Set[str],
) -> List[str] | None:
    test_name = normalize_text(str(record.get("test_name", "")))
    board_prefixes = ("IOLD_", "Rdson_", "clk_ocp", "Iocp_", "IOCP_")
    if not any(test_name.startswith(prefix) for prefix in board_prefixes):
        return None

    pins = record.get("pins", {})
    if not isinstance(pins, dict):
        return None

    test_method = normalize_ascii_punctuation(str(record.get("test_method", "")))
    commands: List[str] = []

    fv_parts: List[str] = []
    connect_parts: List[str] = []
    float_parts: List[str] = []

    for header, raw_value in pins.items():
        pin_name = normalize_pin_name(header)
        value = normalize_units(str(raw_value))
        if not value:
            continue
        if normalize_text(value).upper() in {"F", "FLT", "FLOAT", "DISC"}:
            if pin_name not in {"SDI", "SDO", "NSCS", "SCLK"}:
                float_parts.append(pin_name)
            continue
        if normalize_text(value).upper() == "SPI":
            continue
        merged_lines = merge_pin_lines(clean_multiline(value))
        for line in merged_lines:
            if is_float_value(line):
                float_parts.append(pin_name)
                continue
            connect_cmds = parse_connect_components(pin_name, line)
            if connect_cmds:
                connect_parts.extend(cmd[len("Connect["):-1] for cmd in connect_cmds)
                continue
            cmd_type, parsed = parse_voltage_or_current_value(line)
            if cmd_type == "FV" and parsed:
                fv_parts.append(f"{pin_name}={parsed}")

    spi_pins = build_spi_pins(pins)
    if "GND" in allowed_pin_names:
        gnd_display = None
    else:
        gnd_display = None
    if fv_parts:
        commands.append(f"FV[{','.join(dict.fromkeys(fv_parts))}]")
    if spi_pins:
        commands.append(f"SPI[{','.join(dict.fromkeys(spi_pins))}]")
    if connect_parts:
        commands.append(f"Connect[{','.join(dict.fromkeys(connect_parts))}]")
    if float_parts:
        commands.append(f"Float[{','.join(dict.fromkeys(float_parts))}]")

    writes = extract_register_writes(test_method)
    if writes:
        commands.append(f"WR[{','.join(dict.fromkeys(writes))}]")

    target_pin = extract_target_pin_from_test_name(test_name, allowed_pin_names)
    is_iold = test_name.startswith("IOLD_")
    is_rdson = "Rdson" in test_name or "RDSON" in test_name
    is_clk = test_name.startswith("clk_ocp")

    if "Ramp OUTx" in test_method or "Ramp OUTx 脚电流" in test_method:
        ramp_target = target_pin or "OUTx"
        commands.append(f"RampI[{ramp_target},auto,auto,auto]")

    if "nFAULT拉低" in test_method or "NFAULT拉低" in test_method or "nFAULT" in test_method:
        nfault_pin = "Nfault" if "Nfault" in allowed_pin_names else None
        if nfault_pin:
            commands.append(f"Monitor[{nfault_pin}=Low]")

    if "频率" in test_method and "nFAULT" in test_method:
        nfault_pin = "Nfault" if "Nfault" in allowed_pin_names else None
        if nfault_pin:
            commands.append(f"MT[{nfault_pin}]")
            commands.append(f"Display[MT[{nfault_pin}]]")
        return commands

    if is_rdson:
        if target_pin:
            if "Source 0.5A/MV" in json.dumps(pins, ensure_ascii=False):
                commands.append(f"FI[{target_pin}=-0.5A]")
            commands.append(f"MV[{target_pin}]")
            commands.append(f"Display[MV[{target_pin}]]")
        return commands

    if is_iold or test_name.startswith("Iocp_") or test_name.startswith("IOCP_"):
        if target_pin:
            commands.append(f"MI[{target_pin}]")
            commands.append(f"Display[MI[{target_pin}]]")
        return commands

    if is_clk:
        nfault_pin = "Nfault" if "Nfault" in allowed_pin_names else None
        if nfault_pin:
            commands.append(f"MT[{nfault_pin}]")
            commands.append(f"Display[MT[{nfault_pin}]]")
        return commands

    return commands if commands else None


def parse_method_line(line: str, allowed_pin_names: Set[str]) -> List[str]:
    text = normalize_units(normalize_ascii_punctuation(STEP_LINE_PATTERN.sub("", line).strip()))
    if not text:
        return []

    commands: List[str] = []

    delay_match = re.search(r"(?:延迟|Delay)\s*([0-9]+(?:\.[0-9]+)?\s*(?:ms|us|s|mS|uS|nS))", text, re.IGNORECASE)
    if delay_match:
        commands.append(f"Delay[{delay_match.group(1).replace(' ', '')}]")

    apply_match = re.search(r"apply voltage\s+([-\w\.]+)\s+on\s+([A-Za-z0-9_ ]+?)\s+with", text, re.IGNORECASE)
    if apply_match:
        voltage, node = apply_match.groups()
        commands.append(f"Display[ApplyVoltage[{normalize_text(node)}={voltage}]]")

    if "when" in text.lower():
        when_match = re.search(r"when\s+(.+)", text, re.IGNORECASE)
        if when_match:
            commands.append(f"Monitor[{normalize_text(when_match.group(1))}]")

    wr_matches = re.findall(r"([0-9A-Fa-f]{2})\s*[-=]\s*([0-9A-Fa-f]{2})", text)
    if wr_matches:
        items = [f"{addr}={value}" for addr, value in wr_matches]
        commands.append(f"WR[{','.join(items)}]")

    ramp_out_match = re.search(r"Ramp\s+OUTx\s+脚?电流", text, re.IGNORECASE)
    if ramp_out_match:
        commands.append("RampI[OUTx,auto,auto,auto]")

    ramp_pin_match = re.search(r"Ramp\s+([A-Za-z0-9_]+)\s+脚?(电压|电流)", text, re.IGNORECASE)
    if ramp_pin_match:
        pin_name, quantity = ramp_pin_match.groups()
        if pin_name in allowed_pin_names:
            if quantity == "电流":
                commands.append(f"RampI[{pin_name},auto,auto,auto]")
            else:
                commands.append(f"RampV[{pin_name},auto,auto,auto]")

    upper_text = text.upper()

    if "记录对应" in text and "电流值" in text:
        nfault_name = "Nfault" if "Nfault" in allowed_pin_names else ("ERR" if "ERR" in allowed_pin_names else None)
        if nfault_name:
            commands.append(f"Monitor[{nfault_name}=Low]")
        if "OUT1" in upper_text:
            commands.append("MI[OUT1]")
        if "OUT2" in upper_text:
            commands.append("MI[OUT2]")

    if "频率" in text and ("nFAULT" in text or "NFAULT" in text):
        nfault_name = "Nfault" if "Nfault" in allowed_pin_names else ("ERR" if "ERR" in allowed_pin_names else None)
        if nfault_name:
            commands.append(f"MT[{nfault_name}]")

    for pin_name in allowed_pin_names:
        if f"IV{pin_name.upper()}" in upper_text or f"I{pin_name.upper()}" in upper_text:
            commands.append(f"MI[{pin_name}]")
        if f"V{pin_name.upper()}" in upper_text:
            commands.append(f"MV[{pin_name}]")

    return list(dict.fromkeys(commands))


def convert_test_method_to_commands(test_method: str, allowed_pin_names: Set[str]) -> List[str]:
    raw_commands: List[str] = []
    for line in clean_multiline(test_method):
        raw_commands.extend(parse_method_line(line, allowed_pin_names))
    buckets = split_commands_by_type(raw_commands)
    return order_grouped_commands(buckets, allowed_pin_names)


def parse_natural_language_to_pseudocode(test_method: str, pins: Dict[str, str], allowed_pin_names: Set[str], test_name: str = "") -> List[str]:
    """
    按照规则将自然语言测试方法转换为伪代码格式
    1. 读取pins配置和test_method，求同存异
    2. 严格遵循提供的伪代码规则进行转换
    """
    commands: List[str] = []
    test_method_text = normalize_text(str(test_method))

    # 第一步：处理引脚配置（pins字段）
    fv_settings: Dict[str, str] = {}  # 电压设置
    fi_settings: Dict[str, str] = {}  # 电流设置
    float_pins: List[str] = []        # 浮空引脚
    connect_commands: List[str] = []  # 连接命令

    for pin_header, pin_value in pins.items():
        pin_name = normalize_pin_name(pin_header)
        if pin_name not in allowed_pin_names:
            continue

        value = normalize_text(str(pin_value))

        # 1. 浮空引脚处理
        if "悬空" in value or is_float_value(value):
            float_pins.append(pin_name)
            continue

        # 2. 电压设置 FV
        # 匹配数字电压值（如：12, 12V, 0, 0V）
        voltage_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:V|v)?', value)
        if voltage_match and not re.search(r'方波|信号|扫描', value):
            voltage_num = voltage_match.group(1)
            voltage_unit = 'V'
            fv_settings[pin_name] = f"{voltage_num}{voltage_unit}"
            continue

        # 3. 电流设置 FI（如果需要）
        # TODO: 根据具体内容识别电流配置

    # 第二步：处理测试方法（test_method字段）

    # 1. FV命令 - 电压设置
    if fv_settings:
        fv_parts = [f"{pin}={voltage}" for pin, voltage in fv_settings.items()]
        commands.append(f"FV[{','.join(fv_parts)}]")

    # 2. Float命令 - 浮空引脚
    if float_pins:
        commands.append(f"Float[{','.join(float_pins)}]")

    # 3. Delay命令 - 延迟时间
    if "延迟" in test_method_text or "delay" in test_method_text.lower():
        # 匹配各种时间格式
        time_matches = re.findall(r'(\d+(?:\.\d+)?)\s*(ms|mS|us|uS|ns|nS|s)', test_method_text, re.IGNORECASE)
        for time_val, time_unit in time_matches:
            unit_map = {'ms': 'ms', 'us': 'us', 'ns': 'ns', 's': 's'}
            normalized_unit = unit_map.get(time_unit.lower(), 'ms')
            commands.append(f"Delay[{time_val}{normalized_unit}]")

    # 4. MI命令 - 电流测量
    if any(keyword in test_method_text for keyword in ["测电流", "电流稳定", "电流就是", "MI"]):
        # 根据测试名称和上下文判断测量引脚
        if "IDD" in test_name and "VDD" in test_method_text:
            commands.append("MI[VDD]")
        elif "IHB" in test_name and "HB" in test_method_text:
            commands.append("MI[HB]")
        elif "HS" in test_method_text:
            commands.append("MI[HS]")

    # 5. MV命令 - 电压测量
    if any(keyword in test_method_text for keyword in ["测电压", "电压稳定", "MV"]):
        # 根据上下文判断
        if "EN" in test_method_text:
            commands.append("MV[EN]")
        elif "HB" in test_method_text:
            commands.append("MV[HB]")

    # 6. WR命令 - 寄存器写入
    wr_matches = re.findall(r'([0-9A-Fa-f]{1,2})\s*[=-]\s*([0-9A-Fa-f]{1,2})', test_method_text)
    if wr_matches:
        wr_parts = [f"{addr}={value}" for addr, value in wr_matches]
        commands.append(f"WR[{','.join(wr_parts)}]")

    # 7. FI命令 - 电流设置（方波信号）
    if "方波信号" in test_method_text:
        if "HI" in test_method_text and "0到5V" in test_method_text:
            commands.append("FI[HI=0A,5A,500K]")
        if "LI" in test_method_text and "0到5V" in test_method_text:
            commands.append("FI[LI=0A,5A,500K]")

    # 8. Connect命令 - 外部连接
    if "挂" in test_method_text:
        # 电容连接
        cap_matches = re.findall(r'(\w+)对(\w+)挂(\S+)', test_method_text)
        for pin, comp, value in cap_matches:
            pin_norm = normalize_pin_name(pin)
            comp_norm = normalize_text(comp)
            if pin_norm in allowed_pin_names:
                connect_commands.append(f"{pin_norm}-{value}-{comp_norm}")

    if connect_commands:
        commands.append(f"Connect[{','.join(connect_commands)}]")

    # 9. RampV/RampI命令 - 电压/电流扫描
    if "扫描" in test_method_text:
        if "V" in test_method_text:
            for pin in allowed_pin_names:
                if pin in test_method_text and pin != "VSS":
                    commands.append(f"RampV[{pin},auto,auto,auto]")
        elif "A" in test_method_text or "电流" in test_method_text:
            for pin in allowed_pin_names:
                if pin in test_method_text:
                    commands.append(f"RampI[{pin},auto,auto,auto]")

    # 去重
    seen = set()
    unique_commands = []
    for cmd in commands:
        if cmd not in seen:
            seen.add(cmd)
            unique_commands.append(cmd)

    return unique_commands

def convert_record(record: Dict[str, object], sequence_number: int, allowed_pin_names: Set[str]) -> List[object]:
    """转换单个测试记录"""
    section = normalize_text(str(record.get("section", ""))) or "General"
    test_name = normalize_text(str(record.get("test_name", "")))
    test_method = str(record.get("test_method", ""))
    unit = normalize_text(str(record.get("unit", "")))
    pins = record.get("pins", {})

    if not isinstance(pins, dict):
        pins = {}

    # 使用新的自然语言解析逻辑
    commands = parse_natural_language_to_pseudocode(test_method, pins, allowed_pin_names, test_name)

    # 去重
    unique_commands = list(dict.fromkeys(commands))

    return [section, f"{sequence_number}", test_name, ",".join(unique_commands), unit]


def convert_json(input_data: Dict[str, object]) -> Dict[str, object]:
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
        "pin_order": build_pin_order(pin_columns),
        "records": output_records,
    }


def build_default_output_path(input_path: Path) -> Path:
    return input_path.with_name(f"{input_path.stem}_pseudocode.json")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert extracted test-item JSON into exchange-style pseudocode JSON."
    )
    parser.add_argument("--input", required=True, help="Input JSON path.")
    parser.add_argument("--output", default=None, help="Optional output JSON path.")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    input_path = Path(args.input)

    if not input_path.exists():
        raise FileNotFoundError(f"Input JSON not found: {input_path}")
    if input_path.suffix.lower() != ".json":
        raise ValueError("Only .json input files are supported.")

    input_data = load_input(input_path)
    output_data = convert_json(input_data)
    output_path = Path(args.output) if args.output else build_default_output_path(input_path)
    output_text = json.dumps(output_data, ensure_ascii=False, indent=2 if args.pretty else None)
    output_path.write_text(output_text, encoding="utf-8")
    print(output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
