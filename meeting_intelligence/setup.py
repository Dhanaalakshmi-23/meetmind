# Copyright (c) 2026, Dhanaa Lakshmi and contributors
# For license information, please see license.txt

import frappe

MEETMIND_ROLES = ("MeetMind Admin", "MeetMind Manager", "MeetMind User")


def after_install():
    create_roles()


def create_roles():
    for role_name in MEETMIND_ROLES:
        if not frappe.db.exists("Role", role_name):
            frappe.get_doc(
                {
                    "doctype": "Role",
                    "role_name": role_name,
                    "desk_access": 1,
                }
            ).insert(ignore_permissions=True)
