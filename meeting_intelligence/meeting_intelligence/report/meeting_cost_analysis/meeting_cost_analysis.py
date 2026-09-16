# Copyright (c) 2026, Dhanaa Lakshmi and contributors
# For license information, please see license.txt

import frappe


def execute(filters=None):
	filters = frappe._dict(filters or {})

	conditions = []
	if filters.department:
		conditions.append(["department", "=", filters.department])
	if filters.meeting_type:
		conditions.append(["meeting_type", "=", filters.meeting_type])
	if filters.from_date:
		conditions.append(["meeting_date", ">=", filters.from_date])
	if filters.to_date:
		conditions.append(["meeting_date", "<=", filters.to_date])

	sessions = frappe.get_all(
		"Meeting Session",
		filters=conditions,
		fields=[
			"name",
			"meeting_title",
			"meeting_date",
			"meeting_type",
			"department",
			"duration_minutes",
			"meeting_cost",
			"health_score",
			"health_label",
		],
		order_by="meeting_date desc",
	)

	attendee_counts = get_attendee_counts([session.name for session in sessions])

	data = []
	for session in sessions:
		data.append(
			{
				"name": session.name,
				"meeting_title": session.meeting_title,
				"meeting_date": session.meeting_date,
				"meeting_type": session.meeting_type,
				"department": session.department,
				"duration_minutes": session.duration_minutes,
				"attendee_count": attendee_counts.get(session.name, 0),
				"meeting_cost": session.meeting_cost,
				"health_score": session.health_score,
				"health_label": session.health_label,
			}
		)

	return get_columns(), data


def get_attendee_counts(session_names):
	if not session_names:
		return {}

	rows = frappe.get_all(
		"Meeting Attendee",
		filters={
			"parenttype": "Meeting Session",
			"parent": ["in", session_names],
			"attended": 1,
		},
		fields=["parent", {"COUNT": "name", "as": "attendee_count"}],
		group_by="parent",
	)

	return {row.parent: row.attendee_count for row in rows}


def get_columns():
	return [
		{
			"label": "Meeting ID",
			"fieldname": "name",
			"fieldtype": "Link",
			"options": "Meeting Session",
			"width": 140,
		},
		{"label": "Meeting Title", "fieldname": "meeting_title", "fieldtype": "Data", "width": 220},
		{"label": "Date", "fieldname": "meeting_date", "fieldtype": "Date", "width": 100},
		{"label": "Meeting Type", "fieldname": "meeting_type", "fieldtype": "Data", "width": 110},
		{"label": "Department", "fieldname": "department", "fieldtype": "Data", "width": 130},
		{"label": "Duration (min)", "fieldname": "duration_minutes", "fieldtype": "Int", "width": 110},
		{"label": "Attendees", "fieldname": "attendee_count", "fieldtype": "Int", "width": 90},
		{"label": "Total Cost", "fieldname": "meeting_cost", "fieldtype": "Currency", "width": 130},
		{"label": "Health Score", "fieldname": "health_score", "fieldtype": "Int", "width": 100},
		{"label": "Health Label", "fieldname": "health_label", "fieldtype": "Data", "width": 120},
	]
