# Copyright (c) 2026, BWH and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class SamvaadMember(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		can_post: DF.Check
		designation: DF.Link
		full_name: DF.Data | None
		place: DF.Link | None
		user: DF.Link
	# end: auto-generated types

	_DOCTYPE_NAME = "Samvaad Member"
