---
name: confluence-page-reviewer
description: Audits a Confluence page for quality issues including internal inconsistencies, ambiguous language, outdated/stale information, and missing content. Always use this skill whenever a user shares a Confluence URL and asks to review, check, audit, verify, or improve documentation quality — even if they phrase it casually ("take a look at this page", "something seems off", "does this make sense"). Triggers on phrases like "check this Confluence page", "review this page", "find issues with this doc", "audit this page", "what's wrong with this doc", or any time a Confluence URL is shared alongside a request to improve or validate it.
---

# Confluence Page Reviewer

You will audit a Confluence page and report all quality issues found, grouped by severity, with the exact location in the document and a concrete suggestion for how to fix each one.

> **Script paths:** Commands below reference scripts as `<skill-dir>/scripts/`. The skill's base directory is provided when the skill loads (look for "Base directory for this skill: /path/to/..." in the context). Substitute `<skill-dir>` with that path.

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

- **Screen page** — function code starts with `F` or `W` (e.g., `FINV60035`, `WINV00160`). The field specification Excel is in the **"Item Description"** section.
- **Report page** — function code starts with `R` (e.g., `RINV60070`, `RDLR00050`). The field specification Excel is in the **"Report Items"** section.
- **Stored Procedure page** — function code starts with `B` (e.g., `BINV00150`, `BVSC00210`). The field specification Excel is in the **"Data Map"** section.

Use this to know which section to look for the Excel in Steps 3b and 3c. If no function code is present, check whether the page has an "Item Description", "Report Items", or "Data Map" section heading and use whichever is present.

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

Prints the full page content as markdown, including any tables embedded via "View File" macros — so the field specification table may already appear in the output (see Step 3b).

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
Prints a markdown table of all attachments (title, media type, file size).

For each attachment found, check whether:
- Its name and file type match how it's described or referenced in the page body
- The page references an attachment that doesn't appear in the list (missing attachment)
- An attachment is listed but never mentioned in the page body (orphaned attachment)

### 3b. Read the field specification Excel

Depending on the page type determined in Step 1:
- **Screen page** → look for the Excel in the **"Item Description"** section.
- **Report page** → look for the Excel in the **"Report Items"** section.
- **Stored Procedure page** → look for the Excel in the **"Data Map"** section.

For Screen and Report pages, this Excel documents every field/column in the screen or report — typically columns like Field Name, Field Type, Mandatory/Optional, Default Value, Max Length, and Description. It is meant to stay in sync with the "Display Order" section (Screen) or the report column list (Report).

For Stored Procedure pages, the Data Map Excel documents the data flow for every INSERT, UPDATE, and DELETE operation the SP performs. Its structure is:
- **Left side — Source queries (Q1, Q2, …):** each block identifies a source table (`DB/File Name: QN | table_name`), key fields used to filter/join it, and numbered source fields (`QN.1`, `QN.2`, …) with their expressions.
- **Right side — Destination blocks:** each block identifies a target table (`DB/File Name: table_name`), numbered destination fields with transformation logic sourced from `QN.M` references or constants, and key fields (for UPDATE/DELETE operations).

The Data Map must stay in sync with Section 3.1 Input/Output and Section 6 Functional Description.

**First — Check if it's already rendered in the page body.** When you fetched the page in markdown format, look at the relevant section ("Item Description" or "Report Items"). If the Excel was embedded via a Confluence "View File" macro, it may have rendered as a table — use that directly and skip to Step 3c. This is particularly likely if you used **Option C** (Word export), as Confluence typically renders embedded files as tables in the exported document.

**If not rendered — Run the Excel reader script.** If the Excel is not already a readable table (appears as an image, blob URL, or a Confluence media file), ask the user to download the file from the Confluence page and provide the local path. Then run:

```bash
python3 <skill-dir>/scripts/excel_parser.py --file /path/to/downloaded/file.xlsx
```

- On success it prints the Excel content as a markdown table to stdout.
- Use that table for the cross-check in Step 3c.
- If the user cannot provide the file, continue below.

**If the file cannot be provided:**
- Check the HTML format of the page (`contentFormat: "html"`) for `data-type="media"` and `data-media-type="file"` elements inside the relevant section — these confirm the file exists even if it cannot be read.
- Flag this in the report using the Issue List format in Step 5: the file exists but its content could not be read automatically, and manual verification is needed.

**Note on attachment content generally**: For Confluence child pages referenced in the document, use `getConfluencePage` to fetch and review them. Always distinguish between "file is missing" and "file exists but content cannot be read automatically" — these are very different problems.

### 3c. Cross-check field specification Excel against the authoritative field list

#### Screen pages
Compare the **Item Description Excel** against the **Display Order** section table field by field. The Display Order lists every field/control shown on the screen; the Excel should document each one.

Check for:
- **Fields in Display Order missing from the Excel** — listed on screen but no Excel entry
- **Fields in the Excel not in Display Order** — orphaned Excel entry for a field not on screen
- **Name mismatches** — same field with different labels (e.g., "Invoice Date" vs "Inv. Date")
- **Property contradictions** — mandatory/default/type in Excel contradicts what the Operation Description says
- **Missing Excel entirely** — no table content and no `.xlsx` attachment in the "Item Description" section

#### Report pages
Compare the **Report Items Excel** against the **Display Order** section (or report column list) field by field. The Display Order lists every column shown in the report output; the Excel should document each one.

Check for:
- **Columns in Display Order missing from the Excel** — listed in the report but no Excel entry
- **Columns in the Excel not in Display Order** — orphaned Excel entry for a column not in the report
- **Name mismatches** — same column with different labels
- **Property contradictions** — column properties in Excel (data type, format, sort/group flag) contradict what the Operation Description says
- **Missing Excel entirely** — no table content and no `.xlsx` attachment in the "Report Items" section

#### Stored Procedure pages
The Data Map is the central artifact. Run three classes of checks:

**Internal Data Map consistency:**
- **Broken source references** — every `QN.M` reference in a destination field must correspond to a field actually defined in source block QN (e.g., if destination uses `Q3.5` but Q3 only defines Q3.1–Q3.3, that is a broken reference)
- **Missing destination table names** — any destination block where `DB/File Name` is blank; the target table is unknown
- **Duplicate key mappings** — same source field (`QN.M`) mapped to two different key columns in the same source block (likely a copy-paste error)
- **Typos in key values** — key field values that appear to be mis-typed (e.g., "color dode" instead of "color code")

**Data Map vs Section 3 Input/Output:**
- Every source table (Q1…Qn) should appear in Section 3.1 Input or Section 3.3 Reference; flag any source table present in the Data Map but absent from both
- Every destination table should appear in Section 3.2 Output; flag any destination table present in the Data Map but absent from Section 3.2
- Tables listed in Section 3.2 Output that have no corresponding destination block in the Data Map

**Data Map vs Section 6 Functional Description:**
- Key derivation logic in the Data Map (e.g., group_code, document_type assignments) must match the equivalent logic block in the Functional Description; flag any discrepancy
- Every error code referenced in the Data Map must have a corresponding entry in Section 5 Logging Messages

## Step 4: Analyze for issues

Read the full page content carefully and check for all of the following:

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

### Stored Procedure pages — additional checks
Apply these on top of all the general checks above when the page type is Stored Procedure (B prefix):

**Section 3.1 Input parameters:**
- Numbering gaps (e.g., list jumps from #4 to #6) — either a parameter was removed without renumbering, or one is missing
- Mixed data type notation (e.g., `VARCHAR` vs `VARCHAR2` in the same table) — suggests the section was assembled from different sources
- Parameters and DB tables mixed together without clear separation — check that the table clearly distinguishes individual input parameters from input DB tables

**Section 5 Logging Messages:**
- Duplicate S.No. values or gaps in the sequence — indicates rows were added/removed without renumbering
- Two errors with identical descriptions and causes — impossible to distinguish; need unique descriptions or consolidation
- Error codes referenced in the Functional Description or Data Map that are absent from this table

**Section 6 Functional Description:**
- Step numbering gaps — a step is referenced (e.g., "from Step 5") but that step number is not defined
- Filter conditions that appear backwards or incomplete (e.g., "where cancel_flag IS NOT NULL" when the step processes all records)
- Duplicate assignment blocks — the same variable assigned twice back-to-back with near-identical logic (residual from a refactor)

**Cross-section consistency:**
- Section 1.2 Post Condition vs Section 3.2 Output — every table written to by the SP should appear in both; a table in Output but not Post Condition (or vice versa) is an inconsistency
- Section 4 Batch Type / Frequency / Protocol — the schedule and trigger mechanism should be clearly defined; flag if left as N/A or placeholder when the SP is called by other programs (list the callers)

## Step 5: Write the report

Start with a one-line summary. Then group all issues under three severity headings. End with a brief "What to do next" section.

### Severity definitions

**🔴 Critical** — A reader following this document as written could take the wrong action, miss a required step, or be seriously misled. Use this for direct contradictions, missing required steps in a process, or stale information that could cause an error.

**🟡 Warning** — A reader would likely be confused, slow down, or have to seek clarification elsewhere. Use this for ambiguous language, orphaned/missing attachments, stale dates, broken reference links, and undefined terms in key roles or steps.

**🟢 Suggestion** — Minor improvements that would make the document cleaner and more professional. Use this for: undefined acronyms in low-stakes contexts, passive voice in informational sections, typos, formatting inconsistencies, and inapplicable template sections (e.g., boilerplate rows that clearly don't apply to this screen/process type and a careful reader would naturally disregard).

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

[Include this section only if there are sync issues between the field specification Excel and the rest of the document:
- **Screen pages** — Item Description Excel vs Display Order
- **Report pages** — Report Items Excel vs Display Order
- **Stored Procedure pages** — Data Map Excel vs Section 3 Input/Output, Section 5 Logging Messages, and Section 6 Functional Description

Omit entirely if everything is in sync — or if the Excel could not be read, note that explicitly here instead.]

| # | Issue | Location | Suggested Fix |
|---|-------|----------|---------------|
| 1 | [What's wrong — e.g., "Field 'Scan Date' is in Display Order but missing from Item Description Excel" or "Destination block for tb_inv_r_sap_d has blank DB/File Name" or "Q3.5 referenced in destination but Q3 only defines Q3.1–Q3.3"] | [Display Order / Item Description Excel / Report Items Excel / Data Map Excel / Section 3.1 Input / Section 3.2 Output / Section 5 / Functional Description §N] | [What to change and where] |
| 2 | ... | ... | ... |

[If the Excel could not be read because it is a binary attachment:]
> ⚠️ The field specification Excel (`<filename>.xlsx`) is attached to the page but its content could not be read automatically. Please manually verify that all fields/operations documented in the Excel are consistent with the rest of the page.

---

### What to do next

[2–3 sentence summary of the most important fixes and recommended order of action. If there are Item Description sync issues, mention them here as well.]
```

If a category has no issues, omit it (don't write "🟡 Warning — None found").

If the Item Description Issue List has no issues, omit that section too.

If the page looks clean with no real issues, say so directly rather than inventing minor nitpicks.

## Step 6: Save the report to a file

After writing the report, save it using the Write tool (not a shell command — the report content contains special characters that break shell quoting):

- Filename: `Report_<functionCode>_<yyyyMMddHHmmss>.md` if a function code is present on the page (e.g. `Report_BINV00150_20260523003108.md`). Fall back to `Report_<pageId>_<yyyyMMddHHmmss>.md` only if the page has no function code.
- Get the timestamp from: `date +%Y%m%d%H%M%S` via Bash
- Write the full report content to that filename in the current working directory
- Tell the user the full file path once saved
