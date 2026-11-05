# Copyright (c) 2026, BWH and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class CrecheConnectPollVote(Document):
	pass


def on_doctype_update():
	frappe.db.add_unique(
		"CrecheConnect Poll Vote", ["thread", "option", "user"], constraint_name="unique_poll_vote"
	)
