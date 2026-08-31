# Copyright 2026 OpenSynergy Indonesia
# Copyright 2026 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests import tagged
from odoo.tests.common import HttpSavepointCase


@tagged("post_install", "-at_install")
class TestUiCustomerInvoiceExport(HttpSavepointCase):
    """UI/UX tour tests for ``customer_invoice_export``.

    Every ``test_*`` method below runs the tour pairing with the IK file
    named in its docstring (``docs/customer_invoice_export/NN-*.md``).
    Pre-Condition data required by each IK is prepared here in Python --
    never through UI steps. Fixtures are built in instance-level
    ``setUp`` (rolled back after each test method), matching the
    structure already used in
    ``test_ui_customer_invoice_export_type.py``, this module.
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

        # -- cancel: plain draft record. The Cancellation Reason is a
        # global one (``global_use``), so it does not need to be linked
        # to this model through ``ir.model`` to appear in the wizard.
        self.cancel_reason = self.env["base.cancel_reason"].create(
            {
                "name": "TOUR CIE Cancel Reason",
                "code": "TOURCIECN",
                "global_use": True,
            }
        )
        self.type_cancel = self.env["customer_invoice_export_type"].create(
            {"name": "TOUR CIE Cancel Type", "code": "TOURCIECNT"}
        )
        self.export_cancel = (
            self.env["customer_invoice_export"]
            .with_user(self.admin)
            .create(
                {
                    "type_id": self.type_cancel.id,
                    "date": "2026-03-01",
                    "output_format": "csv",
                }
            )
        )

        # -- restart: cancelled record, reached through action_cancel so
        # the Cancellation Reason is stored exactly as the Select Cancel
        # Reason wizard exercised by the cancel tour above would store
        # it.
        self.type_restart = self.env["customer_invoice_export_type"].create(
            {"name": "TOUR CIE Redraft Type", "code": "TOURCIERT"}
        )
        self.export_restart = (
            self.env["customer_invoice_export"]
            .with_user(self.admin)
            .create(
                {
                    "type_id": self.type_restart.id,
                    "date": "2026-03-01",
                    "output_format": "csv",
                }
            )
        )
        self.export_restart.with_context(bypass_policy_check=True).action_cancel(
            self.cancel_reason
        )

        # -- reset document number: draft record carrying a manually
        # assigned number, so the reset is observable at all -- an
        # untouched draft already carries "/" (rendered by name_get as
        # "*<id>"), and resetting it would leave the title unchanged.
        self.type_reset_number = self.env["customer_invoice_export_type"].create(
            {"name": "TOUR CIE Reset Number Type", "code": "TOURCIERN"}
        )
        self.export_reset_number = (
            self.env["customer_invoice_export"]
            .with_user(self.admin)
            .create(
                {
                    "type_id": self.type_reset_number.id,
                    "date": "2026-03-01",
                    "output_format": "csv",
                }
            )
        )
        self.export_reset_number.write({"name": "TOURCIE-RESET-0001"})

        # -- restart approval process: a document stuck in Waiting for
        # Approval without an approval template resolved. ``state`` is
        # written directly instead of calling ``action_confirm``,
        # because confirming resolves the module's own matching
        # approval.template -- writing the state directly reproduces the
        # stalled situation the IK describes, a document that reached
        # Waiting for Approval without ever getting a template resolved.
        self.type_restart_approval = self.env["customer_invoice_export_type"].create(
            {"name": "TOUR CIE Restart Approval Type", "code": "TOURCIERA"}
        )
        self.export_restart_approval = (
            self.env["customer_invoice_export"]
            .with_user(self.admin)
            .create(
                {
                    "type_id": self.type_restart_approval.id,
                    "date": "2026-03-01",
                    "output_format": "csv",
                }
            )
        )
        self.export_restart_approval.write({"state": "confirm"})

        # -- requeue / recompute queue done result: both IK files require
        # a document already in Queue To Done. It is reached through the
        # real action_confirm/action_approve_approval methods, called
        # ``with_user(self.admin)`` for the approval step so the
        # approval record actually matches admin as its approver (the
        # same production approval.template used by the approve tour
        # above) -- rather than by writing ``state`` directly, since
        # reaching Queue To Done this way also creates the To Done Queue
        # Job Batch and its queued job that both tours below depend on.
        self.type_requeue = self.env["customer_invoice_export_type"].create(
            {"name": "TOUR CIE Requeue Type", "code": "TOURCIERQ"}
        )
        self.export_requeue = (
            self.env["customer_invoice_export"]
            .with_user(self.admin)
            .create(
                {
                    "type_id": self.type_requeue.id,
                    "date": "2026-03-01",
                    "output_format": "csv",
                }
            )
        )
        self.export_requeue.with_context(bypass_policy_check=True).action_confirm()
        # action_confirm's own _check_confirm_policy() already reads
        # confirm_ok, which computes -- and caches -- every policy field
        # in the same pass (mixin.policy._compute_policy), approve_ok
        # included, while active_approver_user_ids is still empty (no
        # approval record exists yet). approve_ok has no @api.depends on
        # approval_ids, so without this invalidate_cache() the stale
        # False value would still be served after action_request_approval
        # creates the approval record below, and action_approve_approval
        # would refuse admin as an approver.
        self.export_requeue.invalidate_cache()
        self.export_requeue.with_user(self.admin).action_approve_approval()

        self.type_recompute = self.env["customer_invoice_export_type"].create(
            {"name": "TOUR CIE Recompute Type", "code": "TOURCIERC"}
        )
        self.export_recompute = (
            self.env["customer_invoice_export"]
            .with_user(self.admin)
            .create(
                {
                    "type_id": self.type_recompute.id,
                    "date": "2026-03-01",
                    "output_format": "csv",
                }
            )
        )
        self.export_recompute.with_context(bypass_policy_check=True).action_confirm()
        # See the matching invalidate_cache() call for export_requeue
        # above -- the same stale approve_ok caching applies here.
        self.export_recompute.invalidate_cache()
        self.export_recompute.with_user(self.admin).action_approve_approval()
        # Mark the queued job itself Done, without touching the batch's
        # own "state" field here, so the tour's own Recompute click is
        # what transitions the batch (and this document) the rest of the
        # way -- not this setUp. Writing the batch's "state" directly
        # instead would flip this document's own
        # "done_queue_job_batch_state" (a stored related field) to
        # "Finished" immediately, which the module's own
        # base.automation (docs/customer_invoice_export/
        # 16-recompute-queue-done-result.md Pre-Condition) would then
        # pick up before the tour ever runs, reaching Done here in
        # setUp instead of through the button under test.
        self.export_recompute.done_queue_job_batch_id.job_ids.write({"state": "done"})

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

        Sets both ``invoice_date`` and ``date`` to ``invoice_date``.
        ORM ``create()`` never derives ``date`` from ``invoice_date``
        (only the web client onchange does), so it defaults to today's
        date unless set explicitly -- and the Populate date range
        (``date_start``/``date_end``) filters on ``date``, not
        ``invoice_date`` (issue #38). The edit tour's Flow 3 depends on
        ``invoice_edit_early``/``invoice_edit_late`` carrying distinct,
        deliberate dates for narrowing Date Start to provably drop one
        of them -- leaving ``date`` unset would make both default to
        today and defeat that distinction.

        :param partner: ``res.partner`` recordset (the customer).
        :param journal: ``account.journal`` recordset.
        :param product: ``product.product`` recordset for the single
            invoice line.
        :param invoice_date: invoice date, ``"YYYY-MM-DD"``, also used
            as ``date``.
        :return: the posted ``account.move`` recordset.
        :rtype: recordset
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

    def test_cancel(self):
        """Run the cancel tour for ``customer_invoice_export``.

        IK: docs/customer_invoice_export/10-cancel.md
        """
        self.start_tour("/web", "ssi_customer_invoice_export_cancel", login="admin")

    def test_restart(self):
        """Run the restart tour for ``customer_invoice_export``.

        IK: docs/customer_invoice_export/12-restart.md
        """
        self.start_tour("/web", "ssi_customer_invoice_export_restart", login="admin")

    def test_reset_number(self):
        """Run the reset document number tour for ``customer_invoice_export``.

        IK: docs/customer_invoice_export/13-reset-number.md
        """
        self.start_tour(
            "/web", "ssi_customer_invoice_export_reset_number", login="admin"
        )

    def test_restart_approval(self):
        """Run the restart approval process tour for ``customer_invoice_export``.

        IK: docs/customer_invoice_export/14-restart-approval.md
        """
        self.start_tour(
            "/web", "ssi_customer_invoice_export_restart_approval", login="admin"
        )

    def test_requeue(self):
        """Run the requeue tour for ``customer_invoice_export``.

        IK: docs/customer_invoice_export/15-requeue.md
        """
        self.start_tour("/web", "ssi_customer_invoice_export_requeue", login="admin")

    def test_recompute_queue_done_result(self):
        """Run the recompute queue done result tour for ``customer_invoice_export``.

        IK: docs/customer_invoice_export/16-recompute-queue-done-result.md
        """
        self.start_tour(
            "/web",
            "ssi_customer_invoice_export_recompute_queue_done_result",
            login="admin",
        )
