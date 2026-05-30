# Screen Page Checks

Apply these checks for pages whose function code starts with `F` or `W` (e.g., `FINV60035`, `WVSC00160`).

## What the Item Description Excel contains

The Item Description Excel documents every field/control shown on the screen — typically columns like Field Name, Field Type, Mandatory/Optional, Default Value, Max Length, and Description. It is meant to stay in sync with the **Display Order** section.

## Step 3c: Cross-check Item Description Excel vs Display Order

Compare the **Item Description Excel** against the **Display Order** section table field by field. The Display Order lists every field/control shown on the screen; the Excel should document each one.

Check for:
- **Fields in Display Order missing from the Excel** — listed on screen but no Excel entry
- **Fields in the Excel not in Display Order** — orphaned Excel entry for a field not on screen
- **Name mismatches** — same field with different labels (e.g., "Invoice Date" vs "Inv. Date")
- **Property contradictions** — mandatory/default/type in Excel contradicts what the Operation Description says
- **Missing Excel entirely** — no table content and no `.xlsx` attachment in the "Item Description" section

## Step 4: Additional checks for Screen pages

### Table naming conventions
- **Missing logical table name** — every database table referenced in the document (Sections 3.1, 3.2, 3.3, Functional Description) must be cited in the format `Logical Name (Physical_Table_Name)`, e.g., `Series Master (DS_SRS_MST)`; flag any table cited only by its physical name
- **Non-conforming physical table name** — physical table names must follow the agreed naming convention; flag any name that uses an old or non-standard prefix/pattern

### Legacy function reference
- **Legacy function ID absent** — the document must state the equivalent legacy system function ID; flag as Warning if blank, missing, or N/A without explanation

### Screen layout
- **Layout does not reflect user requirements** — the Display Order / screen layout section should represent the agreed design, not a template placeholder; flag if it appears generic or incomplete
- **No actual sample data** — the screen layout must show realistic sample data (not blank or "xxx" placeholders); flag if absent
- **Inquiry/detail data mismatch** — if the screen has both an Inquiry and a Detail section, the sample data in the Detail section must be consistent with the Inquiry criteria shown; flag any mismatch
- **Sort order unspecified** — the screen layout must show data in the agreed sort order; flag if sort order is absent or contradicts the Functional Description

### Button Control section
- **Button not documented** — every button referenced in the Display Order must have a corresponding entry in the Button Control section describing its functionality; flag any button missing from Button Control
- **Button Control section absent** — if the screen has any action buttons but no Button Control section exists, flag as Critical
- **Button State vs Button Control mismatch** — compare the button names listed as columns in the Button State table (Section 3) against the button column headers in the Button Control table (Section 4.b); any button present in one table but absent from the other is a Critical issue, as the enable/disable behaviour for that button across screen modes is either undefined or undocumented in the access specification

### UX link
- **UX link absent** — for screens with a new UI design, a UX link must be present in the document; flag as Warning if missing

### Screen Flow
- **Screen Flow section absent or empty** — a Screen Flow section must exist showing the complete navigation path for creating or accessing a new item; flag as Critical if missing, flag as Warning if present but empty or generic

### Error and Warning messages
- **Validation without an error/warning message** — every validation check and every operation described in the Functional Description must reference a corresponding error or warning message code; flag any validation or operation that has no associated message code
- **Delete operation missing CNF00003** — any Delete functionality must reference `CNF00003` ("Are you sure to delete this record?") as the confirmation message; flag as Critical if a delete operation is described but CNF00003 is not referenced

### Screen-specific error codes
- **Errors not in Error Master Excel** — screen-specific error codes must be maintained in the Error Master Excel; always include a reminder in the report: "Manually verify that all screen-specific error codes for this DR are recorded in the Error Master Excel"

### Error code hyperlink integrity
- **Error code not hyperlinked in Operation Description** — every error code cited in the Operation Description (Section 10) must be a hyperlink pointing to the corresponding anchor on the matching row in the Specific Errors table (Section 9.2); a plain-text code with no link forces readers to scroll and search manually and makes stale references invisible — flag as Warning for each code that appears as plain text rather than a hyperlink
- **Hyperlink target missing in Specific Errors table** — if an error code in the Operation Description is hyperlinked but the target anchor does not exist in Section 9.2 (i.e., the code is absent from the table), the link is broken and the error is undocumented — flag as Critical

### Performance section
- **Performance section blank** — the Performance section must not be empty or contain only "N/A"; if it is blank, flag as Warning and note that expected content includes estimated data volume, response time targets, and pagination approach

### Pagination
- **Pagination not addressed for large data** — if the screen displays lists or search results that could return large volumes of data, the document must address pagination; flag as Warning if this is not mentioned

### Logging and Audit Trail
- **Logging/Audit Trail section missing or incomplete** — the section must have two explicit subsections: (a) **Logging** — tracking every update and delete operation (who and when); (b) **Audit Trail** — PDPA-related log of who changed what, and old vs new values; flag as Warning if either subsection is absent or contains only placeholder text
- **Logging marked N/A despite CRUD operations** — if Section 10 describes any Add, Edit, or Delete operation but the Logging section is marked N/A, flag as **Warning**: "Logging is marked N/A but the screen performs data modifications. Please confirm with IS whether operation logging is required."
- **Audit Trail marked N/A without confirmation** — if Section 10 modifies data and the Audit Trail section is marked N/A, flag as **Warning**: "Audit Trail is marked N/A but the screen writes data. Please confirm with IS whether PDPA-related audit trail logging (who changed what, old vs new values) applies to this screen."

### Like search / wildcard
- **Wildcard search not documented** — if the screen has any free-text search fields, the document must specify that `*` (asterisk) is the wildcard character, with examples (`*THE*` to find records containing "THE", etc.); flag as Warning if absent
- **Tooltip not mentioned** — any field supporting wildcard search must have a tooltip informing the user; flag as Warning if no tooltip is mentioned for such fields

### Dependent combos
- **Dependent combo not noted** — if any combo/dropdown is populated based on another field's selection (e.g., Model/SFX filtered by Series), a "Note to developer" must appear at the end of Section 10 listing all dependent combos; flag as Warning if dependent combos exist in the Functional Description but no such note is present

### Inquiry section
- **New screen missing Inquiry section** — screens that did not have an Inquiry section in the legacy application must now include one; flag as Warning if the Functional Description describes a screen with no Inquiry/Search section at all

### Label sync
- **UI / Item Description / Display Order labels out of sync** — the field labels in the UI section, the "Item Description" Excel, and the "Display Order" section must all use exactly the same names; flag any field where the label differs across these three places

### Access section
- **Access Detail Excel not referenced** — the Access section must reference the "Access Detail" Excel for As-Is access assignments; flag as Warning if absent or blank
- **Access Control roles not listed** — the Access Control section must list applicable roles per the agreed access Excel; flag as Warning if empty or generic
- **TMTECR user must not have access** — verify TMTECR is not listed in the Access Control section; flag as Critical if present

### Cross-section consistency
- **Pre/Post Condition scope** — Section 1.2 Pre and Post Conditions must list related screens, batches, and interfaces, not just table names; flag as Warning if only tables appear
- **Screen access note missing from Post Condition** — Post Condition for screens must include: "Users with roles which has been assigned access to the screen will be able to access the screen as per allowed access settings"; flag as Warning if absent
- **Function ID prefix** — the function ID must start with `W` or `F`; flag as Critical if it uses any other prefix

### Domain-specific reminders (manual verification required)
Always include these as a reminder block in the report for the human reviewer:

- **Series/brand dropdown** — if the screen includes a Series field, a brand dropdown must precede it; sort order: Toyota first, then other brands alphabetically
- **Model/SFX sort order** — Model/SFX dropdowns must be sorted as `generation_value DESC, rpt_sequence ASC`; verify this is stated in the relevant operation
- **Dealer dropdown On-Load** — if the screen has a Dealer dropdown in the Inquiry block, the On-Load operation must state: dealer users see only their own dealer code; TMT users can select from assigned dealers
- **Branch dropdown On-Load** — same pattern as Dealer: branch code fixed for dealer users, selectable for TMT users
- **Salesman dropdown On-Load** — same pattern: salesman code fixed for dealer users, selectable for TMT users
- **Valid series/model/color** — only valid values should be displayed (`to_date > current date OR to_date IS NULL`); check with SA if filtering logic is not stated
- **PDPA masking** — if the screen displays any of: Name/Surname, Citizen ID, DOB, Address, Email Address, Mobile/Telephone No. — confirm PDPA masking handling with SA
- **Dummy Dealer handling** — if dealer information is shown: specific dealer sees own data; Dummy Dealer hidden from non-privileged roles; only privileged roles can see Dummy Dealer; if VIN or booking data is shown, check with SA separately

### Function list CR check
- **Pending CRs not considered** — always include a reminder in the report: "Manually verify in the Function List with CR document whether any pending CRs are related to this DR"
