# Copyright (c) 2026, Dhanaa Lakshmi and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import cint, flt, today

class MeetingSession(Document):

    def validate(self):
        self.validate_duration()
        self.validate_attendees()
        self.validate_talk_percentages()
        self.validate_date()
        self.calculate_attendee_costs()
        self.calculate_meeting_cost()
        self.detect_monologue()
        self.update_linked_counts()
        self.calculate_health_score()

    def validate_duration(self):
        duration = cint(self.duration_minutes)

        if duration < 15:
            frappe.throw("Meeting duration must be at least 15 minutes.")

        if duration > 480:
            frappe.throw("Meeting duration cannot exceed 8 hours.")

    def validate_attendees(self):
        if not self.attendees:
            frappe.throw("Add at least one attendee.")

        participants = []

        for attendee in self.attendees:
            if not attendee.participant:
                frappe.throw("Every attendee row must have a participant.")

            if attendee.participant in participants:
                frappe.throw(
                    f"Participant {attendee.participant} cannot be added more than once."
                )

            participants.append(attendee.participant)

    def validate_talk_percentages(self):
        total = sum(
            flt(attendee.talk_percentage)
            for attendee in self.attendees
        )

        if total > 0 and abs(total - 100) > 1:
            frappe.throw(
                f"Talk percentages must total 100%. Current total: {total}%."
            )

    def validate_date(self):
        if str(self.meeting_date) > str(today()):
            frappe.throw("Meeting date cannot be in the future.")

    def calculate_attendee_costs(self):
        config = frappe.get_single("Meeting Config")

        working_hours = cint(config.working_hours_per_day) or 8
        working_days = cint(config.working_days_per_month) or 22

        for attendee in self.attendees:

            if not attendee.attended:
                attendee.annual_ctc = 0
                attendee.hourly_rate = 0
                continue

            annual_ctc = 0

            if attendee.participant:
                annual_ctc = flt(
                    frappe.db.get_value(
                        "Meeting Participant",
                        attendee.participant,
                        "annual_ctc"
                    )
                )

            attendee.annual_ctc = annual_ctc

            attendee.hourly_rate = (
                annual_ctc / 12 / working_days / working_hours
                if working_days and working_hours
                else 0
            )

    def calculate_meeting_cost(self):
        total_hourly_rate = sum(
            flt(attendee.hourly_rate)
            for attendee in self.attendees
            if attendee.attended
        )

        self.meeting_cost = (
            total_hourly_rate * flt(self.duration_minutes) / 60
        )

    def detect_monologue(self):
        config = frappe.get_single("Meeting Config")

        threshold = cint(config.monologue_threshold_pct) or 65

        self.has_monologue = any(
            flt(attendee.talk_percentage) > threshold
            for attendee in self.attendees
        )

    def update_linked_counts(self):
        self.decisions_count = frappe.db.count(
            "Decision Log",
            {
                "meeting_session": self.name
            }
        )

        self.open_actions_count = frappe.db.count(
            "Action Item",
            {
                "meeting_session": self.name,
                "status": ["in", ["Open", "In Progress", "Overdue"]]
            }
        )

    def calculate_health_score(self):
        score = 50

        if self.agenda_followed == "Yes":
            score += 20

        elif self.agenda_followed == "Partially":
            score += 8

        if self.decisions_count > 0:
            score += 15

        if self.open_actions_count > 0:
            score += 10

        if not self.agenda:
            score -= 10

        if self.has_monologue:
            score -= 8

        if (
            cint(self.duration_minutes) > 90
            and self.decisions_count == 0
        ):
            score -= 10

        self.health_score = max(0, min(100, score))

        if self.health_score >= 80:
            self.health_label = "Excellent"

        elif self.health_score >= 60:
            self.health_label = "Good"

        elif self.health_score >= 40:
            self.health_label = "Below Average"

        else:
            self.health_label = "Poor"
