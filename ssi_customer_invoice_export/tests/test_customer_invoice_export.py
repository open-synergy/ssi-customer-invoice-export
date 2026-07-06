# Copyright 2026 OpenSynergy Indonesia
# Copyright 2026 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo_yaml_test import YamlTransactionCase

from odoo.exceptions import UserError
from odoo.tests import Form, tagged


@tagged("post_install", "-at_install")
class TestCustomerInvoiceExport(YamlTransactionCase):
    # -------------------------------------------------------------------
    # Shared setup helpers.
    #
    # Building a valid posted customer invoice needs a sale journal, an
    # income account, and (for the "fully paid" case) a bank journal plus
    # reconciliation -- none of which the odoo-yaml-test framework can
    # express (no conditional "search or create" step, no reconcile
    # helper). This entire test therefore lives in Python rather than
    # YAML, mirroring the precedent set in
    # ssi_customer_payment_import/tests/test_customer_payment_import.py.
    # -------------------------------------------------------------------

    def _get_income_account(self):
        account_type = self.env.ref("account.data_account_type_revenue")
        account = self.env["account.account"].search(
            [
                ("user_type_id", "=", account_type.id),
                ("company_id", "=", self.env.company.id),
            ],
            limit=1,
        )
        if not account:
            account = self.env["account.account"].create(
                {
                    "name": "Test Income Account",
                    "code": "TESTINC01",
                    "user_type_id": account_type.id,
                    "company_id": self.env.company.id,
                }
            )
        return account

    def _get_sale_journal(self):
        # Always create a dedicated journal rather than reusing/searching an
        # existing one -- demo data may already contain posted, unpaid
        # customer invoices in a shared default sale journal, which would
        # leak into this test's Populate results.
        return self.env["account.journal"].create(
            {"name": "Test Sales Journal", "type": "sale", "code": "TSJ"}
        )

    def _get_bank_journal(self):
        return self.env["account.journal"].create(
            {"name": "Test Bank Journal", "type": "bank", "code": "TBNK"}
        )

    def _create_product(self, name, income_account):
        return self.env["product.product"].create(
            {
                "name": name,
                "type": "service",
                "property_account_income_id": income_account.id,
            }
        )

    def _create_invoice(self, partner, journal, lines, invoice_date):
        move = self.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": partner.id,
                "invoice_date": invoice_date,
                "journal_id": journal.id,
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": product.id,
                            "quantity": 1,
                            "price_unit": price,
                            "name": product.name,
                            "account_id": product.property_account_income_id.id,
                        },
                    )
                    for product, price in lines
                ],
            }
        )
        move.action_post()
        return move

    def _pay_invoice_fully(self, invoice, bank_journal):
        payment_method = self.env.ref("account.account_payment_method_manual_in")
        payment = self.env["account.payment"].create(
            {
                "payment_type": "inbound",
                "partner_type": "customer",
                "partner_id": invoice.partner_id.id,
                "amount": invoice.amount_total,
                "journal_id": bank_journal.id,
                "payment_method_id": payment_method.id,
            }
        )
        payment.action_post()
        receivable_account = invoice.line_ids.mapped("account_id").filtered(
            lambda a: a.user_type_id.type == "receivable"
        )
        (invoice.line_ids + payment.line_ids).filtered(
            lambda line: line.account_id in receivable_account
        ).reconcile()
        invoice.invalidate_cache()

    def _create_export_type(self, journal, product_a, **extra_values):
        values = {
            "name": "Test Export Type",
            "code": "TEXP001",
            "default_output_format": "csv",
            "journal_selection_method": "manual",
            "journal_ids": [(6, 0, journal.ids)],
            "product_selection_method": "manual",
            "product_ids": [(6, 0, product_a.ids)],
            "parser_python_code": (
                "result = [[s.move_id.name, s.amount_total] for s in summary_ids]"
            ),
        }
        values.update(extra_values)
        return self.env["customer_invoice_export_type"].create(values)

    # -------------------------------------------------------------------
    # Onchange (Form API)
    # -------------------------------------------------------------------

    def test_onchange_output_format_from_type(self):
        journal = self._get_sale_journal()
        income_account = self._get_income_account()
        product_a = self._create_product("Onchange Product A", income_account)
        ctype = self._create_export_type(journal, product_a)

        form = Form(self.env["customer_invoice_export"])
        form.type_id = ctype
        self.assertEqual(form.output_format, "csv")

    # -------------------------------------------------------------------
    # Populate
    # -------------------------------------------------------------------

    def test_populate_filters_by_product_journal_and_date(self):
        journal = self._get_sale_journal()
        bank_journal = self._get_bank_journal()
        income_account = self._get_income_account()
        product_a = self._create_product("Populate Product A", income_account)
        product_b = self._create_product("Populate Product B", income_account)
        partner = self.env["res.partner"].create({"name": "Populate Partner"})
        ctype = self._create_export_type(journal, product_a)

        invoice_1 = self._create_invoice(
            partner, journal, [(product_a, 100.0), (product_b, 50.0)], "2026-01-10"
        )
        invoice_2 = self._create_invoice(
            partner, journal, [(product_a, 200.0)], "2026-02-10"
        )
        invoice_paid = self._create_invoice(
            partner, journal, [(product_a, 300.0)], "2026-01-15"
        )
        self._pay_invoice_fully(invoice_paid, bank_journal)
        self.assertEqual(invoice_paid.payment_state, "paid")

        export_doc = (
            self.env["customer_invoice_export"]
            .with_user(self.env.ref("base.user_admin"))
            .create({"type_id": ctype.id, "date": "2026-03-01", "output_format": "csv"})
        )
        export_doc.action_populate()

        self.assertEqual(set(export_doc.move_ids.ids), {invoice_1.id, invoice_2.id})
        self.assertTrue(
            all(line.product_id == product_a for line in export_doc.line_ids)
        )
        self.assertEqual(len(export_doc.summary_ids), 2)
        summary_1 = export_doc.summary_ids.filtered(lambda s: s.move_id == invoice_1)
        self.assertEqual(summary_1.amount_total, 100.0)

        # date_start filters out invoice_1 (invoice_date 2026-01-10)
        export_doc.write({"date_start": "2026-02-01"})
        export_doc.action_populate()
        self.assertEqual(export_doc.move_ids, invoice_2)

    def test_populate_idempotent(self):
        journal = self._get_sale_journal()
        income_account = self._get_income_account()
        product_a = self._create_product("Idempotent Product A", income_account)
        partner = self.env["res.partner"].create({"name": "Idempotent Partner"})
        ctype = self._create_export_type(journal, product_a)
        self._create_invoice(partner, journal, [(product_a, 100.0)], "2026-01-01")

        export_doc = self.env["customer_invoice_export"].create(
            {"type_id": ctype.id, "date": "2026-03-01", "output_format": "csv"}
        )
        export_doc.action_populate()
        first_count = len(export_doc.summary_ids)
        export_doc.action_populate()
        self.assertEqual(len(export_doc.summary_ids), first_count)

    # -------------------------------------------------------------------
    # Render output (CSV / TXT) -- unit-level, no queue involved
    # -------------------------------------------------------------------

    def test_render_csv_and_txt(self):
        journal = self._get_sale_journal()
        income_account = self._get_income_account()
        product_a = self._create_product("Render Product A", income_account)
        ctype = self._create_export_type(journal, product_a)
        ctype.txt_field_separator = "|"

        export_doc = self.env["customer_invoice_export"].create(
            {"type_id": ctype.id, "date": "2026-03-01", "output_format": "csv"}
        )
        rows = [["INV/1", 100.0], ["INV/2", 200.0]]

        csv_bytes = export_doc._render_output(rows)
        self.assertEqual(
            csv_bytes.decode("utf-8").strip().splitlines(),
            ["INV/1,100.0", "INV/2,200.0"],
        )

        export_doc.output_format = "txt"
        txt_bytes = export_doc._render_output(rows)
        self.assertEqual(
            txt_bytes.decode("utf-8").splitlines(),
            ["INV/1|100.0", "INV/2|200.0"],
        )

    def test_generate_export_file_without_summary_raises(self):
        journal = self._get_sale_journal()
        income_account = self._get_income_account()
        product_a = self._create_product("NoSummary Product A", income_account)
        ctype = self._create_export_type(journal, product_a)
        export_doc = self.env["customer_invoice_export"].create(
            {"type_id": ctype.id, "date": "2026-03-01", "output_format": "csv"}
        )
        with self.assertRaises(UserError):
            export_doc._generate_export_file()

    # -------------------------------------------------------------------
    # Full workflow: draft -> confirm -> queue_done -> done, export_file
    # generated synchronously (queue_job__no_delay), then cancel/restart.
    # -------------------------------------------------------------------

    def test_workflow_to_done_generates_export_file(self):
        journal = self._get_sale_journal()
        income_account = self._get_income_account()
        product_a = self._create_product("Workflow Product A", income_account)
        partner = self.env["res.partner"].create({"name": "Workflow Partner"})
        ctype = self._create_export_type(journal, product_a)
        self._create_invoice(partner, journal, [(product_a, 150.0)], "2026-01-20")

        export_doc = (
            self.env["customer_invoice_export"]
            .with_user(self.env.ref("base.user_admin"))
            .create({"type_id": ctype.id, "date": "2026-03-01", "output_format": "csv"})
        )
        export_doc.action_populate()
        self.assertTrue(export_doc.summary_ids)

        export_doc.action_confirm()
        export_doc.invalidate_cache()
        self.assertEqual(export_doc.state, "confirm")

        export_doc.with_context(queue_job__no_delay=True).action_approve_approval()
        export_doc.invalidate_cache()
        self.assertEqual(export_doc.state, "done")
        self.assertTrue(export_doc.export_file)
        self.assertTrue(export_doc.export_filename.endswith(".csv"))

        attachment = self.env["ir.attachment"].search(
            [
                ("res_model", "=", "customer_invoice_export"),
                ("res_id", "=", export_doc.id),
            ]
        )
        self.assertTrue(attachment)

    def test_cancel_from_draft_and_restart(self):
        journal = self._get_sale_journal()
        income_account = self._get_income_account()
        product_a = self._create_product("Cancel Product A", income_account)
        ctype = self._create_export_type(journal, product_a)

        export_doc = (
            self.env["customer_invoice_export"]
            .with_user(self.env.ref("base.user_admin"))
            .create({"type_id": ctype.id, "date": "2026-03-01", "output_format": "csv"})
        )
        export_doc.action_cancel()
        export_doc.invalidate_cache()
        self.assertEqual(export_doc.state, "cancel")

        export_doc.action_restart()
        export_doc.invalidate_cache()
        self.assertEqual(export_doc.state, "draft")
