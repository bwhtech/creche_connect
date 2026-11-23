# Copyright (c) 2026, BWH and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document

from creche_connect.api import MEMBER_FIELDS, can_see_resource, is_admin


class CrecheConnectResource(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		from creche_connect.crecheconnect.doctype.crecheconnect_resource_file.crecheconnect_resource_file import CrecheConnectResourceFile
		from creche_connect.crecheconnect.doctype.crecheconnect_thread_designation.crecheconnect_thread_designation import CrecheConnectThreadDesignation
		from creche_connect.crecheconnect.doctype.crecheconnect_thread_place.crecheconnect_thread_place import CrecheConnectThreadPlace

		description: DF.SmallText | None
		designations: DF.Table[CrecheConnectThreadDesignation]
		files: DF.Table[CrecheConnectResourceFile]
		kind: DF.Literal["Video", "Course", "Document", "Link"]
		pinned: DF.Check
		places: DF.Table[CrecheConnectThreadPlace]
		title: DF.Data
	# end: auto-generated types

	_DOCTYPE_NAME = "CrecheConnect Resource"

	def validate(self):
		for f in self.files:
			if not f.url.startswith(("/files/", "/private/files/", "https://", "http://")):
				frappe.throw(_("Row {0}: add a file, or a link that starts with https://").format(f.idx))


def has_permission(doc=None, ptype=None, user=None):
	user = user or frappe.session.user
	if is_admin(user):
		return True
	me = frappe.db.get_value("CrecheConnect Member", user, MEMBER_FIELDS, as_dict=True)
	if not me or not doc:
		return False
	audience = frappe._dict(
		places=[p.place for p in doc.get("places") or []],
		designations=[d.designation for d in doc.get("designations") or []],
	)
	return can_see_resource(me, audience)


def permission_query_conditions(user=None):
	return "" if is_admin(user) else "1=0"
