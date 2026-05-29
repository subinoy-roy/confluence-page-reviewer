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

### Section 3.1 vs Section 6 parameter usage
- **Declared parameter not used in Section 6** — for every input parameter listed in Section 3.1, verify it appears by name in the Section 6 Functional Description (as a filter condition, assignment source, or passed argument); a parameter declared but never referenced in Section 6 is stale and should be removed or its usage documented; flag as Critical
- **Undeclared parameter used in Section 6** — if Section 6 references a named parameter (e.g., used in a WHERE clause or assigned to a variable) that does not appear in Section 3.1, that parameter has no documented type, description, or contract; flag as Critical since callers have no specification for it

### Section 5 Logging Messages
- Duplicate S.No. values or gaps in the sequence — indicates rows were added/removed without renumbering
- Two errors with identical descriptions and causes — impossible to distinguish; need unique descriptions or consolidation
- Error codes referenced in the Functional Description or Data Map that are absent from this table
- Apply the message code format rules from the "Message code validation" section of SKILL.md — verify each code is either a valid common code (check the Common Errors page) or a correctly formed page-specific code for this module

### Section 6 Functional Description
- Step numbering gaps — a step is referenced (e.g., "from Step 5") but that step number is not defined
- Filter conditions that appear backwards or incomplete (e.g., "where cancel_flag IS NOT NULL" when the step processes all records)
- Duplicate assignment blocks — the same variable assigned twice back-to-back with near-identical logic (residual from a refactor)
- **DB write step with no error code** — for every step that performs an INSERT, UPDATE, or DELETE operation, at least one error code referencing that step must be present in Section 5 Logging Messages; a write step with no error handling documented means failures will be silent; flag as Warning for each such step
- **Transaction boundaries not documented** — if Section 6 describes write operations (INSERT, UPDATE, DELETE) across more than one table, the document must state the transaction strategy: which steps are grouped in a single transaction, what triggers a ROLLBACK, and whether partial commits are allowed; if multiple writes exist but no transaction handling is mentioned anywhere in Section 6, flag as Warning
- **Cursor or loop missing entry/exit conditions** — if Section 6 describes processing records in a cursor or loop, three things must be explicitly documented: (a) the filter/WHERE condition that determines which records enter the loop, (b) the termination condition (e.g., "loop ends when no more records"), and (c) what happens when the result set is empty (e.g., skip, log, raise error); flag as Warning for each condition that is absent

### Cross-section consistency
- Section 1.2 Post Condition vs Section 3.2 Output — every table written to by the SP should appear in both; a table in Output but not Post Condition (or vice versa) is an inconsistency
- **Section 3.2 Output vs Section 6 write operations** — cross-check in both directions:
  - Every table that Section 6 writes to (INSERT, UPDATE, or DELETE) must appear in Section 3.2 Output; a table written to in Section 6 but absent from Section 3.2 is an undocumented output — flag as Critical
  - Every table listed in Section 3.2 Output must have at least one corresponding INSERT, UPDATE, or DELETE operation targeting it in Section 6; a table in Section 3.2 with no write in Section 6 is a phantom output — flag as Critical
- **Pre/Post Condition scope** — Section 1.2 Pre Condition and Post Condition must list not only table names but also related screens, batches, and interfaces that interact with this SP; flag as Warning if only table names appear with no mention of related functions
- **Section 3.2 Output column headers** — the table heading should say "Output Name" (not "Input Name"); a wrong label is a clear copy-paste error
- **Section 3.2 vs Section 3.3 overlap** — a table that appears in both Section 3.2 Output and Section 3.3 Reference is contradictory; a table is either a destination written to or a reference read from, not both
- **Data Map "N/A" for an active SP** — if Section 7 Data Map says "N/A" but Section 6 describes INSERT, UPDATE, or DELETE operations, flag as Critical; the Data Map is the authoritative data-flow artifact for stored procedures and cannot be omitted for any SP that writes data
- Section 4 Batch Type / Frequency / Protocol — the schedule and trigger mechanism should be clearly defined; flag if left as N/A or placeholder when the SP is called by other programs (list the callers)
- **Section 4 "called by" not documented** — if Section 6 describes the SP being triggered externally (e.g., "called from the batch job", "invoked by the interface"), Section 4 must explicitly name the calling programs or jobs; if callers are referenced in Section 6 but Section 4 is silent on who calls this SP, flag as Warning; a developer or support engineer cannot trace the call chain without this information

### Function list CR check
- **Pending CRs not considered** — the reviewer must check the "Function List with CR" reference document to verify whether any pending Change Requests affect this DR; since this requires an external Excel, always include a reminder in the report: "Manually verify in the Function List with CR document whether any pending CRs are related to this DR"
