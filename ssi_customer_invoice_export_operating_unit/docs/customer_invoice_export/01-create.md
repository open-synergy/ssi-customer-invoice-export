# Create Customer Invoice Export

> **Module:** ssi_customer_invoice_export_operating_unit\
> **Extends:** ssi_customer_invoice_export — model `customer_invoice_export`, aksi
> `01-create`

## Additional Pre-Condition

- **Module:** `ssi_customer_invoice_export_operating_unit` is installed.
- **Access:** User is in group _Operating Unit_, under the _Customer Invoice Export_ data
  ownership category, to see and set the **Operating Unit** field.

## Additional Fields

- **Operating Unit**: Many2one to the operating unit that owns this document. Only visible
  to users in the _Operating Unit_ group (multi operating unit). Editable while the
  document is in Draft. Scopes the invoices and journals selected by **Populate** to this
  operating unit; leave empty to keep **Populate** unrestricted by operating unit.

## Modified Flow

- Anchor: on the base Flow step 4 (**Populate**, on the **Invoices** tab), when
  **Operating Unit** is set, **Populate** is scoped in two separate ways:
  - it only selects customer invoices belonging to the selected operating unit —
    invoices of other operating units are excluded even if they otherwise match the
    Type's allowed journals, allowed partners, and date range;
  - the journals **Populate** is allowed to use also shrink to journals belonging to
    the selected operating unit; a journal that has **no** operating unit configured is
    unrestricted and remains usable regardless of the document's operating unit.

  When **Operating Unit** is left empty, both effects are inactive and **Populate**
  behaves exactly as in the base Flow.

## Modified — Record Visibility

- A record rule restricts the Customer Invoice Export list to documents whose
  **Operating Unit** is empty, or belongs to one of the user's assigned operating units.
  A user who is not assigned to a document's operating unit cannot see it in the list or
  open it directly. This is not a Flow step.
