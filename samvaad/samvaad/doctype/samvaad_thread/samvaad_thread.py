# Copyright (c) 2026, BWH and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.query_builder import DocType

from samvaad.api import check_content_length, notify_audience


class SamvaadThread(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		from samvaad.samvaad.doctype.samvaad_thread_designation.samvaad_thread_designation import (
			SamvaadThreadDesignation,
		)
		from samvaad.samvaad.doctype.samvaad_thread_place.samvaad_thread_place import SamvaadThreadPlace
		from samvaad.samvaad.doctype.samvaad_thread_tag.samvaad_thread_tag import SamvaadThreadTag

		ack_required: DF.Check
		content: DF.TextEditor | None
		designations: DF.TableMultiSelect[SamvaadThreadDesignation]
		last_activity: DF.Datetime | None
		name: DF.Int | None
		places: DF.TableMultiSelect[SamvaadThreadPlace]
		reply_count: DF.Int
		reply_policy: DF.Literal["everyone", "posters", "none"]
		tags: DF.TableMultiSelect[SamvaadThreadTag]
		title: DF.Data
	# end: auto-generated types

	_DOCTYPE_NAME = "Samvaad Thread"

	def validate(self):
		check_content_length(self.content)

	def on_update(self):
		notify_audience(self.name)

	def on_trash(self):
		Reaction, Reply = DocType("Samvaad Reaction"), DocType("Samvaad Reply")
		replies = frappe.qb.from_(Reply).select(Reply.name).where(Reply.thread == self.name)
		(
			frappe.qb.from_(Reaction)
			.delete()
			.where(
				((Reaction.reference_doctype == "Samvaad Thread") & (Reaction.reference_name == str(self.name)))
				| ((Reaction.reference_doctype == "Samvaad Reply") & Reaction.reference_name.isin(replies))
			)
			.run()
		)
		for doctype in ("Samvaad Reply", "Samvaad Thread Visit", "Samvaad Acknowledgement"):
			frappe.db.delete(doctype, {"thread": self.name})


def on_doctype_update():
	frappe.db.add_index("Samvaad Thread", ["owner", "last_activity"])
