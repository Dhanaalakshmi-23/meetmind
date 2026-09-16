// Copyright (c) 2026, Dhanaa Lakshmi and contributors
// For license information, please see license.txt

frappe.query_reports["Zombie Decision Tracker"] = {
	filters: [
		{
			fieldname: "decision_status",
			label: __("Status"),
			fieldtype: "Select",
			options: "\nOpen\nIn Progress\nCompleted\nAbandoned\nRevisited",
		},
		{
			fieldname: "owner_participant",
			label: __("Owner"),
			fieldtype: "Link",
			options: "Meeting Participant",
		},
		{
			fieldname: "only_zombies",
			label: __("Only Zombie Decisions"),
			fieldtype: "Check",
			default: 1,
		},
	],
};
