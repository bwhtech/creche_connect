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
		notify_audience(frappe.get_doc("Samvaad Thread", self.thread))

	def on_trash(self):
		self.update_thread_stats(exclude=self.name)

	def update_thread_stats(self, exclude=None):
		filters = {"thread": self.thread, "name": ["!=", exclude or 0]}
		last = frappe.get_all(
			"Samvaad Reply", filters=filters, pluck="creation", order_by="creation desc", limit=1
		)
		frappe.db.set_value(
			"Samvaad Thread",
			self.thread,
			{
				"last_activity": last[0]
				if last
				else frappe.db.get_value("Samvaad Thread", self.thread, "creation"),
				"reply_count": frappe.db.count("Samvaad Reply", filters),
			},
		)
