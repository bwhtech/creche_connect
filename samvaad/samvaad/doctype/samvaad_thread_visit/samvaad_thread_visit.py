# Copyright (c) 2026, BWH and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class SamvaadThreadVisit(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		last_visit: DF.Datetime | None
		thread: DF.Link
		user: DF.Link
	# end: auto-generated types

	_DOCTYPE_NAME = "Samvaad Thread Visit"
