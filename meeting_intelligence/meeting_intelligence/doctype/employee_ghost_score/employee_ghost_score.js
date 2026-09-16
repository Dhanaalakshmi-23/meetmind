// Copyright (c) 2026, Dhanaa Lakshmi and contributors
// For license information, please see license.txt

frappe.ui.form.on("Employee Ghost Score", {
	refresh(frm) {
		frm.disable_save();
		frm.set_intro(
			__(
				"This score is generated automatically by MeetMind from action item behaviour. Open the participant and run Refresh Metrics to update it."
			)
		);

		const colors = {
			Critical: "red",
			High: "orange",
			Medium: "yellow",
			Low: "green",
		};

		frm.dashboard.set_headline(
			__("Ghost Score: {0}% · Risk: {1}", [flt(frm.doc.ghost_score_pct), frm.doc.risk_level || "-"]),
			colors[frm.doc.risk_level] || "blue"
		);
	},
});
