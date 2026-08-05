# Requeue Customer Invoice Export

> **Module:** ssi*customer_invoice_export\
> **Model:** `customer_invoice_export`\
> **Menu:** Financial Accounting > Account Receivable > Customer Invoice Exports\
> **Actor:** user in group \_Customer Invoice Export — Viewer*\
> **Requires:** `05-approve`

## Pre-Condition

- **Record:** Status is **Queue To Done**, and the To Done Queue Job Batch is not yet in
  the **Finished** state.
- **Access:** User is in group _Customer Invoice Export — Viewer_ (or above). This
  button is not guarded by a dedicated policy field, so it is visible to anyone who can
  open the record.

## Flow

1. Open the **Financial Accounting > Account Receivable > Customer Invoice Exports**
   menu.
2. Open the record to requeue.
3. Open the **Queue Processing** tab.
4. Click the **Requeue** button.

## Post-Condition

- Status remains **Queue To Done**.
- Every job in the To Done Queue Job Batch that is not yet **Done** is requeued for
  another execution attempt.
