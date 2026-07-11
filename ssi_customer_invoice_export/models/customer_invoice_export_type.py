# Copyright 2026 OpenSynergy Indonesia
# Copyright 2026 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models

PARSER_HELP = """Python code that must set the `result` variable to a list of \
rows (each row a list of cell values) to be written to the export file.

Available in the local scope:
* env -- the Odoo environment
* document -- the customer_invoice_export record being generated
* summary_ids -- the document's summary lines (one per export row; per
  invoice or per partner, depending on the Type's Grouping Method)
* move_ids -- the document's selected customer invoices
* line_ids -- the document's selected invoice lines

Example:
result = [
    [s.move_ids.mapped("name"), s.partner_id.name, s.amount_total]
    for s in summary_ids
]"""


class CustomerInvoiceExportType(models.Model):
    """
    Represents a reusable export template that determines which customer
    invoices and invoice lines are eligible for a Customer Invoice Export
    document, the default output file format, and the Python parser code
    used to turn the selected data into the rows of the exported file.
    """

    _name = "customer_invoice_export_type"
    _inherit = ["mixin.master_data", "mixin.many2one_configurator"]
    _description = "Customer Invoice Export Type"

    default_output_format = fields.Selection(
        string="Default Output Format",
        selection=[
            ("csv", "CSV"),
            ("xlsx", "XLSX"),
            ("txt", "TXT"),
        ],
        default="csv",
        required=True,
        help=(
            "File format automatically proposed on a new Customer Invoice "
            "Export document created with this type."
        ),
    )
    grouping_method = fields.Selection(
        string="Grouping Method",
        selection=[
            ("invoice", "One Row per Invoice"),
            ("partner", "One Row per Partner"),
        ],
        default="invoice",
        required=True,
        help=(
            "Determines what one summary row -- and therefore one row of "
            "the exported file -- represents. One Row per Invoice: each "
            "qualifying invoice becomes its own row. One Row per Partner: "
            "all qualifying invoices of the same partner are merged into "
            "a single row, as required by bank formats keyed on a "
            "per-customer virtual account."
        ),
    )

    # --- Journal criteria (many2one configurator) ---

    journal_selection_method = fields.Selection(
        string="Journal Selection Method",
        selection=[
            ("manual", "Manual"),
            ("domain", "Domain"),
            ("code", "Python Code"),
        ],
        default="domain",
        required=True,
        help=(
            "Method used to determine which journals are allowed when "
            "selecting invoices on an export document of this type."
        ),
    )
    journal_ids = fields.Many2many(
        string="Journals",
        comodel_name="account.journal",
        relation="rel_cust_inv_export_type_2_journal",
        column1="type_id",
        column2="journal_id",
        help=(
            "Manually selected list of allowed journals. Used when Journal "
            "Selection Method = Manual."
        ),
    )
    journal_domain = fields.Text(
        string="Journal Domain",
        default="[]",
        help=(
            "Domain expression evaluated against account.journal to "
            "determine the allowed journals. Used when Journal Selection "
            "Method = Domain."
        ),
    )
    journal_python_code = fields.Text(
        string="Journal Python Code",
        default="result = []",
        help=(
            "Python code that must set the `result` variable to a "
            "recordset of account.journal. Used when Journal Selection "
            "Method = Python Code."
        ),
    )

    # --- Product criteria (many2one configurator) ---

    product_selection_method = fields.Selection(
        string="Product Selection Method",
        selection=[
            ("manual", "Manual"),
            ("domain", "Domain"),
            ("code", "Python Code"),
        ],
        default="domain",
        required=True,
        help=(
            "Method used to determine which products are allowed when "
            "selecting invoice lines on an export document of this type."
        ),
    )
    product_ids = fields.Many2many(
        string="Products",
        comodel_name="product.product",
        relation="rel_cust_inv_export_type_2_product",
        column1="type_id",
        column2="product_id",
        help=(
            "Manually selected list of allowed products. Used when Product "
            "Selection Method = Manual."
        ),
    )
    product_domain = fields.Text(
        string="Product Domain",
        default="[]",
        help=(
            "Domain expression evaluated against product.product to "
            "determine the allowed products. Used when Product Selection "
            "Method = Domain."
        ),
    )
    product_python_code = fields.Text(
        string="Product Python Code",
        default="result = []",
        help=(
            "Python code that must set the `result` variable to a "
            "recordset of product.product. Used when Product Selection "
            "Method = Python Code."
        ),
    )

    # --- Parser ---

    parser_python_code = fields.Text(
        string="Parser Python Code",
        default="result = []",
        help=PARSER_HELP,
    )

    # --- Output format options ---

    file_encoding = fields.Selection(
        string="Encoding",
        selection=[
            ("utf-8", "UTF-8"),
            ("utf-8-sig", "UTF-8 (with BOM)"),
            ("windows-1252", "Western (Windows-1252)"),
            ("iso-8859-1", "Western (Latin-1 / ISO 8859-1)"),
        ],
        default="utf-8",
        help="Character encoding used when writing the CSV or TXT export file.",
    )
    csv_delimiter = fields.Selection(
        string="CSV Delimiter",
        selection=[
            ("comma", "comma (,)"),
            ("semicolon", "semicolon (;)"),
            ("tab", "tab"),
            ("pipe", "pipe (|)"),
            ("space", "space"),
        ],
        default="comma",
        help="Field delimiter used when writing a CSV export file.",
    )
    csv_quotechar = fields.Char(
        string="CSV Text Qualifier",
        size=1,
        default='"',
        help="Character used to quote CSV fields containing special characters.",
    )
    xlsx_sheet_name = fields.Char(
        string="XLSX Sheet Name",
        help="Name of the worksheet created in the XLSX export file. Leave empty for 'Sheet1'.",
    )
    txt_field_separator = fields.Char(
        string="TXT Field Separator",
        help=(
            "Separator inserted between cell values when writing a TXT "
            "export file. Leave empty to concatenate cells without a "
            "separator (fixed-width style)."
        ),
    )

    def _get_csv_delimiter_character(self):
        self.ensure_one()
        return {
            "comma": ",",
            "semicolon": ";",
            "tab": "\t",
            "pipe": "|",
            "space": " ",
        }.get(self.csv_delimiter, ",")
