# Edit Customer Invoice Export

> **Module:** ssi_customer_invoice_export_operating_unit\
> **Extends:** ssi_customer_invoice_export — model `customer_invoice_export`, aksi `02-edit`

## Additional Pre-Condition

- **Module:** `ssi_customer_invoice_export_operating_unit` is installed.
- **Access:** User is in group _Operating Unit_, under the _Customer Invoice Export_
  data ownership category, to see and change the **Operating Unit** field.

## Additional Fields

- **Operating Unit**: Many2one to the operating unit that owns this document. Only
  visible to users in the _Operating Unit_ group (multi operating unit). Editable while
  the document is in Draft. Changing it changes the scope the next time **Populate** is
  run.

## Modified Flow

- Anchor: on the base Flow step 4 (**Populate**, on the **Invoices** tab), when
  **Operating Unit** is set, **Populate** is scoped in two separate ways:

  - it only selects customer invoices belonging to the selected operating unit;
  - the journals **Populate** is allowed to use also shrink to journals belonging to the
    selected operating unit; a journal that has **no** operating unit configured is
    unrestricted and remains usable regardless of the document's operating unit.

  When **Operating Unit** is left empty, both effects are inactive and **Populate**
  behaves exactly as in the base Flow. Changing **Operating Unit** and then re-running
  **Populate** refreshes **Invoices**, **Invoice Lines**, and **Summary** under the new
  scope; skipping this step after changing **Operating Unit** leaves them built from the
  previous scope.
