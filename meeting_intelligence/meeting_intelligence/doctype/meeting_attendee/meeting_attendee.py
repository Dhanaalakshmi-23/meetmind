# Copyright (c) 2026, Dhanaa Lakshmi and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import flt

class MeetingAttendee(Document):

    def validate(self):
        self.validate_talk_percentage()
        self.validate_rates()

    def validate_talk_percentage(self):
        talk_percentage = flt(self.talk_percentage)

        if talk_percentage < 0 or talk_percentage > 100:
            frappe.throw("Talk Percentage must be between 0 and 100.")