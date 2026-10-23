# Copyright (c) 2026, BWH and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

from samvaad.api import notify_audience


class SamvaadReply(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		content: DF.TextEditor
		name: DF.Int | None
		thread: DF.Link
	# end: auto-generated types

	_DOCTYPE_NAME = "Samvaad Reply"

	def after_insert(self):
		self.update_thread_stats()
		notify_audience(self.thread)

	def on_trash(self):
		self.update_thread_stats(exclude=self.name)

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
