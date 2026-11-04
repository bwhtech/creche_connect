# Copyright (c) 2026, BWH and contributors
# For license information, please see license.txt

from frappe.model.document import Document


class CrecheConnectPlace(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		code: DF.Data
		color: DF.Literal["blue", "green", "amber", "violet", "red"]
		kind: DF.Literal["Country", "State", "District", "Block"]
		parent_place: DF.Link | None
		place_name: DF.Data
	# end: auto-generated types

	_DOCTYPE_NAME = "CrecheConnect Place"

	def autoname(self):
		self.code = self.code.strip().upper()
		self.name = f"{self.parent_place}-{self.code}" if self.kind in ("District", "Block") else self.code
