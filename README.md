# Confluence Page Reviewer

A Claude Code skill (plugin) that audits Confluence pages for documentation quality issues and produces a structured review report.

## What it does

The skill fetches a Confluence page, reads the embedded field specification Excel, fetches all open inline comments, and checks everything for:

- **Internal inconsistencies** — contradictory statements, conflicting numbers or dates across sections
- **Ambiguous language** — vague time/quantity references, undefined acronyms, unclear pronouns
- **Outdated information** — past dates presented as future, deprecated tool references, stale status labels
- **Missing content** — incomplete steps, TODO markers, empty sections, unlinked references
- **Field specification sync** — cross-checks the embedded Excel spec against the Display Order field by field
- **Attachment issues** — missing or orphaned attachments
- **Message code validation** — validates error/warning/info/confirmation codes against documented formats and checks the Common Errors cache
- **Error code hyperlink integrity** — verifies that every error code in the Operation Description is hyperlinked to its anchor in the Specific Errors table, and that the anchor exists
- **IS feedback** — fetches all open inline and footer comments, groups identical comments, and links each finding directly to the comment in Confluence
- **Verdict** — classifies the page as Ready, Conditionally Ready, or Not Ready for sign-off based on critical issue count

### Supported page types

| Function code prefix | Page type | Reference checks file |
|---|---|---|
| `F`, `W` | Screen | `checks-screen.md` |
| `R` | Report | `checks-report.md` |
| `B` | Stored Procedure | `checks-sp.md` |
| `I` | Interface | `checks-interface.md` |

Each page type has its own additional checks defined in [`confluence-page-reviewer/references/`](confluence-page-reviewer/references/).

## Output

At the start of each review the skill asks whether you want the report saved as **Markdown** or **HTML**.

| Format | Filename | Description |
|---|---|---|
| Markdown | `Report_<functionCode>_<timestamp>.md` | Plain text, renders in any Markdown viewer |
| HTML | `Report_<functionCode>_<timestamp>.html` | Self-contained file with severity badges, colour-coded verdict, alternating row shading, and direct "View in Confluence →" links for unresolved comments — opens in any browser with no external dependencies |

Both formats group issues by severity:

- **🔴 Critical** — a reader could take the wrong action or miss a required step
- **🟡 Warning** — a reader would be confused or need to seek clarification elsewhere
- **🟢 Suggestion** — minor clarity or formatting improvements

Report templates live in [`confluence-page-reviewer/assets/`](confluence-page-reviewer/assets/) and are loaded on demand — only the chosen format is read, keeping context lean.

## Installation

This plugin is registered in [`.claude-plugin/marketplace.json`](.claude-plugin/marketplace.json). Claude Code picks it up automatically when you open this directory.

Run `/plugin` then `/reload-plugins` inside Claude Code to install or refresh the skill.

## Usage

Share a Confluence page URL and ask for a review:

```
Review this Confluence page: https://myco.atlassian.net/wiki/spaces/ENG/pages/123456789/Title
```

The skill will:
1. Ask whether you want the report as Markdown or HTML
2. Fetch the page, list attachments, and fetch all open comments in parallel
3. Inspect Section 8 (Item Description) — if the Excel is not rendered as a table, **ask you to download and provide the file path before continuing**
4. Run the field specification cross-check once you provide the file (or note it as Critical if you cannot)
5. Analyse the full page against all checks
6. Write the report to a timestamped file in the working directory

### Fetching page content

The skill tries three methods in order:

1. **Atlassian MCP** (preferred) — requires the Atlassian MCP server to be configured
2. **REST API** — requires `ATLASSIAN_EMAIL` and `ATLASSIAN_API_TOKEN` environment variables
3. **Word export** — ask Confluence to export the page as Word and provide the local path

### Field specification Excel

The skill **always pauses and asks you to download the file** if it cannot be read automatically (i.e., it is embedded as a non-rendered attachment rather than a Confluence table macro). Do not expect the review to proceed without the file — provide the local path, or explicitly say you cannot provide it (the skill will then flag it as Critical and continue).

### Common Errors cache

Rather than fetching the Common Errors page on every review, the skill uses a local cache at [`confluence-page-reviewer/references/common_errors.json`](confluence-page-reviewer/references/common_errors.json). The cache is pre-seeded and only refreshed when a code lookup misses:

```bash
# Manually refresh the cache if the Common Errors page is updated:
python3 confluence-page-reviewer/scripts/fetch_common_errors.py \
  --refresh --cloud-id myco.atlassian.net
```

## Scripts

| Script | Purpose |
|---|---|
| `confluence_api.py` | Fetches page content and lists attachments via the Confluence REST API |
| `docx_parser.py` | Parses Confluence Word exports (MHTML format) |
| `excel_parser.py` | Reads the field specification Excel file |
| `fetch_common_errors.py` | Manages the local Common Errors cache — load, check a code, or refresh from Confluence |
| `html_utils.py` | HTML-to-markdown conversion utilities |

## Project structure

```
.
├── .claude-plugin/
│   └── marketplace.json               # Plugin registry (points to plugins/)
├── confluence-page-reviewer/          # Source — edit here, commit, push
│   ├── SKILL.md                       # Skill definition (instructions for Claude)
│   ├── assets/
│   │   ├── report-template.html       # HTML report template (loaded on demand)
│   │   └── report-template.md         # Markdown report template (loaded on demand)
│   ├── references/
│   │   ├── checks-screen.md           # Screen page checks
│   │   ├── checks-report.md           # Report page checks
│   │   ├── checks-sp.md               # Stored Procedure page checks
│   │   ├── checks-interface.md        # Interface page checks
│   │   └── common_errors.json         # Cached Common Errors page codes
│   └── scripts/                       # Helper scripts
└── plugins/
    └── confluence-page-reviewer/      # Installed copy — do not edit directly
```

## Updating the skill

Always edit files under `confluence-page-reviewer/` (the source), never under `plugins/` (the installed copy). After making changes:

```bash
# 1. Copy changes to the installed copy
cp confluence-page-reviewer/SKILL.md \
   plugins/confluence-page-reviewer/skills/confluence-page-reviewer/SKILL.md

# Copy other changed files the same way (references/, scripts/, assets/)

# 2. Reload the skill in Claude Code
/plugin
/reload-plugins

# 3. Commit and push to GitHub
git add confluence-page-reviewer/
git commit -m "Description of change"
git push origin main
```

> **Note:** GitHub URL source type is not yet supported by the installed Claude Code version. Until it is, the manual `cp` step is required to sync source changes to `plugins/`.
