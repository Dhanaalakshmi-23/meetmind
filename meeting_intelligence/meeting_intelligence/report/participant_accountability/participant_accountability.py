# Copyright (c) 2026, Dhanaa Lakshmi and contributors
# For license information, please see license.txt

import frappe


def execute(filters=None):
	filters = frappe._dict(filters or {})

	conditions = []
	if filters.participant_type:
		conditions.append(["participant_type", "=", filters.participant_type])
	if filters.department:
		conditions.append(["department", "=", filters.department])

	participants = frappe.get_all(
		"Meeting Participant",
		filters=conditions,
		fields=[
			"name",
			"participant_name",
			"participant_type",
			"department",
			"is_active",
			"meeting_count",
			"average_talk_percentage",
			"total_meeting_cost",
		],
		order_by="participant_name",
	)

	scores_by_participant = {
		score.participant: score
		for score in frappe.get_all(
			"Employee Ghost Score",
			fields=[
				"participant",
				"total_assigned",
				"total_completed",
				"total_overdue",
				"total_ghost",
				"ghost_score_pct",
				"completion_rate_pct",
				"risk_level",
			],
		)
	}

	data = []
	for participant in participants:
		score = scores_by_participant.get(participant.name, frappe._dict())
		if filters.risk_level and score.risk_level != filters.risk_level:
			continue

		data.append(
			{
				"name": participant.name,
				"participant_name": participant.participant_name,
				"participant_type": participant.participant_type,
				"department": participant.department,
				"is_active": participant.is_active,
				"meeting_count": participant.meeting_count,
				"average_talk_percentage": participant.average_talk_percentage,
				"total_meeting_cost": participant.total_meeting_cost,
				"total_assigned": score.get("total_assigned", 0),
				"total_completed": score.get("total_completed", 0),
				"total_overdue": score.get("total_overdue", 0),
				"total_ghost": score.get("total_ghost", 0),
				"ghost_score_pct": score.get("ghost_score_pct", 0),
				"completion_rate_pct": score.get("completion_rate_pct", 0),
				"risk_level": score.get("risk_level", "Low"),
			}
		)

	data.sort(key=lambda row: (-(row["ghost_score_pct"] or 0), row["participant_name"]))

	return get_columns(), data


def get_columns():
	return [
		{
			"label": "Participant",
			"fieldname": "name",
			"fieldtype": "Link",
			"options": "Meeting Participant",
			"width": 140,
		},
		{"label": "Participant Name", "fieldname": "participant_name", "fieldtype": "Data", "width": 180},
		{"label": "Type", "fieldname": "participant_type", "fieldtype": "Data", "width": 100},
		{"label": "Department", "fieldname": "department", "fieldtype": "Data", "width": 130},
		{"label": "Active", "fieldname": "is_active", "fieldtype": "Check", "width": 70},
		{"label": "Meetings", "fieldname": "meeting_count", "fieldtype": "Int", "width": 90},
		{"label": "Avg Talk %", "fieldname": "average_talk_percentage", "fieldtype": "Percent", "width": 100},
		{"label": "Total Meeting Cost", "fieldname": "total_meeting_cost", "fieldtype": "Currency", "width": 150},
		{"label": "Assigned", "fieldname": "total_assigned", "fieldtype": "Int", "width": 90},
		{"label": "Completed", "fieldname": "total_completed", "fieldtype": "Int", "width": 90},
		{"label": "Overdue", "fieldname": "total_overdue", "fieldtype": "Int", "width": 80},
		{"label": "Ghost", "fieldname": "total_ghost", "fieldtype": "Int", "width": 70},
		{"label": "Ghost Score %", "fieldname": "ghost_score_pct", "fieldtype": "Percent", "width": 110},
		{"label": "Completion %", "fieldname": "completion_rate_pct", "fieldtype": "Percent", "width": 110},
		{"label": "Risk Level", "fieldname": "risk_level", "fieldtype": "Data", "width": 100},
	]
