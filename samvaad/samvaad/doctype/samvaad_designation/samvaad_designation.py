# Copyright (c) 2026, BWH and contributors
# For license information, please see license.txt

from frappe.model.document import Document


class SamvaadDesignation(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		designation_name: DF.Data
		is_national: DF.Check
		seniority: DF.Int
	# end: auto-generated types

	_DOCTYPE_NAME = "Samvaad Designation"
