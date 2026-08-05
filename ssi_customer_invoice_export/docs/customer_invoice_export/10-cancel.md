# Cancel Customer Invoice Export

> **Module:** ssi_customer_invoice_export\
> **Model:** `customer_invoice_export`\
> **Menu:** Financial Accounting > Account Receivable > Customer Invoice Exports\
> **Actor:** user in group _Customer Invoice Export — Validator_\
> **State:** `draft` | `confirm` | `queue_done` | `done` → `cancel`\
> **Requires:** `01-create`

## Pre-Condition

- **Record:** Status is **Draft**, **Waiting for Approval**, **Queue To Done**, or
  **Done**.
- **Config:** An active `policy.template` for this model grants `cancel_ok` for that
  state to the actor's group.
- **Access:** User is in group _Customer Invoice Export — Validator_.

## Flow

1. Open the **Financial Accounting > Account Receivable > Customer Invoice Exports**
   menu.
2. Open the record to cancel.
3. Click the **Cancel** button.
4. In the wizard that appears, select the **Cancellation Reason**.
5. Click **Confirm**.
6. Click **OK** on the confirmation dialog.

## Post-Condition

- Status changes to **Cancelled**.
- The selected Cancellation Reason is recorded on the document and displayed next to its
  title.
