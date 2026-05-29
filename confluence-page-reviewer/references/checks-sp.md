# Stored Procedure Page Checks

Apply these checks for pages whose function code starts with `B` (e.g., `BINV00150`, `BVSC00210`).

## What the Data Map Excel contains

The Data Map Excel documents the data flow for every INSERT, UPDATE, and DELETE operation the SP performs. Its structure is:

- **Left side — Source queries (Q1, Q2, …):** each block identifies a source table (`DB/File Name: QN | table_name`), key fields used to filter/join it, and numbered source fields (`QN.1`, `QN.2`, …) with their expressions.
- **Right side — Destination blocks:** each block identifies a target table (`DB/File Name: table_name`), numbered destination fields with transformation logic sourced from `QN.M` references or constants, and key fields (for UPDATE/DELETE operations).

The Data Map must stay in sync with Section 3.1 Input/Output and Section 6 Functional Description.

## Step 3c: Cross-check Data Map

Run three classes of checks:

### Internal Data Map consistency
- **Broken source references** — every `QN.M` reference in a destination field must correspond to a field actually defined in source block QN (e.g., if destination uses `Q3.5` but Q3 only defines Q3.1–Q3.3, that is a broken reference)
- **Missing destination table names** — any destination block where `DB/File Name` is blank; the target table is unknown
- **Duplicate key mappings** — same source field (`QN.M`) mapped to two different key columns in the same source block (likely a copy-paste error)
- **Typos in key values** — key field values that appear to be mis-typed (e.g., "color dode" instead of "color code")

### Data Map vs Section 3 Input/Output
- Every source table (Q1…Qn) should appear in Section 3.1 Input or Section 3.3 Reference; flag any source table present in the Data Map but absent from both
- Every destination table should appear in Section 3.2 Output; flag any destination table present in the Data Map but absent from Section 3.2
- Tables listed in Section 3.2 Output that have no corresponding destination block in the Data Map

### Data Map vs Section 6 Functional Description
- Key derivation logic in the Data Map (e.g., group_code, document_type assignments) must match the equivalent logic block in the Functional Description; flag any discrepancy
- Every error code referenced in the Data Map must have a corresponding entry in Section 5 Logging Messages

## Step 4: Additional checks for SP pages

### Table naming conventions
- **Missing logical table name** — every database table referenced anywhere in the document (Sections 3.1, 3.2, 3.3, Data Map, Functional Description) must be cited in the format `Logical Name (Physical_Table_Name)`, e.g., `Series Master (DS_SRS_MST)`; flag any table that appears only as a physical name with no logical name in parentheses
- **Non-conforming physical table name** — physical table names must follow the agreed naming convention; flag any table whose physical name uses an old or non-standard prefix/pattern that does not match the new naming convention

### Legacy function reference
- **Legacy function ID absent** — the document should state the equivalent legacy system function ID or reference number; if this field is blank, missing, or marked N/A without explanation, flag as Warning

### Access section
- **Access detail not referenced** — the Access section should explicitly reference the "Access Detail" Excel which maintains the As-Is access assignments for the function; flag as Warning if the section is absent, blank, or does not mention the Excel

### Section 3.1 Input parameters
- **No parameter table at all** — if Section 6 lists named input parameters but Section 3.1 contains only prose (e.g., "Input is coming from the parameters passed to the stored procedure") with no table, flag as Critical; the parameter table is the authoritative contract for callers
- Numbering gaps (e.g., list jumps from #4 to #6) — either a parameter was removed without renumbering, or one is missing
- Mixed data type notation (e.g., `VARCHAR` vs `VARCHAR2` in the same table) — suggests the section was assembled from different sources
- Parameters and DB tables mixed together without clear separation — check that the table clearly distinguishes individual input parameters from input DB tables

### Section 5 Logging Messages
- Duplicate S.No. values or gaps in the sequence — indicates rows were added/removed without renumbering
- Two errors with identical descriptions and causes — impossible to distinguish; need unique descriptions or consolidation
- Error codes referenced in the Functional Description or Data Map that are absent from this table
- Apply the message code format rules from the "Message code validation" section of SKILL.md — verify each code is either a valid common code (check the Common Errors page) or a correctly formed page-specific code for this module

### Section 6 Functional Description
- Step numbering gaps — a step is referenced (e.g., "from Step 5") but that step number is not defined
- Filter conditions that appear backwards or incomplete (e.g., "where cancel_flag IS NOT NULL" when the step processes all records)
- Duplicate assignment blocks — the same variable assigned twice back-to-back with near-identical logic (residual from a refactor)

### Cross-section consistency
- Section 1.2 Post Condition vs Section 3.2 Output — every table written to by the SP should appear in both; a table in Output but not Post Condition (or vice versa) is an inconsistency
- **Pre/Post Condition scope** — Section 1.2 Pre Condition and Post Condition must list not only table names but also related screens, batches, and interfaces that interact with this SP; flag as Warning if only table names appear with no mention of related functions
- **Section 3.2 Output column headers** — the table heading should say "Output Name" (not "Input Name"); a wrong label is a clear copy-paste error
- **Section 3.2 vs Section 3.3 overlap** — a table that appears in both Section 3.2 Output and Section 3.3 Reference is contradictory; a table is either a destination written to or a reference read from, not both
- **Data Map "N/A" for an active SP** — if Section 7 Data Map says "N/A" but Section 6 describes INSERT, UPDATE, or DELETE operations, flag as Critical; the Data Map is the authoritative data-flow artifact for stored procedures and cannot be omitted for any SP that writes data
- Section 4 Batch Type / Frequency / Protocol — the schedule and trigger mechanism should be clearly defined; flag if left as N/A or placeholder when the SP is called by other programs (list the callers)

### Function list CR check
- **Pending CRs not considered** — the reviewer must check the "Function List with CR" reference document to verify whether any pending Change Requests affect this DR; since this requires an external Excel, always include a reminder in the report: "Manually verify in the Function List with CR document whether any pending CRs are related to this DR"
