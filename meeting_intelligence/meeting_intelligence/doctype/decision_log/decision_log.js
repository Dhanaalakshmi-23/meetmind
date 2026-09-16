// Copyright (c) 2026, Dhanaa Lakshmi and contributors
// For license information, please see license.txt

frappe.ui.form.on("Decision Log", {
	refresh(frm) {
		if (frm.doc.is_zombie) {
			frm.dashboard.set_headline(
				__("Zombie decision: revisited {0} time(s) since {1}.", [
					frm.doc.revisit_count || 0,
					frm.doc.zombie_since ? frappe.datetime.str_to_user(frm.doc.zombie_since) : "-",
				]),
				"orange"
			);
		}

		if (frm.doc.is_zombie && is_active(frm.doc.decision_status)) {
			frm.add_custom_button(__("Resolve Zombie"), () => resolve_zombie(frm));
		}
	},
});

function is_active(status) {
	return ["Open", "In Progress", "Revisited"].includes(status);
}

function resolve_zombie(frm) {
	frappe.prompt(
		{
			fieldname: "resolution_note",
			fieldtype: "Small Text",
			label: __("Resolution Note"),
			description: __("Explain how this decision was finally settled."),
		},
		(values) => {
			frappe
				.call({
					method: "meeting_intelligence.api.close_zombie_decision",
					args: {
						decision: frm.doc.name,
						resolution_note: values.resolution_note,
					},
				})
				.then(() => {
					frappe.show_alert({
						message: __("Zombie decision resolved."),
						indicator: "green",
					});
					frm.reload_doc();
				});
		},
		__("Resolve Zombie Decision"),
		__("Resolve")
	);
}
