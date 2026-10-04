# Copyright (c) 2026, Dhanaa Lakshmi and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import add_days, add_months, flt, get_first_day, getdate

from meeting_intelligence.helpers import OPEN_ACTION_STATUSES, get_config


@frappe.whitelist()
def get_dashboard_summary():
    check_dashboard_permission()

    config = get_config()
    today = getdate()
    month_start = get_first_day(today)

    month_sessions = frappe.get_all(
        "Meeting Session",
        filters={"meeting_date": (">=", month_start)},
        fields=["meeting_cost", "health_score"],
    )

    month_meeting_count = len(month_sessions)
    month_meeting_cost = sum(flt(session.meeting_cost) for session in month_sessions)
    month_avg_health = 0

    if month_meeting_count:
        month_avg_health = round(
            sum(flt(session.health_score) for session in month_sessions)
            / month_meeting_count,
            1,
        )

    summary = {
        "currency": config["currency"],
        "this_month": {
            "meeting_count": month_meeting_count,
            "meeting_cost": month_meeting_cost,
            "average_health_score": month_avg_health,
        },
        "totals": {
            "meeting_sessions": frappe.db.count("Meeting Session"),
            "open_actions": frappe.db.count(
                "Action Item", {"status": ("in", OPEN_ACTION_STATUSES)}
            ),
            "overdue_actions": frappe.db.count("Action Item", {"status": "Overdue"}),
            "ghost_actions": frappe.db.count("Action Item", {"is_ghost": 1}),
            "zombie_decisions": frappe.db.count("Decision Log", {"is_zombie": 1}),
            "high_risk_participants": frappe.db.count(
                "Employee Ghost Score", {"risk_level": ("in", ("High", "Critical"))}
            ),
            "participants": frappe.db.count("Meeting Participant", {"is_active": 1}),
        },
        "department_cost": get_department_cost(month_start),
        "meeting_type_distribution": get_meeting_type_distribution(),
        "health_trend": get_health_trend(today),
        "action_status_breakdown": get_action_status_breakdown(),
        "upcoming_deadlines": get_upcoming_deadlines(today),
        "ghost_participants": get_ghost_participants(),
    }

    return summary


def check_dashboard_permission():
    if not frappe.has_permission("Meeting Session", "read"):
        frappe.throw(
            "You do not have permission to access MeetMind analytics.",
            frappe.PermissionError,
        )


def get_department_cost(month_start):
    sessions = frappe.get_all(
        "Meeting Session",
        filters={"meeting_date": (">=", month_start)},
        fields=["department", "meeting_cost"],
    )

    costs = {}

    for session in sessions:
        costs.setdefault(session.department or "Unassigned", 0)
        costs[session.department or "Unassigned"] += flt(session.meeting_cost)

    departments = [
        {"department": department, "total_cost": cost}
        for department, cost in costs.items()
    ]

    departments.sort(key=lambda row: row["total_cost"], reverse=True)

    return departments


def get_meeting_type_distribution():
    sessions = frappe.get_all("Meeting Session", fields=["meeting_type", "meeting_cost"])

    distribution = {}

    for session in sessions:
        distribution.setdefault(session.meeting_type, {"count": 0, "total_cost": 0})
        distribution[session.meeting_type]["count"] += 1
        distribution[session.meeting_type]["total_cost"] += flt(session.meeting_cost)

    return [
        {"meeting_type": meeting_type, **values}
        for meeting_type, values in distribution.items()
    ]


def get_health_trend(today):
    six_months_ago = get_first_day(add_months(today, -5))

    sessions = frappe.get_all(
        "Meeting Session",
        filters={"meeting_date": (">=", six_months_ago)},
        fields=["meeting_date", "health_score"],
    )

    months = {}

    for i in range(5, -1, -1):
        month_start = get_first_day(add_months(today, -i))
        months[month_start.strftime("%Y-%m")] = []

    for session in sessions:
        key = getdate(session.meeting_date).strftime("%Y-%m")

        if key in months:
            months[key].append(flt(session.health_score))

    trend = []

    for month, scores in months.items():
        average = sum(scores) / len(scores) if scores else 0

        trend.append(
            {
                "month": month,
                "meeting_count": len(scores),
                "average_health_score": round(average, 1),
            }
        )

    return trend


def get_action_status_breakdown():
    actions = frappe.get_all("Action Item", fields=["status"])

    breakdown = {}

    for action in actions:
        breakdown.setdefault(action.status, 0)
        breakdown[action.status] += 1

    return [
        {"status": status, "count": count} for status, count in breakdown.items()
    ]


def get_upcoming_deadlines(today):
    return frappe.get_all(
        "Action Item",
        filters={
            "status": ("in", OPEN_ACTION_STATUSES),
            "due_date": ("between", [today, add_days(today, 7)]),
        },
        fields=["name", "task_title", "due_date", "priority", "assigned_to"],
        order_by="due_date asc",
        limit_page_length=10,
    )


def get_ghost_participants():
    scores = frappe.get_all(
        "Employee Ghost Score",
        filters={"risk_level": ("in", ("High", "Critical"))},
        fields=[
            "participant",
            "ghost_score_pct",
            "completion_rate_pct",
            "risk_level",
            "total_assigned",
            "total_completed",
        ],
        order_by="ghost_score_pct desc",
        limit_page_length=5,
    )

    for score in scores:
        score["participant_name"] = frappe.db.get_value(
            "Meeting Participant", score.participant, "participant_name"
        )

    return scores


@frappe.whitelist()
def close_zombie_decision(decision, resolution_note=None):
    from meeting_intelligence.meeting_intelligence.doctype.decision_log.decision_log import (
        resolve_zombie,
    )

    return resolve_zombie(decision, resolution_note=resolution_note)


@frappe.whitelist()
def get_active_participants():
    """
    Return all active Meeting Participants for the attendee dropdown.

    Frontend call : getActiveParticipants()
    DocType       : Meeting Participant
    Filter        : is_active = 1
    Fields        : name, participant_name, designation, department
    """
    return frappe.get_list(
        "Meeting Participant",
        filters={"is_active": 1},
        fields=["name", "participant_name", "designation", "department"],
        order_by="participant_name asc",
    )


@frappe.whitelist(allow_guest=True, methods=["GET"])
def get_csrf_token():
    """
    Return the CSRF token for the current session.

    When the MeetMind frontend is served by Frappe, the server injects the token
    into the page automatically (`window.frappe.csrf_token`). For the Vite dev
    proxy case, the frontend calls this (via GET, which bypasses CSRF) to pick up
    the token for the user's existing Frappe session and send it as the
    `X-Frappe-CSRF-Token` header on subsequent POSTs.

    Returns: str — the session CSRF token.
    """
    return frappe.sessions.get_csrf_token()


@frappe.whitelist()
def get_meeting_form_options():
    meeting_types = frappe.get_list(
        "Meeting Type",
        filters={"is_active": 1},
        fields=["name", "meeting_type_name", "description"],
        order_by="meeting_type_name asc",
    )

    meta = frappe.get_meta("Meeting Session")

    return {
        "meeting_types": meeting_types,
        "agenda_followed_options": meta.get_field(
            "agenda_followed"
        ).options.split("\n"),
    }


@frappe.whitelist()
def create_meeting_session(data):
    """
    Insert a new Meeting Session document from the Vue wizard payload.

    Frontend call : createMeetingSession(payload)
    DocType       : Meeting Session  (child: Meeting Attendee)
    Triggers      : MeetingSession.validate() — cost, health score, monologue detection
    Returns       : name, meeting_title, health_score, health_label, meeting_cost, status

    Expected payload structure (JSON string):
    {
        "meeting_title":    str (required),
        "meeting_type":     str (required, Select),
        "department":       str (required),
        "meeting_date":     str YYYY-MM-DD (required),
        "start_time":       str HH:MM:SS   (optional, defaults to now),
        "duration_minutes": int (required, 15–480),
        "agenda_followed":  str (required, Yes/Partially/No),
        "agenda":           str (optional),
        "notes":            str (optional),
        "attendees": [
            {
                "participant":      str (Meeting Participant name, required),
                "talk_percentage":  int (0–100),
                "attended":         bool
            },
            ...
        ]
    }
    """
    import json
    from frappe.utils import now_datetime

    if isinstance(data, str):
        data = json.loads(data)

    # Default start_time to current time if not provided
    if not data.get("start_time"):
        data["start_time"] = now_datetime().strftime("%H:%M:%S")

    doc = frappe.get_doc(
        {
            "doctype": "Meeting Session",
            "meeting_title": data.get("meeting_title"),
            "meeting_type": data.get("meeting_type"),
            "department": data.get("department"),
            "meeting_date": data.get("meeting_date"),
            "start_time": data.get("start_time"),
            "duration_minutes": data.get("duration_minutes", 60),
            "agenda_followed": data.get("agenda_followed"),
            "agenda": data.get("agenda", ""),
            "notes": data.get("notes", ""),
            "status": "Draft",
            "attendees": [
                {
                    "participant": attendee.get("participant"),
                    "talk_percentage": attendee.get("talk_percentage", 0),
                    "attended": 1 if attendee.get("attended", True) else 0,
                }
                for attendee in data.get("attendees", [])
            ],
        }
    )

    doc.insert()

    return {
        "name": doc.name,
        "meeting_title": doc.meeting_title,
        "health_score": doc.health_score,
        "health_label": doc.health_label,
        "meeting_cost": flt(doc.meeting_cost),
        "status": doc.status,
    }
