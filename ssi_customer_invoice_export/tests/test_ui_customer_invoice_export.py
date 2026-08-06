# Copyright 2026 OpenSynergy Indonesia
# Copyright 2026 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests import HttpCase, tagged


@tagged("post_install", "-at_install")
class TestUiCustomerInvoiceExport(HttpCase):
    """UI/UX tour tests for ``customer_invoice_export``.

    Every ``test_*`` method below runs the tour pairing with the IK file
    named in its docstring (``docs/customer_invoice_export/NN-*.md``).
    Pre-Condition data required by each IK is prepared here in Python --
    never through UI steps. ``HttpCase`` (via ``TransactionCase``) only
    exposes ``self.env`` per test method -- unlike ``SavepointCase``, it
    has no ``cls.env`` at ``setUpClass`` time -- so all fixtures below
    are built in instance-level ``setUp`` instead (same constraint
    already documented in
    ``test_ui_customer_invoice_export_type.py``, this module).
    """

    def setUp(self):
        """Create the Types, journals/products/invoices, and draft or
        confirm-state documents every tour below opens.

        Each scenario gets its own ``customer_invoice_export_type``
        fixture (unique ``name``) purely so its document can be located
        in the list view via ``:contains(<type name>)`` -- the
        document's own ``name`` field stays ``"/"`` until the ``done``
        state (``_create_sequence_state = "done"``), so it cannot be
        used to tell rows apart. ``policy.template`` and
        ``approval.template`` are not created here: production data
        already ships matching ones for this model
        (``policy_template/customer_invoice_export.xml``,
        ``approval_template/customer_invoice_export.xml``), and
        ``base.user_admin`` (the tour's login) is already a member of
        the Validator group by default (see
        ``security/res_groups/customer_invoice_export.xml``), so no
        extra group grant is needed either.

        Every ``customer_invoice_export`` document below is created
        with ``.with_user(self.admin)``: ``self.env`` here runs as
        ``SUPERUSER_ID`` (Odoo core ``TransactionCase.setUp``), not as
        ``base.user_admin`` (the tour's login), and
        ``security/ir_rule/customer_invoice_export.xml`` restricts
        every internal user to ``[('user_id', '=', user.id)]`` --
        ``user_id`` defaults to the creating user
        (``mixin_transaction._default_user_id``). A document created as
        superuser would therefore end up owned by ``SUPERUSER_ID`` and
        be invisible to the admin browser session opening the list.
        """
        super().setUp()

        self.admin = self.env.ref("base.user_admin")
        self.income_account = self._get_income_account()

        # -- create: one journal/product/invoice so Populate has exactly
        # one matching invoice to select.
        self.journal_create = self._create_sale_journal(
            "TOUR CIE Create Journal", "TCICR"
        )
        self.product_create = self._create_product(
            "TOUR CIE Create Product", self.income_account
        )
        self.type_create = self._create_export_type(
            "TOUR CIE Create Type",
            "TOURCIECR",
            self.journal_create,
            self.product_create,
        )
        self.partner_create = self.env["res.partner"].create(
            {"name": "TOUR CIE Create Partner"}
        )
        self.invoice_create = self._create_invoice(
            self.partner_create,
            self.journal_create,
            self.product_create,
            "2026-01-10",
        )

        # -- edit: two invoices on different dates so narrowing Date
        # Start and re-Populating provably drops the earlier one.
        self.journal_edit = self._create_sale_journal("TOUR CIE Edit Journal", "TCIED")
        self.product_edit = self._create_product(
            "TOUR CIE Edit Product", self.income_account
        )
        self.type_edit = self._create_export_type(
            "TOUR CIE Edit Type",
            "TOURCIEED",
            self.journal_edit,
            self.product_edit,
        )
        self.partner_edit_early = self.env["res.partner"].create(
            {"name": "TOUR CIE Edit Early Partner"}
        )
        self.partner_edit_late = self.env["res.partner"].create(
            {"name": "TOUR CIE Edit Late Partner"}
        )
        self.invoice_edit_early = self._create_invoice(
            self.partner_edit_early,
            self.journal_edit,
            self.product_edit,
            "2026-01-05",
        )
        self.invoice_edit_late = self._create_invoice(
            self.partner_edit_late,
            self.journal_edit,
            self.product_edit,
            "2026-02-15",
        )
        self.export_edit = (
            self.env["customer_invoice_export"]
            .with_user(self.admin)
            .create(
                {
                    "type_id": self.type_edit.id,
                    "date": "2026-03-01",
                    "output_format": "csv",
                }
            )
        )
        # Baseline Populate with no date range -- both invoices qualify,
        # so the edit tour's narrower Date Start has a row to drop.
        self.export_edit.action_populate()

        # -- delete: plain draft record, no invoice data needed.
        self.type_delete = self.env["customer_invoice_export_type"].create(
            {"name": "TOUR CIE Delete Type", "code": "TOURCIEDL"}
        )
        self.export_delete = (
            self.env["customer_invoice_export"]
            .with_user(self.admin)
            .create(
                {
                    "type_id": self.type_delete.id,
                    "date": "2026-03-01",
                    "output_format": "csv",
                }
            )
        )

        # -- confirm: plain draft record, no invoice data needed.
        self.type_confirm = self.env["customer_invoice_export_type"].create(
            {"name": "TOUR CIE Confirm Type", "code": "TOURCIECF"}
        )
        self.export_confirm = (
            self.env["customer_invoice_export"]
            .with_user(self.admin)
            .create(
                {
                    "type_id": self.type_confirm.id,
                    "date": "2026-03-01",
                    "output_format": "csv",
                }
            )
        )

        # -- approve/reject: pre-confirmed into Waiting for Approval.
        # ``bypass_policy_check`` skips the confirm_ok evaluation only --
        # it still creates real approval records from the production
        # approval.template, so the tour's own Approve/Reject click
        # below is exercised against a genuine pending approval level.
        self.type_approve = self.env["customer_invoice_export_type"].create(
            {"name": "TOUR CIE Approve Type", "code": "TOURCIEAP"}
        )
        self.export_approve = (
            self.env["customer_invoice_export"]
            .with_user(self.admin)
            .create(
                {
                    "type_id": self.type_approve.id,
                    "date": "2026-03-01",
                    "output_format": "csv",
                }
            )
        )
        self.export_approve.with_context(bypass_policy_check=True).action_confirm()

        self.type_reject = self.env["customer_invoice_export_type"].create(
            {"name": "TOUR CIE Reject Type", "code": "TOURCIERJ"}
        )
        self.export_reject = (
            self.env["customer_invoice_export"]
            .with_user(self.admin)
            .create(
                {
                    "type_id": self.type_reject.id,
                    "date": "2026-03-01",
                    "output_format": "csv",
                }
            )
        )
        self.export_reject.with_context(bypass_policy_check=True).action_confirm()

    def _get_income_account(self):
        """Return an existing revenue account, creating one if needed.

        :return: an ``account.account`` recordset.
        :rtype: recordset
        """
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
                    "name": "TOUR CIE Income Account",
                    "code": "TOURCIEINC",
                    "user_type_id": account_type.id,
                    "company_id": self.env.company.id,
                }
            )
        return account

    def _create_sale_journal(self, name, code):
        """Create a dedicated sale journal for one tour scenario.

        A dedicated journal (rather than a shared/demo one) keeps
        Populate's result scoped to this scenario's own fixture
        invoice(s).

        :param name: journal name.
        :param code: journal code.
        :return: an ``account.journal`` recordset.
        :rtype: recordset
        """
        return self.env["account.journal"].create(
            {"name": name, "type": "sale", "code": code}
        )

    def _create_product(self, name, income_account):
        """Create a service product posting to ``income_account``.

        :param name: product name.
        :param income_account: ``account.account`` recordset used as
            the product's income account.
        :return: a ``product.product`` recordset.
        :rtype: recordset
        """
        return self.env["product.product"].create(
            {
                "name": name,
                "type": "service",
                "property_account_income_id": income_account.id,
            }
        )

    def _create_export_type(self, name, code, journal, product):
        """Create a ``customer_invoice_export_type`` scoped to one
        journal and one product.

        :param name: type name.
        :param code: type code.
        :param journal: allowed ``account.journal`` recordset.
        :param product: allowed ``product.product`` recordset.
        :return: a ``customer_invoice_export_type`` recordset.
        :rtype: recordset
        """
        return self.env["customer_invoice_export_type"].create(
            {
                "name": name,
                "code": code,
                "default_output_format": "csv",
                "journal_selection_method": "manual",
                "journal_ids": [(6, 0, journal.ids)],
                "product_selection_method": "manual",
                "product_ids": [(6, 0, product.ids)],
            }
        )

    def _create_invoice(self, partner, journal, product, invoice_date):
        """Create and post an unpaid customer invoice.

        :param partner: ``res.partner`` recordset (the customer).
        :param journal: ``account.journal`` recordset.
        :param product: ``product.product`` recordset for the single
            invoice line.
        :param invoice_date: invoice date, ``"YYYY-MM-DD"``.
        :return: the posted ``account.move`` recordset.
        :rtype: recordset
        """
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
                            "price_unit": 100.0,
                            "name": product.name,
                            "account_id": product.property_account_income_id.id,
                        },
                    )
                ],
            }
        )
        move.action_post()
        return move

    def test_create(self):
        """Run the create tour for ``customer_invoice_export``.

        IK: docs/customer_invoice_export/01-create.md
        """
        self.start_tour("/web", "ssi_customer_invoice_export_create", login="admin")

    def test_edit(self):
        """Run the edit tour for ``customer_invoice_export``.

        IK: docs/customer_invoice_export/02-edit.md
        """
        self.start_tour("/web", "ssi_customer_invoice_export_edit", login="admin")

    def test_delete(self):
        """Run the delete tour for ``customer_invoice_export``.

        IK: docs/customer_invoice_export/03-delete.md
        """
        self.start_tour("/web", "ssi_customer_invoice_export_delete", login="admin")

    def test_confirm(self):
        """Run the confirm tour for ``customer_invoice_export``.

        IK: docs/customer_invoice_export/04-confirm.md
        """
        self.start_tour("/web", "ssi_customer_invoice_export_confirm", login="admin")

    def test_approve(self):
        """Run the approve tour for ``customer_invoice_export``.

        IK: docs/customer_invoice_export/05-approve.md
        """
        self.start_tour("/web", "ssi_customer_invoice_export_approve", login="admin")

    def test_reject(self):
        """Run the reject tour for ``customer_invoice_export``.

        IK: docs/customer_invoice_export/06-reject.md
        """
        self.start_tour("/web", "ssi_customer_invoice_export_reject", login="admin")
