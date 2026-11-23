# Copyright (c) 2026, BWH and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime, strip_html

from creche_connect.api import attach_media, check_content_length, check_only_author_edits, delete_media, notify_audience


class CrecheConnectReply(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		content: DF.TextEditor
		edited_at: DF.Datetime | None
		name: DF.Int | None
		thread: DF.Link
	# end: auto-generated types

	_DOCTYPE_NAME = "CrecheConnect Reply"

	def validate(self):
		content = self.content or ""
		if not strip_html(content).strip() and not any(t in content for t in ("<img", "<audio", "<video")):
			frappe.throw(_("Write a reply or add a picture, audio or video"))
		check_content_length(self.content)
		check_only_author_edits(self, "content")
		if not self.is_new() and self.has_value_changed("content"):
			self.edited_at = now_datetime()

	def after_insert(self):
		self.update_thread_stats()

	def on_update(self):
		attach_media(self.thread, self.content)
		notify_audience(self.thread)

	def on_trash(self):
		self.update_thread_stats(exclude=self.name)
		delete_media(self.thread, self.content, self.owner)
		frappe.db.delete("CrecheConnect Reaction", {"reference_doctype": self.doctype, "reference_name": str(self.name)})
		notify_audience(self.thread)

	def update_thread_stats(self, exclude=None):
		frappe.db.sql(
			"""
			update `tabCrecheConnect Thread` t
			join (
				select count(*) as total, max(creation) as latest from `tabCrecheConnect Reply`
				where thread = %(thread)s and name != %(exclude)s
			) r
			set t.reply_count = r.total, t.last_activity = coalesce(r.latest, t.creation)
			where t.name = %(thread)s
			""",
			{"thread": self.thread, "exclude": exclude or 0},
		)
