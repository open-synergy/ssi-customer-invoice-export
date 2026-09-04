# Copyright 2026 OpenSynergy Indonesia
# Copyright 2026 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64
import csv
import io

import openpyxl

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools.safe_eval import safe_eval

from odoo.addons.ssi_decorator import ssi_decorator

OUTPUT_FORMAT_EXTENSION = {
    "csv": "csv",
    "xlsx": "xlsx",
    "txt": "txt",
}


class CustomerInvoiceExport(models.Model):  # pylint: disable=too-few-public-methods
    """
    Represents a document that selects a set of unpaid customer invoices
    (limited to the journals allowed by its Type and, optionally, to a
    date range), keeps only the invoice lines matching the Type's product
    criteria, and builds one summary row per export file row -- one row
    per qualifying invoice or one row per partner, depending on the
    Type's Grouping Method. On completion the document generates a
    CSV/XLSX/TXT file -- via the Type's Python parser code -- for upload
    to a banking service.

    Lifecycle: draft -> confirm -> queue_done -> done
    Cancellation: any non-done state -> cancel
    """

    _name = "customer_invoice_export"
    _description = "Customer Invoice Export"
    _inherit = [
        "mixin.transaction_cancel",
        "mixin.transaction_queue_done",
        "mixin.transaction_confirm",
        "mixin.many2one_configurator",
    ]

    # Multiple Approval Attribute
    _approval_from_state = "draft"
    _approval_to_state = "action_queue_done"
    _approval_state = "confirm"
    _after_approved_method = "action_queue_done"

    # View auto-insert attributes
    _automatically_insert_view_element = True
    _automatically_insert_multiple_approval_page = True
    _automatically_insert_done_policy_fields = False
    _automatically_insert_done_button = False
    _queue_processing_create_page = True
    _automatically_insert_queue_done_button = False

    _queue_to_done_insert_form_element_ok = True
    _queue_to_done_form_xpath = "//group[@name='queue_processing']"

    _statusbar_visible_label = "draft,confirm,queue_done,done"

    _policy_field_order = [
        "confirm_ok",
        "approve_ok",
        "reject_ok",
        "restart_approval_ok",
        "cancel_ok",
        "restart_ok",
        "done_ok",
        "queue_done_ok",
        "manual_number_ok",
    ]
    _header_button_order = [
        "action_confirm",
        "action_approve_approval",
        "action_reject_approval",
        "%(ssi_transaction_cancel_mixin.base_select_cancel_reason_action)d",
        "action_restart",
    ]

    # Attributes related to add element on search view automatically
    _state_filter_order = [
        "dom_draft",
        "dom_confirm",
        "dom_reject",
        "dom_queue_done",
        "dom_done",
        "dom_cancel",
    ]

    # Sequence attribute
    _create_sequence_state = "done"

    date = fields.Date(
        string="Date",
        required=True,
        default=lambda self: fields.Date.today(),
        readonly=True,
        states={"draft": [("readonly", False)]},
        help="Date of this export document.",
    )
    type_id = fields.Many2one(
        string="Type",
        comodel_name="customer_invoice_export_type",
        required=True,
        ondelete="restrict",
        readonly=True,
        states={"draft": [("readonly", False)]},
        help=(
            "Export type that determines the journal and product criteria, "
            "the parser code, and the default output format for this "
            "document."
        ),
    )
    date_start = fields.Date(
        string="Date Start",
        readonly=True,
        states={"draft": [("readonly", False)]},
        help=(
            "Lower bound (inclusive) on the accounting date (account.move "
            "'date') used to auto-select invoices. Leave empty together "
            "with Date End to select invoices regardless of date."
        ),
    )
    date_end = fields.Date(
        string="Date End",
        readonly=True,
        states={"draft": [("readonly", False)]},
        help=(
            "Upper bound (inclusive) on the accounting date (account.move "
            "'date') used to auto-select invoices. Leave empty together "
            "with Date Start to select invoices regardless of date."
        ),
    )
    output_format = fields.Selection(
        string="Output Format",
        selection=[
            ("csv", "CSV"),
            ("xlsx", "XLSX"),
            ("txt", "TXT"),
        ],
        required=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
        help="File format generated when this document is queued to done.",
    )
    allowed_journal_ids = fields.Many2many(
        string="Allowed Journals",
        comodel_name="account.journal",
        compute="_compute_allowed_journal_ids",
        store=False,
        compute_sudo=True,
        help="Journals allowed to be selected, as configured on the Type.",
    )
    allowed_partner_ids = fields.Many2many(
        string="Allowed Partners",
        comodel_name="res.partner",
        compute="_compute_allowed_partner_ids",
        store=False,
        compute_sudo=True,
        help="Partners allowed to be selected, as configured on the Type.",
    )
    allowed_product_ids = fields.Many2many(
        string="Allowed Products",
        comodel_name="product.product",
        compute="_compute_allowed_product_ids",
        store=False,
        compute_sudo=True,
        help="Products allowed to be selected, as configured on the Type.",
    )
    allowed_receivable_account_ids = fields.Many2many(
        string="Allowed Receivable Accounts",
        comodel_name="account.account",
        compute="_compute_allowed_receivable_account_ids",
        store=False,
        compute_sudo=True,
        help=(
            "Accounts treated as receivable when reading the outstanding "
            "amount of the selected invoices, as configured on the Type."
        ),
    )
    move_ids = fields.Many2many(
        string="Invoices",
        comodel_name="account.move",
        relation="rel_cust_inv_export_2_move",
        column1="export_id",
        column2="move_id",
        readonly=True,
        states={"draft": [("readonly", False)]},
        help=(
            "Customer invoices in scope of this export. Automatically "
            "filled by the Populate button; can be manually adjusted while "
            "in Draft."
        ),
    )
    source_move_ids = fields.Many2many(
        string="Source Invoices",
        comodel_name="account.move",
        relation="rel_cust_inv_export_2_source_move",
        column1="export_id",
        column2="move_id",
        readonly=True,
        copy=False,
        help=(
            "Set by a glue module to point this document directly at the "
            "exact moves it must export, bypassing the standard "
            "invoice-shaped criteria (move type, payment state, journal, "
            "partner) applied by the Populate button when this field is "
            "empty. Used for source models whose moves are never shaped "
            "like a standard Odoo customer invoice (e.g. move_type "
            "'entry')."
        ),
    )
    line_ids = fields.Many2many(
        string="Invoice Lines",
        comodel_name="account.move.line",
        relation="rel_cust_inv_export_2_move_line",
        column1="export_id",
        column2="line_id",
        readonly=True,
        help=(
            "Invoice lines whose product matches the Type's product "
            "criteria. Derived by the Populate button."
        ),
    )
    summary_ids = fields.One2many(
        string="Summary",
        comodel_name="customer_invoice_export.summary",
        inverse_name="export_id",
        readonly=True,
        help=(
            "One row per export file row -- per invoice or per partner, "
            "depending on the Type's Grouping Method -- aggregating its "
            "qualifying lines. Derived by the Populate button; consumed "
            "by the Parser Python Code when generating the export file."
        ),
    )
    export_file = fields.Binary(
        string="Export File",
        readonly=True,
        copy=False,
        help="File generated from the Summary when this document is queued to done.",
    )
    export_filename = fields.Char(
        string="Export File Name",
        readonly=True,
        copy=False,
        help="File name of the generated Export File.",
    )

    @api.depends("type_id")
    def _compute_allowed_journal_ids(self):
        """Resolve the journals allowed by the document's Type.

        Delegates to the many2one configurator filter defined on
        ``type_id`` (selection method, manual recordset, domain, or
        Python code).
        """
        for record in self:
            result = False
            if record.type_id:
                result = record._m2o_configurator_get_filter(
                    object_name="account.journal",
                    method_selection=record.type_id.journal_selection_method,
                    manual_recordset=record.type_id.journal_ids,
                    domain=record.type_id.journal_domain,
                    python_code=record.type_id.journal_python_code,
                )
            record.allowed_journal_ids = result

    @api.depends("type_id")
    def _compute_allowed_partner_ids(self):
        """Resolve the partners allowed by the document's Type.

        Delegates to the many2one configurator filter defined on
        ``type_id`` (selection method, manual recordset, domain, or
        Python code).
        """
        for record in self:
            result = False
            if record.type_id:
                result = record._m2o_configurator_get_filter(
                    object_name="res.partner",
                    method_selection=record.type_id.partner_selection_method,
                    manual_recordset=record.type_id.partner_ids,
                    domain=record.type_id.partner_domain,
                    python_code=record.type_id.partner_python_code,
                )
            record.allowed_partner_ids = result

    @api.depends("type_id")
    def _compute_allowed_product_ids(self):
        """Resolve the products allowed by the document's Type.

        Delegates to the many2one configurator filter defined on
        ``type_id`` (selection method, manual recordset, domain, or
        Python code).
        """
        for record in self:
            result = False
            if record.type_id:
                result = record._m2o_configurator_get_filter(
                    object_name="product.product",
                    method_selection=record.type_id.product_selection_method,
                    manual_recordset=record.type_id.product_ids,
                    domain=record.type_id.product_domain,
                    python_code=record.type_id.product_python_code,
                )
            record.allowed_product_ids = result

    @api.depends("type_id")
    def _compute_allowed_receivable_account_ids(self):
        """Resolve the receivable accounts allowed by the document's Type.

        Delegates to the many2one configurator filter defined on
        ``type_id`` (selection method, manual recordset, domain, or
        Python code).
        """
        for record in self:
            result = False
            if record.type_id:
                result = record._m2o_configurator_get_filter(
                    object_name="account.account",
                    method_selection=(
                        record.type_id.receivable_account_selection_method
                    ),
                    manual_recordset=record.type_id.receivable_account_ids,
                    domain=record.type_id.receivable_account_domain,
                    python_code=record.type_id.receivable_account_python_code,
                )
            record.allowed_receivable_account_ids = result

    @api.onchange("type_id")
    def onchange_output_format(self):
        self.output_format = (
            self.type_id.default_output_format if self.type_id else False
        )

    # -------------------------------------------------------------------
    # Populate
    # -------------------------------------------------------------------

    def action_populate(self):
        """Populate the document with qualifying invoices and lines.

        Runs each record's ``_populate`` under ``sudo`` so users without
        direct access to ``account.move``/``account.move.line`` can still
        trigger the selection from the button.
        """
        for record in self.sudo():
            record._populate()

    def _populate(self):
        """Select qualifying invoices from the Type's search criteria.

        Searches ``account.move`` with ``_prepare_invoice_domain`` and
        replaces ``move_ids`` with the result. Does not rebuild
        ``line_ids``/``summary_ids`` itself: writing ``move_ids``
        triggers ``write()``, which calls ``_rederive_summary`` for
        this record.
        """
        self.ensure_one()
        moves = self.env["account.move"].search(self._prepare_invoice_domain())
        self.move_ids = [(6, 0, moves.ids)]

    def write(self, vals):
        """Rebuild Invoice Lines and Summary whenever Invoices changes.

        Runs ``super()`` first so ``move_ids`` already holds its new
        value, then rebuilds ``line_ids``/``summary_ids`` for every
        affected record under ``sudo()`` -- mirroring
        ``action_populate``'s own use of ``sudo()`` -- so a user
        without direct read access to ``account.move.line`` can still
        edit ``move_ids`` manually from the form. Triggered by any
        write touching ``move_ids``, including ``_populate`` itself, a
        manual edit of the Invoices list, and any import/``queue_job``/
        glue module that writes ``move_ids`` directly -- an
        ``@api.onchange`` would only cover the web form. No recursion:
        ``_rederive_summary`` only ever writes ``line_ids`` and
        ``summary_ids``, neither of which is ``move_ids``.

        :param vals: field values to write
        :return: the value returned by ``super().write()``
        :rtype: bool
        """
        result = super().write(vals)
        if "move_ids" in vals:
            for record in self:
                record.sudo()._rederive_summary()
        return result

    def _rederive_summary(self):
        """Rebuild Invoice Lines and Summary from the current Invoices.

        Reads ``self.move_ids`` (not a fresh search), keeps only the
        lines matching the Type's product criteria
        (``_get_qualifying_lines``), groups them per
        ``_get_summary_grouping_key``, and replaces ``line_ids``/
        ``summary_ids`` with one summary row per group. Called by
        ``write()`` whenever ``move_ids`` changes, so its result stays
        in sync with the current Invoices regardless of whether they
        were set by Populate or edited manually.
        """
        self.ensure_one()
        moves = self.move_ids

        qualifying_by_move = {}
        all_qualifying_ids = []
        for move in moves:
            qualifying = self._get_qualifying_lines(move)
            if qualifying:
                qualifying_by_move[move.id] = qualifying
                all_qualifying_ids += qualifying.ids
        self.line_ids = [(6, 0, all_qualifying_ids)]

        self.summary_ids.unlink()
        groups = {}
        for move in moves:
            qualifying = qualifying_by_move.get(move.id)
            if not qualifying:
                continue
            key = self._get_summary_grouping_key(move)
            if key not in groups:
                groups[key] = {
                    "moves": self.env["account.move"],
                    "lines": self.env["account.move.line"],
                }
            groups[key]["moves"] |= move
            groups[key]["lines"] |= qualifying

        sequence = 5
        summary_vals = []
        for group in groups.values():
            summary_vals.append(
                self._prepare_summary_data(group["moves"], group["lines"], sequence)
            )
            sequence += 5
        if summary_vals:
            self.env["customer_invoice_export.summary"].create(summary_vals)

    def _get_summary_grouping_key(self, move):
        """Key deciding which moves share one export row.

        Override in a glue module to group by another criterion.
        """
        self.ensure_one()
        if self.type_id.grouping_method == "partner":
            return ("partner", move.partner_id.id)
        return ("move", move.id)

    def _prepare_invoice_domain(self):
        """Build the search domain used by ``_populate`` to select moves.

        When ``source_move_ids`` is set, the caller (typically a glue
        module) already knows exactly which moves to export, so this
        method returns a full replacement domain restricted to those
        moves -- it does not delegate to ``super()`` on this branch,
        because the standard invoice-shaped criteria (move type, payment
        state, journal, partner) do not apply to non-invoice moves. When
        ``source_move_ids`` is empty, the standard criteria defined by
        ``super()`` apply unchanged.

        :return: an Odoo domain (list of tuples) for ``account.move``
        :rtype: list
        """
        self.ensure_one()
        if self.source_move_ids:
            domain = [
                ("id", "in", self.source_move_ids.ids),
                ("state", "=", "posted"),
            ]
        else:
            domain = [
                ("move_type", "=", "out_invoice"),
                ("state", "=", "posted"),
                ("payment_state", "in", ("not_paid", "partial")),
                ("journal_id", "in", self.allowed_journal_ids.ids),
                ("partner_id", "in", self.allowed_partner_ids.ids),
            ]
        if self.date_start:
            domain.append(("date", ">=", self.date_start))
        if self.date_end:
            domain.append(("date", "<=", self.date_end))
        return domain

    def _get_qualifying_lines(self, move):
        """Filter ``move``'s invoice lines by the Type's product criteria.

        Excludes display lines (section/note) and keeps only lines whose
        product is in ``allowed_product_ids``.

        :param move: an ``account.move`` record
        :return: an ``account.move.line`` recordset
        """
        self.ensure_one()
        return move.invoice_line_ids.filtered(
            lambda line: not line.display_type
            and line.product_id in self.allowed_product_ids
        )

    def _prepare_summary_data(self, moves, qualifying_lines, sequence):
        """Build the ``customer_invoice_export.summary`` values for a group.

        Extension point: override in a glue module to add fields to the
        Summary row without touching ``_populate``.

        :param moves: the ``account.move`` records aggregated in this row
        :param qualifying_lines: their qualifying ``account.move.line``
        :param sequence: sequence number for the row's ordering
        :return: dict of ``customer_invoice_export.summary`` values
        """
        self.ensure_one()
        return {
            "export_id": self.id,
            "sequence": sequence,
            "move_ids": [(6, 0, moves.ids)],
            "partner_id": moves[0].partner_id.id,
            "currency_id": moves[0].currency_id.id,
            "line_ids": [(6, 0, qualifying_lines.ids)],
        }

    # -------------------------------------------------------------------
    # Queue-to-done: generate export file
    # -------------------------------------------------------------------

    @ssi_decorator.post_queue_done_action()
    def _01_generate_export_on_queue_done(self):
        """Queue ``_generate_export_file`` when reaching ``queue_done``.

        Runs asynchronously via ``queue_job`` so file rendering (and any
        slow parser code) does not block the state transition.
        """
        self.ensure_one()
        description = "Generate export file for %s" % (self.name or self.id)
        self.with_context(job_batch=self.done_queue_job_batch_id).with_delay(
            description=_(description)
        )._generate_export_file()

    def _generate_export_file(self):
        """Render the export file from ``summary_ids`` and store it.

        Runs the Type's parser code (``_run_parser``), renders it to the
        document's Output Format (``_render_output``), writes the result
        to ``export_file``/``export_filename``, and creates a matching
        attachment. Idempotent: does nothing if ``export_file`` is
        already set.

        :raises UserError: if there are no Summary rows to export
        """
        self.ensure_one()
        if self.export_file:
            return

        if not self.summary_ids:
            error_message = """
Context: Generating customer invoice export file
Database ID: %s
Problem: No summary rows to export
Solution: Populate the document with qualifying invoices before queueing to done
""" % (
                self.id,
            )
            raise UserError(_(error_message))

        rows = self._run_parser()
        output = self._render_output(rows)
        filename = self._build_export_filename()
        self.write(
            {
                "export_file": base64.b64encode(output),
                "export_filename": filename,
            }
        )
        self._create_export_attachment(output, filename)

    def _run_parser(self):
        """Execute the Type's Parser Python Code and return its rows.

        Runs ``ptype.parser_python_code`` through ``safe_eval`` with a
        localdict exposing ``env``, ``document`` (self), ``summary_ids``,
        ``move_ids``, ``line_ids``, and an output variable ``result``
        that the code must assign a list of rows to.

        :return: list of rows produced by the parser code
        :raises UserError: if the code raises, or does not assign a
            list to ``result``
        """
        self.ensure_one()
        ptype = self.type_id
        localdict = {
            "env": self.env,
            "document": self,
            "summary_ids": self.summary_ids,
            "move_ids": self.move_ids,
            "line_ids": self.line_ids,
            "result": [],
        }
        try:
            safe_eval(
                ptype.parser_python_code,
                localdict,
                mode="exec",
                nocopy=True,
            )
            result = localdict["result"]
        except Exception as error:
            error_message = """
Context: Running export parser code
Database ID: %s
Problem: Parser code raised an error: %s
Solution: Fix the Parser Python Code on Type '%s', then retry the queue job
""" % (
                self.id,
                error,
                ptype.display_name,
            )
            raise UserError(_(error_message)) from error

        if not isinstance(result, list):
            error_message = """
Context: Running export parser code
Database ID: %s
Problem: Parser code did not set `result` to a list of rows
Solution: Fix the Parser Python Code on Type '%s' to assign a list of rows to `result`
""" % (
                self.id,
                ptype.display_name,
            )
            raise UserError(_(error_message))

        return result

    def _render_output(self, rows):
        """Dispatch ``rows`` to the renderer for the document's format.

        :param rows: list of rows returned by ``_run_parser``
        :return: file content as ``bytes``
        """
        self.ensure_one()
        if self.output_format == "csv":
            return self._render_csv(rows)
        elif self.output_format == "xlsx":
            return self._render_xlsx(rows)
        return self._render_txt(rows)

    def _render_csv(self, rows):
        """Render ``rows`` as a CSV file using the Type's CSV settings.

        :param rows: list of rows returned by ``_run_parser``
        :return: CSV file content as ``bytes``
        """
        self.ensure_one()
        ptype = self.type_id
        buffer = io.StringIO()
        writer = csv.writer(
            buffer,
            delimiter=ptype._get_csv_delimiter_character(),
            quotechar=ptype.csv_quotechar or '"',
        )
        writer.writerows(rows)
        return buffer.getvalue().encode(ptype.file_encoding or "utf-8")

    def _render_xlsx(self, rows):
        """Render ``rows`` as an XLSX file using the Type's sheet name.

        :param rows: list of rows returned by ``_run_parser``
        :return: XLSX file content as ``bytes``
        """
        self.ensure_one()
        ptype = self.type_id
        workbook = openpyxl.Workbook()
        sheet = workbook.active
        sheet.title = ptype.xlsx_sheet_name or "Sheet1"
        for row in rows:
            sheet.append(list(row))
        buffer = io.BytesIO()
        workbook.save(buffer)
        return buffer.getvalue()

    def _render_txt(self, rows):
        """Render ``rows`` as a delimited text file.

        Joins each row's cells with the Type's Field Separator and each
        row with a newline.

        :param rows: list of rows returned by ``_run_parser``
        :return: text file content as ``bytes``
        """
        self.ensure_one()
        ptype = self.type_id
        separator = ptype.txt_field_separator or ""
        lines = [separator.join(str(cell) for cell in row) for row in rows]
        return "\n".join(lines).encode(ptype.file_encoding or "utf-8")

    def _build_export_filename(self):
        """Build the export file name from the document Name and format.

        Falls back to ``export_<id>`` when the document has no Name yet
        (sequence not assigned).

        :return: file name including its extension
        :rtype: str
        """
        self.ensure_one()
        extension = OUTPUT_FORMAT_EXTENSION.get(self.output_format, "csv")
        base = self.name if self.name and self.name != "/" else "export_%s" % self.id
        return "%s.%s" % (base, extension)

    def _create_export_attachment(self, output, filename):
        """Create an ``ir.attachment`` holding the generated export file.

        :param output: file content as ``bytes``
        :param filename: file name including its extension
        """
        self.ensure_one()
        self.env["ir.attachment"].create(
            self._prepare_export_attachment_data(output, filename)
        )

    def _prepare_export_attachment_data(self, output, filename):
        """Build the ``ir.attachment`` values for the generated file.

        Extension point: override in a glue module to add fields (e.g.
        a related document link) without touching
        ``_create_export_attachment``.

        :param output: file content as ``bytes``
        :param filename: file name including its extension
        :return: dict of ``ir.attachment`` values
        """
        self.ensure_one()
        return {
            "name": filename,
            "res_model": self._name,
            "res_id": self.id,
            "type": "binary",
            "datas": base64.b64encode(output),
        }

    # -------------------------------------------------------------------
    # Confirm gate: refuse stale Invoices/Summary
    # -------------------------------------------------------------------

    @ssi_decorator.pre_confirm_check()
    def _01_check_summary_matches_moves(self):
        """Refuse Confirm if Summary still references a dropped invoice.

        ``write()`` now keeps ``summary_ids`` in sync with ``move_ids``
        automatically, so this only ever fires for a document whose
        Invoices were edited before that consistency check existed.

        :raises UserError: when a Summary row references a move that
            is no longer in ``move_ids``
        """
        self.ensure_one()
        stray_moves = self.summary_ids.mapped("move_ids") - self.move_ids
        if stray_moves:
            error_message = """
Context: Confirming customer invoice export
Database ID: %s
Problem: Summary references invoice(s) not in Invoices: %s
Solution: Click Populate to rebuild Invoice Lines and Summary from the current Invoices
""" % (
                self.id,
                ", ".join(stray_moves.mapped("name")),
            )
            raise UserError(_(error_message))

    # -------------------------------------------------------------------
    # Mandatory transactional model hooks
    # -------------------------------------------------------------------

    @ssi_decorator.insert_on_form_view()
    def _insert_form_element(self, view_arch):
        if self._automatically_insert_view_element:
            view_arch = self._reconfigure_statusbar_visible(view_arch)
        return view_arch

    @api.model
    def _get_policy_field(self):
        res = super()._get_policy_field()
        policy_field = [
            "confirm_ok",
            "approve_ok",
            "reject_ok",
            "restart_approval_ok",
            "queue_done_ok",
            "done_ok",
            "cancel_ok",
            "restart_ok",
            "manual_number_ok",
        ]
        res += policy_field
        return res
