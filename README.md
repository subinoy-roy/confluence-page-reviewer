# Confluence Page Reviewer

A Claude Code skill (plugin) that audits Confluence pages for documentation quality issues.

## What it does

The skill fetches a Confluence page and checks it for:

- **Internal inconsistencies** — contradictory statements, conflicting numbers or dates across sections
- **Ambiguous language** — vague time/quantity references, undefined acronyms, unclear pronouns
- **Outdated information** — past dates presented as future, deprecated tool references, stale status labels
- **Missing content** — incomplete steps, TODO markers, empty sections, unlinked references
- **Field specification sync** — cross-checks the embedded Excel spec against the page body
- **Attachment issues** — missing or orphaned attachments
- **Message code validation** — validates error/warning/info codes against documented formats

### Supported page types

| Function code prefix | Page type |
|---|---|
| `F`, `W` | Screen |
| `R` | Report |
| `B` | Stored Procedure |
| `I` | Interface |

Each page type has its own set of additional checks defined in [`confluence-page-reviewer/references/`](confluence-page-reviewer/references/).

## Output

At the start of each review the skill asks whether you want the report saved as **Markdown** or **HTML**. Both formats cover the same content grouped by severity:

- **Critical** — a reader could take the wrong action or miss a required step
- **Warning** — a reader would be confused or need to seek clarification
- **Suggestion** — minor clarity or formatting improvements

| Format | Filename | Description |
|---|---|---|
| Markdown | `Report_<functionCode>_<timestamp>.md` | Plain text, renders in any Markdown viewer |
| HTML | `Report_<functionCode>_<timestamp>.html` | Self-contained file with a sortable table, severity badges, and alternating row shading — opens in any browser with no external dependencies |

The HTML report presents all issues in a single table with columns for severity, issue type, location, problem description, and suggested fix.

## Installation

This plugin is registered in [`.claude-plugin/marketplace.json`](.claude-plugin/marketplace.json). Claude Code picks it up automatically when you open this directory.

The skill is located at [`plugins/confluence-page-reviewer/`](plugins/confluence-page-reviewer/).

## Usage

Share a Confluence page URL in Claude Code and ask for a review:

```
Review this Confluence page: https://myco.atlassian.net/wiki/spaces/ENG/pages/123456789/Title
```

### Fetching page content

The skill tries three methods in order:

1. **Atlassian MCP** (preferred) — requires the Atlassian MCP server to be configured
2. **REST API** — requires `ATLASSIAN_EMAIL` and `ATLASSIAN_API_TOKEN` environment variables
3. **Word export** — ask Confluence to export the page as Word and provide the local path

### Reading the field specification Excel

If the Excel is embedded in the page via a Confluence macro it will be read automatically. Otherwise the skill will ask you to download and provide the file path.

## Scripts

The [`confluence-page-reviewer/scripts/`](confluence-page-reviewer/scripts/) directory contains helper scripts used by the skill:

| Script | Purpose |
|---|---|
| `confluence_api.py` | Fetches page content and lists attachments via the Confluence REST API |
| `docx_parser.py` | Parses Confluence Word exports (MHTML format) |
| `excel_parser.py` | Reads the field specification Excel file |
| `html_utils.py` | HTML parsing utilities |

## Project structure

```
.
├── .claude-plugin/
│   └── marketplace.json          # Plugin registry
├── confluence-page-reviewer/
│   ├── SKILL.md                  # Skill definition (instructions for Claude)
│   ├── references/
│   │   ├── checks-screen.md      # Screen page checks
│   │   ├── checks-report.md      # Report page checks
│   │   ├── checks-sp.md          # Stored Procedure page checks
│   │   └── checks-interface.md   # Interface page checks
│   └── scripts/                  # Helper scripts
└── plugins/
    └── confluence-page-reviewer/ # Installable plugin package
```