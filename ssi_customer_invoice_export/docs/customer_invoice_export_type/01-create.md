# Create Customer Invoice Export Type

> **Module:** ssi_customer_invoice_export\
> **Model:** `customer_invoice_export_type`\
> **Menu:** Financial Accounting > Configuration > Customer Invoice Export Types\
> **Actor:** user in group `Customer Invoice Export Type`\
> **Inline Actions:** `action_generate_code` (Generate Code)

## Pre-Condition

- None.

## Flow

1. Open the **Financial Accounting > Configuration > Customer Invoice Export Types**
   menu.
2. Click the **New** button. **(14.0: "Create")**
3. Fill in the required fields:
   - **Name** _(required)_: Enter the export type name.
   - **Code** _(required)_: Enter a unique code for this type, or leave it as `/` and
     use **Generate Code** afterward (step 4) to have it assigned automatically.
4. _(Optional)_ Click **Generate Code** in the header to have the system assign a code
   from the configured sequence template automatically. It only replaces a **Code**
   value that is still `/`; if you already typed your own code in step 3, skip this step
   -- the button leaves any other value untouched.
5. On the **Output Option** tab, fill in:
   - **Default Output Format** _(required)_: Select the file format (**CSV**, **XLSX**,
     or **TXT**) automatically proposed on a new Customer Invoice Export document
     created with this type. Defaults to **CSV**.
   - **Grouping Method** _(required)_: Select what one summary row -- and therefore one
     row of the exported file -- represents.
     - _One Row per Invoice_ (default): each qualifying invoice becomes its own row.
     - _One Row per Partner_: all qualifying invoices of the same partner are merged
       into a single row, as required by bank formats keyed on a per-customer virtual
       account.
   - _(Optional)_ **Encoding**: Character encoding used when writing the CSV or TXT
     file. Defaults to **UTF-8**.
   - _(Optional)_ **CSV Delimiter**: Field delimiter used when writing a CSV file.
     Defaults to **comma (,)**.
   - _(Optional)_ **CSV Text Qualifier**: Character used to quote CSV fields containing
     special characters. Defaults to `"`.
   - _(Optional)_ **XLSX Sheet Name**: Name of the worksheet created in the XLSX file.
     Leave empty for `Sheet1`.
   - _(Optional)_ **TXT Field Separator**: Separator inserted between cell values when
     writing a TXT file. Leave empty to concatenate cells without a separator
     (fixed-width style).
6. On the **Journal Criteria** tab, select **Journal Selection Method** _(required)_ and
   fill in the field that appears below it, matching the method chosen:
   - _Manual_: select the allowed journals in **Journals**.
   - _Domain_ (default): enter a domain filter in **Journal Domain**. An empty domain
     (`[]`) allows every journal.
   - _Python Code_: enter Python code in **Journal Python Code** that sets the `result`
     variable to a recordset of `account.journal`.
7. On the **Partner Criteria** tab, select **Partner Selection Method** _(required)_ and
   fill in the field that appears below it, matching the method chosen:
   - _Manual_: select the allowed partners in **Partners**.
   - _Domain_ (default): enter a domain filter in **Partner Domain**. An empty domain
     (`[]`) allows every partner.
   - _Python Code_: enter Python code in **Partner Python Code** that sets the `result`
     variable to a recordset of `res.partner`.
8. On the **Product Criteria** tab, select **Product Selection Method** _(required)_ and
   fill in the field that appears below it, matching the method chosen:
   - _Manual_: select the allowed products in **Products**.
   - _Domain_ (default): enter a domain filter in **Product Domain**. An empty domain
     (`[]`) allows every product.
   - _Python Code_: enter Python code in **Product Python Code** that sets the `result`
     variable to a recordset of `product.product`.
9. On the **Parser** tab, enter **Parser Python Code** _(required)_: Python code that
   sets the `result` variable to a list of rows (each row a list of cell values) to be
   written to the export file. `env`, `document`, `summary_ids`, `move_ids`, and
   `line_ids` are available in the local scope.
10. Click **Save**.

## Post-Condition

- A new Customer Invoice Export Type record is created and available for selection when
  creating a Customer Invoice Export document.
