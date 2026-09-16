# Copyright (c) 2026, Dhanaa Lakshmi and contributors
# For license information, please see license.txt

import frappe


def execute(filters=None):
	filters = frappe._dict(filters or {})

	conditions = []
	if filters.from_date:
		conditions.append(["meeting_date", ">=", filters.from_date])
	if filters.to_date:
		conditions.append(["meeting_date", "<=", filters.to_date])
	if filters.department:
		conditions.append(["department", "=", filters.department])

	sessions = frappe.get_all(
		"Meeting Session",
		filters=conditions,
		fields=[
			"meeting_date",
			"duration_minutes",
			"meeting_cost",
			"health_score",
			"health_label",
			"has_monologue",
		],
		order_by="meeting_date",
	)

	grouped = {}
	for session in sessions:
		month = session.meeting_date.strftime("%Y-%m") if session.meeting_date else "Unscheduled"
		summary = grouped.setdefault(
			month,
			{
				"month": month,
				"meeting_count": 0,
				"total_duration": 0,
				"total_cost": 0.0,
				"health_total": 0,
				"excellent": 0,
				"good": 0,
				"below_average": 0,
				"poor": 0,
				"monologue_count": 0,
			},
		)
		summary["meeting_count"] += 1
		summary["total_duration"] += session.duration_minutes or 0
		summary["total_cost"] += session.meeting_cost or 0
		summary["health_total"] += session.health_score or 0

		if session.health_label == "Excellent":
			summary["excellent"] += 1
		elif session.health_label == "Good":
			summary["good"] += 1
		elif session.health_label == "Below Average":
			summary["below_average"] += 1
		elif session.health_label == "Poor":
			summary["poor"] += 1

		if session.has_monologue:
			summary["monologue_count"] += 1

	data = []
	for month in sorted(grouped):
		summary = grouped[month]
		data.append(
			{
				"month": summary["month"],
				"meeting_count": summary["meeting_count"],
				"total_duration": summary["total_duration"],
				"total_cost": summary["total_cost"],
				"average_cost": (summary["total_cost"] / summary["meeting_count"]) if summary["meeting_count"] else 0,
				"average_health_score": (
					summary["health_total"] / summary["meeting_count"] if summary["meeting_count"] else 0
				),
				"excellent": summary["excellent"],
				"good": summary["good"],
				"below_average": summary["below_average"],
				"poor": summary["poor"],
				"monologue_count": summary["monologue_count"],
			}
		)

	return get_columns(), data


def get_columns():
	return [
		{"label": "Month", "fieldname": "month", "fieldtype": "Data", "width": 100},
		{"label": "Meetings", "fieldname": "meeting_count", "fieldtype": "Int", "width": 90},
		{"label": "Total Duration (min)", "fieldname": "total_duration", "fieldtype": "Int", "width": 140},
		{"label": "Total Cost", "fieldname": "total_cost", "fieldtype": "Currency", "width": 130},
		{"label": "Avg Cost / Meeting", "fieldname": "average_cost", "fieldtype": "Currency", "width": 150},
		{"label": "Avg Health Score", "fieldname": "average_health_score", "fieldtype": "Float", "width": 130},
		{"label": "Excellent", "fieldname": "excellent", "fieldtype": "Int", "width": 90},
		{"label": "Good", "fieldname": "good", "fieldtype": "Int", "width": 70},
		{"label": "Below Average", "fieldname": "below_average", "fieldtype": "Int", "width": 110},
		{"label": "Poor", "fieldname": "poor", "fieldtype": "Int", "width": 70},
		{"label": "With Monologue", "fieldname": "monologue_count", "fieldtype": "Int", "width": 130},
	]
