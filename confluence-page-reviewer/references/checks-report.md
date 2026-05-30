# Report Page Checks

Apply these checks for pages whose function code starts with `R` (e.g., `RINV60070`, `RDLR00050`).

## What the Report Items Excel contains

The Report Items Excel documents every column shown in the report output — typically columns like Field Name, Data Type, Format, Sort/Group flag, and Description. It is meant to stay in sync with the **Display Order** section (or report column list).

## Step 3c: Cross-check Report Items Excel vs Display Order

Compare the **Report Items Excel** against the **Display Order** section (or report column list) field by field. The Display Order lists every column shown in the report output; the Excel should document each one.

Check for:
- **Columns in Display Order missing from the Excel** — listed in the report but no Excel entry
- **Columns in the Excel not in Display Order** — orphaned Excel entry for a column not in the report
- **Name mismatches** — same column with different labels
- **Property contradictions** — column properties in Excel (data type, format, sort/group flag) contradict what the Operation Description says
- **Sort/Group flag vs Section 6 mismatch** — for every column marked with a Sort or Group flag in the Excel, verify that Section 6 Functional Description contains a corresponding ORDER BY or GROUP BY clause for that column; conversely, if Section 6 orders or groups by a column that is not flagged in the Excel, that is also an inconsistency; flag each mismatch as a Warning
- **Missing Excel entirely** — no table content and no `.xlsx` attachment in the "Report Items" section

## Step 4: Additional checks for Report pages

### Table naming conventions
- **Missing logical table name** — every database table referenced in the document (Sections 3.1, 3.2, 3.3, Functional Description) must be cited in the format `Logical Name (Physical_Table_Name)`, e.g., `Series Master (DS_SRS_MST)`; flag any table that appears only as a physical name without the logical name in parentheses
- **Non-conforming physical table name** — physical table names must follow the agreed naming convention; flag any table whose physical name uses an old or non-standard prefix/pattern

### Legacy function reference
- **Legacy function ID absent** — the document should state the equivalent legacy system function ID or reference number; if this field is blank, missing, or marked N/A without explanation, flag as Warning

### Display Order vs Section 6 Functional Description
- **Column with no documented source** — for every column listed in the Display Order, Section 6 must identify where its value comes from: the source table and field, or the derivation/calculation logic; a column present in Display Order but with no corresponding source or derivation in Section 6 means a developer must guess its origin — flag as Critical for each such column
- **Column sourced in Section 6 but absent from Display Order** — if Section 6 describes deriving or fetching a field that does not appear in the Display Order, either the column was dropped from the output without removing its logic, or it was added to the logic without being declared in the output specification — flag as Critical

### Section 3.1 Input parameters vs Section 6 Functional Description
- **Declared filter parameter not used in Section 6** — for every filter/search parameter listed in Section 3.1 Input, verify it appears by name in the Section 6 WHERE clause or filter logic; a parameter declared but never applied in the query is stale and misleads callers — flag as Critical
- **Undeclared parameter used in Section 6** — if Section 6 references a filter or input parameter in its WHERE clause or logic that does not appear in Section 3.1 Input, that parameter has no documented type, label, or contract for the user interface — flag as Critical

### Report layout
- **Layout does not match user requirements** — the Display Order / report layout section should reflect the agreed user requirements; flag if the layout appears to be a template placeholder rather than the actual agreed design
- **No actual sample data in layout** — the report layout should show realistic sample data (not blank or "xxx" placeholders) so the reader can verify the format and content; flag if sample data is absent
- **Inquiry criteria and detail data mismatch** — if the report has both an inquiry/filter section and a detail output section, the sample data in the detail section must be consistent with the inquiry criteria shown; flag any mismatch
- **Sorting order not specified or incorrect** — the report layout must show data in the agreed sorting order; flag if sort order is unspecified or contradicts the Functional Description

### Empty result handling
- **No-data behaviour not documented** — the document must state what is printed when no records match the filter criteria; the expected behaviour is: a blank report with the applicable header and footer is printed, with no error message; flag as Warning if this is not mentioned anywhere in the Functional Description or report layout notes

### Report header and footer
- **Header/footer not addressed** — every report must explicitly state whether a header and footer apply; if the document makes no mention of either, flag as Warning
- **Header applies but content not specified** — if the document states a header is present, its content must be described (e.g., report title, run date, filter criteria used, company name); flag as Warning if the header is mentioned but its content is not defined
- **Footer applies but content not specified** — if the document states a footer is present, its content must be described (e.g., page number, total record count, timestamp); flag as Warning if the footer is mentioned but its content is not defined
- **Header or footer not applicable — must be explicitly stated** — if header or footer does not apply to this report, the document must explicitly say so (e.g., "No header", "Footer: N/A"); silence is not acceptable as it leaves the developer guessing; flag as Warning if either is simply absent from the document

### Totals and subtotals
- **Grouping without subtotals documented** — if any column in the Report Items Excel is marked as grouped, the Display Order or Section 6 Functional Description must document the corresponding subtotal and grand total rows (what is summed/counted, where they appear, and their label); if grouping exists but no totals are mentioned anywhere in the document, flag as Warning

### UX link and layout
- **UX link absent for new UI** — for reports with a new UI, either a UX design link or a layout Excel should be present; flag as Warning if neither is provided

### Report output and print configuration
- **Page size and orientation not defined** — the UISS / report configuration section should specify the page size (e.g., A4) and orientation (Portrait/Landscape) for printing; flag as Warning if absent or left as placeholder
- **Common report configuration not referenced** — the document should reference the common report configuration page and identify which standard sections apply to this specific report; flag as Warning if this reference is missing

### Access section
- **Access Detail Excel not referenced** — the Access section should reference the "Access Detail" Excel which maintains the As-Is access assignments; flag as Warning if absent or blank
- **Access Control roles not listed** — the Access Control section should list the applicable roles as per the agreed access Excel; flag as Warning if the section is empty or contains only generic placeholder text
- **TMTECR user must not have access** — verify that the TMTECR user is not listed in the Access Control section; flag as Critical if it is, since this is not a valid user for access assignment

### Cross-section consistency
- **Pre/Post Condition scope** — Section 1.2 Pre Condition and Post Condition must list not only table names but also related screens, batches, and interfaces that interact with this report; flag as Warning if only table names appear
- **Function ID prefix** — the function ID must start with `R`; flag as Critical if it uses any other prefix

### Domain-specific reminders (manual verification required)
These checks cannot be automated — always include them as a reminder block in the report for the human reviewer:

- **Series/brand dropdown** — if the report includes a Series field, verify that a brand dropdown precedes it, and that the sort order places Toyota first followed by other brands alphabetically
- **Valid series/model/color** — confirm that only valid series, model/SFX, and color values are displayed (valid = `to_date > current date OR to_date IS NULL`); check with SA if unsure
- **PDPA masking** — if the report displays any of the following customer data fields, confirm with SA how masking is handled: Name/Surname, Citizen ID, DOB, Address, Email Address, Mobile/Telephone No.
- **Dummy Dealer handling** — if the report shows dealer information: (a) a specific dealer sees only their own data; (b) Dummy Dealer is hidden from roles without that privilege; (c) only roles with explicit privilege can see Dummy Dealer; if VIN or booking data is shown, check with SA separately
- **Toyota heading** — confirm that "Toyota" does not appear in the top-left heading of the report unless specifically required; check with SA if in doubt

### Error code hyperlink integrity
- **Error code not hyperlinked in Functional Description** — every error code cited in the Functional Description (Section 6) must be a hyperlink pointing to the corresponding anchor on the matching row in the Specific Errors table (Section 5 Logging Messages); a plain-text code with no link forces readers to scroll and search manually and makes stale references invisible — flag as Warning for each code that appears as plain text rather than a hyperlink
- **Hyperlink target missing in Logging Messages table** — if an error code in the Functional Description is hyperlinked but the target anchor does not exist in Section 5 (i.e., the code is absent from the table), the link is broken and the error is undocumented — flag as Critical

### Function list CR check
- **Pending CRs not considered** — always include a reminder in the report: "Manually verify in the Function List with CR document whether any pending CRs are related to this DR"
