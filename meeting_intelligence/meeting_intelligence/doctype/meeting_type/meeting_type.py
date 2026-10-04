# Copyright (c) 2026, Dhanaa Lakshmi and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class MeetingType(Document):
	def validate(self):
		# Guard against duplicates that differ only by surrounding whitespace
		self.meeting_type_name = (self.meeting_type_name or "").strip()
