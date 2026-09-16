# Copyright (c) 2026, Dhanaa Lakshmi and Contributors
# See license.txt

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import add_days, nowdate

EXTRA_TEST_RECORD_DEPENDENCIES = []
IGNORE_TEST_RECORD_DEPENDENCIES = []


def make_participant(suffix):
    doc = frappe.get_doc(
        {
            "doctype": "Meeting Participant",
            "participant_name": f"TEST {suffix}",
            "participant_type": "Internal",
            "email": f"{suffix.lower()}.action@test.example.com",
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
            "agenda": "<p>Action setup.</p>",
            "agenda_followed": "Yes",
            "attendees": [
                {"participant": participant.name, "talk_percentage": 100, "attended": 1}
            ],
        }
    )
    doc.insert()

    return doc


def make_action(session, participant, due_in_days, status="Open", **overrides):
    values = {
        "doctype": "Action Item",
        "meeting_session": session.name,
        "task_title": f"TEST-{frappe.generate_hash(length=8)}",
        "assigned_to": participant.name,
        "assigned_by": participant.name,
        "due_date": add_days(nowdate(), due_in_days),
        "priority": "Medium",
        "status": status,
    }
    values.update(overrides)

    doc = frappe.get_doc(values)
    doc.insert()

    return doc


class IntegrationTestActionItem(IntegrationTestCase):
    """Integration tests for Action Item."""

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

    def test_overdue_beyond_threshold_becomes_ghost(self):
        original = frappe.get_singles_dict("Meeting Config")

        try:
            frappe.db.set_single_value("Meeting Config", "ghost_threshold_days", 7)

            owner = make_participant("Owner")
            session = make_session(owner)
            action = make_action(session, owner, -10)

            self.assertEqual(action.status, "Overdue")
            self.assertEqual(action.days_overdue, 10)
            self.assertEqual(action.is_ghost, 1)
        finally:
            for key, value in original.items():
                frappe.db.set_single_value("Meeting Config", key, value)

    def test_overdue_below_threshold_is_not_ghost(self):
        owner = make_participant("Owner")
        session = make_session(owner)
        action = make_action(session, owner, -3)

        self.assertEqual(action.status, "Overdue")
        self.assertEqual(action.days_overdue, 3)
        self.assertEqual(action.is_ghost, 0)

    def test_future_due_date_stays_open(self):
        owner = make_participant("Owner")
        session = make_session(owner)
        action = make_action(session, owner, 5)

        self.assertEqual(action.status, "Open")
        self.assertEqual(action.days_overdue, 0)
        self.assertEqual(action.is_ghost, 0)

    def test_completion_percentage_bounds(self):
        owner = make_participant("Owner")
        session = make_session(owner)

        with self.assertRaises(frappe.ValidationError):
            make_action(session, owner, 5, completion_pct=150)

    def test_completed_action_clears_overdue_state(self):
        owner = make_participant("Owner")
        session = make_session(owner)
        action = make_action(session, owner, -10, status="Completed")

        self.assertEqual(action.completion_pct, 100)
        self.assertEqual(action.days_overdue, 0)
        self.assertEqual(action.is_ghost, 0)
        self.assertTrue(action.completed_on)

    def test_mark_complete_updates_counts_and_score(self):
        original = frappe.get_singles_dict("Meeting Config")

        try:
            frappe.db.set_single_value("Meeting Config", "ghost_threshold_days", 7)

            owner = make_participant("Owner")
            session = make_session(owner)
            action = make_action(session, owner, -10)

            self.assertEqual(
                frappe.db.get_value("Meeting Session", session.name, "open_actions_count"),
                1,
            )

            action.mark_complete()

            status, completion_pct, days_overdue, is_ghost, completed_on = frappe.db.get_value(
                "Action Item",
                action.name,
                ["status", "completion_pct", "days_overdue", "is_ghost", "completed_on"],
            )

            self.assertEqual(status, "Completed")
            self.assertEqual(completion_pct, 100)
            self.assertEqual(days_overdue, 0)
            self.assertEqual(is_ghost, 0)
            self.assertTrue(completed_on)

            self.assertEqual(
                frappe.db.get_value("Meeting Session", session.name, "open_actions_count"),
                0,
            )
            self.assertTrue(
                frappe.db.get_value("Employee Ghost Score", {"participant": owner.name})
            )
        finally:
            for key, value in original.items():
                frappe.db.set_single_value("Meeting Config", key, value)
