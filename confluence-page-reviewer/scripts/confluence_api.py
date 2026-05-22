#!/usr/bin/env python3
"""
Confluence REST API utilities — fetch page content, list attachments, read Excel attachments.

Modes:
  Fetch page content as markdown:
    python3 confluence_api.py --cloud-id myco.atlassian.net --page-id 123456789 --fetch-page

  List all attachments on a page:
    python3 confluence_api.py --cloud-id myco.atlassian.net --page-id 123456789 --list-attachments

  Download and read an Excel attachment:
    python3 confluence_api.py --cloud-id myco.atlassian.net --page-id 123456789
    python3 confluence_api.py --cloud-id myco.atlassian.net --page-id 123456789 --filename ItemDescription.xlsx

  Environment variables required:
    ATLASSIAN_EMAIL      - Your Atlassian account email
    ATLASSIAN_API_TOKEN  - Your Atlassian API token (https://id.atlassian.com/manage-profile/security/api-tokens)
"""

import argparse
import os
import re
import sys
import requests
from html.parser import HTMLParser
from requests.auth import HTTPBasicAuth

from excel_parser import parse_xlsx, rows_to_markdown


# ---------------------------------------------------------------------------
# HTML → markdown  (for --fetch-page output)
# ---------------------------------------------------------------------------

class _HtmlToMarkdown(HTMLParser):
    HEADING_TAGS = {'h1': 1, 'h2': 2, 'h3': 3, 'h4': 4, 'h5': 5, 'h6': 6}
    BLOCK_TAGS = {'p', 'div', 'ul', 'ol', 'blockquote', 'pre', 'section',
                  'article', 'header', 'footer', 'main', 'aside', 'nav'}
    SKIP_TAGS = {'style', 'script', 'head', 'meta', 'link', 'noscript'}

    def __init__(self):
        super().__init__()
        self.buf = []
        self._skip_depth = 0
        self._table_depth = 0
        self._in_cell = False
        self._cell_buf = []
        self._row_cells = []
        self._table_rows = []
        self._list_depth = 0
        self._ordered = []
        self._counters = []

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        if tag in self.SKIP_TAGS:
            self._skip_depth += 1
            return
        if self._skip_depth:
            return

        if tag in self.HEADING_TAGS:
            level = self.HEADING_TAGS[tag]
            self.buf.append(f'\n\n{"#" * level} ')
        elif tag == 'br':
            self.buf.append('\n')
        elif tag in self.BLOCK_TAGS:
            if not self._in_cell:
                self.buf.append('\n\n')
        elif tag == 'li':
            indent = '  ' * max(self._list_depth - 1, 0)
            if self._ordered and self._ordered[-1]:
                self._counters[-1] += 1
                self.buf.append(f'\n{indent}{self._counters[-1]}. ')
            else:
                self.buf.append(f'\n{indent}- ')
        elif tag == 'ul':
            self._list_depth += 1
            self._ordered.append(False)
            self._counters.append(0)
        elif tag == 'ol':
            self._list_depth += 1
            self._ordered.append(True)
            self._counters.append(0)
        elif tag == 'table':
            self._table_depth += 1
            if self._table_depth == 1:
                self._table_rows = []
        elif tag == 'tr':
            if self._table_depth == 1:
                self._row_cells = []
        elif tag in ('td', 'th'):
            if self._table_depth == 1:
                self._in_cell = True
                self._cell_buf = []

    def handle_endtag(self, tag):
        tag = tag.lower()
        if tag in self.SKIP_TAGS:
            self._skip_depth = max(self._skip_depth - 1, 0)
            return
        if self._skip_depth:
            return

        if tag in self.HEADING_TAGS:
            self.buf.append('\n')
        elif tag in ('ul', 'ol'):
            self._list_depth = max(self._list_depth - 1, 0)
            if self._ordered:
                self._ordered.pop()
            if self._counters:
                self._counters.pop()
            self.buf.append('\n')
        elif tag in self.BLOCK_TAGS:
            if not self._in_cell:
                self.buf.append('\n\n')
        elif tag in ('td', 'th'):
            if self._table_depth == 1:
                cell_text = ''.join(self._cell_buf).replace('|', '\\|').replace('\n', ' ').strip()
                self._row_cells.append(cell_text)
                self._in_cell = False
                self._cell_buf = []
        elif tag == 'tr':
            if self._table_depth == 1 and self._row_cells:
                self._table_rows.append(self._row_cells[:])
                self._row_cells = []
        elif tag == 'table':
            if self._table_depth == 1:
                self._flush_table()
            self._table_depth = max(self._table_depth - 1, 0)

    def _flush_table(self):
        if not self._table_rows:
            return
        self.buf.append('\n\n')
        header = self._table_rows[0]
        self.buf.append('| ' + ' | '.join(header) + ' |\n')
        self.buf.append('| ' + ' | '.join('---' for _ in header) + ' |\n')
        for row in self._table_rows[1:]:
            padded = row + [''] * max(0, len(header) - len(row))
            self.buf.append('| ' + ' | '.join(padded[:len(header)]) + ' |\n')
        self.buf.append('\n')
        self._table_rows = []

    def handle_data(self, data):
        if self._skip_depth:
            return
        if self._in_cell:
            self._cell_buf.append(data)
        else:
            self.buf.append(data)

    def get_text(self):
        text = ''.join(self.buf)
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text.strip()


def html_to_markdown(html):
    parser = _HtmlToMarkdown()
    parser.feed(html)
    return parser.get_text()


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

def get_auth():
    email = os.environ.get("ATLASSIAN_EMAIL")
    token = os.environ.get("ATLASSIAN_API_TOKEN")
    if not email or not token:
        sys.exit("ERROR: Set ATLASSIAN_EMAIL and ATLASSIAN_API_TOKEN environment variables.\n"
                 "  Get a token at: https://id.atlassian.com/manage-profile/security/api-tokens")
    return HTTPBasicAuth(email, token)


# ---------------------------------------------------------------------------
# API functions
# ---------------------------------------------------------------------------

def fetch_page(cloud_id, page_id, auth):
    """Fetch page title and HTML body via REST API; return (title, markdown_text)."""
    url = f"https://{cloud_id}/wiki/rest/api/content/{page_id}"
    resp = requests.get(url, auth=auth, params={"expand": "body.view,title"})
    resp.raise_for_status()
    data = resp.json()
    title = data.get("title", "")
    html = data.get("body", {}).get("view", {}).get("value", "")
    return title, html_to_markdown(html)


def list_attachments(cloud_id, page_id, auth):
    """Return list of attachment dicts using Confluence v2 API (covers both traditional and media files)."""
    url = f"https://{cloud_id}/wiki/api/v2/pages/{page_id}/attachments"
    results = []
    while url:
        resp = requests.get(url, auth=auth, params={"limit": 50})
        resp.raise_for_status()
        data = resp.json()
        results.extend(data.get("results", []))
        url = data.get("_links", {}).get("next")
        if url and not url.startswith("http"):
            url = f"https://{cloud_id}" + url
    return results


def find_excel(attachments, filename=None):
    """Find the target Excel attachment from the list."""
    excel_files = [a for a in attachments if a.get("title", "").lower().endswith((".xlsx", ".xls"))]
    all_titles = [a.get("title", "?") for a in attachments]

    print(f"[INFO] All attachments on page: {', '.join(all_titles) or 'none'}", file=sys.stderr)
    print(f"[INFO] Excel files found: {', '.join(a.get('title') for a in excel_files) or 'none'}", file=sys.stderr)

    if filename:
        for att in attachments:
            if att.get("title", "").lower() == filename.lower():
                return att
        sys.exit(f"ERROR: Attachment '{filename}' not found. Available files: " + ", ".join(all_titles))

    if not excel_files:
        sys.exit("ERROR: No .xlsx/.xls attachment found on this page.\nAll files: " + ", ".join(all_titles))

    # Prefer files with both "item" and "description" in the name
    preferred = [a for a in excel_files if "item" in a.get("title", "").lower() and "description" in a.get("title", "").lower()]
    chosen = preferred[0] if preferred else excel_files[0]
    print(f"[INFO] Auto-selected: {chosen.get('title')}", file=sys.stderr)
    return chosen


def download_attachment(cloud_id, attachment, auth):
    """Download attachment binary content."""
    download_path = (
        attachment.get("downloadLink")
        or attachment.get("_links", {}).get("download")
    )
    if not download_path:
        att_id = attachment.get("id")
        download_path = f"/wiki/rest/api/content/{att_id}/download"

    if not download_path.startswith("http"):
        if not download_path.startswith("/"):
            download_path = "/" + download_path
        # Confluence download paths (/download/...) omit the /wiki base; /wiki/... paths include it
        if download_path.startswith("/wiki/"):
            download_path = f"https://{cloud_id}" + download_path
        else:
            download_path = f"https://{cloud_id}/wiki" + download_path

    resp = requests.get(download_path, auth=auth, allow_redirects=True)
    resp.raise_for_status()
    return resp.content


# ---------------------------------------------------------------------------
# Output helpers
# ---------------------------------------------------------------------------

def print_attachments_table(attachments):
    if not attachments:
        print("*(no attachments)*")
        return
    print("| # | Title | Media Type | Size |")
    print("| --- | --- | --- | --- |")
    for i, att in enumerate(attachments, 1):
        title = att.get("title", "")
        media_type = att.get("mediaType", att.get("mimeType", ""))
        size = att.get("fileSize", att.get("extensions", {}).get("fileSize", ""))
        size_str = f"{int(size):,} bytes" if size else ""
        print(f"| {i} | {title} | {media_type} | {size_str} |")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Confluence REST API utilities.\n\n"
                    "Modes:\n"
                    "  --fetch-page          Fetch page content as markdown text\n"
                    "  --list-attachments    List all attachments on a page\n"
                    "  (no flag)             Download and read an Excel attachment\n",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--cloud-id", required=True, help="Confluence host, e.g. myco.atlassian.net")
    parser.add_argument("--page-id", required=True, help="Confluence page ID (numeric or slug)")
    parser.add_argument("--filename", help="Exact Excel attachment filename (optional; auto-selects first .xlsx if omitted)")
    parser.add_argument("--fetch-page", action="store_true", help="Fetch page content as markdown text")
    parser.add_argument("--list-attachments", action="store_true", help="List all attachments on the page")
    args = parser.parse_args()

    auth = get_auth()

    if args.fetch_page:
        print(f"[INFO] Fetching page {args.page_id} from {args.cloud_id}...", file=sys.stderr)
        title, content = fetch_page(args.cloud_id, args.page_id, auth)
        print(f"# {title}\n\n{content}")

    elif args.list_attachments:
        print(f"[INFO] Listing attachments on page {args.page_id}...", file=sys.stderr)
        attachments = list_attachments(args.cloud_id, args.page_id, auth)
        print_attachments_table(attachments)

    else:
        print(f"[INFO] Listing attachments on page {args.page_id}...", file=sys.stderr)
        attachments = list_attachments(args.cloud_id, args.page_id, auth)
        if not attachments:
            sys.exit("ERROR: No attachments found on this page.")
        attachment = find_excel(attachments, args.filename)
        print(f"[INFO] Downloading '{attachment.get('title')}'...", file=sys.stderr)
        content = download_attachment(args.cloud_id, attachment, auth)
        print(f"[INFO] Parsing Excel ({len(content):,} bytes)...", file=sys.stderr)
        rows = parse_xlsx(content)
        print(rows_to_markdown(rows))


if __name__ == "__main__":
    main()
