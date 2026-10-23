# Copyright (c) 2026, BWH and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime

from samvaad.api import check_content_length, check_only_author_edits, notify_audience


class SamvaadReply(Document):
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

	_DOCTYPE_NAME = "Samvaad Reply"

	def validate(self):
		check_content_length(self.content)
		check_only_author_edits(self, "content")
		if not self.is_new() and self.has_value_changed("content"):
			self.edited_at = now_datetime()

	def after_insert(self):
		self.update_thread_stats()

	def on_update(self):
		notify_audience(self.thread)

	def on_trash(self):
		self.update_thread_stats(exclude=self.name)
		frappe.db.delete("Samvaad Reaction", {"reference_doctype": self.doctype, "reference_name": str(self.name)})
		notify_audience(self.thread)

	def update_thread_stats(self, exclude=None):
		frappe.db.sql(
			"""
			update `tabSamvaad Thread` t
			join (
				select count(*) as total, max(creation) as latest from `tabSamvaad Reply`
				where thread = %(thread)s and name != %(exclude)s
			) r
			set t.reply_count = r.total, t.last_activity = coalesce(r.latest, t.creation)
			where t.name = %(thread)s
			""",
			{"thread": self.thread, "exclude": exclude or 0},
		)
