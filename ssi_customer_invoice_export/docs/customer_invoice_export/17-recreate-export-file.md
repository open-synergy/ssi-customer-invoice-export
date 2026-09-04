# Recreate Export File — Customer Invoice Export

> **Module:** ssi*customer_invoice_export\
> **Model:** `customer_invoice_export`\
> **Menu:** Financial Accounting > Account Receivable > Customer Invoice Exports\
> **Actor:** user in group \_Customer Invoice Export — User*\
> **Requires:** `05-approve`

## Pre-Condition

- **Record:** Status is **Done**, and an Export File has already been generated at least
  once.
- **Access:** User is in group _Customer Invoice Export — User_ (or above). This button
  is not guarded by a dedicated policy field, so it is visible to anyone who can open
  the record and is in this group.

## Flow

1. Open the **Financial Accounting > Account Receivable > Customer Invoice Exports**
   menu.
2. Open the record to regenerate.
3. Open the **Export File** tab.
4. Click the **Recreate Export File** button.

## Post-Condition

- If the Type's Parser Python Code runs without error: Export File is filled in again
  with the file the current Parser Python Code produces, and a new attachment is added
  without deleting the previous one -- Export File always points to the most recent
  attachment.
- If the Type's Parser Python Code raises an error: a dialog shows the error message
  (naming the Type), and Export File keeps the file from the previous generation
  unchanged.
