# Copyright (c) 2026, Dhanaa Lakshmi and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import cint, validate_email_address

class MeetingConfig(Document):

    def validate(self):
        self.validate_positive_numbers()
        self.validate_monologue_threshold()

    def validate_positive_numbers(self):
        for fieldname, label in (
            ("ghost_threshold_days", "Ghost Threshold Days"),
            ("zombie_revisit_threshold", "Zombie Revisit Threshold"),
            ("working_hours_per_day", "Working Hours Per Day"),
            ("working_days_per_month", "Working Days Per Month"),
        ):
            if cint(self.get(fieldname)) < 1:
                frappe.throw(f"{label} must be at least 1.")

    def validate_monologue_threshold(self):
        threshold = cint(self.monologue_threshold_pct)

        if threshold < 0 or threshold > 100:
            frappe.throw("Monologue Threshold (%) must be between 0 and 100.")
