# Copyright (c) 2026, Dhanaa Lakshmi and Contributors
# See license.txt

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import add_days, nowdate

from meeting_intelligence.meeting_intelligence.doctype.employee_ghost_score.employee_ghost_score import (
    get_risk_level,
    update_participant_ghost_score,
)

EXTRA_TEST_RECORD_DEPENDENCIES = []
IGNORE_TEST_RECORD_DEPENDENCIES = []


def make_participant(suffix):
    doc = frappe.get_doc(
        {
            "doctype": "Meeting Participant",
            "participant_name": f"TEST {suffix}",
            "participant_type": "Internal",
            "email": f"{suffix.lower()}.ghost@test.example.com",
            "designation": "Engineer",
            "department": "QA",
            "annual_ctc": 844800,
        }
    )
    doc.insert()

    return doc


def make_session(participant):
    doc = frappe.get_doc(
        {
            "doctype": "Meeting Session",
            "meeting_title": f"TEST Session {frappe.generate_hash(length=6)}",
            "meeting_type": "Planning",
            "department": "QA",
            "meeting_date": nowdate(),
            "start_time": "10:00:00",
            "duration_minutes": 60,
            "agenda": "<p>Ghost score setup.</p>",
            "agenda_followed": "Yes",
            "attendees": [
                {"participant": participant.name, "talk_percentage": 100, "attended": 1}
            ],
        }
    )
    doc.insert()

    return doc


def make_action(session, participant, task_title, due_in_days, status="Open"):
    doc = frappe.get_doc(
        {
            "doctype": "Action Item",
            "meeting_session": session.name,
            "task_title": task_title,
            "assigned_to": participant.name,
            "assigned_by": participant.name,
            "due_date": add_days(nowdate(), due_in_days),
            "priority": "Medium",
            "status": status,
        }
    )
    doc.insert()

    return doc


class IntegrationTestEmployeeGhostScore(IntegrationTestCase):
    """Integration tests for Employee Ghost Score."""

    @classmethod
    def tearDownClass(cls):
        frappe.db.delete("Action Item", {"task_title": ("like", "TEST%")})
        frappe.db.delete("Meeting Session", {"meeting_title": ("like", "TEST%")})
        participants = frappe.get_all(
            "Meeting Participant",
            filters={"email": ("like", "%@test.example.com")},
            pluck="name",
        )

        if participants:
            frappe.db.delete("Employee Ghost Score", {"participant": ("in", participants)})
            frappe.db.delete("Meeting Participant", {"email": ("like", "%@test.example.com")})

    def test_risk_level_boundaries(self):
        self.assertEqual(get_risk_level(0), "Low")
        self.assertEqual(get_risk_level(10), "Medium")
        self.assertEqual(get_risk_level(24.9), "Medium")
        self.assertEqual(get_risk_level(25), "High")
        self.assertEqual(get_risk_level(49.9), "High")
        self.assertEqual(get_risk_level(50), "Critical")

    def test_update_participant_ghost_score(self):
        original = frappe.get_singles_dict("Meeting Config")

        try:
            frappe.db.set_single_value("Meeting Config", "ghost_threshold_days", 7)

            owner = make_participant("Owner")
            session = make_session(owner)

            make_action(session, owner, "TEST-Completed task", 5, status="Completed")
            make_action(session, owner, "TEST-Ghost task", -10)
            make_action(session, owner, "TEST-Healthy task", 5)

            values = update_participant_ghost_score(owner.name)

            self.assertEqual(values["total_assigned"], 3)
            self.assertEqual(values["total_completed"], 1)
            self.assertEqual(values["total_overdue"], 1)
            self.assertEqual(values["total_ghost"], 1)
            self.assertAlmostEqual(values["ghost_score_pct"], 33.33, places=2)
            self.assertAlmostEqual(values["completion_rate_pct"], 33.33, places=2)
            self.assertEqual(values["risk_level"], "High")

            score = frappe.get_doc("Employee Ghost Score", {"participant": owner.name})

            self.assertEqual(score.total_ghost, 1)
            self.assertAlmostEqual(score.ghost_score_pct, 33.33, places=2)
            self.assertEqual(score.risk_level, "High")
        finally:
            for key, value in original.items():
                frappe.db.set_single_value("Meeting Config", key, value)
