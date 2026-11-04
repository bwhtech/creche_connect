# Copyright (c) 2026, BWH and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime
from frappe.query_builder import DocType

from creche_connect.api import check_content_length, check_only_author_edits, notify_audience


class CrecheConnectThread(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		from creche_connect.crecheconnect.doctype.crecheconnect_thread_designation.crecheconnect_thread_designation import (
			CrecheConnectThreadDesignation,
		)
		from creche_connect.crecheconnect.doctype.crecheconnect_thread_place.crecheconnect_thread_place import CrecheConnectThreadPlace
		from creche_connect.crecheconnect.doctype.crecheconnect_thread_tag.crecheconnect_thread_tag import CrecheConnectThreadTag

		ack_required: DF.Check
		content: DF.TextEditor | None
		designations: DF.TableMultiSelect[CrecheConnectThreadDesignation]
		edited_at: DF.Datetime | None
		last_activity: DF.Datetime | None
		name: DF.Int | None
		places: DF.TableMultiSelect[CrecheConnectThreadPlace]
		reply_count: DF.Int
		reply_policy: DF.Literal["everyone", "posters", "none"]
		tags: DF.TableMultiSelect[CrecheConnectThreadTag]
		title: DF.Data
	# end: auto-generated types

	_DOCTYPE_NAME = "CrecheConnect Thread"

	def validate(self):
		check_content_length(self.content)
		check_only_author_edits(self, "content", "title")
		if not self.is_new() and (self.has_value_changed("content") or self.has_value_changed("title")):
			self.edited_at = now_datetime()

	def on_update(self):
		notify_audience(self.name)

	def on_trash(self):
		Reaction, Reply = DocType("CrecheConnect Reaction"), DocType("CrecheConnect Reply")
		replies = frappe.qb.from_(Reply).select(Reply.name).where(Reply.thread == self.name)
		(
			frappe.qb.from_(Reaction)
			.delete()
			.where(
				((Reaction.reference_doctype == "CrecheConnect Thread") & (Reaction.reference_name == str(self.name)))
				| ((Reaction.reference_doctype == "CrecheConnect Reply") & Reaction.reference_name.isin(replies))
			)
			.run()
		)
		for doctype in ("CrecheConnect Reply", "CrecheConnect Thread Visit", "CrecheConnect Acknowledgement"):
			frappe.db.delete(doctype, {"thread": self.name})


def on_doctype_update():
	frappe.db.add_index("CrecheConnect Thread", ["owner", "last_activity"])
