# Copyright (c) 2026, BWH and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class SamvaadResource(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		description: DF.SmallText | None
		kind: DF.Literal["Video", "Course", "Document", "Link"]
		pinned: DF.Check
		title: DF.Data
		url: DF.Data
	# end: auto-generated types

	_DOCTYPE_NAME = "Samvaad Resource"
