# Copyright (c) 2026, BWH and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class SamvaadTag(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		color: DF.Literal["blue", "green", "amber", "violet", "red"]
		tag_name: DF.Data
	# end: auto-generated types

	_DOCTYPE_NAME = "Samvaad Tag"
