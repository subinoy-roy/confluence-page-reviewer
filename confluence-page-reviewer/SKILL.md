---
name: confluence-page-reviewer
description: Audits a Confluence page for quality issues including internal inconsistencies, ambiguous language, outdated/stale information, and missing content. Always use this skill whenever a user shares a Confluence URL and asks to review, check, audit, verify, or improve documentation quality — even if they phrase it casually ("take a look at this page", "something seems off", "does this make sense"). Triggers on phrases like "check this Confluence page", "review this page", "find issues with this doc", "audit this page", "what's wrong with this doc", or any time a Confluence URL is shared alongside a request to improve or validate it.
---

# Confluence Page Reviewer

You will audit a Confluence page and report all quality issues found, grouped by severity, with the exact location in the document and a concrete suggestion for how to fix each one.

> **Script paths:** Commands below reference scripts as `<skill-dir>/scripts/`. The skill's base directory is provided when the skill loads (look for "Base directory for this skill: /path/to/..." in the context). Substitute `<skill-dir>` with that path.

## Step 0: Choose report format

Before doing anything else, ask the user:

> "Would you like the report saved as **Markdown** (.md) or **HTML** (.html)?"

Wait for their answer and store it as `report_format` (`markdown` or `html`). Use it in Step 6 to determine how to save the report.

## Step 1: Parse the URL and determine page type

Extract the `cloudId` and `pageId` from the URL the user provides. Confluence URLs come in a few forms:

| URL format | cloudId | pageId |
|---|---|---|
| `https://myco.atlassian.net/wiki/spaces/ENG/pages/123456789/Title` | `myco.atlassian.net` | `123456789` |
| `https://myco.atlassian.net/wiki/x/AbCdEf` | `myco.atlassian.net` | `AbCdEf` |
| `https://myco.atlassian.net/wiki/pages/viewpage.action?pageId=123456789` | `myco.atlassian.net` | `123456789` |

If the URL doesn't match any of these patterns, ask the user to confirm the page ID.

### Determine the page type

After fetching the page (Step 2), check the page title or function code in the heading (e.g., `[FINV60035]`, `[RINV60070]`, `[WVSC00160]`):

- **Screen page** — function code starts with `F` or `W` (e.g., `FINV60035`, `WINV00160`). Reference file: `<skill-dir>/references/checks-screen.md`
- **Report page** — function code starts with `R` (e.g., `RINV60070`, `RDLR00050`). Reference file: `<skill-dir>/references/checks-report.md`
- **Stored Procedure page** — function code starts with `B` (e.g., `BINV00150`, `BVSC00210`). Reference file: `<skill-dir>/references/checks-sp.md`
- **Interface page** — function code starts with `I` (e.g., `IINV04002`, `IVSC00120`). Reference file: `<skill-dir>/references/checks-interface.md`

If no function code is present, check for section headings ("Item Description" → Screen, "Report Items" → Report, "Data Map" → SP, "Interface File Format" → Interface).

> **Read the type-specific reference file now** before continuing. It contains the Excel structure description (for Step 3b), the field-level cross-checks (Step 3c), and all additional checks for Step 4.

## Step 2: Fetch the page content

**Option A — Atlassian MCP (preferred):**
Use `getConfluencePage` with `contentFormat: "markdown"` so you get clean, readable text.

```
cloudId: <extracted from URL>
pageId: <extracted from URL>
contentFormat: "markdown"
```

**Option B — REST API fallback (no MCP required):**
```bash
python3 <skill-dir>/scripts/confluence_api.py \
  --cloud-id <cloudId> --page-id <pageId> --fetch-page
```
Requires `ATLASSIAN_EMAIL` and `ATLASSIAN_API_TOKEN` env vars. Prints the page title and full content as markdown to stdout.

**Option C — Exported Word document (no credentials required):**
If both MCP and the REST API are unavailable or blocked, ask the user to export the page from Confluence (page menu → **Export** → **Word**) and provide the local path. Then run:
```bash
python3 <skill-dir>/scripts/docx_parser.py --file /path/to/exported-page.doc
```
**Note:** Confluence's Word export produces a `.doc` file that is actually MHTML (a MIME-wrapped HTML document), not a binary Word file. The script detects the format automatically — pass the file as-is regardless of extension.

Note the page title and any section headings — you'll use these as location references in your report.

## Step 3: Find attachments and read the field specification file

Run both of these in parallel.

### 3a. List all attachments

**Option A — Atlassian MCP (preferred):**
Use `searchConfluenceUsingCql` to list attachments on this page:

```
cql: type = attachment AND parent = "<pageId>"
cloudId: <same cloudId>
```

**Option B — REST API fallback (no MCP required):**
```bash
python3 <skill-dir>/scripts/confluence_api.py \
  --cloud-id <cloudId> --page-id <pageId> --list-attachments
```

For each attachment found, check whether:
- Its name and file type match how it's described or referenced in the page body
- The page references an attachment that doesn't appear in the list (missing attachment)
- An attachment is listed but never mentioned in the page body (orphaned attachment)

### 3b. Read the field specification Excel

The type-specific reference file describes what the Excel contains and its structure. The process for obtaining it is the same for all page types:

**First — Check if it's already rendered in the page body.** Look at the relevant section in the fetched markdown ("Item Description", "Report Items", "Data Map", or "Interface File Format"). If the Excel was embedded via a Confluence "View File" macro it may have rendered as a table — use that directly and skip to Step 3c. This is particularly likely when using Option C (Word export).

**If not rendered — STOP and ask the user to download the file.**

> "I can see the [Item Description / Report Items / Data Map / Interface File Format] Excel is embedded on the page but I can't read it directly. Could you download it from Confluence (click the file to open it, then download) and share the local path?"

Once the user provides the path, run:
```bash
python3 <skill-dir>/scripts/excel_parser.py --file /path/to/downloaded/file.xlsx
```

**Only if the user explicitly says they cannot provide the file:**
- Check the HTML format of the page (`contentFormat: "html"`) for `data-type="media"` and `data-media-type="file"` elements inside the relevant section — these confirm the file exists even if unreadable.
- Flag in the report: the file exists but its content could not be read automatically, and manual verification is needed.

Always distinguish between "file is missing" and "file exists but content cannot be read automatically" — these are very different problems.

### 3c. Cross-check field specification Excel

Apply the cross-check rules from the type-specific reference file. Compare every field/entry in the Excel against the authoritative field list in the page body, as directed by that file.

## Step 4: Analyze for issues

Read the full page content carefully and check for all of the following. **Also apply the additional type-specific checks from the reference file loaded in Step 1.**

### Internal inconsistencies
- Contradictory statements in different sections (e.g., Section A says "approved by manager", Section B says "no approval needed")
- Conflicting numbers, dates, names, or version numbers within the same document
- A decision or policy stated differently in different places
- Steps that contradict each other in a process

### Ambiguous language
- Vague time references with no anchor ("soon", "in the near future", "recently")
- Vague quantities ("some", "several", "a few", "various") where precision matters
- Acronyms used without being defined on first use
- Pronouns ("it", "this", "they") where the referent is genuinely unclear
- Passive voice that hides who is responsible ("it should be approved" — approved by whom?)
- Undefined jargon or internal shorthand that a new reader wouldn't understand

### Outdated or stale information
- Dates presented as future that are now in the past
- Version numbers or product names that appear to be superseded
- References to tools, systems, or processes that may have been deprecated or renamed
- Status fields or labels (e.g., "In Progress", "Planned") that seem inconsistent with the page's last-modified date

### Missing information
- Incomplete process steps — a step describes an outcome without explaining how to get there
- "TODO", "TBD", "placeholder", or "[add details here]" markers left in the document
- Section headings with no body content
- References to external documents, policies, or links that are not actually linked
- Logical gaps — for a process with steps 1, 2, 4, 5, what happened to step 3?
- Roles or responsibilities mentioned without contact information or team names

### Attachment cross-check
- Check whether the page's narrative is consistent with what the attachments are described as containing
- Flag any discrepancies between attachment names and how they're described in the body

### Document metadata
- **Reviewer name and date blank** — if the page has a reviewer or approver field, flag it as a Warning if it is empty or contains placeholder text (e.g., "TBD", "[Name]", "N/A")
- **Version history absent** — the page should have a version history table recording changes over time; flag as Warning if entirely absent or empty

### Standard notation
- **Abbreviations missing trailing dot** — check abbreviations such as "No", "Cnt", "Qty", "Sr"; the correct form is "No.", "Cnt.", "Qty.", "Sr." — flag each instance where the dot is omitted
- **Singular noun for multiple objects** — when a sentence describes more than one item (screens, tables, files, batches), the noun should be plural; flag where singular is incorrectly used for multiple objects
- **Special conditions unmarked** — when the same condition or exception applies to multiple line items, it should be marked with `*` and explained in a clearly labelled note at the bottom of the page; flag as Suggestion if such a pattern exists in the document but the `*` notation and end-of-page note are absent

### Examples and scenarios
- **No examples for complex logic** — if the Functional Description contains calculations, conditional derivations, or multi-step business rules, at least one worked example must be present; flag as Warning if none exists
- **Incomplete examples** — each example should: (a) state its purpose before showing any data, (b) show input/source data, and (c) show what changed after the calculation or operation; flag any example that skips one of these three parts

### IS feedback
- **Unresolved comments** — use `getConfluencePageFooterComments` and `getConfluencePageInlineComments` to fetch all page comments; flag any open or unresolved comment as a Warning, since it may represent feedback that should be incorporated into the document body before it is considered final
- **Common IS feedback not addressed** — if the page contains a link to a common IS feedback checklist (typically near the reviewer section or in a note at the bottom), verify that the standard points from that checklist are visibly addressed in the document; flag as Warning if the link is present but there is no indication the points were reviewed

### Message code validation (all page types)

Message codes appear in Section 5 Logging Messages and throughout the Functional Description. There are two distinct formats — always classify each code before checking it.

**Common codes** — suffix is digits only, e.g. `ERR50025`, `WRN10003`. These are shared across all pages and maintained on the Common Errors page linked from Section 5. To verify a common code:
- Fetch the Common Errors page using `getConfluencePage` (or the REST API)
- Confirm the code is listed there; if not, flag as Critical

**Page-specific codes** — Format: `ERR` + module identifier (single letter) + running ID section + running number, e.g. `ERRV00100001`.

Derive the running ID section by stripping the page-type prefix and module name from the function code, leaving only the numeric tail:
- `BVSC00100` → strip `B` + `VSC` → running ID = `00100`
- `WINV0010` → strip `W` + `INV` → running ID = `0010`

Module identifiers: `I` (INV), `V` (VSC), `D` (DLR), `N` (DNS). Same structure applies to `WRN` (warnings), `INV` (information), and `CNF` (confirmation).
- Verify the module letter matches the page's module (e.g., a `BVSC00100` page should only use `V` codes)
- Flag any code whose module letter doesn't match the page's module as a likely copy-paste from another module

**Malformed codes** — any code that fits neither pattern should be flagged as a Warning.

When Section 5 contains only a link to the Common Errors page and no page-specific entries, that is acceptable — but any page-specific code referenced in the Functional Description must still be listed in Section 5.

## Step 5: Write the report

Start with a one-line summary. Then group all issues under three severity headings. End with a brief "What to do next" section.

### Severity definitions

**🔴 Critical** — A reader following this document as written could take the wrong action, miss a required step, or be seriously misled. Use this for direct contradictions, missing required steps in a process, or stale information that could cause an error.

**🟡 Warning** — A reader would likely be confused, slow down, or have to seek clarification elsewhere. Use this for ambiguous language, orphaned/missing attachments, stale dates, broken reference links, and undefined terms in key roles or steps.

**🟢 Suggestion** — Minor improvements that would make the document cleaner and more professional. Use this for: undefined acronyms in low-stakes contexts, passive voice in informational sections, typos, formatting inconsistencies, and inapplicable template sections.

### Format for each issue

```
• **[Issue type]** — *[Location]*
  **Problem:** [One sentence describing what's wrong and why it matters]
  **Suggested fix:** [Specific, actionable rewrite or change]
```

**Location** should be one of:
- A section heading: *"Section: Approval Process"*
- A quoted excerpt: *"Near: 'the system will be updated accordingly'"*
- The page title if the issue is structural: *"Page-level"*
- The attachment name: *"Attachment: Q4_Process_v2.pdf"*

### Report template

```
## Confluence Page Review: [Page Title]

**[X critical issues · Y warnings · Z suggestions]**

---

### 🔴 Critical

• ...

### 🟡 Warning

• ...

### 🟢 Suggestions

• ...

---

### 📋 Field Specification Issue List

[Include this section only if there are sync issues between the field specification Excel and the rest of the document. Omit entirely if everything is in sync — or if the Excel could not be read, note that explicitly here instead.]

| # | Issue | Location | Suggested Fix |
|---|-------|----------|---------------|
| 1 | ... | ... | ... |

[If the Excel could not be read because it is a binary attachment:]
> ⚠️ The field specification Excel (`<filename>.xlsx`) is attached to the page but its content could not be read automatically. Please manually verify that all fields/operations documented in the Excel are consistent with the rest of the page.

---

### What to do next

[2–3 sentence summary of the most important fixes and recommended order of action.]
```

If a category has no issues, omit it. If the Field Specification Issue List has no issues, omit that section too. If the page looks clean, say so directly rather than inventing nitpicks.

## Step 6: Save the report to a file

Save using the Write tool (not a shell command — the report content contains special characters that break shell quoting). Get the timestamp first via Bash: `date +%Y%m%d%H%M%S`.

Use the base name `Report_<functionCode>_<timestamp>` (fall back to `Report_<pageId>_<timestamp>` if no function code).

### If `report_format` is `markdown`

Write the report template from Step 5 verbatim to `<base name>.md`.

### If `report_format` is `html`

Write a self-contained HTML file (`<base name>.html`) using the template below. Fill in all placeholders with the actual report content. All CSS is inline so the file opens correctly in any browser without external dependencies.

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Confluence Page Review: {PAGE_TITLE}</title>
<style>
  body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; max-width: 1100px; margin: 40px auto; padding: 0 24px; color: #1a1a1a; line-height: 1.5; }
  h1 { font-size: 1.4rem; margin-bottom: 4px; }
  .summary-badge { display: inline-block; background: #f0f0f0; border-radius: 6px; padding: 6px 14px; font-size: 0.9rem; color: #444; margin-bottom: 28px; }
  .summary-badge .c { color: #c0392b; font-weight: 600; }
  .summary-badge .w { color: #b7770d; font-weight: 600; }
  .summary-badge .s { color: #27ae60; font-weight: 600; }
  hr { border: none; border-top: 1px solid #e0e0e0; margin: 24px 0; }
  h2 { font-size: 1.05rem; margin-top: 28px; margin-bottom: 10px; }
  table { width: 100%; border-collapse: collapse; font-size: 0.88rem; }
  th { background: #f0f0f0; text-align: left; padding: 9px 12px; border: 1px solid #d0d0d0; font-size: 0.82rem; text-transform: uppercase; letter-spacing: 0.04em; color: #555; }
  td { padding: 10px 12px; border: 1px solid #ddd; vertical-align: top; }
  tr:nth-child(even) td { background: #fafafa; }
  .badge { display: inline-block; padding: 2px 8px; border-radius: 10px; font-size: 0.78rem; font-weight: 600; white-space: nowrap; }
  .badge-critical { background: #fdecea; color: #c0392b; }
  .badge-warning  { background: #fef8e7; color: #b7770d; }
  .badge-suggest  { background: #eafaf1; color: #27ae60; }
  .location { font-style: italic; color: #666; font-size: 0.85rem; }
  .next-steps { background: #f0f7ff; border-radius: 6px; padding: 14px 18px; margin-top: 24px; font-size: 0.95rem; }
  .next-steps h2 { margin-top: 0; }
</style>
</head>
<body>

<h1>Confluence Page Review: {PAGE_TITLE}</h1>
<div class="summary-badge">
  <span class="c">{N_CRITICAL} critical</span> &nbsp;·&nbsp;
  <span class="w">{N_WARNINGS} warnings</span> &nbsp;·&nbsp;
  <span class="s">{N_SUGGESTIONS} suggestions</span>
</div>

<hr>

<!-- Single table with all issues ordered Critical → Warning → Suggestion -->
<table>
  <thead>
    <tr>
      <th style="width:3%">#</th>
      <th style="width:9%">Severity</th>
      <th style="width:18%">Issue</th>
      <th style="width:20%">Location</th>
      <th style="width:25%">Problem</th>
      <th style="width:25%">Suggested Fix</th>
    </tr>
  </thead>
  <tbody>
    <!-- One <tr> per issue. Use the badge class matching the severity. -->
    <tr>
      <td>{N}</td>
      <td><span class="badge badge-critical">🔴 Critical</span></td>
      <td><strong>{ISSUE_TYPE}</strong></td>
      <td class="location">{LOCATION}</td>
      <td>{PROBLEM}</td>
      <td>{FIX}</td>
    </tr>
    <tr>
      <td>{N}</td>
      <td><span class="badge badge-warning">🟡 Warning</span></td>
      <td><strong>{ISSUE_TYPE}</strong></td>
      <td class="location">{LOCATION}</td>
      <td>{PROBLEM}</td>
      <td>{FIX}</td>
    </tr>
    <tr>
      <td>{N}</td>
      <td><span class="badge badge-suggest">🟢 Suggestion</span></td>
      <td><strong>{ISSUE_TYPE}</strong></td>
      <td class="location">{LOCATION}</td>
      <td>{PROBLEM}</td>
      <td>{FIX}</td>
    </tr>
  </tbody>
</table>

<hr>

<!-- Include this section only if there are field specification sync issues; omit entirely otherwise -->
<h2>📋 Field Specification Issue List</h2>
<table>
  <thead><tr><th>#</th><th>Issue</th><th>Location</th><th>Suggested Fix</th></tr></thead>
  <tbody>
    <!-- Repeat for each row: -->
    <tr><td>{N}</td><td>{ISSUE}</td><td>{LOCATION}</td><td>{FIX}</td></tr>
  </tbody>
</table>

<div class="next-steps">
  <h2>📋 What to do next</h2>
  <p>{NEXT_STEPS}</p>
</div>

</body>
</html>
```

Tell the user the full file path once saved.
