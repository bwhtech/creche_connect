# Copyright (c) 2026, BWH and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

from creche_connect.api import is_admin


class CrecheConnectResource(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		from creche_connect.crecheconnect.doctype.crecheconnect_resource_file.crecheconnect_resource_file import CrecheConnectResourceFile

		description: DF.SmallText | None
		files: DF.Table[CrecheConnectResourceFile]
		kind: DF.Literal["Video", "Course", "Document", "Link"]
		pinned: DF.Check
		title: DF.Data
	# end: auto-generated types

	_DOCTYPE_NAME = "CrecheConnect Resource"


def has_permission(doc=None, ptype=None, user=None):
	user = user or frappe.session.user
	return is_admin(user) or bool(frappe.db.exists("CrecheConnect Member", user))


def permission_query_conditions(user=None):
	return "" if has_permission(user=user) else "1=0"
