# Copyright (c) 2026, Dhanaa Lakshmi and Contributors
# See license.txt

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import add_days, nowdate

from meeting_intelligence.meeting_intelligence.doctype.decision_log.decision_log import (
    normalize_title,
    resolve_zombie,
)

EXTRA_TEST_RECORD_DEPENDENCIES = []
IGNORE_TEST_RECORD_DEPENDENCIES = []


def make_participant(suffix):
    doc = frappe.get_doc(
        {
            "doctype": "Meeting Participant",
            "participant_name": f"TEST {suffix}",
            "participant_type": "Internal",
            "email": f"{suffix.lower()}.decision@test.example.com",
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
            "agenda": "<p>Decision setup.</p>",
            "agenda_followed": "Yes",
            "attendees": [
                {"participant": participant.name, "talk_percentage": 100, "attended": 1}
            ],
        }
    )
    doc.insert()

    return doc


def make_decision(session, participant, title, status="Open"):
    doc = frappe.get_doc(
        {
            "doctype": "Decision Log",
            "meeting_session": session.name,
            "decision_title": title,
            "owner_participant": participant.name,
            "confidence_level": "Medium",
            "decision_status": status,
            "target_date": add_days(nowdate(), 14),
        }
    )
    doc.insert()

    return doc


class IntegrationTestDecisionLog(IntegrationTestCase):
    """Integration tests for Decision Log."""

    @classmethod
    def tearDownClass(cls):
        frappe.db.delete("Decision Log", {"decision_title": ("like", "TEST%")})
        frappe.db.delete("Meeting Session", {"meeting_title": ("like", "TEST%")})
        participants = frappe.get_all(
            "Meeting Participant",
            filters={"email": ("like", "%@test.example.com")},
            pluck="name",
        )

        if participants:
            frappe.db.delete("Employee Ghost Score", {"participant": ("in", participants)})
            frappe.db.delete("Meeting Participant", {"email": ("like", "%@test.example.com")})

    def test_normalize_title(self):
        self.assertEqual(
            normalize_title("Switch  to Weekly-Release!"), "switch to weekly release"
        )

    def test_zombie_chain(self):
        original = frappe.get_singles_dict("Meeting Config")

        try:
            frappe.db.set_single_value("Meeting Config", "zombie_revisit_threshold", 2)

            maker = make_participant("Maker")
            session = make_session(maker)
            title = f"TEST-ZOMBIE-{frappe.generate_hash(length=8)}"

            first = make_decision(session, maker, title)
            second = make_decision(session, maker, title)
            third = make_decision(session, maker, title)

            root = frappe.get_doc("Decision Log", first.name)

            self.assertEqual(root.revisit_count, 2)
            self.assertEqual(root.is_zombie, 1)
            self.assertTrue(root.zombie_since)

            self.assertEqual(
                frappe.db.get_value("Decision Log", second.name, "previous_decision"),
                first.name,
            )
            self.assertEqual(
                frappe.db.get_value("Decision Log", third.name, "previous_decision"),
                first.name,
            )
            self.assertEqual(
                frappe.db.get_value("Decision Log", first.name, "decision_status"),
                "Revisited",
            )
            self.assertEqual(
                frappe.db.get_value("Decision Log", second.name, "decision_status"),
                "Revisited",
            )

            result = resolve_zombie(first.name, "Settled by vote")

            self.assertEqual(result["decision_status"], "Completed")
            self.assertEqual(result["is_zombie"], 0)

            decision_status, is_zombie, zombie_since, resolution_note = frappe.db.get_value(
                "Decision Log",
                first.name,
                ["decision_status", "is_zombie", "zombie_since", "resolution_note"],
            )

            self.assertEqual(decision_status, "Completed")
            self.assertEqual(is_zombie, 0)
            self.assertFalse(zombie_since)
            self.assertEqual(resolution_note, "Settled by vote")
        finally:
            for key, value in original.items():
                frappe.db.set_single_value("Meeting Config", key, value)

    def test_resolve_zombie_requires_permission(self):
        maker = make_participant("Guest")
        session = make_session(maker)
        decision = make_decision(
            session, maker, f"TEST-GUEST-{frappe.generate_hash(length=8)}"
        )

        frappe.set_user("Guest")

        try:
            with self.assertRaises(frappe.PermissionError):
                resolve_zombie(decision.name, "Should not be allowed")
        finally:
            frappe.set_user("Administrator")
