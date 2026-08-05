# Approve Customer Invoice Export

> **Module:** ssi_customer_invoice_export\
> **Model:** `customer_invoice_export`\
> **Menu:** Financial Accounting > Account Receivable > Customer Invoice Exports\
> **Actor:** approver on the approval level that is currently pending (user in group
> *Customer Invoice Export — Validator*)\
> **State:** `confirm` → `queue_done`\
> **Requires:** `04-confirm`

## Pre-Condition

- **Record:** Status is **Waiting for Approval**.
- **Config:** An active `policy.template` grants `approve_ok` to the actor's group.
- **Config:** An active `approval.template` for this model matches this record.
- **Access:** User is registered as an approver on the approval level that is currently
  **pending**. When the template uses sequential approval, only the first unapproved
  level is pending.
- **Access:** User is in group *Customer Invoice Export — Validator*.

## Flow

1. Open the **Financial Accounting > Account Receivable > Customer Invoice Exports**
   menu.
2. Open the record to approve.
3. Click the **Approve** button.
4. Click **OK** on the confirmation dialog.

## Post-Condition

- If all approval levels are fulfilled, status automatically changes to
  **Queue To Done** (triggered by the last approval, not a button), and a background
  job is queued to generate the **Export File** from the **Summary** rows.
- If there are still pending approval levels, status remains **Waiting for Approval**
  and the next level becomes pending.
