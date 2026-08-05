# Edit Customer Invoice Export Type

> **Module:** ssi_customer_invoice_export\
> **Model:** `customer_invoice_export_type`\
> **Menu:** Financial Accounting > Configuration > Customer Invoice Export Types\
> **Actor:** user in group `Customer Invoice Export Type`\
> **Inline Actions:** `action_generate_code` (Generate Code)\
> **Requires:** `01-create`

## Pre-Condition

- None.

## Flow

1. Open the **Financial Accounting > Configuration > Customer Invoice Export Types** menu.
2. Find and open the record to edit.
3. Change the required fields.
4. _(Optional)_ If the **Code** field still shows `/`, click **Generate Code** in the
   header to assign a code from the configured sequence template automatically. It leaves
   any other value untouched, so skip this step if the record already has a code you want
   to keep.
5. Click **Save**.

## Post-Condition

- The Customer Invoice Export Type record is updated with the new values.
