# Interface Page Checks

Apply these checks for pages whose function code starts with `I` (e.g., `IINV04002`, `IVSC00120`).

## What the Interface File Format Excel contains

The Interface File Format Excel documents the physical layout of every output file record type (Header, Detail, Footer). Each entry typically covers: field name, start position, end position (or length), data type (Character/Numeric/Date), Mandatory/Optional flag, and description. The Detail section is authoritative for the interface's data fields. It must stay in sync with Section 6.4 Record construction & mapping.

## Step 3b.1: Determine interface direction

Before cross-checking the Excel, determine whether this is a **Send (Outbound)**, **Receive (Inbound)**, or **Bidirectional** interface. This affects which checks apply.

**Look for signals in this order:**

| Location | Send signals | Receive signals |
|---|---|---|
| Page title / Section 1 Objective | "Send", "Export", "Generate", "Output", "Outbound" | "Receive", "Import", "Input", "Inbound", "Load", "Upload" |
| Section 4 Protocol | File transferred *to* external system | File received *from* external system |
| Section 6 Functional Description | SELECTs from DB → writes to file | Reads from file → INSERTs/UPDATEs to DB |
| Section 10 Paths | Destination path populated, Source path N/A | Source path populated, Destination path N/A |

**Decision rules:**
- If all signals point the same way → conclude the direction and proceed
- If signals are mixed or ambiguous in any way → **stop and ask the user**:

> "I want to confirm the direction of this interface before applying checks. Based on the document it appears to be a **[Send / Receive / unclear]** interface — is that correct, or is it [the other / bidirectional]?"

Do not proceed with Step 3c until the direction is confirmed. Store the confirmed direction as `interface_direction` (`send`, `receive`, or `both`) and apply the appropriate type-specific checks in Step 4 below.

## Step 3c: Cross-check Interface File Format Excel vs Section 6.4

Compare the **Interface File Format Excel** (Section 7) against the field list in **Section 6.4 Record construction & mapping** record type by record type. Apply the checks below to **all three record types — Header, Detail, and Footer** — not just the Detail section.

### Detail record (Section 6.4 Detail fields)
- **Fields in Section 6.4 missing from the Excel** — field is described in the Functional Description but has no row in the Interface File Format Excel
- **Fields in the Excel not in Section 6.4** — the Excel documents a field that has no mapping logic in the Functional Description
- **Name mismatches** — same field labeled differently in the two places (e.g., "PDIDate" vs "PDI Date")
- **Length contradictions** — field length in the Excel differs from the length implied by the source DB column or the fixed-record total in Section 6.1
- **Mandatory/Optional contradictions** — a field marked Mandatory in the Excel but the Functional Description treats it as optional (no validation), or vice versa

### Header record (Section 6.4.1)
- **Header fields in Excel missing from Section 6.4.1** — the Excel has a Header record block but Section 6.4.1 does not document the construction of one or more of those fields; flag each missing field
- **Header fields in Section 6.4.1 missing from the Excel** — Section 6.4.1 describes constructing a header field that has no corresponding row in the Excel Header block; flag each missing row
- **Header record type indicator not documented** — the first field of the Header record should identify the record type (e.g., a literal "H" or "01"); if absent from both the Excel and Section 6.4.1, flag as Warning

### Footer record (Section 6.4.3)
- **Footer fields in Excel missing from Section 6.4.3** — the Excel has a Footer record block but Section 6.4.3 does not document one or more of those fields; flag each missing field
- **Footer fields in Section 6.4.3 missing from the Excel** — Section 6.4.3 describes a footer field that has no corresponding row in the Excel Footer block; flag each missing row
- **Footer record count or total not documented** — the Footer record should include a record count (total Detail records written) and, where applicable, control totals (e.g., sum of amounts); if neither appears in Section 6.4.3 or the Excel Footer block, flag as Warning

### Common to all record types
- **Missing Excel entirely** — no table content and no `.xlsx` attachment in the "Interface File Format" section
- **Date field with no format specified** — for every field in the Excel whose data type is Date (or Date-Time), the format must be explicitly stated (e.g., `YYYYMMDD`, `DD/MM/YYYY`, `YYYY-MM-DD HH:MM:SS`); a Date field with no format means the developer must guess, which causes mismatches between the sending and receiving systems — flag as Warning for each unformatted Date field

## Step 4: Additional checks for Interface pages

### File structure consistency (Section 6.1 + Section 7 Interface File Format Excel)
- The total fixed record length stated in Section 6.1 must equal the sum of all field lengths in the Detail section of the Interface File Format Excel; a mismatch means a field is missing or a length is wrong
- The field separator stated in Section 6.1 (e.g., `|`) must match what is shown in Section 6.4.2 and the Interface File Format Excel
- The file type (fixed-length, delimited, etc.) must be consistent across Section 6.1, Section 6.4, and the Interface File Format Excel
- **File encoding not specified** — Section 6.1 must state the file character encoding (e.g., UTF-8, TIS-620); flag as Warning if absent, as the wrong encoding will corrupt non-ASCII characters (particularly Thai text)
- **Line terminator not specified** — Section 6.1 should state the line ending format (e.g., CRLF for Windows, LF for Unix); flag as Suggestion if absent

### Send (Outbound) specific checks
*Apply only when `interface_direction` is `send` or `both`.*
- **DB source mapping missing** — for each Detail field in the Excel, Section 6.4 must document which DB table and column it is sourced from, or the derivation/calculation logic; a file field with no documented DB source leaves the developer guessing — flag as Warning
- **Empty file handling not documented** — the document must state what happens when no DB records match the selection criteria: does the system generate a file containing only Header and Footer records, or skip file generation entirely? — flag as Warning if absent
- **Resend/regeneration behaviour not documented** — if an Auto/Resend Flag or equivalent parameter exists, the document must describe what happens when the interface is rerun for the same period: does it regenerate the file from scratch, only include records not previously sent, or refuse to regenerate if a file already exists? — flag as Warning if the parameter exists but regeneration behaviour is undocumented

### Receive (Inbound) specific checks
*Apply only when `interface_direction` is `receive` or `both`.*
- **DB target mapping missing** — for each Detail field in the Excel, Section 6.4 must document which DB table and column the value is loaded into; a file field with no documented DB target — flag as Warning
- **Rejected/invalid record handling not documented** — Section 6.5 must describe what happens to records that fail validation: are they written to a rejection file, skipped with a log entry, or cause the entire file to be rejected? — flag as Warning if absent
- **Empty incoming file handling not documented** — the document must state what happens when the incoming file contains no Detail records: does the system process it silently (writing nothing to DB), or raise an error? — flag as Warning if absent
- **Duplicate file / resend handling** — if an Auto/Resend Flag parameter exists, the document must describe what happens when the same file is received again: does the system re-process all records, skip already-loaded records, or require manual intervention? — flag as Warning if the parameter exists but reprocessing behaviour is undocumented

### Section 6.2 Parameters vs Section 3.1 Input
- **Parameter in Section 6.2 not declared in Section 3.1** — every parameter listed in Section 6.2 (e.g., Auto/Resend Flag, Submit Time, From Date, To Date) must appear in Section 3.1 Input; a parameter used in Section 6.2 but absent from Section 3.1 has no documented type, label, or contract for the caller — flag as Critical
- **Parameter declared in Section 3.1 not used in Section 6.2** — every input parameter listed in Section 3.1 must be referenced by name in Section 6.2 or elsewhere in the Functional Description; a parameter declared but never applied in the interface logic is stale and misleads callers — flag as Critical

### Section 6.5 Validations & error handling
- Every error code referenced in Section 6.5 must appear in Section 5 Logging Messages (or the Common Errors reference page linked from Section 5); apply the message code format rules from the "Message code validation" section of SKILL.md to verify each code
- Conditional mandatory rules (e.g., Engine fields mandatory for Non-EV, Motor fields mandatory for BEV) must correspond to fields flagged as Mandatory in the Interface File Format Excel; flag any mandatory field in the Excel that has no validation in 6.5
- Step numbering gaps in Sections 6.3/6.4 — a sub-step is referenced but that number is not defined

### Cross-section consistency
- Section 1.2 Post Condition vs Section 3.2 Output — output tables/files written must appear in both
- Section 3.2 Output file name pattern must match the file name format constructed in Section 6.4.1 (Header record); flag any mismatch in naming convention
- Section 4 Batch Type / Protocol vs Section 10 Destination/Source/Archive Path — the transfer protocol (e.g., SFTP) and schedule stated in Section 4 should be consistent with the paths and protocol described in Section 10; flag if one says SFTP and the other implies a different mechanism
- **Section 10 paths incomplete** — Section 10 must specify all three paths; apply based on `interface_direction`:
  - Send: Destination path (where the file is delivered) and Archive path (where the generated file is archived) must be populated; flag as Warning if either is blank or N/A without explanation
  - Receive: Source path (where the incoming file is picked up) and Archive path (where the processed file is moved) must be populated; flag as Warning if either is blank or N/A without explanation
  - Both directions: all three paths must be populated; flag each that is blank or N/A without explanation
