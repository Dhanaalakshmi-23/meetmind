# Copyright (c) 2026, Dhanaa Lakshmi and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import cint

OPEN_ACTION_STATUSES = ("Open", "In Progress", "Overdue")
ACTIVE_DECISION_STATUSES = ("Open", "In Progress", "Revisited")
CLOSED_DECISION_STATUSES = ("Completed", "Cancelled", "Abandoned")


def get_config():
    values = frappe.get_singles_dict("Meeting Config")

    return {
        "ghost_threshold_days": cint(values.get("ghost_threshold_days")) or 7,
        "zombie_revisit_threshold": cint(values.get("zombie_revisit_threshold")) or 2,
        "monologue_threshold_pct": cint(values.get("monologue_threshold_pct")) or 65,
        "working_hours_per_day": cint(values.get("working_hours_per_day")) or 8,
        "working_days_per_month": cint(values.get("working_days_per_month")) or 22,
        "currency": values.get("currency") or "INR",
        "manager_email": values.get("manager_email"),
        "hr_email": values.get("hr_email"),
        "enable_email_alerts": 1 if values.get("enable_email_alerts") else 0,
    }


def get_ghost_flag(days_overdue, config=None):
    config = config or get_config()

    return 1 if days_overdue > cint(config["ghost_threshold_days"]) else 0


def get_participant_email(participant):
    return frappe.db.get_value("Meeting Participant", participant, "email")


def email_alerts_enabled(config=None):
    config = config or get_config()

    return bool(config["enable_email_alerts"])
