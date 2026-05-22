#!/usr/bin/env python3
"""
Read a local .docx or Confluence-exported .doc (MHTML) file and print as markdown.

Confluence's "Export → Word" produces a .doc file that is actually MHTML
(a MIME-wrapped HTML document), not a binary Word file. This script detects
the format automatically and handles both.

Usage:
  python3 docx_parser.py --file /path/to/file.docx
  python3 docx_parser.py --file /path/to/exported-page.doc

No network access or credentials required.
"""

import argparse
import email
import io
import quopri
import re
import sys
import zipfile
import xml.etree.ElementTree as ET

from html_utils import html_to_markdown

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"

_HEADING_RE = re.compile(r"(?:confluence)?heading(\d)")


# ---------------------------------------------------------------------------
# .docx parser
# ---------------------------------------------------------------------------

def _heading_level(style_val):
    if not style_val:
        return 0
    s = style_val.lower()
    if s == "title":
        return 1
    m = _HEADING_RE.match(s)
    return int(m.group(1)) if m else 0


def _para_style(para):
    ppr = para.find(f"{W}pPr")
    if ppr is None:
        return ""
    ps = ppr.find(f"{W}pStyle")
    return ps.get(f"{W}val", "") if ps is not None else ""


def _para_is_list(para):
    ppr = para.find(f"{W}pPr")
    if ppr is None:
        return False, 0
    numpr = ppr.find(f"{W}numPr")
    if numpr is None:
        return False, 0
    ilvl = numpr.find(f"{W}ilvl")
    level = int(ilvl.get(f"{W}val", "0")) if ilvl is not None else 0
    return True, level


def _para_text(para):
    return "".join(t.text or "" for t in para.findall(f".//{W}t"))


def _cell_text(tc):
    parts = []
    for p in tc.findall(f".//{W}p"):
        text = _para_text(p).strip()
        if text:
            parts.append(text)
    return " ".join(parts)


def _table_to_markdown(tbl):
    rows = []
    for tr in tbl.findall(f"{W}tr"):
        cells = [_cell_text(tc).replace("|", "\\|") for tc in tr.findall(f"{W}tc")]
        rows.append(cells)

    if not rows:
        return ""

    max_cols = max(len(r) for r in rows)
    rows = [r + [""] * (max_cols - len(r)) for r in rows]

    lines = [
        "| " + " | ".join(rows[0]) + " |",
        "| " + " | ".join("---" for _ in rows[0]) + " |",
    ]
    for row in rows[1:]:
        if any(c.strip() for c in row):
            lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)


def parse_docx(content):
    """Parse .docx binary → markdown string."""
    zf = zipfile.ZipFile(io.BytesIO(content))

    if "word/document.xml" not in zf.namelist():
        sys.exit("ERROR: word/document.xml not found — this may not be a valid .docx file.")

    root = ET.parse(zf.open("word/document.xml")).getroot()
    body = root.find(f"{W}body")
    if body is None:
        sys.exit("ERROR: No <w:body> found in document.xml.")

    lines = []
    for child in body:
        tag = child.tag

        if tag == f"{W}p":
            style = _para_style(child)
            text = _para_text(child).strip()
            level = _heading_level(style)

            if level:
                lines.append(f"\n{'#' * level} {text}\n" if text else "")
            else:
                is_list, ilvl = _para_is_list(child)
                if is_list and text:
                    indent = "  " * ilvl
                    lines.append(f"{indent}- {text}")
                else:
                    lines.append(text)

        elif tag == f"{W}tbl":
            md = _table_to_markdown(child)
            if md:
                lines.append("")
                lines.append(md)
                lines.append("")

    text = "\n".join(lines)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


# ---------------------------------------------------------------------------
# MHTML parser (Confluence "Export → Word" format)
# ---------------------------------------------------------------------------

def _is_mhtml(content):
    """Return True if the file looks like a MIME message (Confluence Word export)."""
    try:
        head = content[:300].decode("ascii", errors="ignore")
        return any(marker in head for marker in ("MIME-Version:", "Content-Type: multipart/", "Exported From Confluence"))
    except Exception:
        return False


def parse_mhtml(content):
    """Parse a Confluence MHTML export (.doc) → markdown string."""
    msg = email.message_from_bytes(content)

    for part in msg.walk():
        if part.get_content_type() == "text/html":
            raw = part.get_payload(decode=False)
            # Confluence MHTML payloads use quoted-printable without declaring it
            decoded = quopri.decodestring(
                raw.encode("ascii", errors="replace")
            ).decode("utf-8", errors="replace")

            # Extract only the <body> content
            m = re.search(r"<body[^>]*>(.*)</body>", decoded, re.DOTALL | re.IGNORECASE)
            body = m.group(1) if m else decoded

            # Strip inline <style> blocks Confluence embeds for colour tokens
            body = re.sub(r"<style\b[^>]*>.*?</style>", "", body, flags=re.DOTALL | re.IGNORECASE)

            return html_to_markdown(body)

    sys.exit("ERROR: No text/html part found in MHTML file.")


# ---------------------------------------------------------------------------
# Auto-detect entry point
# ---------------------------------------------------------------------------

def parse_file(content):
    """Detect format (.docx or MHTML .doc) and parse to markdown."""
    try:
        zipfile.ZipFile(io.BytesIO(content))
        return parse_docx(content)
    except zipfile.BadZipFile:
        pass

    if _is_mhtml(content):
        return parse_mhtml(content)

    sys.exit(
        "ERROR: Unrecognised file format.\n"
        "  Expected a .docx file or a Confluence MHTML export (.doc).\n"
        "  Export the page from Confluence via: page menu → Export → Word"
    )


def main():
    parser = argparse.ArgumentParser(
        description="Read a .docx or Confluence-exported .doc file and print as markdown."
    )
    parser.add_argument("--file", required=True, help="Path to the .docx or .doc file")
    args = parser.parse_args()

    print(f"[INFO] Reading: {args.file}", file=sys.stderr)
    with open(args.file, "rb") as f:
        content = f.read()
    print(f"[INFO] File size: {len(content):,} bytes", file=sys.stderr)
    print(parse_file(content))


if __name__ == "__main__":
    main()
