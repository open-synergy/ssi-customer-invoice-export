# Recompute Queue Done Result — Customer Invoice Export

> **Module:** ssi*customer_invoice_export\
> **Model:** `customer_invoice_export`\
> **Menu:** Financial Accounting > Account Receivable > Customer Invoice Exports\
> **Actor:** user in group \_Customer Invoice Export — Viewer*\
> **State:** `queue_done` → `done`\
> **Requires:** `05-approve`

## Pre-Condition

- **Record:** Status is **Queue To Done**.
- **Config:** A `base.automation` on this model already runs the same recompute logic
  automatically, on every write, whenever the **To Done Queue Job Batch State**
  (`done_queue_job_batch_state`) becomes **Finished** — so this document frequently
  reaches Done on its own, without this button ever being clicked.
- **Access:** User is in group _Customer Invoice Export — Viewer_ (or above). This
  button is not guarded by a dedicated policy field, so it is visible to anyone who can
  open the record.

## Flow

1. Open the **Financial Accounting > Account Receivable > Customer Invoice Exports**
   menu.
2. Open the record to recompute.
3. Open the **Queue Processing** tab.
4. Click the **Recompute Queue Done Result** button.
5. Click **OK** on the confirmation dialog.

## Post-Condition

- The To Done Queue Job Batch is enqueued again.
- If the To Done Queue Job Batch is already **Finished**, status changes to **Done**.
- Otherwise, status remains **Queue To Done**.
- As noted in Pre-Condition, the same transition to **Done** commonly happens on its own
  once the queue job batch finishes, triggered by the module's `base.automation` rather
  than by a user clicking this button.
