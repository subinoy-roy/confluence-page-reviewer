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
