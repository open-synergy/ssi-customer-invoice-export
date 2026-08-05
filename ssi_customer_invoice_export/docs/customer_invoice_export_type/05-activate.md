# Activate Customer Invoice Export Type

> **Module:** ssi_customer_invoice_export\
> **Model:** `customer_invoice_export_type`\
> **Menu:** Financial Accounting > Configuration > Customer Invoice Export Types\
> **Actor:** user in group `Customer Invoice Export Type`\
> **Active:** `false` → `true`\
> **Requires:** `04-deactivate`

## Pre-Condition

- **Record:** The record is currently archived.

## Flow

1. Open the **Financial Accounting > Configuration > Customer Invoice Export Types** menu.
2. Enable the **Archived** filter in the search bar.
3. Select one or more records to reactivate (check the checkbox).
4. Click **Action** > **Unarchive**.
5. Click **OK** to confirm.

## Post-Condition

- The records are restored and appear again in the default list view.
- The types can be selected on new Customer Invoice Export documents.
