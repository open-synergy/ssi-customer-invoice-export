// Copyright 2026 OpenSynergy Indonesia
// Copyright 2026 PT. Simetri Sinergi Indonesia
// License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

odoo.define(
    "ssi_customer_invoice_export.customer_invoice_export_type_tour",
    function (require) {
        "use strict";

        var tour = require("web_tour.tour");

        // Shared navigation block reused by every tour below -- corresponds
        // to Flow 1 of every customer_invoice_export_type IK: "Open the
        // Financial Accounting > Configuration > Customer Invoice Export
        // Types menu."
        function openCustomerInvoiceExportTypeList() {
            return [
                tour.stepUtils.showAppsMenuItem(),
                {
                    content: "Open the Financial Accounting app",
                    trigger:
                        '.o_app[data-menu-xmlid="ssi_financial_accounting.menu_root_financial_accounting"]',
                },
                {
                    content: "Open the Configuration menu",
                    trigger:
                        '.o_menu_sections [data-menu-xmlid="ssi_financial_accounting.menu_financial_accounting_configuration"]',
                },
                {
                    content: "Open the Customer Invoice Export Types menu",
                    trigger:
                        '.o_menu_sections [data-menu-xmlid="ssi_customer_invoice_export.customer_invoice_export_type_menu"]',
                },
                {
                    // Gerbang: tunggu action TUJUAN benar-benar terpasang,
                    // bukan sekadar "ada list di layar" (lihat patterns.md
                    // skill odoo-development-ui-test §A).
                    content: "Customer Invoice Export Types list is displayed",
                    trigger:
                        ".o_control_panel .breadcrumb-item.active:contains(Customer Invoice Export Types)",
                    extra_trigger: ".o_list_view",
                    run: function () {
                        // Assertion only.
                    },
                },
            ];
        }

        // IK: docs/customer_invoice_export_type/01-create.md
        tour.register(
            "ssi_customer_invoice_export_type_create",
            {
                test: true,
                url: "/web",
            },
            [].concat(
                // Flow 1 -- Open the Financial Accounting > Configuration >
                // Customer Invoice Export Types menu.
                openCustomerInvoiceExportTypeList(),
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

                    // Flow 3 -- Fill in the required fields: Name, Code
                    // (left as "/" so Generate Code below has something to
                    // do -- Flow step 4).
                    {
                        content: "Fill in the Name",
                        trigger: ".o_field_widget[name='name']",
                        extra_trigger: ".o_form_view.o_form_editable",
                        run: "text TOUR CIET Create",
                    },
                    {
                        content: "Fill in the Code",
                        trigger: ".o_field_widget[name='code']",
                        run: "text /",
                    },

                    // Flow 4 -- Click Generate Code in the header.
                    {
                        content: "Click Generate Code",
                        trigger:
                            ".o_statusbar_buttons button[name='action_generate_code']",
                    },
                    {
                        // Gerbang: tunggu RPC action_generate_code (auto-save
                        // + write + reload) selesai sebelum langkah
                        // berikutnya (lihat patterns.md §M "Menunggu UI tak
                        // lagi terblokir").
                        content: "Generate Code call has completed",
                        trigger: "body:not(.o_ui_blocked)",
                        run: function () {
                            // Assertion only.
                        },
                    },

                    // Flow 5 -- On the Output Option tab, the Default Output
                    // Format field is displayed (its "csv" default already
                    // satisfies the required constraint -- verifying the
                    // stored value is unit test territory).
                    {
                        content: "Open the Output Option tab",
                        trigger: ".o_notebook .nav-link:contains(Output Option)",
                    },
                    {
                        content: "Default Output Format field is displayed",
                        trigger: ".o_field_widget[name='default_output_format']",
                        run: function () {
                            // Assertion only.
                        },
                    },

                    // Flow 6 -- On the Journal Criteria tab, Journal
                    // Selection Method is displayed and its "domain" default
                    // reveals the Journal Domain field (attrs-driven
                    // visibility).
                    {
                        content: "Open the Journal Criteria tab",
                        trigger: ".o_notebook .nav-link:contains(Journal Criteria)",
                    },
                    {
                        content: "Journal Selection Method field is displayed",
                        trigger: ".o_field_widget[name='journal_selection_method']",
                        run: function () {
                            // Assertion only.
                        },
                    },
                    {
                        content: "Journal Domain field is displayed",
                        trigger: ".o_field_widget[name='journal_domain']",
                        run: function () {
                            // Assertion only.
                        },
                    },

                    // Flow 7 -- On the Partner Criteria tab, Partner
                    // Selection Method is displayed and its "domain" default
                    // reveals the Partner Domain field.
                    {
                        content: "Open the Partner Criteria tab",
                        trigger: ".o_notebook .nav-link:contains(Partner Criteria)",
                    },
                    {
                        content: "Partner Selection Method field is displayed",
                        trigger: ".o_field_widget[name='partner_selection_method']",
                        run: function () {
                            // Assertion only.
                        },
                    },
                    {
                        content: "Partner Domain field is displayed",
                        trigger: ".o_field_widget[name='partner_domain']",
                        run: function () {
                            // Assertion only.
                        },
                    },

                    // Flow 8 -- On the Product Criteria tab, Product
                    // Selection Method is displayed and its "domain" default
                    // reveals the Product Domain field.
                    {
                        content: "Open the Product Criteria tab",
                        trigger: ".o_notebook .nav-link:contains(Product Criteria)",
                    },
                    {
                        content: "Product Selection Method field is displayed",
                        trigger: ".o_field_widget[name='product_selection_method']",
                        run: function () {
                            // Assertion only.
                        },
                    },
                    {
                        content: "Product Domain field is displayed",
                        trigger: ".o_field_widget[name='product_domain']",
                        run: function () {
                            // Assertion only.
                        },
                    },

                    // Flow 9 -- On the Parser tab, Parser Python Code is
                    // displayed (its "result = []" default already
                    // satisfies the required constraint).
                    {
                        content: "Open the Parser tab",
                        trigger: ".o_notebook .nav-link:contains(Parser)",
                    },
                    {
                        content: "Parser Python Code field is displayed",
                        trigger: ".o_field_widget[name='parser_python_code']",
                        run: function () {
                            // Assertion only.
                        },
                    },

                    // Flow 10 -- Click Save.
                    {
                        content: "Save the record",
                        trigger: ".o_form_button_save",
                    },

                    // Post-Condition -- a new Customer Invoice Export Type
                    // record is created (its availability for selection on
                    // a Customer Invoice Export document is exercised by the
                    // customer_invoice_export tour, out of this tour's
                    // scope).
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

        // IK: docs/customer_invoice_export_type/02-edit.md
        tour.register(
            "ssi_customer_invoice_export_type_edit",
            {
                test: true,
                url: "/web",
            },
            [].concat(
                // Flow 1 -- Open the Customer Invoice Export Types menu.
                openCustomerInvoiceExportTypeList(),
                [
                    // Flow 2 -- Find and open the record to edit.
                    {
                        content: "Open the record",
                        trigger:
                            ".o_data_row:contains(TOUR CIET Edit) .o_data_cell:first",
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

                    // Flow 3 -- Change the required fields.
                    {
                        content: "Change the Name",
                        trigger: ".o_field_widget[name='name']",
                        run: "text TOUR CIET Edit Changed",
                    },

                    // Flow 4 -- Code still shows "/" (set by setUpClass) --
                    // click Generate Code in the header.
                    {
                        content: "Click Generate Code",
                        trigger:
                            ".o_statusbar_buttons button[name='action_generate_code']",
                    },
                    {
                        // Gerbang -- lihat catatan gerbang di tour create
                        // di atas.
                        content: "Generate Code call has completed",
                        trigger: "body:not(.o_ui_blocked)",
                        run: function () {
                            // Assertion only.
                        },
                    },

                    // Flow 5 -- Click Save.
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

        // IK: docs/customer_invoice_export_type/03-delete.md
        tour.register(
            "ssi_customer_invoice_export_type_delete",
            {
                test: true,
                url: "/web",
            },
            [].concat(
                // Flow 1 -- Open the Customer Invoice Export Types menu.
                openCustomerInvoiceExportTypeList(),
                [
                    // Flow 2 -- Select the record to delete (checkbox).
                    {
                        content: "Select the record to delete",
                        trigger:
                            ".o_data_row:contains(TOUR CIET Delete) .o_list_record_selector input",
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
                            ".o_list_view:not(:has(.o_data_row:contains(TOUR CIET Delete)))",
                        run: function () {
                            // Assertion only.
                        },
                    },
                ]
            )
        );

        // IK: docs/customer_invoice_export_type/04-deactivate.md
        tour.register(
            "ssi_customer_invoice_export_type_deactivate",
            {
                test: true,
                url: "/web",
            },
            [].concat(
                // Flow 1 -- Open the Customer Invoice Export Types menu.
                openCustomerInvoiceExportTypeList(),
                [
                    // Flow 2 -- Select the record to deactivate (checkbox).
                    {
                        content: "Select the record to deactivate",
                        trigger:
                            ".o_data_row:contains(TOUR CIET Deactivate) .o_list_record_selector input",
                        run: "click",
                    },

                    // Flow 3 -- Click Action > Archive.
                    {
                        content: "Open the Action menu",
                        trigger: ".o_cp_action_menus button:contains(Action)",
                    },
                    {
                        content: "Click Archive",
                        trigger: ".o_cp_action_menus .o_menu_item a",
                        run: function () {
                            var $archive = $(
                                ".o_cp_action_menus .o_menu_item a"
                            ).filter(function () {
                                return $(this).text().trim() === "Archive";
                            });
                            $archive[0].click();
                        },
                    },

                    // Flow 4 -- Click OK to confirm.
                    {
                        content: "Confirm the dialog",
                        trigger: ".modal-footer button.btn-primary",
                        in_modal: true,
                    },

                    // Post-Condition -- the record is archived and no longer
                    // appears in the default (active) list view. (Its
                    // unavailability on new Customer Invoice Export
                    // documents, and that existing documents already using
                    // it are unaffected, are not kasatmata UI facts -- out
                    // of tour scope.)
                    {
                        content: "Record no longer appears in the active list",
                        trigger:
                            ".o_list_view:not(:has(.o_data_row:contains(TOUR CIET Deactivate)))",
                        run: function () {
                            // Assertion only.
                        },
                    },
                ]
            )
        );

        // IK: docs/customer_invoice_export_type/05-activate.md
        tour.register(
            "ssi_customer_invoice_export_type_activate",
            {
                test: true,
                url: "/web",
            },
            [].concat(
                // Flow 1 -- Open the Customer Invoice Export Types menu.
                openCustomerInvoiceExportTypeList(),
                [
                    // Flow 2 -- Enable the Archived filter in the search
                    // bar.
                    {
                        content: "Open the Filters menu",
                        trigger: ".o_filter_menu .o_dropdown_toggler_btn",
                        // 14.0: the Filters dropdown is an Owl component
                        // that does not always open on a synthetic click --
                        // use a real browser click (patterns.md skill
                        // odoo-development-ui-test §I/§J).
                        run: function () {
                            this.$anchor[0].click();
                        },
                    },
                    {
                        content: "Enable the Archived filter",
                        trigger: ".o_filter_menu .o_menu_item a:contains(Archived)",
                        run: function () {
                            this.$anchor[0].click();
                        },
                    },

                    // Flow 3 -- Select the record to reactivate (checkbox).
                    {
                        content: "Select the record to reactivate",
                        trigger:
                            ".o_data_row:contains(TOUR CIET Activate) .o_list_record_selector input",
                        run: "click",
                    },

                    // Flow 4 -- Click Action > Unarchive.
                    {
                        content: "Open the Action menu",
                        trigger: ".o_cp_action_menus button:contains(Action)",
                    },
                    {
                        content: "Click Unarchive",
                        trigger: ".o_cp_action_menus .o_menu_item a",
                        run: function () {
                            var $unarchive = $(
                                ".o_cp_action_menus .o_menu_item a"
                            ).filter(function () {
                                return $(this).text().trim() === "Unarchive";
                            });
                            $unarchive[0].click();
                        },
                    },

                    // Flow 5 (IK text) -- "Click OK to confirm." Verified
                    // against Odoo 14.0 core
                    // (web/static/src/js/views/list/list_controller.js
                    // `_getActionMenuItems`): only the "Archive" action
                    // wraps its callback in `Dialog.confirm(...)`;
                    // "Unarchive" calls `_toggleArchiveState(false)`
                    // directly with no confirmation dialog. There is
                    // therefore no dialog step to add here -- this is the
                    // same known inaccuracy in the IK text already noted in
                    // ssi_customer_invoice's customer_invoice_type_tour.js
                    // and ssi_vendor_bill's vendor_bill_type_tour.js, out of
                    // scope for this tour-only change.

                    // Enabling/disabling the Archived filter re-opens the
                    // Filters dropdown -- selecting "Unarchive" above closed
                    // it (any click outside the dropdown closes it; see
                    // web.DropdownMenu `_onWindowClick`).
                    {
                        content: "Open the Filters menu again",
                        trigger: ".o_filter_menu .o_dropdown_toggler_btn",
                        run: function () {
                            this.$anchor[0].click();
                        },
                    },
                    {
                        content: "Disable the Archived filter",
                        trigger: ".o_filter_menu .o_menu_item a:contains(Archived)",
                        run: function () {
                            this.$anchor[0].click();
                        },
                    },

                    // Post-Condition -- the record is restored and appears
                    // again in the default (active) list view.
                    {
                        content: "Record appears again in the active list",
                        trigger: ".o_data_row:contains(TOUR CIET Activate)",
                        run: function () {
                            // Assertion only.
                        },
                    },
                ]
            )
        );
    }
);
