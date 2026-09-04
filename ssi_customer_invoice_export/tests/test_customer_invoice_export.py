# Copyright 2026 OpenSynergy Indonesia
# Copyright 2026 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import re

from odoo_yaml_test import YamlTransactionCase

from odoo.exceptions import UserError
from odoo.tests import Form, tagged


@tagged("post_install", "-at_install")
class TestCustomerInvoiceExport(YamlTransactionCase):
    """Cover ``customer_invoice_export``: populate, render, workflow.

    Pure Python throughout -- trigger P10 (L-09, L-10: building a valid
    posted customer invoice needs a conditional search-or-create step
    for the income/temp account and, for the "fully paid" case, a bank
    journal plus a ``reconcile()`` call, none of which a single EVAL:
    expression can express).
    """

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
        """Return an income account, creating one if none exists yet."""
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
        """Create a dedicated sale journal for this test.

        Always creates a new one rather than reusing/searching an
        existing one -- demo data may already contain posted, unpaid
        customer invoices in a shared default sale journal, which would
        leak into this test's Populate results.
        """
        return self.env["account.journal"].create(
            {"name": "Test Sales Journal", "type": "sale", "code": "TSJ"}
        )

    def _get_bank_journal(self):
        """Create a dedicated bank journal used to pay an invoice."""
        return self.env["account.journal"].create(
            {"name": "Test Bank Journal", "type": "bank", "code": "TBNK"}
        )

    def _create_product(self, name, income_account):
        """Create a service product posting to ``income_account``."""
        return self.env["product.product"].create(
            {
                "name": name,
                "type": "service",
                "property_account_income_id": income_account.id,
            }
        )

    def _create_invoice(self, partner, journal, lines, invoice_date):
        """Create and post a customer invoice with the given lines.

        Sets both ``invoice_date`` and ``date`` to ``invoice_date``.
        ORM ``create()`` (unlike the web client onchange) never derives
        ``date`` from ``invoice_date``, so it defaults to today's date
        unless set explicitly -- and ``_prepare_invoice_domain`` filters
        the Populate date range on ``date``, not ``invoice_date``
        (issue #38). Leaving ``date`` unset would make fixtures built
        with this helper silently fail date-range assertions.

        :param partner: ``res.partner`` invoiced
        :param journal: ``account.journal`` (type ``sale``) used
        :param lines: list of ``(product, price_unit)`` tuples
        :param invoice_date: invoice date string, also used as ``date``
        :return: the posted ``account.move``
        """
        move = self.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": partner.id,
                "invoice_date": invoice_date,
                "date": invoice_date,
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
        """Register and reconcile a full payment for ``invoice``.

        :param invoice: the posted ``account.move`` to pay
        :param bank_journal: ``account.journal`` (type ``bank``) used
        """
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
        """Create a Type restricted to ``journal`` and ``product_a``.

        :param journal: ``account.journal`` set as the only allowed one
        :param product_a: ``product.product`` set as the only allowed one
        :param extra_values: additional field values overriding defaults
        :return: the created ``customer_invoice_export_type``
        """
        values = {
            "name": "Test Export Type",
            "code": "TEXP001",
            "default_output_format": "csv",
            "journal_selection_method": "manual",
            "journal_ids": [(6, 0, journal.ids)],
            "product_selection_method": "manual",
            "product_ids": [(6, 0, product_a.ids)],
            "parser_python_code": (
                "result = [[s.move_ids.mapped('name'), s.amount_total] "
                "for s in summary_ids]"
            ),
        }
        values.update(extra_values)
        return self.env["customer_invoice_export_type"].create(values)

    def _create_minimal_export_type(self, **extra_values):
        """Create a Type with no journal/product/partner criteria.

        Used for ``source_move_ids`` scenarios, where those criteria
        are bypassed entirely by ``_prepare_invoice_domain``.

        :param extra_values: additional field values overriding defaults
        :return: the created ``customer_invoice_export_type``
        """
        values = {
            "name": "Test Minimal Export Type",
            "code": "TMIN001",
            "default_output_format": "csv",
            "parser_python_code": "result = []",
        }
        values.update(extra_values)
        return self.env["customer_invoice_export_type"].create(values)

    def _get_temp_account(self):
        """Return a current-assets account, creating one if needed."""
        account_type = self.env.ref("account.data_account_type_current_assets")
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
                    "name": "Test Temp Account",
                    "code": "TESTTMP01",
                    "user_type_id": account_type.id,
                    "company_id": self.env.company.id,
                }
            )
        return account

    def _get_general_journal(self):
        """Create a dedicated general journal for journal-entry moves."""
        return self.env["account.journal"].create(
            {"name": "Test General Journal", "type": "general", "code": "TGEN"}
        )

    def _create_journal_entry(self, journal, amount, date, post=True):
        """Create a plain ``move_type="entry"`` journal entry.

        Never shaped like a standard Odoo customer invoice: no
        ``partner_id``/``invoice_date``/``invoice_line_ids`` semantics,
        and ``payment_state`` is always ``False`` (core
        ``account_move.py``: ``"not_paid"`` only applies when
        ``move_type != "entry"``). Used to prove
        ``_prepare_invoice_domain``'s ``source_move_ids`` branch
        bypasses the invoice-shaped criteria.

        :param journal: ``account.journal`` (type ``general``) used
        :param amount: debit/credit amount of the two balancing lines
        :param date: move date string
        :param post: whether to post the move before returning it
        :return: the created ``account.move``
        """
        income_account = self._get_income_account()
        temp_account = self._get_temp_account()
        move = self.env["account.move"].create(
            {
                "move_type": "entry",
                "journal_id": journal.id,
                "date": date,
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "account_id": income_account.id,
                            "name": "Credit Line",
                            "debit": 0.0,
                            "credit": amount,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "account_id": temp_account.id,
                            "name": "Debit Line",
                            "debit": amount,
                            "credit": 0.0,
                        },
                    ),
                ],
            }
        )
        if post:
            move.action_post()
        return move

    def _create_journal_entry_with_product(
        self, journal, product, amount, date, partner
    ):
        """Create a posted ``move_type="entry"`` entry with a product.

        Mirrors ``_create_journal_entry`` but attaches ``product`` to
        the credit line, so the move carries a qualifying line under
        ``_get_qualifying_lines``'s product criterion even though it is
        never invoice-shaped (``invoice_date`` stays NULL). Used to
        prove the Populate date range (issue #38) filters
        ``source_move_ids`` moves on ``date``, not ``invoice_date``.
        ``partner`` is required: ``customer_invoice_export_summary
        .partner_id`` is ``required=True`` and ``_prepare_summary_data``
        copies it from ``moves[0].partner_id``, so an entry without a
        partner makes Summary creation violate the NOT NULL constraint.

        :param journal: ``account.journal`` (type ``general``) used
        :param product: ``product.product`` set on the credit line
        :param amount: debit/credit amount of the two balancing lines
        :param date: move date string
        :param partner: ``res.partner`` set on the move
        :return: the posted ``account.move``
        """
        income_account = self._get_income_account()
        temp_account = self._get_temp_account()
        move = self.env["account.move"].create(
            {
                "move_type": "entry",
                "journal_id": journal.id,
                "date": date,
                "partner_id": partner.id,
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "account_id": income_account.id,
                            "product_id": product.id,
                            "name": "Credit Line",
                            "debit": 0.0,
                            "credit": amount,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "account_id": temp_account.id,
                            "name": "Debit Line",
                            "debit": amount,
                            "credit": 0.0,
                        },
                    ),
                ],
            }
        )
        move.action_post()
        return move

    # -------------------------------------------------------------------
    # Onchange (Form API)
    # -------------------------------------------------------------------

    def test_onchange_output_format_from_type(self):
        """Assert ``output_format`` defaults from the selected Type.

        Pure Python -- trigger P10 (L-09, L-10: fixture setup needs a
        conditional search-or-create for the income account, which a
        single EVAL: expression cannot express).
        """
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
        """Assert Populate excludes paid invoices, other products, dates.

        Pure Python -- trigger P10 (L-09, L-10: building a fully paid
        invoice needs a bank journal and a ``reconcile()`` call, which a
        single EVAL: expression cannot express).
        """
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
        summary_1 = export_doc.summary_ids.filtered(lambda s: invoice_1 in s.move_ids)
        self.assertEqual(summary_1.amount_total, 100.0)

        # date_start filters out invoice_1 (date 2026-01-10)
        export_doc.write({"date_start": "2026-02-01"})
        export_doc.action_populate()
        self.assertEqual(export_doc.move_ids, invoice_2)

    def test_populate_idempotent(self):
        """Assert calling Populate twice does not duplicate Summary rows.

        Pure Python -- trigger P10 (L-09, L-10: fixture setup needs a
        conditional search-or-create for the income account, which a
        single EVAL: expression cannot express).
        """
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
    # source_move_ids (issue #16) -- bypasses the invoice-shaped criteria
    # in _prepare_invoice_domain when set.
    # -------------------------------------------------------------------

    def test_populate_with_source_move_ids_bypasses_invoice_criteria(self):
        """Assert ``source_move_ids`` bypasses the invoice-shaped domain.

        Pure Python -- trigger P10 (L-09, L-10: building a plain
        journal-entry move with balancing lines needs real control flow,
        impossible in a single EVAL: expression).
        """
        journal = self._get_general_journal()
        ctype = self._create_minimal_export_type()
        move = self._create_journal_entry(journal, 100.0, "2026-01-10")
        self.assertEqual(move.move_type, "entry")
        self.assertEqual(move.state, "posted")
        self.assertFalse(move.payment_state)

        export_doc = self.env["customer_invoice_export"].create(
            {
                "type_id": ctype.id,
                "date": "2026-03-01",
                "output_format": "csv",
                "source_move_ids": [(6, 0, move.ids)],
            }
        )
        export_doc.action_populate()

        self.assertEqual(export_doc.move_ids, move)

    def test_populate_without_source_move_ids_keeps_legacy_domain(self):
        """Assert an empty ``source_move_ids`` keeps the standard domain.

        Pure Python -- trigger P10 (L-09, L-10: fixture setup needs a
        conditional search-or-create for the income account, which a
        single EVAL: expression cannot express).
        """
        journal = self._get_sale_journal()
        income_account = self._get_income_account()
        product_a = self._create_product("Legacy Domain Product A", income_account)
        partner = self.env["res.partner"].create({"name": "Legacy Domain Partner"})
        ctype = self._create_export_type(journal, product_a)
        invoice = self._create_invoice(
            partner, journal, [(product_a, 100.0)], "2026-01-10"
        )

        export_doc = self.env["customer_invoice_export"].create(
            {"type_id": ctype.id, "date": "2026-03-01", "output_format": "csv"}
        )
        self.assertFalse(export_doc.source_move_ids)
        export_doc.action_populate()

        self.assertEqual(export_doc.move_ids, invoice)

    def test_populate_with_source_move_ids_excludes_non_posted(self):
        """Assert a draft ``source_move_ids`` move is never selected.

        Pure Python -- trigger P10 (L-09, L-10: building a plain
        journal-entry move with balancing lines needs real control flow,
        impossible in a single EVAL: expression).
        """
        journal = self._get_general_journal()
        ctype = self._create_minimal_export_type()
        draft_move = self._create_journal_entry(
            journal, 100.0, "2026-01-10", post=False
        )
        self.assertEqual(draft_move.state, "draft")

        export_doc = self.env["customer_invoice_export"].create(
            {
                "type_id": ctype.id,
                "date": "2026-03-01",
                "output_format": "csv",
                "source_move_ids": [(6, 0, draft_move.ids)],
            }
        )
        export_doc.action_populate()

        self.assertNotIn(draft_move, export_doc.move_ids)
        self.assertFalse(export_doc.summary_ids)

    def test_populate_date_range_filters_entry_move_by_date_not_invoice_date(self):
        """Assert the date range selects a ``source_move_ids`` entry
        move by ``date``, even though its ``invoice_date`` is NULL.

        Regression test for issue #38: ``_prepare_invoice_domain``
        used to filter on ``invoice_date``, which is always NULL for
        ``move_type="entry"`` moves (the shape produced by the School
        Enrollment/Admission glue via ``source_move_ids``). In
        PostgreSQL, ``NULL >= '<date>'`` evaluates to NULL, so every
        such move was silently discarded and ``action_populate`` never
        produced a Summary row. This test must fail on the pre-fix
        code. Pure Python -- trigger P10 (L-09, L-10: building a plain
        journal-entry move with balancing lines needs real control
        flow, impossible in a single EVAL: expression).
        """
        journal = self._get_general_journal()
        income_account = self._get_income_account()
        product_a = self._create_product("Entry In-Range Product A", income_account)
        partner = self.env["res.partner"].create({"name": "Entry In-Range Partner"})
        ctype = self._create_export_type(journal, product_a)
        move = self._create_journal_entry_with_product(
            journal, product_a, 100.0, "2026-09-15", partner
        )
        self.assertEqual(move.move_type, "entry")
        self.assertFalse(move.invoice_date)
        self.assertEqual(str(move.date), "2026-09-15")

        export_doc = self.env["customer_invoice_export"].create(
            {
                "type_id": ctype.id,
                "date": "2026-09-01",
                "output_format": "csv",
                "date_start": "2026-09-01",
                "date_end": "2026-09-30",
                "source_move_ids": [(6, 0, move.ids)],
            }
        )
        export_doc.action_populate()

        self.assertEqual(export_doc.move_ids, move)
        self.assertTrue(export_doc.summary_ids)

    def test_populate_date_range_excludes_entry_move_outside_range(self):
        """Assert a ``source_move_ids`` entry move outside the Populate
        date range is excluded, proving the date filter still applies.

        Companion negative case for issue #38: proves the fix filters
        by ``date`` rather than simply dropping the date filter for
        ``source_move_ids`` moves altogether. Pure Python -- trigger
        P10 (L-09, L-10: building a plain journal-entry move with
        balancing lines needs real control flow, impossible in a
        single EVAL: expression).
        """
        journal = self._get_general_journal()
        income_account = self._get_income_account()
        product_a = self._create_product("Entry Out-Of-Range Product A", income_account)
        partner = self.env["res.partner"].create({"name": "Entry Out-Of-Range Partner"})
        ctype = self._create_export_type(journal, product_a)
        move = self._create_journal_entry_with_product(
            journal, product_a, 100.0, "2026-08-15", partner
        )

        export_doc = self.env["customer_invoice_export"].create(
            {
                "type_id": ctype.id,
                "date": "2026-09-01",
                "output_format": "csv",
                "date_start": "2026-09-01",
                "date_end": "2026-09-30",
                "source_move_ids": [(6, 0, move.ids)],
            }
        )
        export_doc.action_populate()

        self.assertFalse(export_doc.move_ids)
        self.assertFalse(export_doc.summary_ids)

    # -------------------------------------------------------------------
    # Grouping Method (BL-0104)
    # -------------------------------------------------------------------

    def test_default_type_grouping_method_is_invoice(self):
        """Assert the Type's Grouping Method defaults to "invoice".

        Pure Python -- co-located with the rest of this file's Populate
        coverage (P10, L-09/L-10: the file's fixtures need real control
        flow, impossible in a single EVAL: expression) rather than split
        into a separate YAML-only test file.
        """
        ctype = self.env["customer_invoice_export_type"].create(
            {"name": "Default Grouping Type", "code": "TGRP000"}
        )
        self.assertEqual(ctype.grouping_method, "invoice")

    def test_populate_grouping_invoice_one_row_per_invoice(self):
        """Assert grouping "invoice" creates one Summary row per move.

        Pure Python -- trigger P10 (L-09, L-10: fixture setup needs a
        conditional search-or-create for the income account, which a
        single EVAL: expression cannot express).
        """
        journal = self._get_sale_journal()
        income_account = self._get_income_account()
        product_a = self._create_product("Grouping Product A", income_account)
        product_b = self._create_product("Grouping Product B", income_account)
        partner = self.env["res.partner"].create({"name": "Grouping Partner P1"})
        ctype = self._create_export_type(journal, product_a, grouping_method="invoice")

        invoice_1 = self._create_invoice(
            partner, journal, [(product_a, 100.0), (product_b, 20.0)], "2026-01-05"
        )
        invoice_2 = self._create_invoice(
            partner, journal, [(product_a, 150.0), (product_b, 30.0)], "2026-01-10"
        )

        export_doc = self.env["customer_invoice_export"].create(
            {"type_id": ctype.id, "date": "2026-03-01", "output_format": "csv"}
        )
        export_doc.action_populate()

        self.assertEqual(len(export_doc.summary_ids), 2)
        for summary in export_doc.summary_ids:
            self.assertEqual(len(summary.move_ids), 1)
            self.assertTrue(
                all(line.product_id == product_a for line in summary.line_ids)
            )
        summary_1 = export_doc.summary_ids.filtered(lambda s: invoice_1 in s.move_ids)
        self.assertEqual(summary_1.amount_total, 100.0)
        summary_2 = export_doc.summary_ids.filtered(lambda s: invoice_2 in s.move_ids)
        self.assertEqual(summary_2.amount_total, 150.0)

    def test_populate_grouping_partner_merges_same_partner_invoices(self):
        """Assert grouping "partner" merges same-partner invoices.

        Pure Python -- trigger P10 (L-09, L-10: fixture setup needs a
        conditional search-or-create for the income account, which a
        single EVAL: expression cannot express).
        """
        journal = self._get_sale_journal()
        income_account = self._get_income_account()
        product_a = self._create_product("Merge Product A", income_account)
        product_b = self._create_product("Merge Product B", income_account)
        partner = self.env["res.partner"].create({"name": "Merge Partner P1"})
        ctype = self._create_export_type(journal, product_a, grouping_method="partner")

        invoice_1 = self._create_invoice(
            partner, journal, [(product_a, 100.0), (product_b, 20.0)], "2026-01-05"
        )
        invoice_2 = self._create_invoice(
            partner, journal, [(product_a, 150.0), (product_b, 30.0)], "2026-01-10"
        )

        export_doc = self.env["customer_invoice_export"].create(
            {"type_id": ctype.id, "date": "2026-03-01", "output_format": "csv"}
        )
        export_doc.action_populate()

        self.assertEqual(len(export_doc.summary_ids), 1)
        summary = export_doc.summary_ids
        self.assertEqual(set(summary.move_ids.ids), {invoice_1.id, invoice_2.id})
        self.assertEqual(summary.partner_id, partner)
        self.assertEqual(summary.amount_total, 250.0)
        qualifying_lines = (invoice_1 + invoice_2).invoice_line_ids.filtered(
            lambda line: line.product_id == product_a
        )
        self.assertEqual(set(summary.line_ids.ids), set(qualifying_lines.ids))

    def test_populate_grouping_partner_does_not_merge_different_partners(self):
        """Assert grouping "partner" keeps different partners separate.

        Pure Python -- trigger P10 (L-09, L-10: fixture setup needs a
        conditional search-or-create for the income account, which a
        single EVAL: expression cannot express).
        """
        journal = self._get_sale_journal()
        income_account = self._get_income_account()
        product_a = self._create_product("Distinct Product A", income_account)
        partner_1 = self.env["res.partner"].create({"name": "Distinct Partner P1"})
        partner_2 = self.env["res.partner"].create({"name": "Distinct Partner P2"})
        ctype = self._create_export_type(journal, product_a, grouping_method="partner")

        invoice_1 = self._create_invoice(
            partner_1, journal, [(product_a, 100.0)], "2026-01-05"
        )
        invoice_2 = self._create_invoice(
            partner_2, journal, [(product_a, 200.0)], "2026-01-06"
        )

        export_doc = self.env["customer_invoice_export"].create(
            {"type_id": ctype.id, "date": "2026-03-01", "output_format": "csv"}
        )
        export_doc.action_populate()

        self.assertEqual(len(export_doc.summary_ids), 2)
        for summary in export_doc.summary_ids:
            self.assertEqual(len(summary.move_ids), 1)
        self.assertEqual(
            set(export_doc.summary_ids.mapped("partner_id").ids),
            {partner_1.id, partner_2.id},
        )
        self.assertEqual(
            set(export_doc.summary_ids.mapped("move_ids").ids),
            {invoice_1.id, invoice_2.id},
        )

    def test_populate_grouping_partner_skips_invoice_without_qualifying_lines(self):
        """Assert an invoice with no qualifying lines gets no Summary row.

        Pure Python -- trigger P10 (L-09, L-10: fixture setup needs a
        conditional search-or-create for the income account, which a
        single EVAL: expression cannot express).
        """
        journal = self._get_sale_journal()
        income_account = self._get_income_account()
        product_a = self._create_product("Skip Product A", income_account)
        product_b = self._create_product("Skip Product B", income_account)
        partner = self.env["res.partner"].create({"name": "Skip Partner P1"})
        ctype = self._create_export_type(journal, product_a, grouping_method="partner")

        non_qualifying_invoice = self._create_invoice(
            partner, journal, [(product_b, 75.0)], "2026-01-05"
        )

        export_doc = self.env["customer_invoice_export"].create(
            {"type_id": ctype.id, "date": "2026-03-01", "output_format": "csv"}
        )
        export_doc.action_populate()

        self.assertFalse(export_doc.summary_ids)
        self.assertIn(non_qualifying_invoice, export_doc.move_ids)

    def test_populate_grouping_partner_idempotent(self):
        """Assert Populate stays idempotent under partner grouping too.

        Pure Python -- trigger P10 (L-09, L-10: fixture setup needs a
        conditional search-or-create for the income account, which a
        single EVAL: expression cannot express).
        """
        journal = self._get_sale_journal()
        income_account = self._get_income_account()
        product_a = self._create_product("Idempotent Partner Product A", income_account)
        partner = self.env["res.partner"].create({"name": "Idempotent Partner P1"})
        ctype = self._create_export_type(journal, product_a, grouping_method="partner")
        self._create_invoice(partner, journal, [(product_a, 100.0)], "2026-01-01")
        self._create_invoice(partner, journal, [(product_a, 200.0)], "2026-01-02")

        export_doc = self.env["customer_invoice_export"].create(
            {"type_id": ctype.id, "date": "2026-03-01", "output_format": "csv"}
        )
        export_doc.action_populate()
        first_count = len(export_doc.summary_ids)
        self.assertEqual(first_count, 1)
        export_doc.action_populate()
        self.assertEqual(len(export_doc.summary_ids), first_count)

    # -------------------------------------------------------------------
    # Partner Criteria (BL-0128)
    # -------------------------------------------------------------------

    def test_default_type_partner_criteria(self):
        """Assert the Type's default partner criteria allow everyone.

        Pure Python -- co-located with the rest of this file's partner
        criteria coverage (P10, L-09/L-10: the file's fixtures need real
        control flow, impossible in a single EVAL: expression) rather
        than split into a separate YAML-only test file.
        """
        ctype = self.env["customer_invoice_export_type"].create(
            {"name": "Default Partner Criteria Type", "code": "TPTN000"}
        )
        self.assertEqual(ctype.partner_selection_method, "domain")
        self.assertEqual(ctype.partner_domain, "[]")
        self.assertEqual(ctype.partner_python_code, "result = []")

    def test_allowed_partner_ids_computed_from_type(self):
        """Assert ``allowed_partner_ids`` recomputes when Type changes.

        Pure Python -- trigger P10 (L-09, L-10: fixture setup needs a
        conditional search-or-create for the income account, which a
        single EVAL: expression cannot express).
        """
        journal = self._get_sale_journal()
        income_account = self._get_income_account()
        product_a = self._create_product("Allowed Partner Product A", income_account)
        partner_1 = self.env["res.partner"].create({"name": "Allowed Partner P1"})
        partner_2 = self.env["res.partner"].create({"name": "Allowed Partner P2"})
        ctype = self._create_export_type(
            journal,
            product_a,
            partner_selection_method="manual",
            partner_ids=[(6, 0, partner_1.ids)],
        )

        export_doc = self.env["customer_invoice_export"].create(
            {"type_id": ctype.id, "date": "2026-03-01", "output_format": "csv"}
        )
        self.assertEqual(export_doc.allowed_partner_ids, partner_1)
        self.assertNotIn(partner_2, export_doc.allowed_partner_ids)

        ctype.partner_ids = [(6, 0, (partner_1 + partner_2).ids)]
        export_doc.invalidate_cache()
        self.assertEqual(
            set(export_doc.allowed_partner_ids.ids), {partner_1.id, partner_2.id}
        )

    def test_populate_filters_by_partner(self):
        """Assert Populate excludes invoices of a disallowed partner.

        Pure Python -- trigger P10 (L-09, L-10: fixture setup needs a
        conditional search-or-create for the income account, which a
        single EVAL: expression cannot express).
        """
        journal = self._get_sale_journal()
        income_account = self._get_income_account()
        product_a = self._create_product("Partner Filter Product A", income_account)
        partner_1 = self.env["res.partner"].create({"name": "Partner Filter P1"})
        partner_2 = self.env["res.partner"].create({"name": "Partner Filter P2"})
        ctype = self._create_export_type(
            journal,
            product_a,
            partner_selection_method="manual",
            partner_ids=[(6, 0, partner_1.ids)],
        )

        invoice_allowed = self._create_invoice(
            partner_1, journal, [(product_a, 100.0)], "2026-01-05"
        )
        invoice_excluded = self._create_invoice(
            partner_2, journal, [(product_a, 200.0)], "2026-01-06"
        )

        export_doc = self.env["customer_invoice_export"].create(
            {"type_id": ctype.id, "date": "2026-03-01", "output_format": "csv"}
        )
        export_doc.action_populate()

        self.assertEqual(export_doc.move_ids, invoice_allowed)
        self.assertNotIn(invoice_excluded, export_doc.move_ids)
        self.assertEqual(len(export_doc.summary_ids), 1)
        self.assertEqual(export_doc.summary_ids.partner_id, partner_1)

    def test_populate_partner_domain_allows_every_partner(self):
        """Assert the default "[]" partner domain still allows everyone.

        Pure Python -- trigger P10 (L-09, L-10: fixture setup needs a
        conditional search-or-create for the income account, which a
        single EVAL: expression cannot express).
        """
        journal = self._get_sale_journal()
        income_account = self._get_income_account()
        product_a = self._create_product("Partner Domain Product A", income_account)
        partner_1 = self.env["res.partner"].create({"name": "Partner Domain P1"})
        partner_2 = self.env["res.partner"].create({"name": "Partner Domain P2"})
        # Default partner criteria (domain "[]") must keep the pre-BL-0128
        # behaviour: every partner qualifies.
        ctype = self._create_export_type(journal, product_a)
        self.assertEqual(ctype.partner_selection_method, "domain")

        invoice_1 = self._create_invoice(
            partner_1, journal, [(product_a, 100.0)], "2026-01-05"
        )
        invoice_2 = self._create_invoice(
            partner_2, journal, [(product_a, 200.0)], "2026-01-06"
        )

        export_doc = self.env["customer_invoice_export"].create(
            {"type_id": ctype.id, "date": "2026-03-01", "output_format": "csv"}
        )
        export_doc.action_populate()

        self.assertEqual(set(export_doc.move_ids.ids), {invoice_1.id, invoice_2.id})

    # -------------------------------------------------------------------
    # Render output (CSV / TXT) -- unit-level, no queue involved
    # -------------------------------------------------------------------

    def test_render_csv_and_txt(self):
        """Assert ``_render_output`` bytes for CSV and TXT formats.

        Pure Python -- trigger P1 (L-01: ``_render_output``'s return
        value -- the encoded file bytes -- is discarded by ``action:
        call`` and cannot be asserted from YAML).
        """
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
        """Assert ``_generate_export_file`` raises with no Summary rows.

        Pure Python -- trigger P10 (L-09, L-10: fixture setup needs a
        conditional search-or-create for the income account, which a
        single EVAL: expression cannot express).
        """
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
        """Assert draft->confirm->queue_done->done generates the file.

        Pure Python -- trigger P10 (L-09, L-10: fixture setup needs a
        conditional search-or-create for the income account, which a
        single EVAL: expression cannot express).
        """
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

    # -------------------------------------------------------------------
    # Form view arch (BL-0105) -- move_ids inline tree must declare
    # "state" so the web client can evaluate readonly modifiers deriving
    # from account.move fields declared with states={'draft': [...]}.
    # -------------------------------------------------------------------

    def test_form_view_move_ids_subview_declares_state(self):
        """Assert the ``move_ids`` subview arch declares "state".

        Pure Python -- trigger P1 (L-01, L-02: ``fields_view_get``'s
        return dict cannot be captured or asserted by dotted ``getattr``
        from YAML).
        """
        view = self.env.ref(
            "ssi_customer_invoice_export.customer_invoice_export_view_form"
        )
        result = self.env["customer_invoice_export"].fields_view_get(
            view_id=view.id, view_type="form"
        )
        move_ids_subview_fields = result["fields"]["move_ids"]["views"]["tree"][
            "fields"
        ]
        self.assertIn("state", move_ids_subview_fields)

    def test_form_view_renders_with_populated_moves(self):
        """Assert the populated ``move_ids`` subview fields are readable.

        Pure Python -- trigger P10 (L-09, L-10: fixture setup needs a
        conditional search-or-create for the income account, which a
        single EVAL: expression cannot express).
        """
        journal = self._get_sale_journal()
        income_account = self._get_income_account()
        product_a = self._create_product("FormView Product A", income_account)
        partner = self.env["res.partner"].create({"name": "FormView Partner"})
        ctype = self._create_export_type(journal, product_a)
        self._create_invoice(partner, journal, [(product_a, 100.0)], "2026-01-10")

        export_doc = self.env["customer_invoice_export"].create(
            {"type_id": ctype.id, "date": "2026-03-01", "output_format": "csv"}
        )
        export_doc.action_populate()
        self.assertTrue(export_doc.move_ids)

        export_doc.move_ids.read(
            [
                "state",
                "name",
                "partner_id",
                "invoice_date",
                "journal_id",
                "amount_total",
                "payment_state",
            ]
        )

    def test_cancel_from_draft_and_restart(self):
        """Assert cancel from draft, then restart back to draft.

        Pure Python -- co-located with the rest of this file's workflow
        coverage (P10, L-09/L-10: the file's fixtures need real control
        flow, impossible in a single EVAL: expression) rather than split
        into a separate YAML-only test file.
        """
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

    # -------------------------------------------------------------------
    # Receivable account criteria + Amount Residual
    #
    # Amount Total sums the invoice lines' price_subtotal, which stays 0
    # on a move_type="entry" move (core only recomputes price_subtotal
    # for is_invoice() moves). Amount Residual instead reads the move's
    # receivable journal item, which is also where every reduction --
    # payments, and the scholarship / fee waiver / promotion deductions,
    # which all reconcile a credit against the receivable rather than
    # touching the invoice -- has already been applied.
    # -------------------------------------------------------------------

    def _get_receivable_account(self):
        """Return a dedicated reconcilable receivable account."""
        account = self.env["account.account"].search(
            [
                ("code", "=", "TESTREC01"),
                ("company_id", "=", self.env.company.id),
            ],
            limit=1,
        )
        if not account:
            account = self.env["account.account"].create(
                {
                    "name": "Test Receivable Account",
                    "code": "TESTREC01",
                    "user_type_id": self.env.ref(
                        "account.data_account_type_receivable"
                    ).id,
                    "reconcile": True,
                    "company_id": self.env.company.id,
                }
            )
        return account

    def _create_receivable_entry(
        self, journal, product, amount, date, partner, with_currency=False
    ):
        """Create a posted entry whose debit line sits on receivable.

        Mirrors the shape an SSI ``customer_invoice`` produces: a
        ``move_type="entry"`` move carrying one receivable debit line
        (what the customer owes) and one revenue credit line bearing the
        product, with ``price_subtotal`` left at 0 throughout.

        :param journal: ``account.journal`` (type ``general``) used
        :param product: ``product.product`` set on the revenue line
        :param amount: amount of the two balancing lines
        :param date: move date string
        :param partner: ``res.partner`` set on the move and receivable
        :param with_currency: when True, stamp the company currency and
            ``amount_currency`` on both lines, the way the SSI
            accounting entry mixin does, so ``amount_residual_currency``
            is populated instead of being left at 0.0
        :return: the posted ``account.move``
        """
        currency = self.env.company.currency_id
        revenue_values = {
            "account_id": self._get_income_account().id,
            "product_id": product.id,
            "name": "Revenue Line",
            "debit": 0.0,
            "credit": amount,
        }
        receivable_values = {
            "account_id": self._get_receivable_account().id,
            "partner_id": partner.id,
            "name": "Receivable Line",
            "debit": amount,
            "credit": 0.0,
        }
        if with_currency:
            revenue_values.update(
                {"currency_id": currency.id, "amount_currency": -amount}
            )
            receivable_values.update(
                {"currency_id": currency.id, "amount_currency": amount}
            )
        move = self.env["account.move"].create(
            {
                "move_type": "entry",
                "journal_id": journal.id,
                "date": date,
                "partner_id": partner.id,
                "line_ids": [(0, 0, revenue_values), (0, 0, receivable_values)],
            }
        )
        move.action_post()
        return move

    def _reduce_receivable(self, journal, move, amount, date, partner):
        """Reconcile a credit entry against ``move``'s receivable line.

        Stands in for a scholarship deduction, a fee waiver deduction or
        a promotion usage: all three post their own journal entry
        crediting the receivable account and reconcile it against the
        invoice's receivable item, leaving the invoice itself untouched.

        :param journal: ``account.journal`` (type ``general``) used
        :param move: the ``account.move`` whose receivable is reduced
        :param amount: amount credited against the receivable
        :param date: move date string
        :param partner: ``res.partner`` set on the move and receivable
        :return: the posted counter ``account.move``
        """
        receivable_account = self._get_receivable_account()
        counter = self.env["account.move"].create(
            {
                "move_type": "entry",
                "journal_id": journal.id,
                "date": date,
                "partner_id": partner.id,
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "account_id": receivable_account.id,
                            "partner_id": partner.id,
                            "name": "Deduction Line",
                            "debit": 0.0,
                            "credit": amount,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "account_id": self._get_temp_account().id,
                            "name": "Contra Line",
                            "debit": amount,
                            "credit": 0.0,
                        },
                    ),
                ],
            }
        )
        counter.action_post()
        (move.line_ids + counter.line_ids).filtered(
            lambda line: line.account_id == receivable_account
        ).reconcile()
        return counter

    def _populate_from_source(self, moves, **type_values):
        """Create and populate an export document over ``moves``.

        :param moves: ``account.move`` recordset fed via source_move_ids
        :param type_values: additional Type field values
        :return: the populated ``customer_invoice_export``
        """
        ctype = self._create_minimal_export_type(**type_values)
        export_doc = self.env["customer_invoice_export"].create(
            {
                "type_id": ctype.id,
                "date": "2026-03-01",
                "output_format": "csv",
                "source_move_ids": [(6, 0, moves.ids)],
            }
        )
        export_doc.action_populate()
        return export_doc

    def test_default_type_receivable_account_criteria(self):
        """Assert the receivable criteria defaults to every receivable.

        Pure Python -- trigger P10 (L-09: asserting a field default on a
        freshly created record needs the shared type helper).
        """
        ctype = self._create_minimal_export_type()

        self.assertEqual(ctype.receivable_account_selection_method, "domain")
        self.assertEqual(
            ctype.receivable_account_domain,
            "[('user_type_id.type', '=', 'receivable')]",
        )

    def test_allowed_receivable_account_ids_computed_from_type(self):
        """Assert the manual criteria resolves onto the document.

        Pure Python -- trigger P10 (L-09: the receivable account fixture
        needs a conditional search-or-create step).
        """
        receivable_account = self._get_receivable_account()
        ctype = self._create_minimal_export_type(
            receivable_account_selection_method="manual",
            receivable_account_ids=[(6, 0, receivable_account.ids)],
        )

        export_doc = self.env["customer_invoice_export"].create(
            {"type_id": ctype.id, "date": "2026-03-01", "output_format": "csv"}
        )

        self.assertEqual(export_doc.allowed_receivable_account_ids, receivable_account)

    def test_amount_residual_reads_receivable_line_not_invoice_lines(self):
        """Assert Amount Residual is filled where Amount Total is 0.

        Pure Python -- trigger P10 (L-09, L-10: building the entry move
        and its receivable fixture needs real control flow).
        """
        journal = self._get_general_journal()
        product = self._create_product("Residual Product", self._get_income_account())
        partner = self.env["res.partner"].create({"name": "Residual Partner"})
        move = self._create_receivable_entry(
            journal, product, 200000.0, "2026-01-10", partner
        )

        export_doc = self._populate_from_source(move)

        self.assertEqual(len(export_doc.summary_ids), 1)
        summary = export_doc.summary_ids
        self.assertEqual(summary.amount_total, 0.0)
        self.assertEqual(summary.amount_residual, 200000.0)

    def test_amount_residual_is_net_of_reconciled_deduction(self):
        """Assert a deduction reconciled against receivable is netted.

        Mirrors a real record: a 7.250.000 invoice reduced to 990.000
        outstanding by scholarship/waiver deductions, where Amount Total
        would still report the gross.

        Pure Python -- trigger P10 (L-09, L-10: posting a counter move
        and calling reconcile() cannot be expressed in YAML).
        """
        journal = self._get_general_journal()
        product = self._create_product("Deducted Product", self._get_income_account())
        partner = self.env["res.partner"].create({"name": "Deducted Partner"})
        move = self._create_receivable_entry(
            journal, product, 7250000.0, "2026-01-10", partner
        )
        self._reduce_receivable(journal, move, 6260000.0, "2026-01-20", partner)

        export_doc = self._populate_from_source(move)

        self.assertEqual(export_doc.summary_ids.amount_residual, 990000.0)

    def test_amount_residual_zero_when_fully_reconciled(self):
        """Assert a fully settled invoice reports nothing outstanding.

        Pure Python -- trigger P10 (L-09, L-10: reconcile() call).
        """
        journal = self._get_general_journal()
        product = self._create_product("Settled Product", self._get_income_account())
        partner = self.env["res.partner"].create({"name": "Settled Partner"})
        move = self._create_receivable_entry(
            journal, product, 500000.0, "2026-01-10", partner
        )
        self._reduce_receivable(journal, move, 500000.0, "2026-01-20", partner)

        export_doc = self._populate_from_source(move)

        self.assertEqual(export_doc.summary_ids.amount_residual, 0.0)

    def test_amount_residual_ignores_non_receivable_debit_line(self):
        """Assert a debit line outside the criteria is not counted.

        Pure Python -- trigger P10 (L-09, L-10: entry move fixture).
        """
        journal = self._get_general_journal()
        product = self._create_product("Non Rec Product", self._get_income_account())
        partner = self.env["res.partner"].create({"name": "Non Rec Partner"})
        move = self._create_journal_entry_with_product(
            journal, product, 300000.0, "2026-01-10", partner
        )

        export_doc = self._populate_from_source(move)

        self.assertEqual(len(export_doc.summary_ids), 1)
        self.assertEqual(export_doc.summary_ids.amount_residual, 0.0)

    def test_amount_residual_reads_currency_residual_when_line_has_currency(self):
        """Assert a currency-stamped line is read in its own currency.

        Covers the branch taken by every move the SSI accounting entry
        mixin builds, which always stamps currency_id and
        amount_currency -- there core fills amount_residual_currency,
        whereas a line without a currency leaves it at 0.0 and must fall
        back to amount_residual.

        Pure Python -- trigger P10 (L-09, L-10: entry move fixture).
        """
        journal = self._get_general_journal()
        product = self._create_product("Currency Product", self._get_income_account())
        partner = self.env["res.partner"].create({"name": "Currency Partner"})
        move = self._create_receivable_entry(
            journal,
            product,
            150000.0,
            "2026-01-10",
            partner,
            with_currency=True,
        )
        receivable_line = move.line_ids.filtered(
            lambda line: line.account_id == self._get_receivable_account()
        )
        self.assertTrue(receivable_line.currency_id)
        self.assertEqual(receivable_line.amount_residual_currency, 150000.0)

        export_doc = self._populate_from_source(move)

        self.assertEqual(export_doc.summary_ids.amount_residual, 150000.0)

    def test_amount_residual_grouping_partner_sums_every_move(self):
        """Assert per-partner rows add up the residual of each invoice.

        Pure Python -- trigger P10 (L-09, L-10: two entry move fixtures).
        """
        journal = self._get_general_journal()
        product = self._create_product("Grouped Product", self._get_income_account())
        partner = self.env["res.partner"].create({"name": "Grouped Partner"})
        first = self._create_receivable_entry(
            journal, product, 100000.0, "2026-01-10", partner
        )
        second = self._create_receivable_entry(
            journal, product, 50000.0, "2026-01-11", partner
        )

        export_doc = self._populate_from_source(
            first + second, grouping_method="partner"
        )

        self.assertEqual(len(export_doc.summary_ids), 1)
        self.assertEqual(export_doc.summary_ids.amount_residual, 150000.0)

    # -------------------------------------------------------------------
    # write() rebuilds Invoice Lines/Summary + Confirm gate (issue #42)
    #
    # move_ids can be edited manually while Draft; write() must rebuild
    # line_ids/summary_ids from the current move_ids every time, not
    # only when action_populate is pressed -- otherwise a dropped
    # invoice's Summary row survives and gets exported again.
    # -------------------------------------------------------------------

    def test_write_move_ids_removes_dropped_invoice_from_summary(self):
        """Assert dropping an invoice from ``move_ids`` rebuilds Summary.

        Pure Python -- trigger P10 (L-09, L-10: fixture setup needs a
        conditional search-or-create for the income account, which a
        single EVAL: expression cannot express).
        """
        journal = self._get_sale_journal()
        income_account = self._get_income_account()
        product_a = self._create_product("Write Drop Product A", income_account)
        partner_1 = self.env["res.partner"].create({"name": "Write Drop Partner 1"})
        partner_2 = self.env["res.partner"].create({"name": "Write Drop Partner 2"})
        ctype = self._create_export_type(journal, product_a)
        invoice_1 = self._create_invoice(
            partner_1, journal, [(product_a, 100.0)], "2026-01-05"
        )
        invoice_2 = self._create_invoice(
            partner_2, journal, [(product_a, 200.0)], "2026-01-06"
        )

        export_doc = self.env["customer_invoice_export"].create(
            {"type_id": ctype.id, "date": "2026-03-01", "output_format": "csv"}
        )
        export_doc.write({"move_ids": [(6, 0, (invoice_1 + invoice_2).ids)]})
        self.assertEqual(len(export_doc.summary_ids), 2)

        export_doc.write({"move_ids": [(6, 0, invoice_1.ids)]})

        self.assertEqual(export_doc.move_ids, invoice_1)
        self.assertEqual(len(export_doc.summary_ids), 1)
        self.assertEqual(export_doc.summary_ids.move_ids, invoice_1)
        self.assertTrue(all(line.move_id == invoice_1 for line in export_doc.line_ids))

    def test_write_move_ids_adding_invoice_creates_summary_row(self):
        """Assert adding an invoice to ``move_ids`` builds its row.

        Pure Python -- trigger P10 (L-09, L-10: fixture setup needs a
        conditional search-or-create for the income account, which a
        single EVAL: expression cannot express).
        """
        journal = self._get_sale_journal()
        income_account = self._get_income_account()
        product_a = self._create_product("Write Add Product A", income_account)
        partner_1 = self.env["res.partner"].create({"name": "Write Add Partner 1"})
        partner_2 = self.env["res.partner"].create({"name": "Write Add Partner 2"})
        ctype = self._create_export_type(journal, product_a)
        invoice_1 = self._create_invoice(
            partner_1, journal, [(product_a, 100.0)], "2026-01-05"
        )
        invoice_2 = self._create_invoice(
            partner_2, journal, [(product_a, 200.0)], "2026-01-06"
        )

        export_doc = self.env["customer_invoice_export"].create(
            {"type_id": ctype.id, "date": "2026-03-01", "output_format": "csv"}
        )
        export_doc.write({"move_ids": [(6, 0, invoice_1.ids)]})
        self.assertEqual(len(export_doc.summary_ids), 1)

        export_doc.write({"move_ids": [(6, 0, (invoice_1 + invoice_2).ids)]})

        self.assertEqual(len(export_doc.summary_ids), 2)
        self.assertEqual(
            set(export_doc.summary_ids.mapped("move_ids").ids),
            {invoice_1.id, invoice_2.id},
        )

    def test_write_move_ids_empty_clears_summary_and_lines(self):
        """Assert clearing ``move_ids`` empties Summary and Invoice Lines.

        Pure Python -- trigger P10 (L-09, L-10: fixture setup needs a
        conditional search-or-create for the income account, which a
        single EVAL: expression cannot express).
        """
        journal = self._get_sale_journal()
        income_account = self._get_income_account()
        product_a = self._create_product("Write Clear Product A", income_account)
        partner = self.env["res.partner"].create({"name": "Write Clear Partner"})
        ctype = self._create_export_type(journal, product_a)
        invoice = self._create_invoice(
            partner, journal, [(product_a, 100.0)], "2026-01-05"
        )

        export_doc = self.env["customer_invoice_export"].create(
            {"type_id": ctype.id, "date": "2026-03-01", "output_format": "csv"}
        )
        export_doc.write({"move_ids": [(6, 0, invoice.ids)]})
        self.assertTrue(export_doc.summary_ids)
        self.assertTrue(export_doc.line_ids)

        export_doc.write({"move_ids": [(6, 0, [])]})

        self.assertFalse(export_doc.move_ids)
        self.assertFalse(export_doc.summary_ids)
        self.assertFalse(export_doc.line_ids)

    # -------------------------------------------------------------------
    # Reload (action_rederive_summary) -- rebuilds Invoice Lines/Summary
    # from the current Invoices without touching move_ids, unlike
    # Populate.
    # -------------------------------------------------------------------

    def test_rederive_summary_after_type_criteria_changed(self):
        """Assert Reload rebuilds Summary after the Type's Type changed.

        Editing the Type's product criteria never writes to the export
        document itself, so ``write()``'s own trigger never fires --
        Invoice Lines/Summary stay stale until ``action_rederive_summary``
        (the Reload button) is called directly. Pure Python -- trigger
        P10 (L-09, L-10: fixture setup needs a conditional
        search-or-create for the income account, which a single EVAL:
        expression cannot express).
        """
        journal = self._get_sale_journal()
        income_account = self._get_income_account()
        product_a = self._create_product("Reload Product A", income_account)
        product_b = self._create_product("Reload Product B", income_account)
        partner = self.env["res.partner"].create({"name": "Reload Partner"})
        ctype = self._create_export_type(journal, product_a)
        invoice = self._create_invoice(
            partner, journal, [(product_a, 100.0), (product_b, 50.0)], "2026-01-05"
        )

        export_doc = self.env["customer_invoice_export"].create(
            {"type_id": ctype.id, "date": "2026-03-01", "output_format": "csv"}
        )
        export_doc.action_populate()
        self.assertEqual(export_doc.line_ids.mapped("product_id"), product_a)
        self.assertEqual(export_doc.summary_ids.amount_total, 100.0)

        # Fix the Type's product criteria to product_b -- this never
        # writes to export_doc, so line_ids/summary_ids stay stale on
        # product_a until Reload is clicked.
        ctype.write({"product_ids": [(6, 0, product_b.ids)]})
        self.assertEqual(export_doc.line_ids.mapped("product_id"), product_a)
        self.assertEqual(export_doc.summary_ids.amount_total, 100.0)

        # allowed_product_ids is a non-stored compute depending only on
        # type_id (models/customer_invoice_export.py), so ctype.write()
        # above never invalidates it within this same transaction; without
        # this, action_rederive_summary below would still filter with the
        # stale product_a. In production, editing the Type and clicking
        # Reload are two separate requests/transactions, so this staleness
        # never happens there.
        export_doc.invalidate_cache(["allowed_product_ids"], export_doc.ids)

        export_doc.action_rederive_summary()

        self.assertEqual(export_doc.move_ids, invoice)
        self.assertEqual(export_doc.line_ids.mapped("product_id"), product_b)
        self.assertEqual(export_doc.summary_ids.amount_total, 50.0)

    def test_rederive_summary_keeps_manual_move_ids_adjustment(self):
        """Assert Reload never restores an invoice dropped from Invoices.

        Contrasts with ``action_populate``, which always re-runs
        ``_prepare_invoice_domain`` and would bring the dropped invoice
        back. Pure Python -- trigger P10 (L-09, L-10: fixture setup
        needs a conditional search-or-create for the income account,
        which a single EVAL: expression cannot express).
        """
        journal = self._get_sale_journal()
        income_account = self._get_income_account()
        product_a = self._create_product("Reload Keep Product A", income_account)
        product_b = self._create_product("Reload Keep Product B", income_account)
        partner_1 = self.env["res.partner"].create({"name": "Reload Keep Partner 1"})
        partner_2 = self.env["res.partner"].create({"name": "Reload Keep Partner 2"})
        ctype = self._create_export_type(journal, product_a)
        invoice_1 = self._create_invoice(
            partner_1, journal, [(product_a, 100.0)], "2026-01-05"
        )
        invoice_2 = self._create_invoice(
            partner_2, journal, [(product_a, 200.0)], "2026-01-06"
        )

        export_doc = self.env["customer_invoice_export"].create(
            {"type_id": ctype.id, "date": "2026-03-01", "output_format": "csv"}
        )
        export_doc.action_populate()
        self.assertEqual(set(export_doc.move_ids.ids), {invoice_1.id, invoice_2.id})

        # Manually drop invoice_2, then fix an unrelated Type criterion.
        export_doc.write({"move_ids": [(6, 0, invoice_1.ids)]})
        ctype.write({"product_ids": [(6, 0, (product_a + product_b).ids)]})

        export_doc.action_rederive_summary()

        self.assertEqual(export_doc.move_ids, invoice_1)
        self.assertEqual(export_doc.summary_ids.move_ids, invoice_1)

    def test_rederive_summary_on_empty_move_ids_clears_lines(self):
        """Assert Reload on a Draft document without Invoices is a no-op.

        Pure Python -- trigger P10 (L-09: the Type fixture needs a
        conditional search-or-create for the income account, which a
        single EVAL: expression cannot express).
        """
        journal = self._get_sale_journal()
        income_account = self._get_income_account()
        product_a = self._create_product("Reload Empty Product A", income_account)
        ctype = self._create_export_type(journal, product_a)

        export_doc = self.env["customer_invoice_export"].create(
            {"type_id": ctype.id, "date": "2026-03-01", "output_format": "csv"}
        )

        export_doc.action_rederive_summary()

        self.assertFalse(export_doc.move_ids)
        self.assertFalse(export_doc.line_ids)
        self.assertFalse(export_doc.summary_ids)

    def test_confirm_with_consistent_summary_succeeds(self):
        """Assert Confirm succeeds when Summary matches Invoices.

        Pure Python -- trigger P10 (L-09, L-10: fixture setup needs a
        conditional search-or-create for the income account, which a
        single EVAL: expression cannot express).
        """
        journal = self._get_sale_journal()
        income_account = self._get_income_account()
        product_a = self._create_product("Confirm OK Product A", income_account)
        partner = self.env["res.partner"].create({"name": "Confirm OK Partner"})
        ctype = self._create_export_type(journal, product_a)
        self._create_invoice(partner, journal, [(product_a, 100.0)], "2026-01-05")

        export_doc = (
            self.env["customer_invoice_export"]
            .with_user(self.env.ref("base.user_admin"))
            .create({"type_id": ctype.id, "date": "2026-03-01", "output_format": "csv"})
        )
        export_doc.action_populate()

        export_doc.action_confirm()
        export_doc.invalidate_cache()

        self.assertEqual(export_doc.state, "confirm")

    def test_confirm_raises_when_summary_references_stray_invoice(self):
        """Assert Confirm refuses a Summary row outside Invoices.

        Regression test for issue #42: ``write()`` never produces a
        stray Summary row on its own (it always rebuilds from the
        current ``move_ids``), so the only way to reproduce a document
        left inconsistent before this consistency check existed is to
        create the stray row directly -- exactly as
        ``_01_check_summary_matches_moves``'s docstring describes.
        Pure Python -- trigger P10 (L-09, L-10: fixture setup needs a
        conditional search-or-create for the income account, which a
        single EVAL: expression cannot express).
        """
        journal = self._get_sale_journal()
        income_account = self._get_income_account()
        product_a = self._create_product("Stray Summary Product A", income_account)
        partner_in = self.env["res.partner"].create({"name": "Stray In Partner"})
        partner_out = self.env["res.partner"].create({"name": "Stray Out Partner"})
        ctype = self._create_export_type(journal, product_a)
        invoice_in = self._create_invoice(
            partner_in, journal, [(product_a, 100.0)], "2026-01-05"
        )
        invoice_out = self._create_invoice(
            partner_out, journal, [(product_a, 200.0)], "2026-01-06"
        )

        export_doc = (
            self.env["customer_invoice_export"]
            .with_user(self.env.ref("base.user_admin"))
            .create({"type_id": ctype.id, "date": "2026-03-01", "output_format": "csv"})
        )
        export_doc.write({"move_ids": [(6, 0, invoice_in.ids)]})
        self.assertEqual(len(export_doc.summary_ids), 1)

        self.env["customer_invoice_export.summary"].create(
            {
                "export_id": export_doc.id,
                "sequence": 100,
                "move_ids": [(6, 0, invoice_out.ids)],
                "partner_id": partner_out.id,
                "currency_id": invoice_out.currency_id.id,
            }
        )

        with self.assertRaises(UserError) as error_catcher:
            export_doc.action_confirm()
        self.assertIn(invoice_out.name, str(error_catcher.exception))

    # -------------------------------------------------------------------
    # Recreate Export File (issue #43): regenerate a Done document,
    # bertimestamp file names.
    # -------------------------------------------------------------------

    def _build_done_export_doc(self, product_name, partner_name, price):
        """Build a document that has already reached ``done`` for real.

        Populates and confirms/approves it synchronously
        (``queue_job__no_delay``) so ``_01_generate_export_on_queue_done``
        actually runs and ``export_file``/``export_filename`` hold a
        real generated file -- not just a pending queue job.

        :param product_name: name for the fixture product
        :param partner_name: name for the fixture partner
        :param price: unit price for the fixture invoice line
        :return: a tuple ``(export_doc, ctype)`` of the ``done``
            document and its ``customer_invoice_export_type``
        """
        journal = self._get_sale_journal()
        income_account = self._get_income_account()
        product_a = self._create_product(product_name, income_account)
        partner = self.env["res.partner"].create({"name": partner_name})
        ctype = self._create_export_type(journal, product_a)
        self._create_invoice(partner, journal, [(product_a, price)], "2026-01-25")

        export_doc = (
            self.env["customer_invoice_export"]
            .with_user(self.env.ref("base.user_admin"))
            .create({"type_id": ctype.id, "date": "2026-03-01", "output_format": "csv"})
        )
        export_doc.action_populate()
        export_doc.action_confirm()
        export_doc.invalidate_cache()
        export_doc.with_context(queue_job__no_delay=True).action_approve_approval()
        export_doc.invalidate_cache()
        self.assertEqual(export_doc.state, "done")
        return export_doc, ctype

    def test_recreate_export_file_regenerates_with_new_parser_code(self):
        """Assert Recreate re-runs the parser and adds a new attachment.

        Pure Python -- trigger P10 (L-09, L-10: fixture setup needs a
        conditional search-or-create for the income account, which a
        single EVAL: expression cannot express).
        """
        export_doc, ctype = self._build_done_export_doc(
            "Recreate Product A", "Recreate Partner", 175.0
        )
        old_filename = export_doc.export_filename
        attachment_domain = [
            ("res_model", "=", "customer_invoice_export"),
            ("res_id", "=", export_doc.id),
        ]
        old_attachment_count = self.env["ir.attachment"].search_count(attachment_domain)

        ctype.parser_python_code = "result = [['FIXED', 999.0]]"
        export_doc.action_recreate_export_file()

        self.assertEqual(
            self.env["ir.attachment"].search_count(attachment_domain),
            old_attachment_count + 1,
        )
        self.assertNotEqual(export_doc.export_filename, old_filename)

    def test_generate_export_file_without_force_is_idempotent(self):
        """Assert ``_generate_export_file()`` without ``force`` no-ops.

        Pure Python -- trigger P10 (L-09, L-10: fixture setup needs a
        conditional search-or-create for the income account, which a
        single EVAL: expression cannot express).
        """
        export_doc, _ctype = self._build_done_export_doc(
            "Idempotent Product A", "Idempotent Partner", 90.0
        )
        old_filename = export_doc.export_filename
        attachment_domain = [
            ("res_model", "=", "customer_invoice_export"),
            ("res_id", "=", export_doc.id),
        ]
        old_attachment_count = self.env["ir.attachment"].search_count(attachment_domain)

        export_doc._generate_export_file()

        self.assertEqual(export_doc.export_filename, old_filename)
        self.assertEqual(
            self.env["ir.attachment"].search_count(attachment_domain),
            old_attachment_count,
        )

    def test_export_filename_matches_timestamped_pattern(self):
        """Assert the built file name is timestamped and slash-free.

        Pure Python -- trigger P4 (L-05: no regex assert exists in the
        odoo-yaml-test DSL).
        """
        export_doc, _ctype = self._build_done_export_doc(
            "Filename Product A", "Filename Partner", 60.0
        )

        self.assertIn("/", export_doc.name)
        self.assertNotIn("/", export_doc.export_filename)
        self.assertIsNotNone(
            re.match(r"^.+_\d{8}_\d{6}\.(csv|xlsx|txt)$", export_doc.export_filename)
        )

    def test_recreate_export_file_on_non_done_raises(self):
        """Assert Recreate refuses a document that is not Done.

        Pure Python -- trigger P10 (L-09, L-10: fixture setup needs a
        conditional search-or-create for the income account, which a
        single EVAL: expression cannot express).
        """
        journal = self._get_sale_journal()
        income_account = self._get_income_account()
        product_a = self._create_product("NonDone Product A", income_account)
        ctype = self._create_export_type(journal, product_a)
        export_doc = self.env["customer_invoice_export"].create(
            {"type_id": ctype.id, "date": "2026-03-01", "output_format": "csv"}
        )
        self.assertEqual(export_doc.state, "draft")

        with self.assertRaises(UserError):
            export_doc.action_recreate_export_file()

    def test_recreate_export_file_parser_error_keeps_previous_file(self):
        """Assert a parser error during Recreate keeps the old file.

        Pure Python -- trigger P10 (L-09, L-10: fixture setup needs a
        conditional search-or-create for the income account, which a
        single EVAL: expression cannot express).
        """
        export_doc, ctype = self._build_done_export_doc(
            "ParserError Product A", "ParserError Partner", 45.0
        )
        old_file = export_doc.export_file
        old_filename = export_doc.export_filename
        self.assertTrue(old_file)

        ctype.parser_python_code = "raise ValueError('boom')"

        with self.assertRaises(UserError) as error_catcher:
            export_doc.action_recreate_export_file()
        self.assertIn(ctype.display_name, str(error_catcher.exception))

        self.assertEqual(export_doc.export_file, old_file)
        self.assertEqual(export_doc.export_filename, old_filename)
