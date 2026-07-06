# Copyright 2026 OpenSynergy Indonesia
# Copyright 2026 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models


class CustomerInvoiceExport(models.Model):  # pylint: disable=too-few-public-methods
    _name = "customer_invoice_export"
    _inherit = [
        "customer_invoice_export",
        "mixin.single_operating_unit",
    ]

    def _prepare_invoice_domain(self):
        domain = super()._prepare_invoice_domain()
        if self.operating_unit_id:
            domain.append(("operating_unit_id", "=", self.operating_unit_id.id))
        return domain

    @api.depends("type_id", "operating_unit_id")
    def _compute_allowed_journal_ids(self):
        super()._compute_allowed_journal_ids()
        for record in self:
            if record.operating_unit_id and record.allowed_journal_ids:
                # A journal with no operating_unit_ids is unrestricted (usable
                # by any OU) -- same convention as account.move's own
                # _check_journal_operating_unit constraint. Only exclude
                # journals that are restricted to a different OU.
                record.allowed_journal_ids = record.allowed_journal_ids.filtered(
                    lambda journal, record=record: not journal.operating_unit_ids
                    or record.operating_unit_id in journal.operating_unit_ids
                )
