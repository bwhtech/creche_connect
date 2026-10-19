# Copyright (c) 2026, BWH and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class SamvaadReaction(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		emoji: DF.Data
		reference_doctype: DF.Link
		reference_name: DF.DynamicLink
		user: DF.Link
	# end: auto-generated types

	_DOCTYPE_NAME = "Samvaad Reaction"


def on_doctype_update():
	frappe.db.add_unique(
		"Samvaad Reaction",
		["reference_doctype", "reference_name", "emoji", "user"],
		constraint_name="unique_reaction",
	)
