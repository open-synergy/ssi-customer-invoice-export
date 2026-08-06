// Copyright 2026 OpenSynergy Indonesia
// Copyright 2026 PT. Simetri Sinergi Indonesia
// License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

odoo.define("ssi_customer_invoice_export.customer_invoice_export_tour", function (
    require
) {
    "use strict";

    var tour = require("web_tour.tour");

    // Shared navigation block reused by every tour below -- corresponds
    // to Flow 1 of every customer_invoice_export IK: "Open the Financial
    // Accounting > Account Receivable > Customer Invoice Exports menu."
    function openCustomerInvoiceExportList() {
        return [
            tour.stepUtils.showAppsMenuItem(),
            {
                content: "Open the Financial Accounting app",
                trigger:
                    '.o_app[data-menu-xmlid="ssi_financial_accounting.menu_root_financial_accounting"]',
            },
            {
                content: "Open the Account Receivable menu",
                trigger:
                    '.o_menu_sections [data-menu-xmlid="ssi_financial_accounting.menu_account_receivable"]',
            },
            {
                content: "Open the Customer Invoice Exports menu",
                trigger:
                    '.o_menu_sections [data-menu-xmlid="ssi_customer_invoice_export.customer_invoice_export_menu"]',
            },
            {
                // Gerbang: tunggu action TUJUAN benar-benar terpasang,
                // bukan sekadar "ada list di layar" (lihat patterns.md
                // skill odoo-development-ui-test §A).
                content: "Customer Invoice Exports list is displayed",
                trigger:
                    ".o_control_panel .breadcrumb-item.active:contains(Customer Invoice Exports)",
                extra_trigger: ".o_list_view",
                run: function () {
                    // Assertion only.
                },
            },
        ];
    }

    // IK: docs/customer_invoice_export/01-create.md
    tour.register(
        "ssi_customer_invoice_export_create",
        {
            test: true,
            url: "/web",
        },
        [].concat(
            // Flow 1 -- Open the Financial Accounting > Account
            // Receivable > Customer Invoice Exports menu.
            openCustomerInvoiceExportList(),
            [
                // Flow 2 -- Click the New button.
                {
                    content: "Click New",
                    trigger: ".o_list_button_add",
                    extra_trigger: ".o_list_view",
                },
                {
                    content: "Form is open in edit mode",
                    trigger: ".o_form_view.o_form_editable",
                    run: function () {
                        // Assertion only.
                    },
                },

                // Flow 3 -- Select the Type (Date defaults to today,
                // Date Start/Date End are left empty per IK, and Output
                // Format is automatically filled from Type by the
                // onchange -- none of these need an interactive step).
                {
                    content: "Select the Type",
                    trigger: ".o_field_many2one[name='type_id'] input",
                    extra_trigger: ".o_form_view.o_form_editable",
                    run: "text TOUR CIE Create Type",
                },
                {
                    content: "Pick the Type from the dropdown",
                    trigger:
                        ".ui-autocomplete .ui-menu-item a:contains(TOUR CIE Create Type)",
                    in_modal: false,
                },

                // Flow 4 -- On the Invoices tab, click Populate.
                {
                    content: "Open the Invoices tab",
                    trigger: ".o_notebook .nav-link:contains(Invoices)",
                },
                {
                    content: "Click Populate",
                    trigger: ".o_form_view button[name='action_populate']",
                },
                {
                    // Gerbang: action_populate is a type="object" button
                    // that writes move_ids/line_ids/summary_ids via an
                    // asynchronous RPC (form_renderer.js
                    // disableButtons()/enableButtons() bracket the call --
                    // same mechanism validated for Generate Code in
                    // customer_invoice_export_type_tour.js). Its own
                    // ":enabled" state would be a false gate here (it is
                    // already enabled before the click too), so the real
                    // token used is the fixture invoice's partner row --
                    // this row is IMPOSSIBLE in move_ids before Populate
                    // ever runs, since the document starts with an empty
                    // move_ids.
                    content: "Populate has filled the Invoices list",
                    trigger:
                        ".o_field_widget[name='move_ids'] .o_data_row:contains(TOUR CIE Create Partner)",
                    run: function () {
                        // Assertion only.
                    },
                },

                // Flow 5 (Inline Action, Settings/Technical group only --
                // admin qualifies via base.group_system) -- on the
                // Policies tab, click Reload Template Policy.
                {
                    content: "Open the Policies tab",
                    trigger: ".o_notebook .nav-link:contains(Policies)",
                },
                {
                    content: "Click Reload Template Policy",
                    trigger: "button[name='action_reload_policy_template']",
                },
                {
                    // Gerbang: same disable/enable idiom as Generate Code
                    // in customer_invoice_export_type_tour.js -- this
                    // button re-selects the matching template (which may
                    // resolve to the SAME template already assigned), so
                    // no distinctive new token is available; the
                    // synchronous disableButtons() on click still makes
                    // this non-racy.
                    content: "Reload Template Policy call has completed",
                    trigger: "button[name='action_reload_policy_template']:enabled",
                    run: function () {
                        // Assertion only.
                    },
                },

                // Flow 6 -- Click Save.
                {
                    content: "Save the record",
                    trigger: ".o_form_button_save",
                },

                // Post-Condition -- a new record is created in Draft
                // status, and the Invoices/Invoice Lines/Summary tabs are
                // filled according to the Type's criteria.
                {
                    content: "Record is saved",
                    trigger: ".o_form_view.o_form_readonly",
                    run: function () {
                        // Assertion only.
                    },
                },
                {
                    content: "Status is Draft",
                    trigger:
                        ".o_statusbar_status .o_arrow_button[data-value='draft'].btn-primary",
                    run: function () {
                        // Assertion only.
                    },
                },
                {
                    content: "Open the Summary tab",
                    trigger: ".o_notebook .nav-link:contains(Summary)",
                },
                {
                    content: "Summary tab shows the Populate result",
                    trigger:
                        ".o_field_widget[name='summary_ids'] .o_data_row:contains(TOUR CIE Create Partner)",
                    run: function () {
                        // Assertion only.
                    },
                },
            ]
        )
    );

    // IK: docs/customer_invoice_export/02-edit.md
    tour.register(
        "ssi_customer_invoice_export_edit",
        {
            test: true,
            url: "/web",
        },
        [].concat(
            // Flow 1 -- Open the Customer Invoice Exports menu.
            openCustomerInvoiceExportList(),
            [
                // Flow 2 -- Find and open the record to edit.
                {
                    content: "Open the record",
                    trigger:
                        ".o_data_row:contains(TOUR CIE Edit Type) .o_data_cell:first",
                    extra_trigger: ".o_list_view",
                },
                {
                    content: "Form is open",
                    trigger: ".o_form_view",
                    run: function () {
                        // Assertion only.
                    },
                },
                // 14.0: an existing record opens read-only -- Edit first.
                {
                    content: "Click the Edit button",
                    trigger: ".o_form_button_edit",
                },
                {
                    content: "Form is now editable",
                    trigger: ".o_form_view.o_form_editable",
                    run: function () {
                        // Assertion only.
                    },
                },

                // Flow 3 -- Narrow Date Start so the earlier fixture
                // invoice no longer qualifies.
                {
                    content: "Open the Invoices tab",
                    trigger: ".o_notebook .nav-link:contains(Invoices)",
                },
                {
                    content: "Fill in Date Start",
                    trigger: ".o_field_widget[name='date_start'] input",
                    run: "text 02/01/2026",
                },

                // Flow 4 -- Click Populate to refresh the Invoices list.
                {
                    content: "Click Populate",
                    trigger: ".o_form_view button[name='action_populate']",
                },
                {
                    // Gerbang: the fixture's setUpClass already ran
                    // Populate once with no date range, so the Early
                    // Partner row is present BEFORE this click too --
                    // what is impossible before this click is its
                    // DISAPPEARANCE, which can only happen once the
                    // narrowed Date Start is actually applied by a fresh
                    // Populate run (same disappearance idiom as the
                    // Archived-filter gates in
                    // customer_invoice_export_type_tour.js).
                    content: "Populate has dropped the excluded invoice",
                    trigger:
                        ".o_field_widget[name='move_ids']:not(:has(.o_data_row:contains(TOUR CIE Edit Early Partner)))",
                    run: function () {
                        // Assertion only.
                    },
                },

                // Flow 5 (Inline Action, Settings/Technical group only) --
                // on the Policies tab, click Reload Template Policy.
                {
                    content: "Open the Policies tab",
                    trigger: ".o_notebook .nav-link:contains(Policies)",
                },
                {
                    content: "Click Reload Template Policy",
                    trigger: "button[name='action_reload_policy_template']",
                },
                {
                    // Gerbang -- lihat catatan gerbang yang sama pada
                    // tour create di atas.
                    content: "Reload Template Policy call has completed",
                    trigger: "button[name='action_reload_policy_template']:enabled",
                    run: function () {
                        // Assertion only.
                    },
                },

                // Flow 6 -- Click Save.
                {
                    content: "Save the record",
                    trigger: ".o_form_button_save",
                },

                // Post-Condition -- the record is updated with the new
                // values.
                {
                    content: "Record is saved",
                    trigger: ".o_form_view.o_form_readonly",
                    run: function () {
                        // Assertion only.
                    },
                },
            ]
        )
    );

    // IK: docs/customer_invoice_export/03-delete.md
    tour.register(
        "ssi_customer_invoice_export_delete",
        {
            test: true,
            url: "/web",
        },
        [].concat(
            // Flow 1 -- Open the Customer Invoice Exports menu.
            openCustomerInvoiceExportList(),
            [
                // Flow 2 -- Select the record to delete (checkbox).
                {
                    content: "Select the record to delete",
                    trigger:
                        ".o_data_row:contains(TOUR CIE Delete Type) .o_list_record_selector input",
                    run: "click",
                },

                // Flow 3 -- Click Action > Delete.
                {
                    content: "Open the Action menu",
                    trigger: ".o_cp_action_menus button:contains(Action)",
                },
                {
                    content: "Click Delete",
                    // Item Action menu adalah komponen Owl; cocokkan
                    // LABEL PERSIS -- :contains(Delete) sebagai substring
                    // bisa keliru menunjuk item lain. Lihat patterns.md
                    // skill odoo-development-ui-test §I.
                    trigger: ".o_cp_action_menus .o_menu_item a",
                    run: function () {
                        var $delete = $(".o_cp_action_menus .o_menu_item a").filter(
                            function () {
                                return $(this).text().trim() === "Delete";
                            }
                        );
                        $delete[0].click();
                    },
                },

                // Flow 4 -- Click OK to confirm.
                {
                    content: "Confirm deletion",
                    trigger: ".modal-footer button.btn-primary",
                    in_modal: true,
                },

                // Post-Condition -- the selected record is permanently
                // removed from the system.
                {
                    content: "Record no longer appears in the list",
                    trigger:
                        ".o_list_view:not(:has(.o_data_row:contains(TOUR CIE Delete Type)))",
                    run: function () {
                        // Assertion only.
                    },
                },
            ]
        )
    );

    // IK: docs/customer_invoice_export/04-confirm.md
    tour.register(
        "ssi_customer_invoice_export_confirm",
        {
            test: true,
            url: "/web",
        },
        [].concat(
            // Flow 1 -- Open the Customer Invoice Exports menu.
            openCustomerInvoiceExportList(),
            [
                // Flow 2 -- Open the record to confirm.
                {
                    content: "Open the record",
                    trigger:
                        ".o_data_row:contains(TOUR CIE Confirm Type) .o_data_cell:first",
                    extra_trigger: ".o_list_view",
                },
                {
                    content: "Form is open",
                    trigger: ".o_form_view",
                    run: function () {
                        // Assertion only.
                    },
                },

                // Flow 3 -- Click the Confirm button.
                {
                    content: "Click the Confirm button",
                    trigger: ".o_statusbar_buttons button[name='action_confirm']",
                    extra_trigger: ".o_form_view",
                },

                // Flow 4 -- Click OK on the confirmation dialog.
                {
                    content: "Confirm the dialog",
                    trigger: ".modal-footer button.btn-primary",
                    in_modal: true,
                },

                // Post-Condition -- status changes to Waiting for
                // Approval (approval records are created server-side and
                // are not a kasatmata UI fact -- out of tour scope).
                {
                    content: "Status is Waiting for Approval",
                    trigger:
                        ".o_statusbar_status .o_arrow_button[data-value='confirm'].btn-primary",
                    run: function () {
                        // Assertion only.
                    },
                },
            ]
        )
    );

    // IK: docs/customer_invoice_export/05-approve.md
    tour.register(
        "ssi_customer_invoice_export_approve",
        {
            test: true,
            url: "/web",
        },
        [].concat(
            // Flow 1 -- Open the Customer Invoice Exports menu.
            openCustomerInvoiceExportList(),
            [
                // Flow 2 -- Open the record to approve.
                {
                    content: "Open the record",
                    trigger:
                        ".o_data_row:contains(TOUR CIE Approve Type) .o_data_cell:first",
                    extra_trigger: ".o_list_view",
                },
                {
                    content: "Form is open",
                    trigger: ".o_form_view",
                    run: function () {
                        // Assertion only.
                    },
                },

                // Flow 3 -- Click the Approve button.
                {
                    content: "Click the Approve button",
                    trigger:
                        ".o_statusbar_buttons button[name='action_approve_approval']",
                    extra_trigger: ".o_form_view",
                },

                // Flow 4 -- Click OK on the confirmation dialog.
                {
                    content: "Confirm the dialog",
                    trigger: ".modal-footer button.btn-primary",
                    in_modal: true,
                },

                // Post-Condition -- the fixture's approval.template has a
                // single approval level, so this one Approve click
                // fulfills it and status automatically changes to Queue
                // To Done. The background job that will eventually
                // generate the Export File is queued but NOT awaited
                // here -- it runs without any DOM signal and awaiting it
                // would hang headless Chrome (Keputusan Desain, issue
                // #23).
                {
                    content: "Status is Queue To Done",
                    trigger:
                        ".o_statusbar_status .o_arrow_button[data-value='queue_done'].btn-primary",
                    run: function () {
                        // Assertion only.
                    },
                },
            ]
        )
    );

    // IK: docs/customer_invoice_export/06-reject.md
    tour.register(
        "ssi_customer_invoice_export_reject",
        {
            test: true,
            url: "/web",
        },
        [].concat(
            // Flow 1 -- Open the Customer Invoice Exports menu.
            openCustomerInvoiceExportList(),
            [
                // Flow 2 -- Open the record to reject.
                {
                    content: "Open the record",
                    trigger:
                        ".o_data_row:contains(TOUR CIE Reject Type) .o_data_cell:first",
                    extra_trigger: ".o_list_view",
                },
                {
                    content: "Form is open",
                    trigger: ".o_form_view",
                    run: function () {
                        // Assertion only.
                    },
                },

                // Flow 3 -- Click the Reject button.
                {
                    content: "Click the Reject button",
                    trigger:
                        ".o_statusbar_buttons button[name='action_reject_approval']",
                    extra_trigger: ".o_form_view",
                },

                // Flow 4 -- Click OK on the confirmation dialog.
                {
                    content: "Confirm the dialog",
                    trigger: ".modal-footer button.btn-primary",
                    in_modal: true,
                },

                // Post-Condition -- status changes to Rejected. "reject"
                // is excluded from _statusbar_visible_label
                // ("draft,confirm,queue_done,done"), but Odoo 14's
                // FieldStatus widget always keeps the record's CURRENT
                // value visible even when it is not in that list (same
                // idiom validated in ssi_customer_invoice's
                // customer_invoice_tour.js reject tour).
                {
                    content: "Status is Rejected",
                    trigger:
                        ".o_statusbar_status .o_arrow_button[data-value='reject'].btn-primary",
                    run: function () {
                        // Assertion only.
                    },
                },
            ]
        )
    );
});
