# Copyright (c) 2026, Dhanaa Lakshmi and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import cint, date_diff, nowdate

class ActionItem(Document):

    def validate(self):
        self.validate_completion_percentage()
        self.update_completion_state()
        self.update_overdue_state()

    def validate_completion_percentage(self):
        completion_pct = cint(self.completion_pct)

        if completion_pct < 0 or completion_pct > 100:
            frappe.throw("Completion (%) must be between 0 and 100.")

    def update_completion_state(self):
        if self.status == "Completed":
            self.completion_pct = 100
            self.days_overdue = 0
            self.is_ghost = 0

            if not self.completed_on:
                self.completed_on = nowdate()
        else:
            self.completed_on = None

    def update_overdue_state(self):
        if self.status in ("Completed", "Cancelled"):
            self.days_overdue = 0
            self.is_ghost = 0

            return

        days = date_diff(nowdate(), self.due_date)

        if days > 0:
            self.days_overdue = days
            self.is_ghost = get_ghost_flag(days)

            if self.status in ("Open", "In Progress"):
                self.status = "Overdue"
        else:
            self.days_overdue = 0
            self.is_ghost = 0

            if self.status == "Overdue":
                self.status = "Open"

    @frappe.whitelist()
    def mark_complete(self):
        self.check_permission("write")

        if self.docstatus == 0:
            self.status = "Completed"
            self.save()

            return

        frappe.db.set_value(
            "Action Item",
            self.name,
            {
                "status": "Completed",
                "completion_pct": 100,
                "days_overdue": 0,
                "is_ghost": 0,
                "completed_on": nowdate(),
            },
            update_modified=False,
        )

        update_session_action_count(self)
        update_participant_ghost_score(self.assigned_to)


def get_ghost_flag(days_overdue):
    values = frappe.get_singles_dict("Meeting Config")
    threshold = cint(values.get("ghost_threshold_days")) or 7

    return 1 if days_overdue > threshold else 0


def update_session_action_count(doc, method=None):
    count = frappe.db.count(
        "Action Item",
        {
            "meeting_session": doc.meeting_session,
            "status": ("in", ("Open", "In Progress", "Overdue")),
        },
    )

    frappe.db.set_value(
        "Meeting Session",
        doc.meeting_session,
        "open_actions_count",
        count,
        update_modified=False,
    )

    update_participant_ghost_score(doc.assigned_to)


def update_session_action_count_on_trash(doc, method=None):
    count = frappe.db.count(
        "Action Item",
        {
            "meeting_session": doc.meeting_session,
            "name": ["!=", doc.name],
            "status": ("in", ("Open", "In Progress", "Overdue")),
        },
    )

    frappe.db.set_value(
        "Meeting Session",
        doc.meeting_session,
        "open_actions_count",
        count,
        update_modified=False,
    )

    update_participant_ghost_score(doc.assigned_to)


def update_participant_ghost_score(participant):
    from meeting_intelligence.meeting_intelligence.doctype.employee_ghost_score.employee_ghost_score import (
        update_participant_ghost_score as refresh_score,
    )

    refresh_score(participant)
