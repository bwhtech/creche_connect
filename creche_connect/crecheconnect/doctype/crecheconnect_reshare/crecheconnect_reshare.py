# Copyright (c) 2026, BWH and contributors
# For license information, please see license.txt

from frappe.model.document import Document

from creche_connect import push


class CrecheConnectReshare(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		from creche_connect.crecheconnect.doctype.crecheconnect_thread_designation.crecheconnect_thread_designation import (
			CrecheConnectThreadDesignation,
		)
		from creche_connect.crecheconnect.doctype.crecheconnect_thread_place.crecheconnect_thread_place import (
			CrecheConnectThreadPlace,
		)

		designations: DF.Table[CrecheConnectThreadDesignation]
		note: DF.SmallText | None
		place: DF.Link
		places: DF.Table[CrecheConnectThreadPlace]
		thread: DF.Link
		user: DF.Link
	# end: auto-generated types

	_DOCTYPE_NAME = "CrecheConnect Reshare"

	def after_insert(self):
		if self.places:
			push.queue("reshare_created", self.name)
