# Deactivate Customer Invoice Export Type

> **Module:** ssi_customer_invoice_export\
> **Model:** `customer_invoice_export_type`\
> **Menu:** Financial Accounting > Configuration > Customer Invoice Export Types\
> **Actor:** user in group `Customer Invoice Export Type`\
> **Active:** `true` → `false`\
> **Requires:** `01-create`

## Pre-Condition

- **Record:** The record is currently active.

## Flow

1. Open the **Financial Accounting > Configuration > Customer Invoice Export Types**
   menu.
2. Select one or more records to deactivate (check the checkbox).
3. Click **Action** > **Archive**.
4. Click **OK** to confirm.

## Post-Condition

- The records are archived and no longer appear in the default list view.
- Deactivated types cannot be selected on new Customer Invoice Export documents.
- Existing Customer Invoice Export documents that already use this type are not
  affected.
