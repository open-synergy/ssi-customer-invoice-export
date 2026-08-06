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
    never through UI steps -- following the tour authoring doctrine:
    prerequisite/background data belongs to ``setUpClass``, the tour
    itself only exercises the click-flow documented in the IK.
    """

    @classmethod
    def setUpClass(cls):
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
        """
        super().setUpClass()

        cls.income_account = cls._get_income_account()

        # -- create: one journal/product/invoice so Populate has exactly
        # one matching invoice to select.
        cls.journal_create = cls._create_sale_journal(
            "TOUR CIE Create Journal", "TCICR"
        )
        cls.product_create = cls._create_product(
            "TOUR CIE Create Product", cls.income_account
        )
        cls.type_create = cls._create_export_type(
            "TOUR CIE Create Type",
            "TOURCIECR",
            cls.journal_create,
            cls.product_create,
        )
        cls.partner_create = cls.env["res.partner"].create(
            {"name": "TOUR CIE Create Partner"}
        )
        cls.invoice_create = cls._create_invoice(
            cls.partner_create,
            cls.journal_create,
            cls.product_create,
            "2026-01-10",
        )

        # -- edit: two invoices on different dates so narrowing Date
        # Start and re-Populating provably drops the earlier one.
        cls.journal_edit = cls._create_sale_journal("TOUR CIE Edit Journal", "TCIED")
        cls.product_edit = cls._create_product(
            "TOUR CIE Edit Product", cls.income_account
        )
        cls.type_edit = cls._create_export_type(
            "TOUR CIE Edit Type", "TOURCIEED", cls.journal_edit, cls.product_edit
        )
        cls.partner_edit_early = cls.env["res.partner"].create(
            {"name": "TOUR CIE Edit Early Partner"}
        )
        cls.partner_edit_late = cls.env["res.partner"].create(
            {"name": "TOUR CIE Edit Late Partner"}
        )
        cls.invoice_edit_early = cls._create_invoice(
            cls.partner_edit_early,
            cls.journal_edit,
            cls.product_edit,
            "2026-01-05",
        )
        cls.invoice_edit_late = cls._create_invoice(
            cls.partner_edit_late,
            cls.journal_edit,
            cls.product_edit,
            "2026-02-15",
        )
        cls.export_edit = cls.env["customer_invoice_export"].create(
            {
                "type_id": cls.type_edit.id,
                "date": "2026-03-01",
                "output_format": "csv",
            }
        )
        # Baseline Populate with no date range -- both invoices qualify,
        # so the edit tour's narrower Date Start has a row to drop.
        cls.export_edit.action_populate()

        # -- delete: plain draft record, no invoice data needed.
        cls.type_delete = cls.env["customer_invoice_export_type"].create(
            {"name": "TOUR CIE Delete Type", "code": "TOURCIEDL"}
        )
        cls.export_delete = cls.env["customer_invoice_export"].create(
            {
                "type_id": cls.type_delete.id,
                "date": "2026-03-01",
                "output_format": "csv",
            }
        )

        # -- confirm: plain draft record, no invoice data needed.
        cls.type_confirm = cls.env["customer_invoice_export_type"].create(
            {"name": "TOUR CIE Confirm Type", "code": "TOURCIECF"}
        )
        cls.export_confirm = cls.env["customer_invoice_export"].create(
            {
                "type_id": cls.type_confirm.id,
                "date": "2026-03-01",
                "output_format": "csv",
            }
        )

        # -- approve/reject: pre-confirmed into Waiting for Approval.
        # ``bypass_policy_check`` skips the confirm_ok evaluation only --
        # it still creates real approval records from the production
        # approval.template, so the tour's own Approve/Reject click
        # below is exercised against a genuine pending approval level.
        cls.type_approve = cls.env["customer_invoice_export_type"].create(
            {"name": "TOUR CIE Approve Type", "code": "TOURCIEAP"}
        )
        cls.export_approve = cls.env["customer_invoice_export"].create(
            {
                "type_id": cls.type_approve.id,
                "date": "2026-03-01",
                "output_format": "csv",
            }
        )
        cls.export_approve.with_context(bypass_policy_check=True).action_confirm()

        cls.type_reject = cls.env["customer_invoice_export_type"].create(
            {"name": "TOUR CIE Reject Type", "code": "TOURCIERJ"}
        )
        cls.export_reject = cls.env["customer_invoice_export"].create(
            {
                "type_id": cls.type_reject.id,
                "date": "2026-03-01",
                "output_format": "csv",
            }
        )
        cls.export_reject.with_context(bypass_policy_check=True).action_confirm()

    @classmethod
    def _get_income_account(cls):
        """Return an existing revenue account, creating one if needed.

        :return: an ``account.account`` recordset.
        :rtype: recordset
        """
        account_type = cls.env.ref("account.data_account_type_revenue")
        account = cls.env["account.account"].search(
            [
                ("user_type_id", "=", account_type.id),
                ("company_id", "=", cls.env.company.id),
            ],
            limit=1,
        )
        if not account:
            account = cls.env["account.account"].create(
                {
                    "name": "TOUR CIE Income Account",
                    "code": "TOURCIEINC",
                    "user_type_id": account_type.id,
                    "company_id": cls.env.company.id,
                }
            )
        return account

    @classmethod
    def _create_sale_journal(cls, name, code):
        """Create a dedicated sale journal for one tour scenario.

        A dedicated journal (rather than a shared/demo one) keeps
        Populate's result scoped to this scenario's own fixture
        invoice(s).

        :param name: journal name.
        :param code: journal code.
        :return: an ``account.journal`` recordset.
        :rtype: recordset
        """
        return cls.env["account.journal"].create(
            {"name": name, "type": "sale", "code": code}
        )

    @classmethod
    def _create_product(cls, name, income_account):
        """Create a service product posting to ``income_account``.

        :param name: product name.
        :param income_account: ``account.account`` recordset used as
            the product's income account.
        :return: a ``product.product`` recordset.
        :rtype: recordset
        """
        return cls.env["product.product"].create(
            {
                "name": name,
                "type": "service",
                "property_account_income_id": income_account.id,
            }
        )

    @classmethod
    def _create_export_type(cls, name, code, journal, product):
        """Create a ``customer_invoice_export_type`` scoped to one
        journal and one product.

        :param name: type name.
        :param code: type code.
        :param journal: allowed ``account.journal`` recordset.
        :param product: allowed ``product.product`` recordset.
        :return: a ``customer_invoice_export_type`` recordset.
        :rtype: recordset
        """
        return cls.env["customer_invoice_export_type"].create(
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

    @classmethod
    def _create_invoice(cls, partner, journal, product, invoice_date):
        """Create and post an unpaid customer invoice.

        :param partner: ``res.partner`` recordset (the customer).
        :param journal: ``account.journal`` recordset.
        :param product: ``product.product`` recordset for the single
            invoice line.
        :param invoice_date: invoice date, ``"YYYY-MM-DD"``.
        :return: the posted ``account.move`` recordset.
        :rtype: recordset
        """
        move = cls.env["account.move"].create(
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
