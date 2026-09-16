# Copyright (c) 2026, Dhanaa Lakshmi and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import date_diff, nowdate


def execute(filters=None):
	filters = frappe._dict(filters or {})

	conditions = []
	if filters.decision_status:
		conditions.append(["decision_status", "=", filters.decision_status])
	if filters.owner_participant:
		conditions.append(["owner_participant", "=", filters.owner_participant])
	if filters.only_zombies:
		conditions.append(["is_zombie", "=", 1])

	decisions = frappe.get_all(
		"Decision Log",
		filters=conditions,
		fields=[
			"name",
			"decision_title",
			"meeting_session",
			"owner_participant",
			"decision_status",
			"confidence_level",
			"revisit_count",
			"is_zombie",
			"zombie_since",
			"target_date",
			"previous_decision",
		],
		order_by="is_zombie desc, revisit_count desc",
	)

	participant_names = get_participant_names(
		{decision.owner_participant for decision in decisions if decision.owner_participant}
	)

	today = nowdate()
	data = []
	for decision in decisions:
		data.append(
			{
				"name": decision.name,
				"decision_title": decision.decision_title,
				"meeting_session": decision.meeting_session,
				"owner_participant": decision.owner_participant,
				"owner_name": participant_names.get(decision.owner_participant),
				"decision_status": decision.decision_status,
				"confidence_level": decision.confidence_level,
				"revisit_count": decision.revisit_count,
				"is_zombie": decision.is_zombie,
				"zombie_since": decision.zombie_since,
				"days_stuck": (
					date_diff(today, decision.zombie_since)
					if decision.is_zombie and decision.zombie_since
					else None
				),
				"target_date": decision.target_date,
				"previous_decision": decision.previous_decision,
			}
		)

	return get_columns(), data


def get_participant_names(participants):
	if not participants:
		return {}

	return dict(
		frappe.get_all(
			"Meeting Participant",
			filters=[["name", "in", list(participants)]],
			fields=["name", "participant_name"],
			as_list=True,
		)
	)


def get_columns():
	return [
		{
			"label": "Decision",
			"fieldname": "name",
			"fieldtype": "Link",
			"options": "Decision Log",
			"width": 140,
		},
		{"label": "Decision Title", "fieldname": "decision_title", "fieldtype": "Data", "width": 220},
		{
			"label": "Meeting",
			"fieldname": "meeting_session",
			"fieldtype": "Link",
			"options": "Meeting Session",
			"width": 130,
		},
		{
			"label": "Owner",
			"fieldname": "owner_participant",
			"fieldtype": "Link",
			"options": "Meeting Participant",
			"width": 140,
		},
		{"label": "Owner Name", "fieldname": "owner_name", "fieldtype": "Data", "width": 150},
		{"label": "Status", "fieldname": "decision_status", "fieldtype": "Data", "width": 110},
		{"label": "Confidence", "fieldname": "confidence_level", "fieldtype": "Data", "width": 100},
		{"label": "Revisits", "fieldname": "revisit_count", "fieldtype": "Int", "width": 80},
		{"label": "Zombie", "fieldname": "is_zombie", "fieldtype": "Check", "width": 80},
		{"label": "Zombie Since", "fieldname": "zombie_since", "fieldtype": "Date", "width": 110},
		{"label": "Days Stuck", "fieldname": "days_stuck", "fieldtype": "Int", "width": 100},
		{"label": "Target Date", "fieldname": "target_date", "fieldtype": "Date", "width": 110},
		{
			"label": "Previous Decision",
			"fieldname": "previous_decision",
			"fieldtype": "Link",
			"options": "Decision Log",
			"width": 140,
		},
	]
