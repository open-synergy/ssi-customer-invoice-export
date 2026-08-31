# Create Customer Invoice Export

> **Module:** ssi*customer_invoice_export\
> **Model:** `customer_invoice_export`\
> **Menu:** Financial Accounting > Account Receivable > Customer Invoice Exports\
> **Actor:** user in group \_Customer Invoice Export — User*\
> **State:** `—` → `draft`\
> **Inline Actions:** `action_populate` (Populate), `action_reload_policy_template` (Reload
> Template Policy)

## Pre-Condition

- **Data:** At least one active Customer Invoice Export Type exists.
- **Data:** At least one posted customer invoice exists that is not fully paid and
  matches the selected Type's allowed journals, allowed partners, and, if a date range
  is used, accounting date.
- **Access:** User is in group _Customer Invoice Export — User_.

## Flow

1. Open the **Financial Accounting > Account Receivable > Customer Invoice Exports**
   menu.
2. Click the **New** button. **(14.0: "Create")**
3. Fill in the required fields:
   - **Type** _(required)_: Select the Customer Invoice Export Type that determines the
     allowed journals, allowed partners, and allowed products used by **Populate**, and
     the default output format.
   - **Date**: Defaults to today's date. Change if needed.
   - **Date Start**: Optional. Lower bound (inclusive) on the accounting date used by
     **Populate**. Leave empty together with **Date End** to select invoices regardless
     of date.
   - **Date End**: Optional. Upper bound (inclusive) on the accounting date used by
     **Populate**. Leave empty together with **Date Start** to select invoices
     regardless of date.
   - **Output Format**: Automatically filled from **Type**. Change if needed.
4. On the **Invoices** tab, click **Populate** to auto-select unpaid or partially paid
   posted customer invoices matching the Type's allowed journals, allowed partners, and
   date range into **Invoices**; keep only the lines matching the Type's allowed
   products in **Invoice Lines**; and build the **Summary** rows used later to generate
   the export file. The **Invoices** list can also be adjusted manually afterward while
   the document is still in Draft. Skipping this step leaves **Summary** empty, and the
   export file generation triggered after Confirm/Approve will fail with "No summary
   rows to export".
5. _(Optional, Settings/Technical group only)_ On the **Policies** tab, click **Reload
   Template Policy** to re-evaluate which `policy.template` applies to this document. A
   matching template is already assigned automatically when the record is created; use
   this button only if something that affects the evaluation (e.g. the configured
   templates) changed afterward. Skipping this step leaves the automatically assigned
   template unchanged.
6. Click **Save**.

## Post-Condition

- A new record is created in **Draft** status.
- If **Populate** was used, the **Invoices**, **Invoice Lines**, and **Summary** tabs
  are filled according to the Type's criteria and Grouping Method.
