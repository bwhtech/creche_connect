# Copyright (c) 2026, BWH and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import get_datetime, now_datetime
from frappe.query_builder import DocType

from creche_connect.api import (
	MEMBER_FIELDS,
	attach_media,
	can_see,
	check_content_length,
	check_only_author_edits,
	is_admin,
	load_threads,
	notify_audience,
)

MAX_POLL_OPTIONS = 10


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
		self.validate_poll()

	def validate_poll(self):
		for o in self.poll_options:
			o.option = (o.option or "").strip()
		labels = [o.option.lower() for o in self.poll_options]
		if not labels:
			self.poll_closes_at = None
			return
		if not 2 <= len(labels) <= MAX_POLL_OPTIONS:
			frappe.throw(_("A poll needs between 2 and {0} options").format(MAX_POLL_OPTIONS))
		if len(set(labels)) < len(labels):
			frappe.throw(_("Each poll option must be different"))
		if self.is_new() and self.poll_closes_at and get_datetime(self.poll_closes_at) <= now_datetime():
			frappe.throw(_("Pick a deadline in the future"))

	def on_update(self):
		attach_media(self.name, self.content)
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
		for doctype in (
			"CrecheConnect Reply",
			"CrecheConnect Thread Visit",
			"CrecheConnect Acknowledgement",
			"CrecheConnect Poll Vote",
		):
			frappe.db.delete(doctype, {"thread": self.name})


def on_doctype_update():
	frappe.db.add_index("CrecheConnect Thread", ["owner", "last_activity"])


def has_permission(doc=None, ptype=None, user=None):
	user = user or frappe.session.user
	if is_admin(user):
		return True
	if ptype != "read" or not doc:
		return False
	me = frappe.db.get_value("CrecheConnect Member", user, MEMBER_FIELDS, as_dict=True)
	if not me:
		return frappe.db.get_value("CrecheConnect Thread", doc.name, "owner") == user
	threads = load_threads({"name": doc.name})
	return bool(threads) and can_see(me, threads[0])


def permission_query_conditions(user=None):
	return "" if is_admin(user) else "1=0"
