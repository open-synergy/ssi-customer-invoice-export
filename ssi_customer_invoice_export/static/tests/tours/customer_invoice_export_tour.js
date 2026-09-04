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

                // Flow 5 (Inline Action, Settings/Technical group only --
                // admin qualifies via base.group_system) -- on the
                // Policies tab, click Reload Template Policy. Deliberately
                // sequenced BEFORE Populate (Flow 4), not after: both
                // Populate and Reload Template Policy are type="object"
                // buttons that auto-save the record then reload it
                // (form_controller.js _onButtonClicked ->
                // saveAndExecuteAction, stayInEdit: true) -- clicking
                // Save immediately after TWO such reloads back-to-back
                // races the second reload's re-render (patterns.md skill
                // odoo-development-ui-test §P "Jebakan turunan"): the
                // Save click can land mid-render and the form gets stuck
                // in edit mode, timing out at the Post-Condition
                // (.o_form_view.o_form_readonly) below -- reproduced in
                // CI on this exact tour. Reload Template Policy has no
                // reliable "impossible before" content gate of its own
                // (the template it re-selects is usually the SAME one
                // already assigned at creation, per IK step 5's own
                // text), so it is run first, leaving Populate --
                // whose gate below IS a genuine content token -- as the
                // last asynchronous action before Save.
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
                    // in customer_invoice_export_type_tour.js. Only a
                    // partial guarantee (see comment above) -- relied on
                    // here only because Populate's own robust gate still
                    // follows before Save.
                    content: "Reload Template Policy call has completed",
                    trigger: "button[name='action_reload_policy_template']:enabled",
                    run: function () {
                        // Assertion only.
                    },
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
                    // asynchronous RPC. Its own ":enabled" state would be
                    // a false gate here (it is already enabled before the
                    // click too), so the real token used is the fixture
                    // invoice's partner row -- this row is IMPOSSIBLE in
                    // move_ids before Populate ever runs, since the
                    // document starts with an empty move_ids. Because
                    // this token can only appear once the reload has
                    // actually re-rendered the list, it doubles as the
                    // "everything has settled" signal before Save below.
                    content: "Populate has filled the Invoices list",
                    trigger:
                        ".o_field_widget[name='move_ids'] .o_data_row:contains(TOUR CIE Create Partner)",
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
                // invoice no longer qualifies. Typed BEFORE either
                // object-button reload below (Reload Template Policy,
                // Populate): typing into a field widget while a
                // type="object" button's own reload is still landing in
                // the background raced FieldWrapper.commitChanges against
                // the widget being destroyed and recreated, throwing
                // "Cannot read properties of null" -- reproduced in CI.
                // Typing first, before either reload starts, sidesteps
                // that race entirely.
                {
                    content: "Open the Invoices tab",
                    trigger: ".o_notebook .nav-link:contains(Invoices)",
                },
                {
                    content: "Fill in Date Start",
                    trigger: ".o_field_widget[name='date_start'] input",
                    run: "text 02/01/2026",
                },

                // Flow 5 (Inline Action, Settings/Technical group only) --
                // on the Policies tab, click Reload Template Policy.
                // Deliberately sequenced BEFORE Populate (Flow 4), with no
                // field interaction between the two -- see the detailed
                // comment on the same reordering in the create tour above
                // (patterns.md skill odoo-development-ui-test §P "Jebakan
                // turunan": two type="object" reloads back-to-back race
                // the Save click that follows; only a click, never typing,
                // is safe to place between them and Populate).
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

                // Flow 4 -- Click Populate to refresh the Invoices list.
                {
                    content: "Open the Invoices tab",
                    trigger: ".o_notebook .nav-link:contains(Invoices)",
                },
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
                    // customer_invoice_export_type_tour.js). Because this
                    // can only be observed once the reload has actually
                    // re-rendered the list, it doubles as the
                    // "everything has settled" signal before Save below.
                    content: "Populate has dropped the excluded invoice",
                    trigger:
                        ".o_field_widget[name='move_ids']:not(:has(.o_data_row:contains(TOUR CIE Edit Early Partner)))",
                    run: function () {
                        // Assertion only.
                    },
                },

                // Flow 4 (continued) -- the Invoices list can also be
                // adjusted manually: remove the remaining invoice row
                // by clicking its trash icon (issue #42).
                {
                    content: "Remove the remaining invoice from Invoices",
                    trigger:
                        ".o_field_widget[name='move_ids'] .o_data_row:contains(TOUR CIE Edit Late Partner) .o_list_record_remove",
                },
                {
                    // Gerbang: this row was present BEFORE the click
                    // too (Populate above put it there) -- what is
                    // impossible before the click is its
                    // DISAPPEARANCE, which only the removal above can
                    // cause client-side (same disappearance idiom as
                    // the Populate gate right above).
                    content: "Invoices row is removed",
                    trigger:
                        ".o_field_widget[name='move_ids']:not(:has(.o_data_row:contains(TOUR CIE Edit Late Partner)))",
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

                // Post-Condition (issue #42) -- removing the invoice
                // from Invoices rebuilt Summary too, without clicking
                // Populate again. write() only runs the rebuild once
                // the record is actually saved, so this is checked
                // here rather than right after the client-side removal
                // above.
                {
                    content: "Open the Summary tab",
                    trigger: ".o_notebook .nav-link:contains(Summary)",
                },
                {
                    // Gerbang: this row was present in Summary BEFORE
                    // Save too (Populate above put it there) -- what
                    // is impossible before Save persisted the removal
                    // above is its DISAPPEARANCE from Summary.
                    content: "Summary no longer shows the removed invoice",
                    trigger:
                        ".o_field_widget[name='summary_ids']:not(:has(.o_data_row:contains(TOUR CIE Edit Late Partner)))",
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

    // IK: docs/customer_invoice_export/10-cancel.md
    tour.register(
        "ssi_customer_invoice_export_cancel",
        {
            test: true,
            url: "/web",
        },
        [].concat(
            // Flow 1 -- Open the Customer Invoice Exports menu.
            openCustomerInvoiceExportList(),
            [
                // Flow 2 -- Open the record to cancel.
                {
                    content: "Open the record",
                    trigger:
                        ".o_data_row:contains(TOUR CIE Cancel Type) .o_data_cell:first",
                    extra_trigger: ".o_list_view",
                },
                {
                    content: "Form is open",
                    trigger: ".o_form_view",
                    run: function () {
                        // Assertion only.
                    },
                },

                // Flow 3 -- Click the Cancel button.
                //
                // This button is declared type="action" (button_cancel of
                // ssi_transaction_cancel_mixin), so what ends up in the DOM
                // is name="<numeric id of the Select Cancel Reason window
                // action>" -- an id that differs per database.
                // button[name='action_cancel'] would never match; matching
                // by label is mandatory here (odoo-development-ui-test
                // selectors.md §4).
                {
                    content: "Click the Cancel button",
                    trigger: ".o_statusbar_buttons button:enabled:contains('Cancel')",
                    extra_trigger: ".o_form_view",
                },

                // Flow 4 -- In the wizard that appears, select the
                // Cancellation Reason.
                {
                    content: "The Select Cancel Reason wizard is displayed",
                    trigger: ".o_form_view",
                    run: function () {
                        // Assertion only.
                    },
                },
                {
                    // Cancel_reason_id is rendered with widget="radio" by
                    // the wizard view, so it is a radio item that gets
                    // clicked -- not a many2one autocomplete.
                    content: "Select the cancel reason",
                    trigger:
                        ".o_field_widget[name='cancel_reason_id'] " +
                        ".o_radio_item:contains(TOUR CIE Cancel Reason) input",
                    run: "click",
                },

                // Flow 5 -- Click Confirm.
                {
                    content: "Confirm the wizard",
                    trigger: ".modal-footer button[name='action_confirm']",
                },

                // Flow 6 -- Click OK on the confirmation dialog.
                //
                // The wizard's own Confirm button carries confirm="Are you
                // sure?", which stacks a second dialog on top of the
                // wizard; the topmost visible modal is what this trigger
                // resolves to.
                {
                    content: "Click OK on the confirmation dialog",
                    trigger: ".modal-footer button.btn-primary",
                    in_modal: true,
                },

                // Post-Condition -- Status changes to Cancelled.
                {
                    content: "Status is Cancelled",
                    trigger:
                        ".o_statusbar_status .o_arrow_button[data-value='cancel'].btn-primary",
                    run: function () {
                        // Assertion only.
                    },
                },
                {
                    // The cancel_reason template renders this h2 as a
                    // sibling of the title h1, invisible unless
                    // state == 'cancel', so it cannot pass before the
                    // action above actually ran.
                    content:
                        "The selected Cancellation Reason is displayed next to the title",
                    trigger: ".oe_title h2:contains(TOUR CIE Cancel Reason)",
                    run: function () {
                        // Assertion only.
                    },
                },
            ]
        )
    );

    // IK: docs/customer_invoice_export/12-restart.md
    tour.register(
        "ssi_customer_invoice_export_restart",
        {
            test: true,
            url: "/web",
        },
        [].concat(
            // Flow 1 -- Open the Customer Invoice Exports menu.
            openCustomerInvoiceExportList(),
            [
                // Flow 2 -- Open the record to restart.
                {
                    content: "Open the record",
                    trigger:
                        ".o_data_row:contains(TOUR CIE Redraft Type) .o_data_cell:first",
                    extra_trigger: ".o_list_view",
                },
                {
                    content: "Form is open",
                    trigger: ".o_form_view",
                    run: function () {
                        // Assertion only.
                    },
                },

                // Flow 3 -- Click the Restart button.
                //
                // action_restart is type="object" and carries confirm="
                // Restart data. Are you sure?" in the mixin form view, so
                // the dialog below is part of the Flow rather than a
                // tour-only detour. Targeting the method name also keeps
                // this apart from the Restart Approval Process button,
                // whose label contains "Restart" as well.
                {
                    content: "Click the Restart button",
                    trigger: ".o_statusbar_buttons button[name='action_restart']",
                    extra_trigger: ".o_form_view",
                },

                // Flow 4 -- Click OK on the confirmation dialog.
                {
                    content: "Click OK on the confirmation dialog",
                    trigger: ".modal-footer button.btn-primary",
                    in_modal: true,
                },

                // Post-Condition -- Status returns to Draft.
                {
                    content: "Status is Draft",
                    trigger:
                        ".o_statusbar_status .o_arrow_button[data-value='draft'].btn-primary",
                    run: function () {
                        // Assertion only.
                    },
                },
            ]
        )
    );

    // IK: docs/customer_invoice_export/13-reset-number.md
    tour.register(
        "ssi_customer_invoice_export_reset_number",
        {
            test: true,
            url: "/web",
        },
        [].concat(
            // Flow 1 -- Open the Customer Invoice Exports menu.
            openCustomerInvoiceExportList(),
            [
                // Flow 2 -- Open the record whose document number will be
                // reset.
                {
                    content: "Open the record",
                    trigger:
                        ".o_data_row:contains(TOUR CIE Reset Number Type) .o_data_cell:first",
                    extra_trigger: ".o_list_view",
                },
                {
                    content: "Form is open",
                    trigger: ".o_form_view",
                    run: function () {
                        // Assertion only.
                    },
                },

                // Flow 3 -- Click the Reset Document Number button.
                {
                    content: "Click the Reset Document Number button",
                    trigger:
                        ".o_statusbar_buttons button[name='action_reset_document_number']",
                    extra_trigger: ".o_form_view",
                },

                // Flow 4 -- Click OK on the confirmation dialog.
                {
                    content: "Click OK on the confirmation dialog",
                    trigger: ".modal-footer button.btn-primary",
                    in_modal: true,
                },

                // Post-Condition -- Document number returns to "/".
                //
                // The read-only title shows display_name, and
                // mixin.transaction.name_get renders the number "/" as
                // "*<id>", so the asterisk is the visible marker of the
                // reset. This is a real gate rather than a selector that
                // matches the previous screen too: setUp gives this
                // document a manual number ("TOURCIE-RESET-0001"), which
                // is exactly what the manual_number_ok Pre-Condition of
                // this IK allows a user to type, so the title carries no
                // asterisk before the button is clicked.
                {
                    content: "Document number is reset (display name shows *)",
                    trigger:
                        ".oe_title .o_field_widget[name='display_name']:contains(*)",
                    run: function () {
                        // Assertion only.
                    },
                },
            ]
        )
    );

    // IK: docs/customer_invoice_export/14-restart-approval.md
    tour.register(
        "ssi_customer_invoice_export_restart_approval",
        {
            test: true,
            url: "/web",
        },
        [].concat(
            // Flow 1 -- Open the Customer Invoice Exports menu.
            openCustomerInvoiceExportList(),
            [
                // Flow 2 -- Open the record whose approval process is
                // stalled.
                {
                    content: "Open the record",
                    trigger:
                        ".o_data_row:contains(TOUR CIE Restart Approval Type) .o_data_cell:first",
                    extra_trigger: ".o_list_view",
                },
                {
                    content: "Form is open",
                    trigger: ".o_form_view",
                    run: function () {
                        // Assertion only.
                    },
                },

                // Flow 3 -- Click the Restart Approval Process button.
                //
                // The button only shows while the document has no
                // approval template resolved, which is the second
                // Pre-Condition of this IK; setUp puts the document in
                // exactly that state.
                {
                    content: "Click the Restart Approval Process button",
                    trigger:
                        ".o_statusbar_buttons button[name='action_reload_approval_template']",
                    extra_trigger: ".o_form_view",
                },

                // Flow 4 -- Click OK on the confirmation dialog.
                {
                    content: "Click OK on the confirmation dialog",
                    trigger: ".modal-footer button.btn-primary",
                    in_modal: true,
                },

                // Post-Condition -- the existing approval records are
                // discarded and a new approval process is created from
                // the approval template that now matches the record. The
                // module ships a template matching every
                // customer_invoice_export document
                // (approval_template/customer_invoice_export.xml), so
                // this is the branch the tour walks. approval_ids is
                // hidden while the document has no approval record, so
                // this cannot pass before the button was actually
                // clicked.
                {
                    content: "Open the Approvals tab",
                    trigger: ".o_notebook .nav-link:contains(Approvals)",
                },
                {
                    content: "The Approvals tab lists an approval record",
                    trigger: ".o_field_widget[name='approval_ids'] .o_data_row",
                    run: function () {
                        // Assertion only.
                    },
                },

                // Post-Condition -- Status remains Waiting for Approval;
                // this action never changes the document's state.
                {
                    content: "Status is still Waiting for Approval",
                    trigger:
                        ".o_statusbar_status .o_arrow_button[data-value='confirm'].btn-primary",
                    run: function () {
                        // Assertion only.
                    },
                },
            ]
        )
    );

    // IK: docs/customer_invoice_export/15-requeue.md
    tour.register(
        "ssi_customer_invoice_export_requeue",
        {
            test: true,
            url: "/web",
        },
        [].concat(
            // Flow 1 -- Open the Customer Invoice Exports menu.
            openCustomerInvoiceExportList(),
            [
                // Flow 2 -- Open the record to requeue.
                {
                    content: "Open the record",
                    trigger:
                        ".o_data_row:contains(TOUR CIE Requeue Type) .o_data_cell:first",
                    extra_trigger: ".o_list_view",
                },
                {
                    content: "Form is open",
                    trigger: ".o_form_view",
                    run: function () {
                        // Assertion only.
                    },
                },

                // Flow 3 -- Open the Queue Processing tab.
                {
                    content: "Open the Queue Processing tab",
                    trigger: ".o_notebook .nav-link:contains(Queue Processing)",
                },

                // Flow 4 -- Click the Requeue button. This button carries
                // no confirm= attribute (Keputusan Desain, issue #24), so
                // -- unlike every other button in this file -- no dialog
                // step follows it.
                {
                    content: "Click the Requeue button",
                    trigger: ".o_form_view button[name='action_requeue_done']",
                },
                {
                    // Gerbang: same disable/enable idiom as Reload
                    // Template Policy in the create/edit tours above.
                    // action_requeue_done has no confirm= dialog, and
                    // requeuing an already-pending job produces no other
                    // DOM signal, so the button's own re-enable after the
                    // RPC completes is the only content-bearing gate
                    // available.
                    content: "Requeue call has completed",
                    trigger: "button[name='action_requeue_done']:enabled",
                    run: function () {
                        // Assertion only.
                    },
                },

                // Post-Condition -- Status remains Queue To Done, and
                // every job in the batch that was not yet Done is
                // requeued.
                {
                    content: "Status is still Queue To Done",
                    trigger:
                        ".o_statusbar_status .o_arrow_button[data-value='queue_done'].btn-primary",
                    run: function () {
                        // Assertion only.
                    },
                },
                {
                    content: "The Queue To Done group is still displayed",
                    trigger: ".o_field_widget[name='done_queue_job_batch_id']",
                    run: function () {
                        // Assertion only.
                    },
                },
                {
                    content: "The Requeue button is still rendered",
                    trigger: "button[name='action_requeue_done']",
                    run: function () {
                        // Assertion only.
                    },
                },
            ]
        )
    );

    // IK: docs/customer_invoice_export/16-recompute-queue-done-result.md
    tour.register(
        "ssi_customer_invoice_export_recompute_queue_done_result",
        {
            test: true,
            url: "/web",
        },
        [].concat(
            // Flow 1 -- Open the Customer Invoice Exports menu.
            openCustomerInvoiceExportList(),
            [
                // Flow 2 -- Open the record to recompute.
                {
                    content: "Open the record",
                    trigger:
                        ".o_data_row:contains(TOUR CIE Recompute Type) .o_data_cell:first",
                    extra_trigger: ".o_list_view",
                },
                {
                    content: "Form is open",
                    trigger: ".o_form_view",
                    run: function () {
                        // Assertion only.
                    },
                },

                // Flow 3 -- Open the Queue Processing tab.
                {
                    content: "Open the Queue Processing tab",
                    trigger: ".o_notebook .nav-link:contains(Queue Processing)",
                },

                // Flow 4 -- Click the Recompute Queue Done Result button.
                {
                    content: "Click the Recompute Queue Done Result button",
                    trigger:
                        ".o_form_view button[name='action_recompute_queue_done_result']",
                },

                // Flow 5 -- Click OK on the confirmation dialog.
                {
                    content: "Click OK on the confirmation dialog",
                    trigger: ".modal-footer button.btn-primary",
                    in_modal: true,
                },

                // Post-Condition -- setUp already marks the queued job
                // Done (but leaves the batch itself short of Finished, so
                // the transition below comes from this click, not from
                // setUp), so this recompute finds the To Done Queue Job
                // Batch Finished and transitions the document straight to
                // Done.
                {
                    content: "Status is Done",
                    trigger:
                        ".o_statusbar_status .o_arrow_button[data-value='done'].btn-primary",
                    run: function () {
                        // Assertion only.
                    },
                },
            ]
        )
    );
});
