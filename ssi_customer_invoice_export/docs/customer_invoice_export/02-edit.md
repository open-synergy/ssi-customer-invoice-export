# Edit Customer Invoice Export

> **Module:** ssi*customer_invoice_export\
> **Model:** `customer_invoice_export`\
> **Menu:** Financial Accounting > Account Receivable > Customer Invoice Exports\
> **Actor:** user in group \_Customer Invoice Export — User*\
> **Requires:** `01-create`\
> **Inline Actions:** `action_populate` (Populate), `action_rederive_summary` (Reload), `action_reload_policy_template`
> (Reload Template Policy)

## Pre-Condition

- **Record:** Status is **Draft**.
- **Access:** User is in group _Customer Invoice Export — User_.

## Flow

1. Open the **Financial Accounting > Account Receivable > Customer Invoice Exports**
   menu.
2. Find and open the record to edit.
3. Change the required fields (**Type**, **Date**, **Date Start**, **Date End**,
   **Output Format**) as needed.
4. On the **Invoices** tab, click **Populate** to refresh **Invoices** from the current
   **Type** and date range -- for example after changing **Type** or **Date
   Start**/**Date End** on this document itself. The **Invoices** list can also be
   adjusted manually: adding or removing an invoice there immediately rebuilds **Invoice
   Lines** and **Summary** to match, without clicking Populate again. Populate itself is
   still required after changing **Type** or the date range **on this document**, since
   only Populate re-runs the invoice selection criteria -- skipping it in that case
   leaves **Invoices** built from the previous criteria, which can make the export file
   generated after Confirm/Approve contain the wrong invoices, or fail with "No summary
   rows to export" if none of the previously selected invoices still qualify.
5. If instead a mistake was fixed on the selected **Type** record itself -- its product
   criteria, Grouping Method, or receivable account -- **Invoice Lines** and **Summary**
   go stale without any change on this document to rebuild them, since editing the
   **Type** record never writes to this document. On the **Invoice Lines** tab, click
   **Reload** to rebuild **Invoice Lines** and **Summary** from the **Invoices**
   currently selected. **Invoices** itself is left untouched, so any manual adjustment
   made there is kept -- unlike Populate, which searches for invoices again and would
   discard it.
6. _(Optional, Settings/Technical group only)_ On the **Policies** tab, click **Reload
   Template Policy** to re-evaluate which `policy.template` applies to this document --
   use this after something that affects the evaluation changed. Skipping this step
   leaves the currently assigned template unchanged.
7. Click **Save**.

## Post-Condition

- The record is updated with the new values.
