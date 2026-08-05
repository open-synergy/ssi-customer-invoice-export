# Reject Customer Invoice Export

> **Module:** ssi*customer_invoice_export\
> **Model:** `customer_invoice_export`\
> **Menu:** Financial Accounting > Account Receivable > Customer Invoice Exports\
> **Actor:** approver on the approval level that is currently pending (user in group \_Customer
> Invoice Export — Validator*)\
> **State:** `confirm` → `reject`\
> **Requires:** `04-confirm`

## Pre-Condition

- **Record:** Status is **Waiting for Approval**.
- **Config:** An active `policy.template` grants `reject_ok` to the actor's group.
- **Config:** An active `approval.template` for this model matches this record.
- **Access:** User is registered as an approver on the approval level that is currently
  pending.
- **Access:** User is in group _Customer Invoice Export — Validator_.

## Flow

1. Open the **Financial Accounting > Account Receivable > Customer Invoice Exports**
   menu.
2. Open the record to reject.
3. Click the **Reject** button.
4. Click **OK** on the confirmation dialog.

## Post-Condition

- Status changes to **Rejected**.
