// Copyright (c) 2026, Dhanaa Lakshmi and contributors
// For license information, please see license.txt

frappe.ui.form.on("Meeting Participant", {
	refresh(frm) {
		frm.add_custom_button(__("Refresh Metrics"), () => {
			frappe
				.call({
					method:
						"meeting_intelligence.meeting_intelligence.doctype.meeting_participant.meeting_participant.refresh_metrics",
					args: { participant: frm.doc.name },
				})
				.then((r) => {
					if (r.message) {
						frappe.show_alert({
							message: __("Metrics updated: {0} meeting(s)", [r.message.meeting_count]),
							indicator: "green",
						});
					}

					frm.reload_doc();
				});
		});
	},
});
