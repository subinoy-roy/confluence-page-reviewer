# Interface Page Checks

Apply these checks for pages whose function code starts with `I` (e.g., `IINV04002`, `IVSC00120`).

## What the Interface File Format Excel contains

The Interface File Format Excel documents the physical layout of every output file record type (Header, Detail, Footer). Each entry typically covers: field name, start position, end position (or length), data type (Character/Numeric/Date), Mandatory/Optional flag, and description. The Detail section is authoritative for the interface's data fields. It must stay in sync with Section 6.4 Record construction & mapping.

## Step 3c: Cross-check Interface File Format Excel vs Section 6.4

Compare the **Interface File Format Excel** (Section 7) against the field list in **Section 6.4 Record construction & mapping** (Detail fields numbered list) record type by record type.

Check for:
- **Fields in Section 6.4 missing from the Excel** — field is described in the Functional Description but has no row in the Interface File Format Excel
- **Fields in the Excel not in Section 6.4** — the Excel documents a field that has no mapping logic in the Functional Description
- **Name mismatches** — same field labeled differently in the two places (e.g., "PDIDate" vs "PDI Date")
- **Length contradictions** — field length in the Excel differs from the length implied by the source DB column or the fixed-record total in Section 6.1
- **Mandatory/Optional contradictions** — a field marked Mandatory in the Excel but the Functional Description treats it as optional (no validation), or vice versa
- **Missing Excel entirely** — no table content and no `.xlsx` attachment in the "Interface File Format" section

## Step 4: Additional checks for Interface pages

### File structure consistency (Section 6.1 + Section 7 Interface File Format Excel)
- The total fixed record length stated in Section 6.1 must equal the sum of all field lengths in the Detail section of the Interface File Format Excel; a mismatch means a field is missing or a length is wrong
- The field separator stated in Section 6.1 (e.g., `|`) must match what is shown in Section 6.4.2 and the Interface File Format Excel
- The file type (fixed-length, delimited, etc.) must be consistent across Section 6.1, Section 6.4, and the Interface File Format Excel

### Section 6.2 Parameters vs Section 3.1 Input
- Every parameter listed in Section 6.2 (e.g., Auto/Resend Flag, Submit Time, From Date, To Date) should appear in Section 3.1 Input; flag any parameter in 6.2 that has no corresponding entry in 3.1

### Section 6.5 Validations & error handling
- Every error code referenced in Section 6.5 must appear in Section 5 Logging Messages (or the Common Errors reference page linked from Section 5); apply the message code format rules from the "Message code validation" section of SKILL.md to verify each code
- Conditional mandatory rules (e.g., Engine fields mandatory for Non-EV, Motor fields mandatory for BEV) must correspond to fields flagged as Mandatory in the Interface File Format Excel; flag any mandatory field in the Excel that has no validation in 6.5
- Step numbering gaps in Sections 6.3/6.4 — a sub-step is referenced but that number is not defined

### Cross-section consistency
- Section 1.2 Post Condition vs Section 3.2 Output — output tables/files written must appear in both
- Section 3.2 Output file name pattern must match the file name format constructed in Section 6.4.1 (Header record); flag any mismatch in naming convention
- Section 4 Batch Type / Protocol vs Section 10 Destination/Source/Archive Path — the transfer protocol (e.g., SFTP) and schedule stated in Section 4 should be consistent with the paths and protocol described in Section 10; flag if one says SFTP and the other implies a different mechanism
