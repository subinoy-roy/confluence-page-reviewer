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
- **Missing Excel entirely** — no table content and no `.xlsx` attachment in the "Report Items" section
