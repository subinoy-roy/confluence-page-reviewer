#!/usr/bin/env python3
"""
Common Errors cache manager.

The Common Errors page changes rarely. This script caches its codes locally so
the skill can verify common error codes without making a Confluence API call on
every review.

Modes:
  Load from cache (default / --load-cache):
    python3 fetch_common_errors.py
    python3 fetch_common_errors.py --load-cache

  Check whether a specific code exists in the cache:
    python3 fetch_common_errors.py --check ERR00001

  Rebuild the cache from Confluence (run when a code is not found or on demand):
    python3 fetch_common_errors.py --refresh --cloud-id myco.atlassian.net

Environment variables required for --refresh:
  ATLASSIAN_EMAIL      - Your Atlassian account email
  ATLASSIAN_API_TOKEN  - Your Atlassian API token

Exit codes:
  0  Success (or code found when using --check)
  1  Error / code not found when using --check
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

# Page ID of the Common Errors - Screens page in Confluence
COMMON_ERRORS_PAGE_ID = "725942287"

# Cache lives alongside the other reference files
CACHE_PATH = Path(__file__).parent.parent / "references" / "common_errors.json"


# ---------------------------------------------------------------------------
# Cache I/O
# ---------------------------------------------------------------------------

def load_cache() -> dict:
    if not CACHE_PATH.exists():
        sys.exit(
            f"ERROR: Cache file not found at {CACHE_PATH}\n"
            "Run with --refresh --cloud-id <host> to build it."
        )
    with open(CACHE_PATH, encoding="utf-8") as f:
        return json.load(f)


def save_cache(codes: dict) -> None:
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(codes, f, indent=2, ensure_ascii=False)
    print(f"[INFO] Saved {len(codes)} codes to {CACHE_PATH}", file=sys.stderr)


# ---------------------------------------------------------------------------
# Fetch + parse
# ---------------------------------------------------------------------------

def fetch_and_parse(cloud_id: str) -> dict:
    """Fetch the Common Errors page and extract all message codes."""
    try:
        import requests
        from requests.auth import HTTPBasicAuth
    except ImportError:
        sys.exit("ERROR: 'requests' package is required. Install with: pip install requests")

    # html_utils lives in the same scripts/ directory
    sys.path.insert(0, str(Path(__file__).parent))
    from html_utils import html_to_markdown

    email = os.environ.get("ATLASSIAN_EMAIL")
    token = os.environ.get("ATLASSIAN_API_TOKEN")
    if not email or not token:
        sys.exit(
            "ERROR: Set ATLASSIAN_EMAIL and ATLASSIAN_API_TOKEN environment variables.\n"
            "  Get a token at: https://id.atlassian.com/manage-profile/security/api-tokens"
        )

    auth = HTTPBasicAuth(email, token)
    url = f"https://{cloud_id}/wiki/rest/api/content/{COMMON_ERRORS_PAGE_ID}"
    print(f"[INFO] Fetching page {COMMON_ERRORS_PAGE_ID} from {cloud_id}...", file=sys.stderr)

    resp = requests.get(url, auth=auth, params={"expand": "body.view"})
    resp.raise_for_status()
    html = resp.json().get("body", {}).get("view", {}).get("value", "")
    text = html_to_markdown(html)

    # Match lines like:  **ERR00001** - Mandatory field must be entered.
    codes = {}
    pattern = re.compile(
        r'\*\*((?:ERR|WRN|INF|CNF)\d+)\*\*\s*[-–]\s*(.+?)(?=\n|$)'
    )
    for m in pattern.finditer(text):
        code = m.group(1).strip()
        message = m.group(2).strip()
        codes[code] = message

    print(f"[INFO] Extracted {len(codes)} codes.", file=sys.stderr)
    return codes


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Common Errors cache manager — load, check, or refresh the local cache.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--load-cache", action="store_true",
        help="Print all cached codes as JSON (default behaviour when no flag given)"
    )
    parser.add_argument(
        "--check", metavar="CODE",
        help="Exit 0 and print the message if CODE is in the cache; exit 1 if not found"
    )
    parser.add_argument(
        "--refresh", action="store_true",
        help="Re-fetch the Common Errors page from Confluence and rebuild the cache"
    )
    parser.add_argument(
        "--cloud-id", metavar="HOST",
        help="Confluence host, e.g. myco.atlassian.net (required with --refresh)"
    )
    args = parser.parse_args()

    if args.refresh:
        if not args.cloud_id:
            sys.exit("ERROR: --cloud-id is required when using --refresh")
        codes = fetch_and_parse(args.cloud_id)
        save_cache(codes)
        print(json.dumps(codes, indent=2, ensure_ascii=False))

    elif args.check:
        codes = load_cache()
        code = args.check.strip()
        if code in codes:
            print(f"FOUND: {code} — {codes[code]}")
            sys.exit(0)
        else:
            print(f"NOT FOUND: {code} is not in the cache.")
            sys.exit(1)

    else:
        # Default: --load-cache
        codes = load_cache()
        print(json.dumps(codes, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
