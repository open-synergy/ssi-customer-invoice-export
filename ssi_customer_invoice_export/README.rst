.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

=======================
Customer Invoice Export
=======================

Generate CSV, XLSX, or TXT files from customer invoices for upload to a
banking service.

Unlike Odoo's built-in export or Py3O reporting, this module supports the
common case where a single invoice's lines must be split across several
export files depending on the product on each line.

* **Customer Invoice Export Type** (configuration): defines the journal
  criteria, partner criteria, and product criteria (manual / domain /
  Python code) that determine which invoices and invoice lines are
  eligible, the default output format (CSV/XLSX/TXT) and its options
  (encoding, delimiter, sheet name, field separator), the Grouping Method
  that determines what one export row represents, and the Parser Python
  Code that turns the selected data into the rows of the export file.
* **Customer Invoice Export** (transaction): select a Type and, optionally,
  a date range, then use **Populate** to auto-select unpaid customer
  invoices (limited to the Type's allowed journals, the Type's allowed
  partners, and, if given, the date range) and keep only the invoice lines
  matching the Type's product criteria. One summary row is built per export
  row, according to the Type's Grouping Method:

  * *One Row per Invoice* (default): each qualifying invoice becomes its
    own summary row.
  * *One Row per Partner*: all qualifying invoices of the same partner are
    merged into a single summary row -- required by bank formats keyed on
    a per-customer virtual account, where a customer can have more than
    one invoice in the same period.

  The workflow (Draft -> Confirm -> Queue to Done -> Done) generates the
  export file in the background once approved.

  Summary rows expose ``move_ids`` (the invoice(s) aggregated into that
  row) instead of a single invoice. Parser Python Code must read
  ``s.move_ids`` (a recordset), not ``s.move_id``.


Work Instruction
================

Customer Invoice Export Type
-----------------------------

* `Create Customer Invoice Export Type <docs/customer_invoice_export_type/01-create.html>`_
* `Edit Customer Invoice Export Type <docs/customer_invoice_export_type/02-edit.html>`_
* `Delete Customer Invoice Export Type <docs/customer_invoice_export_type/03-delete.html>`_
* `Deactivate Customer Invoice Export Type <docs/customer_invoice_export_type/04-deactivate.html>`_
* `Activate Customer Invoice Export Type <docs/customer_invoice_export_type/05-activate.html>`_


Installation
============

To install this module, you need to:

1.  Clone the branch 14.0 of the repository https://github.com/open-synergy/ssi-customer-invoice-export
2.  Add the path to this repository in your configuration (addons-path)
3.  Update the module list (Must be on developer mode)
4.  Go to menu *Apps -> Apps -> Main Apps*
5.  Search For *Customer Invoice Export*
6.  Install the module


Bug Tracker
===========

Bugs are tracked on `GitHub Issues
<https://github.com/open-synergy/ssi-customer-invoice-export/issues>`_. In case of trouble, please
check there if your issue has already been reported. If you spotted it first,
help us smash it by providing detailed and welcomed feedback.


Credits
=======

Contributors
------------

* Andhitia Rama <andhitia.r@gmail.com>

Maintainer
----------

.. image:: https://simetri-sinergi.id/logo.png
   :alt: PT. Simetri Sinergi Indonesia
   :target: https://simetri-sinergi.id

This module is maintained by the PT. Simetri Sinergi Indonesia.
