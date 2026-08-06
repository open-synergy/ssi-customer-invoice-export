# Copyright 2026 OpenSynergy Indonesia
# Copyright 2026 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests import HttpCase, tagged


@tagged("post_install", "-at_install")
class TestUiCustomerInvoiceExportOperatingUnit(HttpCase):
    """UI/UX tour test for the Operating Unit delta on the document.

    The single ``test_*`` method below runs the tour pairing with the IK
    delta file named in its docstring
    (``docs/customer_invoice_export/01-create.md`` of this module). Only
    the Operating Unit field is exercised -- the base module's create
    Flow (Type, Date, Populate, Save, ...) is out of this tour's scope,
    per this module's Keputusan Desain.
    """

    def setUp(self):
        """Grant the OU groups and create the fixtures the tour selects.

        ``HttpCase`` (via ``TransactionCase``) only exposes ``self.env``
        per test method -- unlike ``SavepointCase``, it has no
        ``cls.env`` at ``setUpClass`` time (``odoo/tests/common.py``) --
        so Pre-Condition data is prepared here instead, mirroring
        ``ssi_customer_invoice_export``'s
        ``test_ui_customer_invoice_export_type.py``. The tour user needs
        both ``operating_unit.group_multi_operating_unit`` (renders the
        Operating Unit field) and this module's
        ``customer_invoice_export_ou_group`` (the data-ownership group
        the field's ir.rule checks) -- the grant is repeated explicitly
        here so the tour keeps working even if incidental default
        membership from another module changes.
        """
        super().setUp()
        admin = self.env.ref("base.user_admin")
        groups = self.env.ref(
            "operating_unit.group_multi_operating_unit"
        ) + self.env.ref(
            "ssi_customer_invoice_export_operating_unit"
            ".customer_invoice_export_ou_group"
        )
        groups.sudo().write({"users": [(4, admin.id)]})

        self.operating_unit = self._create_operating_unit("TOUR CIEOU Create")
        self._create_type("TOUR CIEOU Create Type")

    def _create_operating_unit(self, name):
        """Pre-Condition helper: create an ``operating.unit``.

        :param name: unique record name the tour locates via
            ``:contains``.
        :return: the created ``operating.unit`` record.
        """
        partner = self.env["res.partner"].create({"name": name + " Partner"})
        return self.env["operating.unit"].create(
            {
                "name": name,
                "code": "TOURCIEOU",
                "partner_id": partner.id,
                "company_id": self.env.company.id,
            }
        )

    def _create_type(self, name):
        """Pre-Condition helper: create an active export type record.

        Only its existence is required (base Pre-Condition "At least one
        active Customer Invoice Export Type exists.") -- the tour never
        selects it, so every other field is left at its model default.

        :param name: unique record name, unused by the tour itself.
        :return: the created ``customer_invoice_export_type`` record.
        """
        return self.env["customer_invoice_export_type"].create(
            {
                "name": name,
                "code": "/",
                "active": True,
            }
        )

    def test_create(self):
        """Run the Operating Unit delta create tour.

        IK: docs/customer_invoice_export/01-create.md
        """
        self.start_tour(
            "/web",
            "ssi_customer_invoice_export_operating_unit_create",
            login="admin",
        )
