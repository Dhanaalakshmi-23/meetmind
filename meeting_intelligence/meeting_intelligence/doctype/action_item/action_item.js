// Copyright (c) 2026, Dhanaa Lakshmi and contributors
// For license information, please see license.txt

frappe.ui.form.on("Action Item", {
	refresh(frm) {
		if (frm.doc.status === "Overdue") {
			frm.dashboard.set_headline(
				__("This action is overdue by {0} day(s).", [frm.doc.days_overdue || 0]),
				"red"
			);
		}

		if (frm.doc.is_ghost) {
			frm.dashboard.set_headline(
				__("Ghost action: overdue beyond the configured threshold and at risk of never being completed."),
				"orange"
			);
		}

		if (
			frm.doc.docstatus === 0 &&
			!["Completed", "Cancelled"].includes(frm.doc.status)
		) {
			frm.add_custom_button(__("Mark Complete"), () => {
				frm.call("mark_complete").then(() => {
					frappe.show_alert({
						message: __("Action item completed."),
						indicator: "green",
					});
					frm.reload_doc();
				});
			});
		}
	},
});
