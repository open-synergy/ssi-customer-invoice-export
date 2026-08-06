# Copyright 2026 OpenSynergy Indonesia
# Copyright 2026 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests import HttpCase, tagged


@tagged("post_install", "-at_install")
class TestUiCustomerInvoiceExportType(HttpCase):
    """UI/UX tour tests for ``customer_invoice_export_type``.

    Every ``test_*`` method below runs the tour pairing with the IK file
    named in its docstring (``docs/customer_invoice_export_type/NN-*.md``).
    Pre-Condition data required by each IK is prepared here in Python --
    never through UI steps.
    """

    @classmethod
    def setUpClass(cls):
        """Grant the type group and create the fixtures the tours edit.

        The menu is gated by ``customer_invoice_export_type_group``; the
        group's security data already includes ``base.user_admin``, but the
        grant is repeated explicitly here so the tour keeps working even if
        that default membership changes. ``code`` is left as ``"/"`` on
        every fixture (per Flow step 3 of
        ``docs/customer_invoice_export_type/01-create.md``) so the Generate
        Code inline action has something to do in the edit tour too, and so
        several fixtures can share it without violating the unique-code
        constraint (``mixin.master_data._check_duplicate_code`` excludes
        ``code == "/"`` from the duplicate check).
        """
        super().setUpClass()
        cls.env.ref(
            "ssi_customer_invoice_export.customer_invoice_export_type_group"
        ).sudo().write({"users": [(4, cls.env.ref("base.user_admin").id)]})

        cls.type_edit = cls._create_type("TOUR CIET Edit")
        cls.type_delete = cls._create_type("TOUR CIET Delete")
        cls.type_deactivate = cls._create_type("TOUR CIET Deactivate")
        cls.type_activate = cls._create_type("TOUR CIET Activate", active=False)

    @classmethod
    def _create_type(cls, name, active=True):
        """Pre-Condition helper: create a ``customer_invoice_export_type``.

        :param name: unique record name the tour locates via ``:contains``.
        :param active: initial value of the ``active`` field.
        :return: the created ``customer_invoice_export_type`` record.
        """
        return cls.env["customer_invoice_export_type"].create(
            {
                "name": name,
                "code": "/",
                "active": active,
            }
        )

    def test_create(self):
        """Run the create tour for ``customer_invoice_export_type``.

        IK: docs/customer_invoice_export_type/01-create.md
        """
        self.start_tour(
            "/web", "ssi_customer_invoice_export_type_create", login="admin"
        )

    def test_edit(self):
        """Run the edit tour for ``customer_invoice_export_type``.

        IK: docs/customer_invoice_export_type/02-edit.md
        """
        self.start_tour("/web", "ssi_customer_invoice_export_type_edit", login="admin")

    def test_delete(self):
        """Run the delete tour for ``customer_invoice_export_type``.

        IK: docs/customer_invoice_export_type/03-delete.md
        """
        self.start_tour(
            "/web", "ssi_customer_invoice_export_type_delete", login="admin"
        )

    def test_deactivate(self):
        """Run the deactivate tour for ``customer_invoice_export_type``.

        IK: docs/customer_invoice_export_type/04-deactivate.md
        """
        self.start_tour(
            "/web", "ssi_customer_invoice_export_type_deactivate", login="admin"
        )

    def test_activate(self):
        """Run the activate tour for ``customer_invoice_export_type``.

        IK: docs/customer_invoice_export_type/05-activate.md
        """
        self.start_tour(
            "/web", "ssi_customer_invoice_export_type_activate", login="admin"
        )
