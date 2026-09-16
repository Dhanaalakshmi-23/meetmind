# Copyright (c) 2026, Dhanaa Lakshmi and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime

class EmployeeGhostScore(Document):

    def validate(self):
        self.last_updated = now_datetime()


def get_risk_level(ghost_score_pct):
    if ghost_score_pct >= 50:
        return "Critical"

    if ghost_score_pct >= 25:
        return "High"

    if ghost_score_pct > 0:
        return "Medium"

    return "Low"


def update_participant_ghost_score(participant):
    if not participant or not frappe.db.exists("Meeting Participant", participant):
        return None

    assigned = frappe.db.count(
        "Action Item",
        {"assigned_to": participant, "status": ["!=", "Cancelled"]},
    )
    completed = frappe.db.count(
        "Action Item",
        {"assigned_to": participant, "status": "Completed"},
    )
    overdue = frappe.db.count(
        "Action Item",
        {"assigned_to": participant, "status": "Overdue"},
    )
    ghost = frappe.db.count(
        "Action Item",
        {"assigned_to": participant, "is_ghost": 1},
    )

    ghost_score_pct = (ghost * 100 / assigned) if assigned else 0
    completion_rate_pct = (completed * 100 / assigned) if assigned else 0

    values = {
        "total_assigned": assigned,
        "total_completed": completed,
        "total_overdue": overdue,
        "total_ghost": ghost,
        "ghost_score_pct": ghost_score_pct,
        "completion_rate_pct": completion_rate_pct,
        "risk_level": get_risk_level(ghost_score_pct),
        "last_updated": now_datetime(),
    }

    name = frappe.db.exists("Employee Ghost Score", {"participant": participant})

    if name:
        frappe.db.set_value("Employee Ghost Score", name, values, update_modified=False)
    else:
        doc = frappe.get_doc(
            {
                "doctype": "Employee Ghost Score",
                "participant": participant,
                **values,
            }
        )
        doc.insert(ignore_permissions=True)

        values["name"] = doc.name

    return values
