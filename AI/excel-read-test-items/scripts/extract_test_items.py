#!/usr/bin/env python3
"""Extract test items from an Excel test-plan workbook without third-party packages."""

from __future__ import annotations

import argparse
import json
import re
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple
from xml.etree import ElementTree as ET

NS_MAIN = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
NS_REL = "http://schemas.openxmlformats.org/package/2006/relationships"
NS_DOC_REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
DEFAULT_SHEET_PATTERNS = ("FT Test Plan", "Final test plan")
HEADER_ANCHORS = ("Test #", "Program Type", "Test Name", "Test Method")
PIN_PLACEHOLDERS = {"XXX", "TBD", "N/A", "NA", "NC", "DUMMY"}
SECTION_HEADER_PATTERN = re.compile(r"^\d+(?:\.\d+)?\s*[\.\)]?\s+.+$")


@dataclass
class WorkbookSheet:
    name: str
    path: str


def excel_column_index(column_name: str) -> int:
    value = 0
    for char in column_name:
        if not char.isalpha():
            continue
        value = value * 26 + (ord(char.upper()) - ord("A") + 1)
    return value


def column_name_from_index(index: int) -> str:
    if index < 1:
        raise ValueError("Excel column indexes start at 1.")

    letters: List[str] = []
    current = index
    while current > 0:
        current, remainder = divmod(current - 1, 26)
        letters.append(chr(ord("A") + remainder))
    return "".join(reversed(letters))


def cell_reference_parts(reference: str) -> Tuple[str, int]:
    letters: List[str] = []
    digits: List[str] = []
    for char in reference:
        if char.isalpha():
            letters.append(char.upper())
        elif char.isdigit():
            digits.append(char)
    if not digits:
        return "".join(letters), 0
    return "".join(letters), int("".join(digits))


def normalize_text(value: str) -> str:
    return " ".join(value.replace("\n", " ").split()).strip()


def clean_cell_text(value: str) -> str:
    return "\n".join(
        line for line in (" ".join(line.split()).strip() for line in value.splitlines()) if line
    )


def clean_header_text(value: str) -> str:
    lines = [" ".join(line.split()).strip() for line in value.splitlines()]
    lines = [line for line in lines if line]
    if lines:
        return " ".join(lines)
    return " ".join(value.split()).strip()


def normalize_match_text(value: str) -> str:
    return normalize_text(value).casefold()


def contains_phrase(text: str, phrase: str) -> bool:
    normalized_text = normalize_match_text(text)
    normalized_phrase = normalize_match_text(phrase)
    if not normalized_phrase:
        return False
    pattern = rf"(?<![a-z0-9]){re.escape(normalized_phrase)}(?![a-z0-9])"
    return re.search(pattern, normalized_text) is not None


def slugify_filename(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9._-]+", "-", value).strip("-._")
    return slug or "sheet"


def resolve_input_path(input_value: Optional[str], cwd: Path) -> Path:
    if input_value:
        return Path(input_value)

    candidates = sorted(
        path for path in cwd.glob("*.xlsx") if path.is_file() and not path.name.startswith("~$")
    )
    if not candidates:
        raise FileNotFoundError("No .xlsx workbook found in the current working directory.")
    if len(candidates) == 1:
        return candidates[0]

    available = ", ".join(path.name for path in candidates)
    raise ValueError(
        "Multiple .xlsx workbooks found in the current working directory. "
        f"Pass --input explicitly. Available files: {available}"
    )


def load_shared_strings(archive: zipfile.ZipFile) -> List[str]:
    try:
        with archive.open("xl/sharedStrings.xml") as handle:
            tree = ET.parse(handle)
    except KeyError:
        return []

    values: List[str] = []
    for item in tree.getroot().findall(f"{{{NS_MAIN}}}si"):
        parts: List[str] = []
        for text_node in item.iterfind(f".//{{{NS_MAIN}}}t"):
            parts.append(text_node.text or "")
        values.append("".join(parts))
    return values


def load_workbook_sheets(archive: zipfile.ZipFile) -> List[WorkbookSheet]:
    with archive.open("xl/workbook.xml") as workbook_handle:
        workbook_tree = ET.parse(workbook_handle)
    with archive.open("xl/_rels/workbook.xml.rels") as rels_handle:
        rels_tree = ET.parse(rels_handle)

    relationships: Dict[str, str] = {}
    for rel in rels_tree.getroot().findall(f"{{{NS_REL}}}Relationship"):
        relationships[rel.attrib["Id"]] = rel.attrib["Target"]

    sheets: List[WorkbookSheet] = []
    for sheet in workbook_tree.getroot().findall(f".//{{{NS_MAIN}}}sheet"):
        rel_id = sheet.attrib[f"{{{NS_DOC_REL}}}id"]
        target = relationships[rel_id]
        if not target.startswith("worksheets/"):
            continue
        sheets.append(WorkbookSheet(name=sheet.attrib["name"], path=f"xl/{target}"))
    return sheets


def select_sheet(
    sheets: List[WorkbookSheet],
    sheet_name: Optional[str],
    sheet_name_contains: Optional[List[str]],
) -> Tuple[WorkbookSheet, Optional[str]]:
    if not sheets:
        raise ValueError("Workbook does not contain any worksheet.")

    if sheet_name:
        for sheet in sheets:
            if sheet.name == sheet_name:
                return sheet, None
        available = ", ".join(sheet.name for sheet in sheets)
        raise ValueError(f"Worksheet '{sheet_name}' not found. Available sheets: {available}")

    if sheet_name_contains:
        for phrase in sheet_name_contains:
            matches = [sheet for sheet in sheets if contains_phrase(sheet.name, phrase)]
            if len(matches) == 1:
                return matches[0], phrase
            if len(matches) > 1:
                names = ", ".join(sheet.name for sheet in matches)
                raise ValueError(
                    f"Multiple worksheets match '{phrase}': {names}. "
                    "Pass --sheet to choose one explicitly."
                )
        available = ", ".join(sheet.name for sheet in sheets)
        tried = ", ".join(f"'{phrase}'" for phrase in sheet_name_contains)
        raise ValueError(
            f"No worksheet name matches any of {tried}. Available sheets: {available}"
        )

    return sheets[0], None


def read_cell_value(cell: ET.Element, shared_strings: List[str]) -> str:
    cell_type = cell.attrib.get("t")
    value_node = cell.find(f"{{{NS_MAIN}}}v")
    inline_node = cell.find(f"{{{NS_MAIN}}}is")

    if cell_type == "inlineStr" and inline_node is not None:
        texts = [node.text or "" for node in inline_node.iterfind(f".//{{{NS_MAIN}}}t")]
        return "".join(texts).strip()

    if value_node is None:
        return ""

    raw_value = value_node.text or ""
    if cell_type == "s":
        try:
            return shared_strings[int(raw_value)].strip()
        except (ValueError, IndexError):
            return raw_value.strip()
    return raw_value.strip()


def parse_merge_range(reference: str) -> Tuple[str, int, str, int]:
    start_ref, end_ref = reference.split(":", 1)
    start_col, start_row = cell_reference_parts(start_ref)
    end_col, end_row = cell_reference_parts(end_ref)
    return start_col, start_row, end_col, end_row


def load_merged_cells(sheet_root: ET.Element) -> Dict[Tuple[int, str], str]:
    merge_map: Dict[Tuple[int, str], str] = {}
    merge_cells = sheet_root.find(f"{{{NS_MAIN}}}mergeCells")
    if merge_cells is None:
        return merge_map

    for merge_cell in merge_cells.findall(f"{{{NS_MAIN}}}mergeCell"):
        reference = merge_cell.attrib.get("ref")
        if not reference or ":" not in reference:
            continue
        start_col, start_row, end_col, end_row = parse_merge_range(reference)
        for row_number in range(start_row, end_row + 1):
            for column_index in range(excel_column_index(start_col), excel_column_index(end_col) + 1):
                merge_map[(row_number, column_name_from_index(column_index))] = f"{start_col}{start_row}"
    return merge_map


def iter_rows(sheet_root: ET.Element, shared_strings: List[str]) -> Iterable[Tuple[int, Dict[str, str]]]:
    for row in sheet_root.findall(f".//{{{NS_MAIN}}}row"):
        row_number = int(row.attrib["r"])
        values: Dict[str, str] = {}
        for cell in row.findall(f"{{{NS_MAIN}}}c"):
            reference = cell.attrib.get("r", "")
            column_name, _ = cell_reference_parts(reference)
            if not column_name:
                continue
            values[column_name] = read_cell_value(cell, shared_strings)
        yield row_number, values


def apply_merged_cells(
    rows_by_number: Dict[int, Dict[str, str]],
    merged_cells: Dict[Tuple[int, str], str],
) -> None:
    for (row_number, column_name), anchor_ref in merged_cells.items():
        anchor_column, anchor_row = cell_reference_parts(anchor_ref)
        anchor_value = rows_by_number.get(anchor_row, {}).get(anchor_column, "")
        if not normalize_text(anchor_value):
            continue

        row_values = rows_by_number.setdefault(row_number, {})
        current_value = row_values.get(column_name, "")
        if normalize_text(current_value):
            continue
        row_values[column_name] = anchor_value


def row_non_empty_count(values: Dict[str, str]) -> int:
    return sum(1 for value in values.values() if normalize_text(value))


def row_text_count(values: Dict[str, str]) -> int:
    count = 0
    for value in values.values():
        text = normalize_text(value)
        if not text:
            continue
        try:
            float(text)
        except ValueError:
            count += 1
    return count


def row_header_score(values: Dict[str, str]) -> float:
    non_empty = row_non_empty_count(values)
    if non_empty == 0:
        return 0.0

    text_count = row_text_count(values)
    unique_count = len(
        {
            normalize_text(value).lower()
            for value in values.values()
            if normalize_text(value)
        }
    )
    return non_empty * 2.0 + text_count * 1.5 + unique_count * 0.5


def header_anchor_match_count(values: Dict[str, str]) -> int:
    normalized_values = {
        normalize_text(value).casefold()
        for value in values.values()
        if normalize_text(value)
    }
    return sum(1 for anchor in HEADER_ANCHORS if anchor.casefold() in normalized_values)


def choose_header_row(rows: List[Tuple[int, Dict[str, str]]], scan_limit: int) -> Tuple[int, Dict[str, str]]:
    best_row_number = 0
    best_values: Dict[str, str] = {}
    best_score = -1.0

    for row_number, values in rows:
        if row_number > max(scan_limit, 1):
            break
        score = row_header_score(values)
        if score > best_score:
            best_row_number = row_number
            best_values = values
            best_score = score

    if best_row_number == 0:
        raise ValueError("Could not identify a header row in the worksheet.")
    return best_row_number, best_values


def infer_header_rows(
    rows_by_number: Dict[int, Dict[str, str]],
    primary_header_row: int,
    max_extra_rows: int = 2,
) -> List[int]:
    selected = [primary_header_row]
    previous_non_empty = row_non_empty_count(rows_by_number.get(primary_header_row, {}))

    for next_row in range(primary_header_row + 1, primary_header_row + max_extra_rows + 1):
        values = rows_by_number.get(next_row, {})
        non_empty = row_non_empty_count(values)
        if non_empty == 0:
            break
        if non_empty <= previous_non_empty and non_empty <= 12:
            selected.append(next_row)
            previous_non_empty = non_empty
            continue
        break

    return selected


def combine_header_parts(parts: List[str]) -> str:
    seen: List[str] = []
    kept_parts: List[str] = []
    for part in parts:
        text = clean_header_text(part)
        normalized = normalize_text(text)
        if not normalized:
            continue
        if not seen or seen[-1] != normalized:
            seen.append(normalized)
            kept_parts.append(text)
    return " / ".join(kept_parts)


def build_header_map(
    rows_by_number: Dict[int, Dict[str, str]],
    header_rows: List[int],
) -> Dict[str, str]:
    column_names = sorted(
        {
            column_name
            for row_number in header_rows
            for column_name in rows_by_number.get(row_number, {}).keys()
        },
        key=excel_column_index,
    )

    header_map: Dict[str, str] = {}
    for column_name in column_names:
        parts = [rows_by_number.get(row_number, {}).get(column_name, "") for row_number in header_rows]
        label = combine_header_parts(parts)
        header_map[column_name] = label or column_name
    return header_map


def score_header_map(header_map: Dict[str, str]) -> float:
    normalized_headers = [normalize_text(value) for value in header_map.values() if normalize_text(value)]
    lower_headers = {value.casefold() for value in normalized_headers}

    score = 10.0 * sum(1 for anchor in HEADER_ANCHORS if anchor.casefold() in lower_headers)
    score += len(normalized_headers) * 0.1

    generic_count = 0
    placeholder_count = 0
    specific_pin_count = 0

    for value in normalized_headers:
        if re.fullmatch(r"[A-Z]{1,3}", value):
            generic_count += 1

        pin_match = re.fullmatch(r"PIN\s*(\d+)\s+(.+)", value, re.IGNORECASE)
        if pin_match:
            suffix = pin_match.group(2).strip()
            if suffix.upper() in PIN_PLACEHOLDERS:
                placeholder_count += 1
            else:
                specific_pin_count += 1
            continue

        if re.search(r"\bXXX\b", value, re.IGNORECASE):
            placeholder_count += 1

    score += specific_pin_count * 4.0
    score -= placeholder_count * 2.5
    score -= generic_count * 1.5
    return score


def choose_best_header_rows(
    raw_rows_by_number: Dict[int, Dict[str, str]],
    expanded_rows_by_number: Dict[int, Dict[str, str]],
    scan_limit: int,
) -> Tuple[int, List[int]]:
    candidates: List[Tuple[float, int, List[int]]] = []

    for row_number in sorted(raw_rows_by_number):
        if row_number > max(scan_limit, 1):
            break

        values = raw_rows_by_number[row_number]
        if header_anchor_match_count(values) < 3:
            continue

        header_rows = infer_header_rows(raw_rows_by_number, row_number)
        header_map = build_header_map(expanded_rows_by_number, header_rows)
        candidates.append((score_header_map(header_map), row_number, header_rows))

    if candidates:
        _, best_row, best_rows = max(candidates, key=lambda item: (item[0], -item[1]))
        return best_row, best_rows

    fallback_row, _ = choose_header_row(sorted(raw_rows_by_number.items()), scan_limit)
    return fallback_row, infer_header_rows(raw_rows_by_number, fallback_row)


def is_placeholder_pin_header(value: str) -> bool:
    normalized = normalize_text(value)
    pin_match = re.fullmatch(r"PIN\s*(\d+)\s+(.+)", normalized, re.IGNORECASE)
    if not pin_match:
        return False
    suffix = pin_match.group(2).strip().upper()
    return suffix in PIN_PLACEHOLDERS


def classify_columns(header_map: Dict[str, str]) -> Tuple[Optional[str], Optional[str], Optional[str], List[Tuple[str, str]], Optional[str]]:
    test_name_column: Optional[str] = None
    test_method_column: Optional[str] = None
    unit_column: Optional[str] = None
    section_column: Optional[str] = None
    pin_columns: List[Tuple[str, str]] = []

    for column_name in sorted(header_map.keys(), key=excel_column_index):
        header = header_map[column_name]
        normalized = normalize_text(header).casefold()

        if normalized == "test name":
            test_name_column = column_name
            continue
        if normalized == "test method":
            test_method_column = column_name
            continue
        if normalized == "unit":
            unit_column = column_name
            continue

        if re.fullmatch(r"pin\s*\d+\s+.+", normalize_text(header), re.IGNORECASE):
            if is_placeholder_pin_header(header):
                continue
            pin_columns.append((column_name, header))
            continue

        if section_column is None and column_name in {"A", "B", "C", "K"}:
            section_column = column_name

    if section_column is None:
        section_column = "A"
    return test_name_column, test_method_column, unit_column, pin_columns, section_column


def is_section_header_row(row_values: Dict[str, str], section_column: str, test_name_column: Optional[str]) -> bool:
    section_text = normalize_text(row_values.get(section_column, ""))
    if not section_text:
        return False
    if not SECTION_HEADER_PATTERN.match(section_text):
        return False

    if test_name_column and normalize_text(row_values.get(test_name_column, "")):
        return False

    populated = [normalize_text(value) for value in row_values.values() if normalize_text(value)]
    return len(populated) <= 3


def is_data_row(
    row_values: Dict[str, str],
    test_name_column: Optional[str],
    test_method_column: Optional[str],
    unit_column: Optional[str],
    pin_columns: List[Tuple[str, str]],
) -> bool:
    if test_name_column and normalize_text(row_values.get(test_name_column, "")):
        return True
    if test_method_column and normalize_text(row_values.get(test_method_column, "")):
        return True
    if unit_column and normalize_text(row_values.get(unit_column, "")):
        return True
    return any(normalize_text(row_values.get(column_name, "")) for column_name, _ in pin_columns)


def is_repeated_header_row(
    row_values: Dict[str, str],
    test_name_column: Optional[str],
    test_method_column: Optional[str],
    unit_column: Optional[str],
) -> bool:
    expected = []
    if test_name_column:
        expected.append((test_name_column, "test name"))
    if test_method_column:
        expected.append((test_method_column, "test method"))
    if unit_column:
        expected.append((unit_column, "unit"))

    if not expected:
        return False

    matches = 0
    for column_name, expected_text in expected:
        value = normalize_text(row_values.get(column_name, "")).casefold()
        if value == expected_text:
            matches += 1
    return matches >= 2


def compact_pin_values(
    row_values: Dict[str, str],
    pin_columns: List[Tuple[str, str]],
) -> Dict[str, str]:
    values: Dict[str, str] = {}
    for column_name, header in pin_columns:
        value = clean_cell_text(row_values.get(column_name, ""))
        if not normalize_text(value):
            continue
        values[header] = value
    return values


def extract_test_items(
    workbook_path: Path,
    sheet_name: Optional[str],
    sheet_name_contains: Optional[List[str]],
    header_row: Optional[int],
    scan_limit: int,
) -> Dict[str, object]:
    with zipfile.ZipFile(workbook_path) as archive:
        shared_strings = load_shared_strings(archive)
        sheets = load_workbook_sheets(archive)
        chosen_sheet, matched_phrase = select_sheet(sheets, sheet_name, sheet_name_contains)
        with archive.open(chosen_sheet.path) as sheet_handle:
            sheet_tree = ET.parse(sheet_handle)

    sheet_root = sheet_tree.getroot()
    merged_cells = load_merged_cells(sheet_root)
    raw_rows = list(iter_rows(sheet_root, shared_strings))
    raw_rows_by_number = {row_number: dict(values) for row_number, values in raw_rows}
    rows_by_number = {row_number: dict(values) for row_number, values in raw_rows}
    apply_merged_cells(rows_by_number, merged_cells)

    if header_row is None:
        detected_row, header_rows = choose_best_header_rows(raw_rows_by_number, rows_by_number, scan_limit)
        header_source = "detected"
    else:
        detected_row = header_row
        if row_non_empty_count(raw_rows_by_number.get(header_row, {})) == 0:
            raise ValueError(f"Header row {header_row} is empty or missing in worksheet '{chosen_sheet.name}'.")
        header_source = "explicit"
        header_rows = infer_header_rows(raw_rows_by_number, detected_row)

    header_map = build_header_map(rows_by_number, header_rows)
    test_name_column, test_method_column, unit_column, pin_columns, section_column = classify_columns(header_map)

    if test_name_column is None:
        raise ValueError("Could not identify the 'Test Name' column.")
    if test_method_column is None:
        raise ValueError("Could not identify the 'Test Method' column.")
    if unit_column is None:
        raise ValueError("Could not identify the 'Unit' column.")
    if not pin_columns:
        # 如果都是占位符，临时启用占位符处理
        for column_name in sorted(header_map.keys(), key=excel_column_index):
            header = header_map[column_name]
            pin_match = re.fullmatch(r"PIN\s*(\d+)\s+(.+)", normalize_text(header), re.IGNORECASE)
            if pin_match:
                pin_columns.append((column_name, header))

        if not pin_columns:
            raise ValueError("Could not identify any valid PIN columns.")

    data_start_row = max(header_rows) + 1
    current_section = ""
    records: List[Dict[str, object]] = []

    for row_number in sorted(rows_by_number.keys()):
        if row_number < data_start_row:
            continue

        row_values = rows_by_number[row_number]
        if is_section_header_row(row_values, section_column, test_name_column):
            current_section = clean_cell_text(row_values.get(section_column, ""))
            continue

        if is_repeated_header_row(row_values, test_name_column, test_method_column, unit_column):
            continue

        if not is_data_row(row_values, test_name_column, test_method_column, unit_column, pin_columns):
            continue

        record = {
            "row_number": row_number,
            "section": current_section,
            "test_name": clean_cell_text(row_values.get(test_name_column, "")),
            "test_method": clean_cell_text(row_values.get(test_method_column, "")),
            "unit": clean_cell_text(row_values.get(unit_column, "")),
            "pins": compact_pin_values(row_values, pin_columns),
        }

        if not (record["test_name"] or record["test_method"] or record["unit"] or record["pins"]):
            continue

        records.append(record)

    return {
        "input_file": str(workbook_path),
        "sheet_name": chosen_sheet.name,
        "sheet_name_match": matched_phrase,
        "header_row": detected_row,
        "header_rows": header_rows,
        "header_source": header_source,
        "test_name_column": test_name_column,
        "test_method_column": test_method_column,
        "unit_column": unit_column,
        "pin_columns": [{"column": column_name, "header": header} for column_name, header in pin_columns],
        "records": records,
    }


def build_default_output_path(workbook_path: Path, sheet_name: str) -> Path:
    sheet_slug = slugify_filename(sheet_name)
    return workbook_path.with_name(f"{workbook_path.stem}_{sheet_slug}_test_items.json")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Extract test items from an .xlsx workbook.")
    parser.add_argument(
        "--input",
        default=None,
        help="Path to the input .xlsx workbook. If omitted, auto-detect a single workbook in the current directory.",
    )
    parser.add_argument(
        "--sheet",
        default=None,
        help="Worksheet name. Overrides keyword matching when provided.",
    )
    parser.add_argument(
        "--sheet-name-contains",
        action="append",
        default=None,
        help="Worksheet name phrase to match. Repeat this option to try multiple phrases in order.",
    )
    parser.add_argument(
        "--header-row",
        type=int,
        default=None,
        help="Explicit first header row number. If omitted, the script will auto-detect it.",
    )
    parser.add_argument(
        "--scan-limit",
        type=int,
        default=500,
        help="Scan rows from 1 through this row number when auto-detecting a header row. Default: 500",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Optional output JSON file path. Default: auto-generate next to the workbook.",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print JSON with indentation.",
    )
    parser.add_argument(
        "--list-sheets",
        action="store_true",
        help="List worksheet names and exit.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    workbook_path = resolve_input_path(args.input, Path.cwd())

    if not workbook_path.exists():
        raise FileNotFoundError(f"Input workbook not found: {workbook_path}")
    if workbook_path.suffix.lower() != ".xlsx":
        raise ValueError("Only .xlsx files are supported by this script.")

    if args.list_sheets:
        with zipfile.ZipFile(workbook_path) as archive:
            result = {
                "input_file": str(workbook_path),
                "sheets": [sheet.name for sheet in load_workbook_sheets(archive)],
            }
        output_text = json.dumps(result, ensure_ascii=False, indent=2 if args.pretty else None)
        if args.output:
            Path(args.output).write_text(output_text, encoding="utf-8")
        else:
            print(output_text)
        return 0

    sheet_name_contains = None if args.sheet else (args.sheet_name_contains or list(DEFAULT_SHEET_PATTERNS))
    result = extract_test_items(
        workbook_path=workbook_path,
        sheet_name=args.sheet,
        sheet_name_contains=sheet_name_contains,
        header_row=args.header_row,
        scan_limit=args.scan_limit,
    )

    output_text = json.dumps(result, ensure_ascii=False, indent=2 if args.pretty else None)
    output_path = Path(args.output) if args.output else build_default_output_path(
        workbook_path, str(result["sheet_name"])
    )
    output_path.write_text(output_text, encoding="utf-8")
    print(output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
