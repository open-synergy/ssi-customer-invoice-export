# Copyright 2026 OpenSynergy Indonesia
# Copyright 2026 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class CustomerInvoiceExportSummary(models.Model):
    """
    One row of the exported file for a Customer Invoice Export document,
    aggregating the invoice lines that matched the export Type's product
    criteria. Depending on the Type's Grouping Method, one row represents
    either a single customer invoice or all qualifying invoices of a
    single partner. Consumed by the Type's Parser Python Code when
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
    move_ids = fields.Many2many(
        string="Invoices",
        comodel_name="account.move",
        relation="rel_cust_inv_export_summary_2_move",
        column1="summary_id",
        column2="move_id",
        help="Customer invoice(s) aggregated into this export row.",
    )
    partner_id = fields.Many2one(
        string="Partner",
        comodel_name="res.partner",
        required=True,
        index=True,
        ondelete="restrict",
        help="Customer this summary row was aggregated for.",
    )
    currency_id = fields.Many2one(
        string="Currency",
        comodel_name="res.currency",
        help="Currency of the aggregated invoice(s), used to display Amount Total.",
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
    amount_residual = fields.Monetary(
        string="Amount Residual",
        compute="_compute_amount_residual",
        store=True,
        compute_sudo=True,
        currency_field="currency_id",
        help=(
            "Outstanding amount still due on this row's invoice(s), read "
            "from their receivable journal items instead of their invoice "
            "lines. Unlike Amount Total this is net of everything "
            "reconciled against the receivable -- payments as well as "
            "scholarship, fee waiver and promotion deductions. Use it in "
            "the Parser Python Code when the bank must be billed the "
            "amount actually still owed."
        ),
    )

    @api.depends("line_ids", "line_ids.price_subtotal")
    def _compute_amount_total(self):
        """Sum the subtotal of this row's qualifying invoice lines."""
        for record in self:
            record.amount_total = sum(record.line_ids.mapped("price_subtotal"))

    @api.depends(
        "move_ids",
        "move_ids.line_ids.amount_residual",
        "move_ids.line_ids.amount_residual_currency",
        "export_id.type_id",
    )
    def _compute_amount_residual(self):
        """Sum the outstanding amount of this row's receivable items.

        Considers only the journal items of this row's invoice(s) whose
        account is one of the export document's allowed receivable
        accounts and that sit on the debit side (``debit > 0`` and no
        ``credit``), which is where a customer invoice carries what the
        customer owes. Their residual is already net of every
        reconciliation made against them -- payments as well as
        scholarship, fee waiver and promotion deductions, which all
        reduce a customer invoice by reconciling a credit against its
        receivable item rather than by touching the invoice itself.

        Reads ``amount_residual_currency`` only for lines that actually
        carry a currency, falling back to ``amount_residual`` for the
        rest: core ``_compute_amount_residual`` leaves
        ``amount_residual_currency`` at 0.0 whenever ``currency_id`` is
        unset, so reading it unconditionally would silently report
        nothing outstanding for every move that does not bother setting
        a currency on its lines.
        """
        for record in self:
            allowed_accounts = record.export_id.allowed_receivable_account_ids
            lines = record.move_ids.mapped("line_ids").filtered(
                lambda line: line.account_id in allowed_accounts
                and line.debit > 0.0
                and not line.credit
            )
            record.amount_residual = sum(
                line.amount_residual_currency
                if line.currency_id
                else line.amount_residual
                for line in lines
            )
