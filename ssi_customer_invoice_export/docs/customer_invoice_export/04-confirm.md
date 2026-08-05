# Confirm Customer Invoice Export

> **Module:** ssi*customer_invoice_export\
> **Model:** `customer_invoice_export`\
> **Menu:** Financial Accounting > Account Receivable > Customer Invoice Exports\
> **Actor:** user in group \_Customer Invoice Export — User*\
> **State:** `draft` → `confirm`\
> **Requires:** `01-create`

## Pre-Condition

- **Record:** Status is **Draft**.
- **Config:** An active `policy.template` for this model grants `confirm_ok` for state
  `draft` to the actor's group.
- **Config:** An active `approval.template` for this model matches this record and has
  at least one approver level.
- **Access:** User is in group _Customer Invoice Export — User_.

## Flow

1. Open the **Financial Accounting > Account Receivable > Customer Invoice Exports**
   menu.
2. Open the record to confirm.
3. Click the **Confirm** button.
4. Click **OK** on the confirmation dialog.

## Post-Condition

- Status changes to **Waiting for Approval**.
- Approval records are created for each approver level defined by the approval template.
