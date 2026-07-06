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
    criteria, and builds one summary row per qualifying invoice. On
    completion the document generates a CSV/XLSX/TXT file -- via the
    Type's Python parser code -- for upload to a banking service.

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
            "Lower bound (inclusive) on invoice date used to auto-select "
            "invoices. Leave empty together with Date End to select "
            "invoices regardless of date."
        ),
    )
    date_end = fields.Date(
        string="Date End",
        readonly=True,
        states={"draft": [("readonly", False)]},
        help=(
            "Upper bound (inclusive) on invoice date used to auto-select "
            "invoices. Leave empty together with Date Start to select "
            "invoices regardless of date."
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
    allowed_product_ids = fields.Many2many(
        string="Allowed Products",
        comodel_name="product.product",
        compute="_compute_allowed_product_ids",
        store=False,
        compute_sudo=True,
        help="Products allowed to be selected, as configured on the Type.",
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
            "One row per qualifying invoice, aggregating its qualifying "
            "lines. Derived by the Populate button; consumed by the "
            "Parser Python Code when generating the export file."
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
    def _compute_allowed_product_ids(self):
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

    @api.onchange("type_id")
    def onchange_output_format(self):
        self.output_format = (
            self.type_id.default_output_format if self.type_id else False
        )

    # -------------------------------------------------------------------
    # Populate
    # -------------------------------------------------------------------

    def action_populate(self):
        for record in self.sudo():
            record._populate()

    def _populate(self):
        self.ensure_one()
        moves = self.env["account.move"].search(self._prepare_invoice_domain())
        self.move_ids = [(6, 0, moves.ids)]

        qualifying_by_move = {}
        all_qualifying_ids = []
        for move in moves:
            qualifying = self._get_qualifying_lines(move)
            if qualifying:
                qualifying_by_move[move.id] = qualifying
                all_qualifying_ids += qualifying.ids
        self.line_ids = [(6, 0, all_qualifying_ids)]

        self.summary_ids.unlink()
        sequence = 5
        summary_vals = []
        for move in moves:
            qualifying = qualifying_by_move.get(move.id)
            if not qualifying:
                continue
            summary_vals.append(self._prepare_summary_data(move, qualifying, sequence))
            sequence += 5
        if summary_vals:
            self.env["customer_invoice_export.summary"].create(summary_vals)

    def _prepare_invoice_domain(self):
        self.ensure_one()
        domain = [
            ("move_type", "=", "out_invoice"),
            ("state", "=", "posted"),
            ("payment_state", "in", ("not_paid", "partial")),
            ("journal_id", "in", self.allowed_journal_ids.ids),
        ]
        if self.date_start:
            domain.append(("invoice_date", ">=", self.date_start))
        if self.date_end:
            domain.append(("invoice_date", "<=", self.date_end))
        return domain

    def _get_qualifying_lines(self, move):
        self.ensure_one()
        return move.invoice_line_ids.filtered(
            lambda line: not line.display_type
            and line.product_id in self.allowed_product_ids
        )

    def _prepare_summary_data(self, move, qualifying_lines, sequence):
        self.ensure_one()
        return {
            "export_id": self.id,
            "sequence": sequence,
            "move_id": move.id,
            "line_ids": [(6, 0, qualifying_lines.ids)],
        }

    # -------------------------------------------------------------------
    # Queue-to-done: generate export file
    # -------------------------------------------------------------------

    @ssi_decorator.post_queue_done_action()
    def _01_generate_export_on_queue_done(self):
        self.ensure_one()
        description = "Generate export file for %s" % (self.name or self.id)
        self.with_context(job_batch=self.done_queue_job_batch_id).with_delay(
            description=_(description)
        )._generate_export_file()

    def _generate_export_file(self):
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
        self.ensure_one()
        if self.output_format == "csv":
            return self._render_csv(rows)
        elif self.output_format == "xlsx":
            return self._render_xlsx(rows)
        return self._render_txt(rows)

    def _render_csv(self, rows):
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
        self.ensure_one()
        ptype = self.type_id
        separator = ptype.txt_field_separator or ""
        lines = [separator.join(str(cell) for cell in row) for row in rows]
        return "\n".join(lines).encode(ptype.file_encoding or "utf-8")

    def _build_export_filename(self):
        self.ensure_one()
        extension = OUTPUT_FORMAT_EXTENSION.get(self.output_format, "csv")
        base = self.name if self.name and self.name != "/" else "export_%s" % self.id
        return "%s.%s" % (base, extension)

    def _create_export_attachment(self, output, filename):
        self.ensure_one()
        self.env["ir.attachment"].create(
            self._prepare_export_attachment_data(output, filename)
        )

    def _prepare_export_attachment_data(self, output, filename):
        self.ensure_one()
        return {
            "name": filename,
            "res_model": self._name,
            "res_id": self.id,
            "type": "binary",
            "datas": base64.b64encode(output),
        }

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
