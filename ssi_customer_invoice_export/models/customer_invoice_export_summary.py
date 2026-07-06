# Copyright 2026 OpenSynergy Indonesia
# Copyright 2026 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class CustomerInvoiceExportSummary(models.Model):
    """
    One row per customer invoice qualifying for a Customer Invoice Export
    document, aggregating the invoice lines that matched the export Type's
    product criteria. Consumed by the Type's Parser Python Code when
    generating the export file.
    """

    _name = "customer_invoice_export.summary"
    _description = "Customer Invoice Export - Summary"
    _order = "export_id, sequence"

    export_id = fields.Many2one(
        string="# Export",
        comodel_name="customer_invoice_export",
        required=True,
        ondelete="cascade",
        help="The export document this summary row belongs to.",
    )
    sequence = fields.Integer(
        string="Sequence",
        required=True,
        default=5,
        help="Row order among the summary lines of the same export document.",
    )
    move_id = fields.Many2one(
        string="Invoice",
        comodel_name="account.move",
        required=True,
        ondelete="cascade",
        help="Customer invoice this summary row aggregates.",
    )
    partner_id = fields.Many2one(
        string="Partner",
        comodel_name="res.partner",
        related="move_id.partner_id",
        store=True,
        compute_sudo=True,
        help="Customer derived from the linked invoice.",
    )
    currency_id = fields.Many2one(
        string="Currency",
        comodel_name="res.currency",
        related="move_id.currency_id",
        store=True,
        compute_sudo=True,
        help="Currency of the linked invoice.",
    )
    line_ids = fields.Many2many(
        string="Invoice Lines",
        comodel_name="account.move.line",
        relation="rel_cust_inv_export_summary_2_move_line",
        column1="summary_id",
        column2="line_id",
        help="Subset of the invoice's lines that matched the Type's product criteria.",
    )
    amount_total = fields.Monetary(
        string="Amount Total",
        compute="_compute_amount_total",
        store=True,
        compute_sudo=True,
        currency_field="currency_id",
        help="Sum of the subtotal of this row's qualifying invoice lines.",
    )

    @api.depends("line_ids", "line_ids.price_subtotal")
    def _compute_amount_total(self):
        for record in self:
            record.amount_total = sum(record.line_ids.mapped("price_subtotal"))
