# Copyright (c) 2026, BWH and contributors
# For license information, please see license.txt

from frappe.model.document import Document

from samvaad.api import notify_audience


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

	def after_insert(self):
		notify_audience(self)
