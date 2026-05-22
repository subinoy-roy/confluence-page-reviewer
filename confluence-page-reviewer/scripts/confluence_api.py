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
from requests.auth import HTTPBasicAuth

from excel_parser import parse_xlsx, rows_to_markdown
from html_utils import html_to_markdown


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
