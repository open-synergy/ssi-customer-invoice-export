# Restart Approval Process — Customer Invoice Export

> **Module:** ssi*customer_invoice_export\
> **Model:** `customer_invoice_export`\
> **Menu:** Financial Accounting > Account Receivable > Customer Invoice Exports\
> **Actor:** user in group \_Customer Invoice Export — Validator*\
> **Requires:** `04-confirm`

## Pre-Condition

- **Record:** Status is **Waiting for Approval**, and the record currently has no
  approval template assigned, so the approval process is stalled without an approver.
- **Config:** An active `policy.template` for this model grants `restart_approval_ok`
  for state `confirm` to the actor's group when the record has no approval template
  assigned.
- **Config:** An active `approval.template` for this model matches this record, with an
  approver group configured for its approval level, so the process can be rebuilt once
  restarted.
- **Access:** User is in group _Customer Invoice Export — Validator_.

## Flow

1. Open the **Financial Accounting > Account Receivable > Customer Invoice Exports**
   menu.
2. Open the record whose approval process is stalled.
3. Click the **Restart Approval Process** button.
4. Click **OK** on the confirmation dialog.

## Post-Condition

- Status remains **Waiting for Approval**.
- The existing approval records are discarded and a new approval process is created from
  the approval template that now matches the record.
