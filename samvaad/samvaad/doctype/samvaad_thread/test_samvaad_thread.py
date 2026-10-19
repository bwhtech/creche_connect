# Copyright (c) 2026, BWH and Contributors
# See license.txt

import frappe
from frappe.tests import IntegrationTestCase

from samvaad import api

EXTRA_TEST_RECORD_DEPENDENCIES = []
IGNORE_TEST_RECORD_DEPENDENCIES = ["User", "Samvaad Place", "Samvaad Designation", "Samvaad Tag"]


def insert(doc: dict):
	return frappe.get_doc(doc).insert(ignore_permissions=True, ignore_if_duplicate=True)


def place(kind: str, code: str, parent: str | None = None) -> str:
	return insert(
		{"doctype": "Samvaad Place", "place_name": code, "kind": kind, "code": code, "parent_place": parent}
	).name


def member(uid: str, designation: str, at: str | None, can_post: bool = False) -> str:
	email = f"{uid}@samvaad.test"
	insert(
		{
			"doctype": "User",
			"email": email,
			"first_name": uid,
			"user_type": "Website User",
			"send_welcome_email": 0,
		}
	)
	insert(
		{
			"doctype": "Samvaad Member",
			"user": email,
			"designation": designation,
			"place": at,
			"can_post": can_post,
		}
	)
	return email


class IntegrationTestSamvaadThread(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls.root = frappe.db.get_value("Samvaad Place", {"kind": "Country"}) or place("Country", "IN")
		cls.state = place("State", "TX", cls.root)
		cls.district = place("District", "DST", cls.state)
		cls.block = place("Block", "BLK", cls.district)
		cls.other_state = place("State", "TY", cls.root)
		for i, name in enumerate(["Test lead", "Test coordinator", "Test volunteer"]):
			insert({"doctype": "Samvaad Designation", "designation_name": name, "seniority": 100 + i})
		cls.lead = member("lead", "Test lead", cls.state, can_post=True)
		cls.coordinator = member("coordinator", "Test coordinator", cls.district, can_post=True)
		cls.volunteer = member("volunteer", "Test volunteer", cls.block)
		cls.outsider = member("outsider", "Test volunteer", cls.other_state)

	def tearDown(self):
		frappe.set_user("Administrator")

	def post(self, user: str, places: list, **kw) -> str:
		frappe.set_user(user)
		return api.create_thread("Test thread", "<p>Hello</p>", places, **kw)["name"]

	def visible_to(self, user: str) -> set:
		frappe.set_user(user)
		return {t["id"] for t in api.get_threads()}

	def test_thread_reaches_everyone_at_or_below_its_places(self):
		name = self.post(self.lead, [self.district])
		self.assertIn(name, self.visible_to(self.volunteer))
		self.assertIn(name, self.visible_to(self.coordinator))
		self.assertNotIn(name, self.visible_to(self.outsider))

	def test_designations_narrow_the_audience(self):
		name = self.post(self.lead, [self.state], designations=["Test coordinator"])
		self.assertIn(name, self.visible_to(self.coordinator))
		self.assertNotIn(name, self.visible_to(self.volunteer))
		self.assertIn(name, self.visible_to(self.lead))

	def test_hidden_thread_cannot_be_opened(self):
		name = self.post(self.lead, [self.block])
		frappe.set_user(self.outsider)
		self.assertRaises(frappe.PermissionError, api.get_thread, name)

	def test_posting_is_limited_to_posters_and_their_own_area(self):
		frappe.set_user(self.volunteer)
		self.assertRaises(frappe.PermissionError, api.create_thread, "x", "<p>x</p>", [self.block])
		frappe.set_user(self.coordinator)
		self.assertRaises(frappe.PermissionError, api.create_thread, "x", "<p>x</p>", [self.other_state])
		self.assertRaises(frappe.PermissionError, api.create_thread, "x", "<p>x</p>", [self.state])

	def test_reply_policies(self):
		leads_only = self.post(self.lead, [self.state], reply_policy="posters")
		announcement = self.post(self.lead, [self.state], reply_policy="none")
		frappe.set_user(self.volunteer)
		self.assertRaises(frappe.PermissionError, api.add_reply, leads_only, "<p>hi</p>")
		self.assertRaises(frappe.PermissionError, api.add_reply, announcement, "<p>hi</p>")
		frappe.set_user(self.coordinator)
		api.add_reply(leads_only, "<p>hi</p>")
		self.assertRaises(frappe.PermissionError, api.add_reply, announcement, "<p>hi</p>")

	def test_acknowledgement_is_recorded_once(self):
		name = self.post(self.lead, [self.state], ack_required=True)
		frappe.set_user(self.volunteer)
		self.assertTrue(api.get_thread(name)["needsAck"])
		api.acknowledge(name)
		api.acknowledge(name)
		self.assertFalse(api.get_thread(name)["needsAck"])
		self.assertEqual(frappe.db.count("Samvaad Acknowledgement", {"thread": name}), 1)

	def test_reading_clears_unread_and_counts_as_seen_once(self):
		name = self.post(self.lead, [self.state])
		frappe.set_user(self.volunteer)
		self.assertTrue(api.get_thread(name)["unread"])
		api.mark_read(name)
		api.mark_read(name)
		self.assertFalse(api.get_thread(name)["unread"])
		self.assertEqual(api.get_thread(name)["seenBy"], [self.volunteer])

	def test_deleting_a_reply_updates_the_thread(self):
		name = self.post(self.lead, [self.state])
		frappe.set_user(self.volunteer)
		reply = api.add_reply(name, "<p>hi</p>")
		self.assertEqual(frappe.db.get_value("Samvaad Thread", name, "reply_count"), 1)
		frappe.set_user("Administrator")
		frappe.delete_doc("Samvaad Reply", reply["id"])
		self.assertEqual(frappe.db.get_value("Samvaad Thread", name, "reply_count"), 0)
