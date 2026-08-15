# Copyright 2026 OpenSynergy Indonesia
# Copyright 2026 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo_yaml_test import YamlTransactionCase

from odoo.tests import tagged

# Plain Python (not YAML): building posted invoices needs an income account,
# a journal, and products -- none expressible as odoo-yaml-test create/assert
# steps -- mirroring the precedent in
# ssi_customer_invoice_export/tests/test_customer_invoice_export.py.


@tagged("post_install", "-at_install")
class TestCustomerInvoiceExportOperatingUnit(YamlTransactionCase):
    """Cover the Operating Unit delta on ``customer_invoice_export``.

    Pure Python throughout -- trigger P10 (L-09, L-10: building a
    posted customer invoice needs a conditional search-or-create step
    for the income account, and the OU/journal fixtures need branching
    ``create()`` calls, none of which a single ``EVAL:`` expression can
    express), mirroring the precedent set in
    ``ssi_customer_invoice_export/tests/test_customer_invoice_export.py``.
    """

    def setUp(self):
        """Cache the current company for the fixture helpers below."""
        super().setUp()
        self.company = self.env.company

    def _create_operating_unit(self, name, code):
        """Create an ``operating.unit`` with a dedicated partner.

        :param name: unique record name
        :param code: unique short code
        :return: the created ``operating.unit``
        """
        partner = self.env["res.partner"].create({"name": "%s Partner" % name})
        return self.env["operating.unit"].create(
            {
                "name": name,
                "code": code,
                "partner_id": partner.id,
                "company_id": self.company.id,
            }
        )

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
                    "name": "Test OU Income Account",
                    "code": "TESTOUINC01",
                    "user_type_id": account_type.id,
                    "company_id": self.env.company.id,
                }
            )
        return account

    def _create_journal(self, name, code, operating_units=None):
        """Create a sale journal, optionally restricted to some OUs.

        :param name: journal name
        :param code: unique short code
        :param operating_units: ``operating.unit`` recordset the
            journal is restricted to; ``None`` leaves it unrestricted
        :return: the created ``account.journal``
        """
        values = {"name": name, "type": "sale", "code": code}
        if operating_units is not None:
            values["operating_unit_ids"] = [(6, 0, operating_units.ids)]
        return self.env["account.journal"].create(values)

    def _create_product(self, name, income_account):
        """Create a service product posting to ``income_account``.

        :param name: product name
        :param income_account: ``account.account`` used as income
            account
        :return: the created ``product.product``
        """
        return self.env["product.product"].create(
            {
                "name": name,
                "type": "service",
                "property_account_income_id": income_account.id,
            }
        )

    def _create_invoice(self, partner, journal, product, price, invoice_date, ou=None):
        """Create and post a customer invoice with a single line.

        :param partner: ``res.partner`` invoiced
        :param journal: ``account.journal`` (type ``sale``) used
        :param product: ``product.product`` invoiced
        :param price: unit price of the single invoice line
        :param invoice_date: invoice date string
        :param ou: ``operating.unit`` set on the invoice, if any
        :return: the posted ``account.move``
        """
        values = {
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
            ],
        }
        if ou is not None:
            values["operating_unit_id"] = ou.id
        move = self.env["account.move"].create(values)
        move.action_post()
        return move

    def _create_export_type(self, journal, product, **extra_values):
        """Create a Type restricted to ``journal`` and ``product``.

        :param journal: ``account.journal`` recordset set as the only
            allowed journal(s)
        :param product: ``product.product`` recordset set as the only
            allowed product(s)
        :param extra_values: additional field values overriding
            defaults
        :return: the created ``customer_invoice_export_type``
        """
        values = {
            "name": "Test OU Export Type",
            "code": "TOUEXP001",
            "default_output_format": "csv",
            "journal_selection_method": "manual",
            "journal_ids": [(6, 0, journal.ids)],
            "product_selection_method": "manual",
            "product_ids": [(6, 0, product.ids)],
            "parser_python_code": (
                "result = [[s.move_ids.mapped('name'), s.amount_total] "
                "for s in summary_ids]"
            ),
        }
        values.update(extra_values)
        return self.env["customer_invoice_export_type"].create(values)

    # -------------------------------------------------------------------
    # allowed_journal_ids compute override — normal (OU set) and empty
    # (OU unset) conditions, per mandatory compute-field coverage.
    # -------------------------------------------------------------------

    def test_allowed_journal_ids_filtered_by_operating_unit(self):
        """Assert ``allowed_journal_ids`` drops journals of another OU.

        Pure Python -- trigger P10 (L-09, L-10: the OU and journal
        fixtures need branching ``create()`` calls no single ``EVAL:``
        expression can express).
        """
        ou_a = self._create_operating_unit("Test Journal Filter OU A", "TESTJFA")
        ou_b = self._create_operating_unit("Test Journal Filter OU B", "TESTJFB")
        journal_a = self._create_journal("Test OU Journal A", "TOUJA", ou_a)
        journal_b = self._create_journal("Test OU Journal B", "TOUJB", ou_b)
        income_account = self._get_income_account()
        product = self._create_product("Journal Filter Product", income_account)
        ctype = self._create_export_type(journal_a + journal_b, product)

        export_doc = self.env["customer_invoice_export"].create(
            {
                "type_id": ctype.id,
                "date": "2026-03-01",
                "output_format": "csv",
                "operating_unit_id": ou_a.id,
            }
        )
        self.assertEqual(export_doc.allowed_journal_ids, journal_a)

    def test_allowed_journal_ids_unfiltered_when_operating_unit_empty(self):
        """Assert an empty OU keeps journals of every OU allowed.

        Pure Python -- trigger P10 (L-09, L-10: the OU and journal
        fixtures need branching ``create()`` calls no single ``EVAL:``
        expression can express).
        """
        ou_a = self._create_operating_unit("Test Journal Empty OU A", "TESTJEA")
        ou_b = self._create_operating_unit("Test Journal Empty OU B", "TESTJEB")
        journal_a = self._create_journal("Test OU Empty Journal A", "TOUEJA", ou_a)
        journal_b = self._create_journal("Test OU Empty Journal B", "TOUEJB", ou_b)
        income_account = self._get_income_account()
        product = self._create_product("Journal Empty Product", income_account)
        ctype = self._create_export_type(journal_a + journal_b, product)

        # operating_unit_id must be cleared explicitly: mixin.single_operating_unit
        # defaults it from the current user's default operating unit, so simply
        # omitting the key from create() does not mean "empty" here.
        export_doc = self.env["customer_invoice_export"].create(
            {
                "type_id": ctype.id,
                "date": "2026-03-01",
                "output_format": "csv",
                "operating_unit_id": False,
            }
        )
        self.assertFalse(export_doc.operating_unit_id)
        self.assertEqual(
            set(export_doc.allowed_journal_ids.ids), {journal_a.id, journal_b.id}
        )

    # -------------------------------------------------------------------
    # Populate — the actual requirement: OU must restrict which invoices
    # the button can select, not just be a passive field.
    # -------------------------------------------------------------------

    def test_populate_filters_invoices_by_operating_unit(self):
        """Assert Populate only selects invoices of the document's OU.

        Pure Python -- trigger P10 (L-09, L-10: building posted
        invoices needs an income account, a journal, and products, none
        of which a single ``EVAL:`` expression can express).
        """
        ou_a = self._create_operating_unit("Test Populate OU A", "TESTPOPA")
        ou_b = self._create_operating_unit("Test Populate OU B", "TESTPOPB")
        # Journal with no OU restriction: moves of either OU can post to it.
        journal = self._create_journal("Test Populate Journal", "TOUPOPJ")
        income_account = self._get_income_account()
        product = self._create_product("Populate OU Product", income_account)
        partner = self.env["res.partner"].create({"name": "Populate OU Partner"})
        ctype = self._create_export_type(journal, product)

        invoice_a = self._create_invoice(
            partner, journal, product, 100.0, "2026-01-10", ou=ou_a
        )
        invoice_b = self._create_invoice(
            partner, journal, product, 200.0, "2026-01-15", ou=ou_b
        )

        export_doc = (
            self.env["customer_invoice_export"]
            .with_user(self.env.ref("base.user_admin"))
            .create(
                {
                    "type_id": ctype.id,
                    "date": "2026-03-01",
                    "output_format": "csv",
                    "operating_unit_id": ou_a.id,
                }
            )
        )
        export_doc.action_populate()

        self.assertEqual(export_doc.move_ids, invoice_a)
        self.assertNotIn(invoice_b.id, export_doc.move_ids.ids)

    def test_populate_unfiltered_when_operating_unit_empty(self):
        """Assert Populate selects invoices of every OU when unset.

        Pure Python -- trigger P10 (L-09, L-10: building posted
        invoices needs an income account, a journal, and products, none
        of which a single ``EVAL:`` expression can express).
        """
        ou_a = self._create_operating_unit("Test Populate Empty OU A", "TESTPOPEA")
        ou_b = self._create_operating_unit("Test Populate Empty OU B", "TESTPOPEB")
        journal = self._create_journal("Test Populate Empty Journal", "TOUPOPEJ")
        income_account = self._get_income_account()
        product = self._create_product("Populate Empty OU Product", income_account)
        partner = self.env["res.partner"].create({"name": "Populate Empty OU Partner"})
        ctype = self._create_export_type(journal, product)

        invoice_a = self._create_invoice(
            partner, journal, product, 100.0, "2026-01-10", ou=ou_a
        )
        invoice_b = self._create_invoice(
            partner, journal, product, 200.0, "2026-01-15", ou=ou_b
        )

        export_doc = (
            self.env["customer_invoice_export"]
            .with_user(self.env.ref("base.user_admin"))
            .create({"type_id": ctype.id, "date": "2026-03-01", "output_format": "csv"})
        )
        export_doc.write({"operating_unit_id": False})
        export_doc.action_populate()

        self.assertEqual(set(export_doc.move_ids.ids), {invoice_a.id, invoice_b.id})

    # -------------------------------------------------------------------
    # ir.rule — empty-OU fallback, matching the established pattern in
    # ssi_financial_accounting_operating_unit (account.move / account.move.line
    # / account.bank.statement rules) so records without an OU stay visible.
    # -------------------------------------------------------------------

    def test_rule_domain_force_has_ou_empty_fallback(self):
        """Assert the OU rule's domain keeps OU-less records visible.

        Pure Python -- trigger P10 (L-09, L-10: comparing
        ``domain_force`` needs whitespace normalization via chained
        ``str.replace()`` calls before the substring check, which a
        single ``EVAL:`` expression cannot express).
        """
        rule = self.env.ref(
            "ssi_customer_invoice_export_operating_unit.customer_invoice_export_rule_ou"
        )
        domain = rule.domain_force.replace(" ", "").replace("\n", "")
        self.assertIn("'operating_unit_id','=',False", domain)
