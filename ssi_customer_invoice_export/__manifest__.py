# Copyright 2026 OpenSynergy Indonesia
# Copyright 2026 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Customer Invoice Export",
    "version": "14.0.2.11.0",
    "website": "https://simetri-sinergi.id",
    "author": "OpenSynergy Indonesia, PT. Simetri Sinergi Indonesia",
    "contributors": [
        "Andhitia Rama <andhitia.r@gmail.com>",
    ],
    "license": "AGPL-3",
    "installable": True,
    "application": False,
    "depends": [
        "account",
        "ssi_master_data_mixin",
        "ssi_m2o_configurator_mixin",
        "ssi_financial_accounting",
        "ssi_transaction_confirm_mixin",
        "ssi_transaction_queue_done_mixin",
        "ssi_transaction_cancel_mixin",
        "queue_job_batch",
        "base_automation",
        "web_tour",
    ],
    "external_dependencies": {
        "python": ["openpyxl"],
    },
    "data": [
        # Security - module categories
        "security/ir_module_category/customer_invoice_export.xml",
        # Security - groups
        "security/res_groups/customer_invoice_export_type.xml",
        "security/res_groups/customer_invoice_export.xml",
        # Security - access
        "security/ir_model_access/customer_invoice_export_type.xml",
        "security/ir_model_access/customer_invoice_export.xml",
        # Security - rules
        "security/ir_rule/customer_invoice_export.xml",
        # Sequence & templates
        "ir_sequence/customer_invoice_export.xml",
        "sequence_template/customer_invoice_export.xml",
        "approval_template/customer_invoice_export.xml",
        "policy_template/customer_invoice_export.xml",
        # Queue automation
        "data/ir_actions_server_data.xml",
        "data/base_automation_data.xml",
        # Views
        "views/customer_invoice_export_type_views.xml",
        "views/customer_invoice_export_views.xml",
        # Tests
        "views/assets.xml",
    ],
    "demo": [],
    "images": [],
}
