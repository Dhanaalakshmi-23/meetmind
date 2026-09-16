# Copyright (c) 2026, Dhanaa Lakshmi and contributors
# For license information, please see license.txt

import re

import frappe
from frappe.model.document import Document
from frappe.utils import cint, cstr, nowdate

def normalize_title(title):
    normalized = re.sub(r"[^a-z0-9 ]+", " ", cstr(title).lower())
    return re.sub(r"\s+", " ", normalized).strip()

class DecisionLog(Document):

    def validate(self):
        if self.is_new():
            self.detect_revisited_decision()

    def detect_revisited_decision(self):
        config = frappe.get_single("Meeting Config")
        threshold = cint(config.zombie_revisit_threshold) or 2

        candidates = frappe.get_all(
            "Decision Log",
            filters={
                "name": ["!=", self.name],
                "decision_status": ("in", ("Open", "In Progress", "Revisited")),
            },
            fields=["name", "decision_title", "decision_status", "previous_decision", "revisit_count"],
            order_by="creation asc",
            limit_page_length=500,
        )

        title = normalize_title(self.decision_title)
        current = None

        for candidate in candidates:
            if normalize_title(candidate.decision_title) == title:
                current = candidate

                if candidate.decision_status in ("Open", "In Progress"):
                    break

        if not current:
            return

        root = current

        while root.previous_decision:
            parent = frappe.db.get_value(
                "Decision Log",
                root.previous_decision,
                ["name", "decision_status", "previous_decision", "revisit_count", "is_zombie"],
                as_dict=True,
            )

            if not parent or parent.decision_status in ("Completed", "Cancelled", "Abandoned"):
                break

            root = parent

        self.previous_decision = root.name

        revisit_count = cint(root.revisit_count) + 1

        frappe.db.set_value(
            "Decision Log",
            root.name,
            {
                "revisit_count": revisit_count,
            },
            update_modified=False,
        )

        if revisit_count >= threshold:
            frappe.db.set_value(
                "Decision Log",
                root.name,
                {
                    "is_zombie": 1,
                    "zombie_since": nowdate(),
                },
                update_modified=False,
            )

        frappe.db.set_value(
            "Decision Log",
            current.name,
            {"decision_status": "Revisited"},
            update_modified=False,
        )

@frappe.whitelist()
def resolve_zombie(decision, resolution_note=None):
    doc = frappe.get_doc("Decision Log", decision)
    doc.check_permission("write")

    values = {
        "decision_status": "Completed",
        "is_zombie": 0,
        "zombie_since": None,
    }

    if resolution_note:
        values["resolution_note"] = resolution_note

    if doc.docstatus == 0:
        doc.update(values)
        doc.save()
    else:
        frappe.db.set_value("Decision Log", doc.name, values, update_modified=False)

    decision_status, is_zombie = frappe.db.get_value(
        "Decision Log", decision, ["decision_status", "is_zombie"]
    )

    return {"name": decision, "decision_status": decision_status, "is_zombie": is_zombie}


def update_session_decision_count(doc, method=None):
    count = frappe.db.count("Decision Log", {"meeting_session": doc.meeting_session})

    frappe.db.set_value(
        "Meeting Session",
        doc.meeting_session,
        "decisions_count",
        count,
        update_modified=False,
    )


def update_session_decision_count_on_trash(doc, method=None):
    count = frappe.db.count(
        "Decision Log",
        {"meeting_session": doc.meeting_session, "name": ["!=", doc.name]},
    )

    frappe.db.set_value(
        "Meeting Session",
        doc.meeting_session,
        "decisions_count",
        count,
        update_modified=False,
    )
