#!/usr/bin/env python3
"""
Read a local .xlsx file and print as a markdown table.

Usage:
  python3 excel_parser.py --file /path/to/file.xlsx

No network access or credentials required.
"""

import argparse
import io
import sys
import zipfile
import xml.etree.ElementTree as ET


def col_to_num(col):
    n = 0
    for c in col.upper():
        n = n * 26 + (ord(c) - ord("A") + 1)
    return n


def num_to_col(n):
    """Convert 1-based column number to letter(s): 1→A, 26→Z, 27→AA."""
    result = ""
    while n > 0:
        n, rem = divmod(n - 1, 26)
        result = chr(ord("A") + rem) + result
    return result


def col_ref_range(start_col, end_col):
    """Yield all column letters from start_col to end_col inclusive."""
    start = col_to_num(start_col)
    end = col_to_num(end_col)
    for n in range(start, end + 1):
        yield num_to_col(n)


def parse_cell_ref(ref):
    """Split 'AB12' into ('AB', 12)."""
    col = "".join(c for c in ref if c.isalpha())
    row = int("".join(c for c in ref if c.isdigit()))
    return col, row


def parse_xlsx(content):
    """Parse xlsx binary → list of row dicts keyed by column letter, respecting merged cells."""
    buf = io.BytesIO(content)
    try:
        zf = zipfile.ZipFile(buf)
    except zipfile.BadZipFile:
        sys.exit("ERROR: File is not a valid xlsx (bad zip). "
                 "It may be an .xls (old format) or corrupted.")

    names = zf.namelist()

    # Shared strings table
    shared_strings = []
    if "xl/sharedStrings.xml" in names:
        ns = {"s": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
        tree = ET.parse(zf.open("xl/sharedStrings.xml"))
        for si in tree.findall(".//s:si", ns):
            texts = [t.text or "" for t in si.findall(".//s:t", ns)]
            shared_strings.append("".join(texts))

    # First worksheet
    sheet_files = sorted(n for n in names if n.startswith("xl/worksheets/sheet") and n.endswith(".xml"))
    if not sheet_files:
        sys.exit("ERROR: No worksheets found inside the Excel file.")

    ns = {"s": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    tree = ET.parse(zf.open(sheet_files[0]))
    root = tree.getroot()

    # Identify pure extension columns (only ever non-anchor in merges) to drop
    anchor_cols = set()
    extension_cols = set()

    for mc in root.findall(".//s:mergeCells/s:mergeCell", ns):
        ref = mc.get("ref", "")
        if ":" not in ref:
            continue
        top_left, bottom_right = ref.split(":")
        tl_col, _ = parse_cell_ref(top_left)
        br_col, _ = parse_cell_ref(bottom_right)
        anchor_cols.add(tl_col)
        for c in col_ref_range(tl_col, br_col):
            if c != tl_col:
                extension_cols.add(c)

    pure_extension_cols = extension_cols - anchor_cols

    # Read cell values
    rows_raw = {}
    for cell in root.findall(".//s:sheetData/s:row/s:c", ns):
        ref = cell.get("r", "")
        col, row_num = parse_cell_ref(ref)
        if col in pure_extension_cols:
            continue
        cell_type = cell.get("t", "n")
        v_el = cell.find("s:v", ns)
        if v_el is None or v_el.text is None:
            value = ""
        elif cell_type == "s":
            idx = int(v_el.text)
            value = shared_strings[idx] if idx < len(shared_strings) else ""
        elif cell_type in ("str", "inlineStr"):
            t_el = cell.find(".//s:t", ns)
            value = t_el.text if t_el is not None else (v_el.text or "")
        else:
            value = v_el.text or ""
        rows_raw.setdefault(row_num, {})[col] = value

    return [rows_raw[r] for r in sorted(rows_raw.keys()) if rows_raw[r]]


def rows_to_markdown(rows):
    if not rows:
        return "*(empty sheet)*"

    all_cols = sorted({c for row in rows for c in row}, key=col_to_num)

    def cell(row, c):
        return row.get(c, "").replace("|", "\\|").replace("\n", " ").strip()

    # Drop columns with data in fewer than 10% of rows (layout/legend artifacts)
    data_rows = rows[1:]
    threshold = max(1, len(data_rows) * 0.10)
    active_cols = [c for c in all_cols if sum(1 for r in rows if cell(r, c)) >= threshold]

    if not active_cols:
        active_cols = all_cols

    headers = [cell(rows[0], c) for c in active_cols]
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in active_cols) + " |",
    ]
    for row in rows[1:]:
        if all(not cell(row, c) for c in active_cols):
            continue
        lines.append("| " + " | ".join(cell(row, c) for c in active_cols) + " |")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Read a local .xlsx file and print as a markdown table."
    )
    parser.add_argument("--file", required=True, help="Path to the .xlsx file")
    args = parser.parse_args()

    print(f"[INFO] Reading local file: {args.file}", file=sys.stderr)
    with open(args.file, "rb") as f:
        content = f.read()
    print(f"[INFO] Parsing Excel ({len(content):,} bytes)...", file=sys.stderr)
    rows = parse_xlsx(content)
    print(rows_to_markdown(rows))


if __name__ == "__main__":
    main()
