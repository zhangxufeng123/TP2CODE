---
name: excel-read-test-items
description: Extract test items from a multi-sheet `.xlsx` workbook by locating the worksheet whose name contains `FT Test Plan` or `Final test plan`, then reading the data rows under the detected header block. Use when Codex needs to parse Excel test plan files and extract each test item's `Test Name`, `Test Method`, `Unit`, and all valid PIN columns as structured JSON.
---

# Excel Read Test Items

Use the bundled Python script to inspect an `.xlsx` workbook, find the worksheet whose name matches `FT Test Plan` or `Final test plan`, detect the worksheet header rows, and extract structured test items from the data rows below.
Prefer this skill for semiconductor or board-test plan workbooks that contain many repeated sections and need item-level extraction rather than header-only inspection.

## Workflow

1. Confirm the workbook path. If not provided, auto-detect a single `.xlsx` file in the current working directory.
2. Search worksheet names in order for `FT Test Plan`, then `Final test plan`.
3. Detect the correct multi-row header block automatically, or pass `--header-row` if it is known.
4. Identify the `Test Name`, `Test Method`, `Unit`, and valid `PIN` columns from the chosen header block.
5. Read the data rows below the header block and extract each test item into JSON.
6. Skip placeholder PIN headers such as `PIN17 XXX`.

## Commands

Default workflow:

```powershell
python scripts/extract_test_items.py
```

Read a specific workbook:

```powershell
python scripts/extract_test_items.py --input FT_Test_Plan.xlsx
```

Choose a worksheet explicitly:

```powershell
python scripts/extract_test_items.py --input FT_Test_Plan.xlsx --sheet "JWXX JPXX Final test plan"
```

Write to a specific JSON file:

```powershell
python scripts/extract_test_items.py --input FT_Test_Plan.xlsx --output FT_Test_Plan_items.json --pretty
```

List worksheet names:

```powershell
python scripts/extract_test_items.py --input FT_Test_Plan.xlsx --list-sheets --pretty
```

## Output Rules

- Support `.xlsx` only.
- Do not require a fixed workbook filename.
- If `--input` is omitted, auto-detect a single `.xlsx` workbook in the current directory.
- Default worksheet matching order is `FT Test Plan`, then `Final test plan`.
- Expand merged cells before extracting headers and row values.
- Combine adjacent header rows when the worksheet uses multi-row headers.
- Convert header line breaks into spaces, for example `PIN1 VIN`.
- Drop placeholder PIN headers whose suffix is a placeholder such as `XXX`.
- Extract the following for each test item row:
  - `test_name`
  - `test_method`
  - `unit`
  - `pins`
- Preserve multi-line cell values inside data rows by keeping line breaks in JSON strings.

## Files

- `scripts/extract_test_items.py`: main workbook test-item extractor
- `agents/openai.yaml`: skill UI metadata
