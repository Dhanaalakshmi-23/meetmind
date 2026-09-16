# Copyright (c) 2026, Dhanaa Lakshmi and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import cint, date_diff, nowdate

from meeting_intelligence.helpers import (
    ACTIVE_DECISION_STATUSES,
    CLOSED_DECISION_STATUSES,
    OPEN_ACTION_STATUSES,
    email_alerts_enabled,
    get_config,
    get_ghost_flag,
    get_participant_email,
)
from meeting_intelligence.meeting_intelligence.doctype.employee_ghost_score.employee_ghost_score import (
    update_participant_ghost_score,
)


def mark_overdue_action_items():
    config = get_config()
    today = nowdate()

    actions = frappe.get_all(
        "Action Item",
        filters={
            "status": ("in", OPEN_ACTION_STATUSES),
            "due_date": ("<", today),
        },
        fields=["name", "assigned_to", "due_date"],
    )

    participants = set()

    for action in actions:
        days_overdue = date_diff(today, action.due_date)

        frappe.db.set_value(
            "Action Item",
            action.name,
            {
                "status": "Overdue",
                "days_overdue": days_overdue,
                "is_ghost": get_ghost_flag(days_overdue, config),
            },
            update_modified=False,
        )

        participants.add(action.assigned_to)

    for participant in participants:
        update_participant_ghost_score(participant)

    return {"marked_overdue": len(actions), "participants_updated": len(participants)}


def update_ghost_scores():
    config = get_config()

    participants = set(frappe.get_all("Action Item", pluck="assigned_to"))
    alerts_sent = 0
    updated = 0

    for participant in participants:
        old_risk = frappe.db.get_value(
            "Employee Ghost Score", {"participant": participant}, "risk_level"
        )
        values = update_participant_ghost_score(participant)

        if not values:
            continue

        updated += 1

        new_risk = values["risk_level"]

        if new_risk in ("High", "Critical") and old_risk not in ("High", "Critical"):
            if email_alerts_enabled(config):
                if send_ghost_score_alert(participant, values, config):
                    alerts_sent += 1

    return {"participants_updated": updated, "alerts_sent": alerts_sent}


def send_ghost_score_alert(participant, values, config):
    email = get_participant_email(participant)

    if not email:
        return False

    participant_name = frappe.db.get_value(
        "Meeting Participant", participant, "participant_name"
    )

    frappe.sendmail(
        recipients=[email],
        subject=f"MeetMind Alert: Ghost Score at {values['ghost_score_pct']}%",
        message=frappe.render_template(
            "emails/ghost_score_alert.html",
            {
                "participant_name": participant_name,
                "ghost_score_pct": values["ghost_score_pct"],
                "completion_rate_pct": values["completion_rate_pct"],
                "total_assigned": values["total_assigned"],
                "total_completed": values["total_completed"],
                "total_overdue": values["total_overdue"],
                "total_ghost": values["total_ghost"],
                "risk_level": values["risk_level"],
            },
        ),
    )

    return True


def send_overdue_reminders():
    config = get_config()

    if not email_alerts_enabled(config):
        return {"reminders_sent": 0, "skipped": "email_alerts_disabled"}

    actions = frappe.get_all(
        "Action Item",
        filters={"status": "Overdue", "reminder_sent": 0},
        fields=[
            "name",
            "task_title",
            "due_date",
            "days_overdue",
            "priority",
            "meeting_session",
            "assigned_to",
        ],
    )

    by_participant = {}

    for action in actions:
        by_participant.setdefault(action.assigned_to, []).append(action)

    reminders_sent = 0

    for participant, items in by_participant.items():
        email = get_participant_email(participant)

        if not email:
            continue

        participant_name = frappe.db.get_value(
            "Meeting Participant", participant, "participant_name"
        )

        frappe.sendmail(
            recipients=[email],
            subject=f"MeetMind Reminder: {len(items)} overdue action item(s)",
            message=frappe.render_template(
                "emails/overdue_reminder.html",
                {
                    "participant_name": participant_name,
                    "actions": items,
                },
            ),
        )

        for item in items:
            frappe.db.set_value(
                "Action Item", item.name, "reminder_sent", 1, update_modified=False
            )

        reminders_sent += 1

    return {"reminders_sent": reminders_sent, "overdue_actions": len(actions)}


def zombie_decision_scan():
    config = get_config()
    threshold = cint(config["zombie_revisit_threshold"])

    flagged = frappe.get_all(
        "Decision Log",
        filters={
            "is_zombie": 0,
            "revisit_count": (">=", threshold),
            "decision_status": ("in", ACTIVE_DECISION_STATUSES),
        },
        fields=["name", "decision_title", "revisit_count", "owner_participant"],
    )

    alerts_sent = 0

    for decision in flagged:
        frappe.db.set_value(
            "Decision Log",
            decision.name,
            {"is_zombie": 1, "zombie_since": nowdate()},
            update_modified=False,
        )

        if email_alerts_enabled(config):
            if send_zombie_alert(decision, config):
                alerts_sent += 1

    cleared = frappe.get_all(
        "Decision Log",
        filters={
            "is_zombie": 1,
            "decision_status": ("in", CLOSED_DECISION_STATUSES),
        },
        pluck="name",
    )

    for name in cleared:
        frappe.db.set_value("Decision Log", name, "is_zombie", 0, update_modified=False)

    return {
        "zombies_flagged": len(flagged),
        "zombies_cleared": len(cleared),
        "alerts_sent": alerts_sent,
    }


def send_zombie_alert(decision, config):
    email = get_participant_email(decision.owner_participant)

    if not email:
        return False

    owner_name = frappe.db.get_value(
        "Meeting Participant", decision.owner_participant, "participant_name"
    )

    frappe.sendmail(
        recipients=[email],
        subject=f"MeetMind Alert: Zombie Decision - {decision.decision_title}",
        message=frappe.render_template(
            "emails/zombie_alert.html",
            {
                "owner_name": owner_name,
                "decision_title": decision.decision_title,
                "decision_name": decision.name,
                "revisit_count": decision.revisit_count,
            },
        ),
    )

    return True


def send_manager_digest():
    config = get_config()

    if not email_alerts_enabled(config):
        return {"digest_sent": 0, "skipped": "email_alerts_disabled"}

    if not config["manager_email"]:
        return {"digest_sent": 0, "skipped": "manager_email_not_configured"}

    from meeting_intelligence.api import get_dashboard_summary

    summary = get_dashboard_summary()

    frappe.sendmail(
        recipients=[config["manager_email"]],
        subject=f"MeetMind Weekly Digest - {nowdate()}",
        message=frappe.render_template(
            "emails/manager_digest.html",
            {
                "summary": summary,
                "currency": config["currency"],
            },
        ),
    )

    return {"digest_sent": 1}
