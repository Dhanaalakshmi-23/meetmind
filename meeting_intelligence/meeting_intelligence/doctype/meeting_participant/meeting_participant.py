# Copyright (c) 2026, Dhanaa Lakshmi and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import cint, flt

class MeetingParticipant(Document):

    def validate(self):
        self.validate_default_talk_percentage()
        self.validate_annual_ctc()

    def validate_default_talk_percentage(self):
        talk_percentage = flt(self.default_talk_percentage)

        if talk_percentage < 0 or talk_percentage > 100:
            frappe.throw("Default Talk Percentage must be between 0 and 100.")

    def validate_annual_ctc(self):
        if flt(self.annual_ctc) < 0:
            frappe.throw("Annual CTC cannot be negative.")


@frappe.whitelist()
def refresh_metrics(participant):
    check_participant_permission(participant)

    return refresh_participant_metrics(participant)


def check_participant_permission(participant):
    if not frappe.has_permission("Meeting Participant", "read", doc=participant):
        frappe.throw(
            "You do not have permission to access this participant.",
            frappe.PermissionError,
        )


def refresh_participant_metrics(participant):
    attendees = frappe.get_all(
        "Meeting Attendee",
        filters={
            "parenttype": "Meeting Session",
            "participant": participant,
            "attended": 1,
        },
        fields=["parent", "hourly_rate", "talk_percentage"],
    )

    rates = {}
    talk_percentages = []

    for attendee in attendees:
        rates[attendee.parent] = flt(attendee.hourly_rate)

        if attendee.talk_percentage is not None:
            talk_percentages.append(flt(attendee.talk_percentage))

    sessions = []

    if rates:
        sessions = frappe.get_all(
            "Meeting Session",
            filters={"name": ["in", list(rates)], "docstatus": ["<", 2]},
            fields=["name", "duration_minutes"],
        )

    meeting_count = len(sessions)
    total_cost = 0

    for session in sessions:
        total_cost += flt(session.duration_minutes) * rates[session.name] / 60

    average_talk_percentage = 0

    if talk_percentages:
        average_talk_percentage = sum(talk_percentages) / len(talk_percentages)

    frappe.db.set_value(
        "Meeting Participant",
        participant,
        {
            "meeting_count": meeting_count,
            "total_meeting_cost": total_cost,
            "average_talk_percentage": average_talk_percentage,
        },
        update_modified=False,
    )

    return {
        "meeting_count": meeting_count,
        "total_meeting_cost": total_cost,
        "average_talk_percentage": average_talk_percentage,
    }


def update_metrics_on_session_change(doc, method=None):
    participants = frappe.get_all(
        "Meeting Attendee",
        filters={"parenttype": "Meeting Session", "parent": doc.name},
        pluck="participant",
    )

    for participant in set(participants):
        refresh_participant_metrics(participant)
