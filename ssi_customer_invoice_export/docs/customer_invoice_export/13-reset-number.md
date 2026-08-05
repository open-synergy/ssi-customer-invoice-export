# Reset Document Number — Customer Invoice Export

> **Module:** ssi_customer_invoice_export\
> **Model:** `customer_invoice_export`\
> **Menu:** Financial Accounting > Account Receivable > Customer Invoice Exports\
> **Actor:** user in group _Customer Invoice Export — Validator_\
> **Requires:** `01-create`

## Pre-Condition

- **Record:** Status is **Draft**.
- **Config:** An active `policy.template` for this model grants `manual_number_ok` for
  state `draft` to the actor's group.
- **Access:** User is in group _Customer Invoice Export — Validator_.

## Flow

1. Open the **Financial Accounting > Account Receivable > Customer Invoice Exports**
   menu.
2. Open the record whose document number will be reset.
3. Click the **Reset Document Number** button (or edit the **# Document** field directly
   and change it to **/**).
4. Click **OK** on the confirmation dialog (only when the button was used).

## Post-Condition

- Document number returns to **/**.
- The record will receive an automatic number when it transitions to **Done**, according
  to the configured sequence.
