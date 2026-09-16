// Copyright (c) 2026, Dhanaa Lakshmi and contributors
// For license information, please see license.txt

frappe.query_reports["Meeting Cost Analysis"] = {
	filters: [
		{
			fieldname: "department",
			label: __("Department"),
			fieldtype: "Data",
		},
		{
			fieldname: "meeting_type",
			label: __("Meeting Type"),
			fieldtype: "Select",
			options: "\nPlanning\nReview\nStandup\nStrategy\nCrisis\nRetrospective",
		},
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
			default: frappe.datetime.add_months(frappe.datetime.get_today(), -3),
		},
		{
			fieldname: "to_date",
			label: __("To Date"),
			fieldtype: "Date",
			default: frappe.datetime.get_today(),
		},
	],
};
