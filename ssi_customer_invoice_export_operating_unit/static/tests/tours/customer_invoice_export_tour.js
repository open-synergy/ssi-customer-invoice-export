// Copyright 2026 OpenSynergy Indonesia
// Copyright 2026 PT. Simetri Sinergi Indonesia
// License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

odoo.define(
    "ssi_customer_invoice_export_operating_unit.customer_invoice_export_tour",
    function (require) {
        "use strict";

        var tour = require("web_tour.tour");

        // IK: docs/customer_invoice_export/01-create.md (this module's
        // delta over ssi_customer_invoice_export's own
        // docs/customer_invoice_export/01-create.md). Delta-only per this
        // module's Keputusan Desain: only the Operating Unit field is
        // exercised here -- the base Flow (Type, Date, Populate, Save,
        // ...) is out of scope and already covered by the base module's
        // own tours.
        tour.register(
            "ssi_customer_invoice_export_operating_unit_create",
            {
                test: true,
                url: "/web",
            },
            [
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
                    // bukan sekadar "ada list di layar" (lihat
                    // patterns.md skill odoo-development-ui-test §A).
                    content: "Customer Invoice Exports list is displayed",
                    trigger:
                        ".o_control_panel .breadcrumb-item.active:contains(Customer Invoice Exports)",
                    extra_trigger: ".o_list_view",
                    run: function () {
                        // Assertion only.
                    },
                },

                // Flow -- click New to open the document form.
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

                // Flow -- select the Operating Unit field. This is the
                // ONLY field this delta tour touches: base Flow fields
                // (Type, Date, Populate, ...) belong to the base module's
                // own tours, per Keputusan Desain. mixin.single_operating
                // _unit defaults operating_unit_id from the current
                // user's default operating unit, so the field may already
                // show a value here (e.g. oca "operating_unit" module's
                // "Main Operating Unit" data record, defaulted for
                // base.user_admin) -- typing over it and picking our own
                // fixture below proves the field is genuinely selectable,
                // not just pre-filled.
                {
                    content: "Select the Operating Unit",
                    trigger: ".o_field_many2one[name='operating_unit_id'] input",
                    extra_trigger: ".o_form_view.o_form_editable",
                    run: "text TOUR CIEOU Create",
                },
                {
                    content: "Pick the Operating Unit from the dropdown",
                    trigger:
                        ".ui-autocomplete .ui-menu-item a:contains(TOUR CIEOU Create)",
                    in_modal: false,
                },

                // Post-Condition -- the Operating Unit field displays the
                // selected value. `.o_external_button` on an editable
                // many2one is only shown once the field isSet() (Odoo 14
                // core, web/static/src/js/fields/relational_fields.js:
                // has_external_button = !noOpen && !floating && isSet()),
                // so it cannot be visible on a genuinely empty field.
                {
                    content: "Operating Unit field shows the filled value",
                    trigger:
                        ".o_field_many2one[name='operating_unit_id'] .o_external_button",
                    run: function () {
                        // Assertion only.
                    },
                },
            ]
        );
    }
);
