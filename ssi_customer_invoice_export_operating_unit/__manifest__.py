# Copyright 2026 OpenSynergy Indonesia
# Copyright 2026 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "Customer Invoice Export + Operating Unit",
    "version": "14.0.1.2.0",
    "website": "https://simetri-sinergi.id",
    "author": "OpenSynergy Indonesia, PT. Simetri Sinergi Indonesia",
    "contributors": [
        "Andhitia Rama <andhitia.r@gmail.com>",
    ],
    "license": "AGPL-3",
    "installable": True,
    "depends": [
        "ssi_customer_invoice_export",
        "ssi_operating_unit_mixin",
        "ssi_financial_accounting_operating_unit",
        "web_tour",
    ],
    "data": [
        "security/res_group/customer_invoice_export.xml",
        "security/ir_rule/customer_invoice_export.xml",
        "views/customer_invoice_export.xml",
        # Tests
        "views/assets.xml",
    ],
}
