// Copyright (c) 2026, Dhanaa Lakshmi and contributors
// For license information, please see license.txt

frappe.query_reports["Participant Accountability"] = {
	filters: [
		{
			fieldname: "participant_type",
			label: __("Participant Type"),
			fieldtype: "Select",
			options: "\nInternal\nClient\nConsultant\nExternal",
		},
		{
			fieldname: "department",
			label: __("Department"),
			fieldtype: "Data",
		},
		{
			fieldname: "risk_level",
			label: __("Ghost Risk Level"),
			fieldtype: "Select",
			options: "\nLow\nMedium\nHigh\nCritical",
		},
	],
};
