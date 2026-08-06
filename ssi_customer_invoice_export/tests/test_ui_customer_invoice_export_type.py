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

    def setUp(self):
        """Grant the type group and create the fixtures the tours edit.

        ``HttpCase`` (via ``TransactionCase``) only exposes ``self.env`` per
        test method -- unlike ``SavepointCase``, it has no ``cls.env`` at
        ``setUpClass`` time -- so Pre-Condition data is prepared here
        instead. The menu is gated by
        ``customer_invoice_export_type_group``; the group's security data
        already includes ``base.user_admin``, but the grant is repeated
        explicitly here so the tour keeps working even if that default
        membership changes. ``code`` is left as ``"/"`` on every fixture
        (per Flow step 3 of ``docs/customer_invoice_export_type/01-create.md``)
        so the Generate Code inline action has something to do in the edit
        tour too, and so several fixtures can share it without violating
        the unique-code constraint
        (``mixin.master_data._check_duplicate_code`` excludes
        ``code == "/"`` from the duplicate check).
        """
        super().setUp()
        self.env.ref(
            "ssi_customer_invoice_export.customer_invoice_export_type_group"
        ).sudo().write({"users": [(4, self.env.ref("base.user_admin").id)]})
        self._create_type_sequence_template()

        self.type_edit = self._create_type("TOUR CIET Edit")
        self.type_delete = self._create_type("TOUR CIET Delete")
        self.type_deactivate = self._create_type("TOUR CIET Deactivate")
        self.type_activate = self._create_type("TOUR CIET Activate", active=False)

    def _create_type_sequence_template(self):
        """Create a test-only ``sequence.template`` for the Generate Code
        button.

        Production data ships a ``sequence.template`` only for the
        transactional ``customer_invoice_export`` document
        (``sequence_template/customer_invoice_export.xml``) -- there is
        none for ``customer_invoice_export_type``, so the header's
        Generate Code button (``action_generate_code``, an Inline Action
        of the create/edit tours per this module's Keputusan Desain)
        always raises "No sequence template found" as shipped. This
        fixture is created here, at the test-transaction level only (like
        every other fixture in this ``setUp``, rolled back after each test
        method), by explicit user decision on
        open-synergy/ssi-customer-invoice-export#22: it makes the tours
        exercise the button without changing production data/behaviour --
        end users still need a real ``sequence.template`` added separately
        before Generate Code works for them.
        """
        model = self.env["ir.model"]._get("customer_invoice_export_type")
        code_field = self.env["ir.model.fields"]._get(
            "customer_invoice_export_type", "code"
        )
        date_field = self.env["ir.model.fields"]._get(
            "customer_invoice_export_type", "create_date"
        )
        sequence = self.env["ir.sequence"].create(
            {
                "name": "TOUR Customer Invoice Export Type Sequence",
                "code": "tour.customer_invoice_export_type",
                "prefix": "TOURCIET",
                "padding": 4,
            }
        )
        self.env["sequence.template"].create(
            {
                "name": "TOUR Customer Invoice Export Type",
                "model_id": model.id,
                "sequence_field_id": code_field.id,
                "date_field_id": date_field.id,
                "computation_method": "use_python",
                "python_code": "result = True",
                "sequence_selection_method": "use_sequence",
                "sequence_id": sequence.id,
            }
        )

    def _create_type(self, name, active=True):
        """Pre-Condition helper: create a ``customer_invoice_export_type``.

        :param name: unique record name the tour locates via ``:contains``.
        :param active: initial value of the ``active`` field.
        :return: the created ``customer_invoice_export_type`` record.
        """
        return self.env["customer_invoice_export_type"].create(
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
