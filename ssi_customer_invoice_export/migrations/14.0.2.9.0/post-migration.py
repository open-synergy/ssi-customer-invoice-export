# Copyright 2026 OpenSynergy Indonesia
# Copyright 2026 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
#
# Migration: 14.0.2.8.2 -> 14.0.2.9.0
#
# Changes: customer_invoice_export_type gained a fourth many2one
#          configurator criteria group, receivable_account_*, naming
#          the accounts that carry what the customer still owes; and
#          customer_invoice_export_summary gained a stored computed
#          column, amount_residual, summing the
#          amount_residual_currency of the selected invoices'
#          receivable journal items.
#
#          Odoo's own _init_column already backfills the two type
#          columns that carry a default (selection method "domain"
#          and the every-receivable-account domain) as soon as they
#          are created, before this script ever runs. The first half
#          of this script makes that backfill explicit and auditable
#          on a live database rather than relying on it having
#          happened silently.
#
#          The second half forces amount_residual to be computed for
#          every pre-existing summary row. It is deliberately applied
#          to ALL rows, including those of documents already in state
#          done or cancel whose export file was generated long ago:
#          amount_residual states what is outstanding NOW, not what
#          was outstanding when the file was written, and being a
#          stored computed field depending on
#          amount_residual_currency it would drift back to today's
#          value on the next reconciliation anyway. Restricting the
#          backfill by document state would therefore buy nothing and
#          leave a misleading zero behind in the meantime.

import logging

from openupgradelib import openupgrade

_logger = logging.getLogger(__name__)

RECEIVABLE_DOMAIN = "[('user_type_id.type', '=', 'receivable')]"


@openupgrade.migrate()
def migrate(env, version):
    """Backfill the receivable account criteria and Amount Residual.

    :param env: the migration environment
    :param version: the version being migrated to (unused)
    :return: nothing; updates ``customer_invoice_export_type`` and
        ``customer_invoice_export_summary`` rows
    """
    _backfill_type_criteria(env)
    _backfill_summary_amount_residual(env)


def _backfill_type_criteria(env):
    """Stamp the receivable account criteria defaults on every type.

    Explicit and auditable stand-in for the backfill Odoo's own
    ``_init_column`` already performs silently when the columns are
    created. Only rows still holding NULL are touched, so a type an
    administrator already narrowed down is never overwritten.

    :param env: the migration environment
    :return: nothing; updates ``customer_invoice_export_type`` rows
    """
    openupgrade.logged_query(
        env.cr,
        """
        UPDATE customer_invoice_export_type
        SET receivable_account_selection_method = 'domain'
        WHERE receivable_account_selection_method IS NULL
        """,
    )
    _logger.info(
        "Stamped receivable_account_selection_method='domain' on %s "
        "customer_invoice_export_type row(s).",
        env.cr.rowcount,
    )
    openupgrade.logged_query(
        env.cr,
        """
        UPDATE customer_invoice_export_type
        SET receivable_account_domain = %s
        WHERE receivable_account_domain IS NULL
        """,
        (RECEIVABLE_DOMAIN,),
    )
    _logger.info(
        "Stamped the every-receivable-account domain on %s "
        "customer_invoice_export_type row(s).",
        env.cr.rowcount,
    )


def _backfill_summary_amount_residual(env):
    """Compute Amount Residual on every pre-existing summary row.

    Goes through the ORM rather than SQL on purpose: the receivable
    accounts a row is measured against come from its document's Type
    through the many2one configurator, whose Python code selection
    method only the ORM can evaluate.

    :param env: the migration environment
    :return: nothing; updates ``customer_invoice_export_summary`` rows
    """
    summaries = env["customer_invoice_export.summary"].search([])
    if not summaries:
        _logger.info("No customer_invoice_export_summary row to backfill.")
        return
    env.add_to_compute(summaries._fields["amount_residual"], summaries)
    summaries.flush(["amount_residual"])
    _logger.info(
        "Computed amount_residual on %s customer_invoice_export_summary row(s).",
        len(summaries),
    )
