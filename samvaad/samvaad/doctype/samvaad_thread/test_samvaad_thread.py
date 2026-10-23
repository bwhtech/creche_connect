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
		return set(self.feed())

	def feed(self, **filters) -> list:
		ids, cursor = [], None
		while True:
			page = api.get_threads(cursor=cursor, **filters)
			self.assertLessEqual(len(page["threads"]), api.PAGE_SIZE)
			ids += [t["id"] for t in page["threads"]]
			cursor = page["cursor"]
			if not cursor:
				return ids

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

	def test_feed_pages_through_every_thread_once(self):
		names = {self.post(self.lead, [self.state]) for _ in range(api.PAGE_SIZE + 5)}
		frappe.set_user(self.volunteer)
		seen = self.feed()
		self.assertEqual(len(seen), len(set(seen)))
		self.assertTrue(names <= set(seen))
		self.assertEqual(len(api.get_threads(limit=len(seen))["threads"]), len(seen))

	def test_filters_and_counts_match_the_feed(self):
		read = self.post(self.lead, [self.state])
		unread = self.post(self.lead, [self.state], ack_required=True, tags=["Test tag"])
		frappe.set_user(self.volunteer)
		api.mark_read(read)
		unread_ids = set(self.feed(filter="unread"))
		ack_ids = set(self.feed(filter="ack"))
		tagged_ids = set(self.feed(tag="Test tag"))
		self.assertIn(unread, unread_ids)
		self.assertNotIn(read, unread_ids)
		self.assertIn(unread, ack_ids)
		self.assertEqual(tagged_ids & {read, unread}, {unread})
		counts = api.get_counts()
		self.assertEqual(counts["unread"], len(unread_ids))
		self.assertEqual(counts["ack"], len(ack_ids))
		self.assertEqual(counts["tags"]["Test tag"], len(tagged_ids))
		self.assertEqual(counts["total"], len(self.feed()))
		frappe.set_user(self.lead)
		self.assertIn(read, self.feed(filter="mine"))
		self.assertNotIn(unread, self.feed(filter="unread"))

	def test_feed_counts_who_has_seen_a_thread(self):
		name = self.post(self.lead, [self.state])
		frappe.set_user(self.volunteer)
		api.mark_read(name)
		frappe.set_user(self.coordinator)
		api.mark_read(name)
		row = next(t for t in api.get_threads()["threads"] if t["id"] == name)
		self.assertEqual(row["seenCount"], 2)

	def test_replies_load_newest_first_page_then_older(self):
		name = self.post(self.lead, [self.state])
		frappe.set_user(self.volunteer)
		ids = [api.add_reply(name, f"<p>{i}</p>")["id"] for i in range(api.REPLY_PAGE_SIZE + 3)]
		thread = api.get_thread(name)
		self.assertEqual([r["id"] for r in thread["replies"]], ids[3:])
		self.assertTrue(thread["hasOlder"])
		older = api.get_replies(name, int(ids[3]))
		self.assertEqual([r["id"] for r in older["replies"]], ids[:3])
		self.assertFalse(older["hasOlder"])
		frappe.set_user(self.outsider)
		self.assertRaises(frappe.PermissionError, api.get_replies, name, int(ids[3]))

	def test_deleting_a_thread_removes_its_activity(self):
		name = self.post(self.lead, [self.state], ack_required=True)
		frappe.set_user(self.volunteer)
		reply = api.add_reply(name, "<p>Hi</p>")
		api.acknowledge(name)
		api.toggle_reaction("Samvaad Thread", name, api.EMOJIS[0])
		api.toggle_reaction("Samvaad Reply", reply["id"], api.EMOJIS[0])
		frappe.set_user("Administrator")
		frappe.delete_doc("Samvaad Thread", name)
		for doctype in ("Samvaad Reply", "Samvaad Thread Visit", "Samvaad Acknowledgement"):
			self.assertFalse(frappe.db.exists(doctype, {"thread": name}))
		self.assertFalse(frappe.db.exists("Samvaad Reaction", {"reference_name": ["in", [name, reply["id"]]]}))

	def test_author_cannot_acknowledge_own_thread(self):
		name = self.post(self.lead, [self.state], ack_required=True)
		self.assertRaises(frappe.ValidationError, api.acknowledge, name)

	def test_malformed_cursor_is_rejected(self):
		frappe.set_user(self.volunteer)
		self.assertRaises(frappe.ValidationError, api.get_threads, cursor="garbage")

	def test_overlong_messages_are_rejected(self):
		name = self.post(self.lead, [self.state])
		too_long = "<p>" + "a" * api.MAX_CONTENT_LENGTH + "</p>"
		frappe.set_user(self.volunteer)
		self.assertRaises(frappe.ValidationError, api.add_reply, name, too_long)
		frappe.set_user(self.lead)
		self.assertRaises(frappe.ValidationError, api.create_thread, "Long", too_long, [self.state])

	def test_removed_thread_says_so(self):
		name = self.post(self.lead, [self.state])
		frappe.set_user("Administrator")
		frappe.delete_doc("Samvaad Thread", name)
		frappe.set_user(self.volunteer)
		self.assertRaises(frappe.DoesNotExistError, api.get_thread, name)
		self.assertRaises(frappe.DoesNotExistError, api.add_reply, name, "<p>Hi</p>")

	def test_author_and_admin_can_edit_others_cannot(self):
		name = self.post(self.lead, [self.state])
		frappe.set_user(self.volunteer)
		reply = api.add_reply(name, "<p>hi</p>")["id"]
		self.assertRaises(frappe.PermissionError, api.update_message, "Samvaad Thread", name, "<p>x</p>")
		api.update_message("Samvaad Reply", reply, "<p>edited</p>")
		frappe.set_user(self.lead)
		self.assertRaises(frappe.PermissionError, api.update_message, "Samvaad Reply", reply, "<p>x</p>")
		self.assertEqual(api.update_message("Samvaad Thread", name, "<p>new</p>", " New title ")["title"], "New title")
		frappe.set_user("Administrator")
		api.update_message("Samvaad Reply", reply, "<p>by admin</p>")
		self.assertEqual(frappe.db.get_value("Samvaad Reply", reply, "content"), "<p>by admin</p>")
		self.assertRaises(frappe.ValidationError, api.update_message, "Samvaad Thread", name, "<p>x</p>", " ")

	def test_edits_are_capped_like_new_messages(self):
		name = self.post(self.lead, [self.state])
		too_long = "<p>" + "a" * api.MAX_CONTENT_LENGTH + "</p>"
		self.assertRaises(frappe.ValidationError, api.update_message, "Samvaad Thread", name, too_long)

	def test_author_and_admin_can_delete_others_cannot(self):
		name = self.post(self.lead, [self.state])
		frappe.set_user(self.volunteer)
		reply = api.add_reply(name, "<p>hi</p>")["id"]
		api.toggle_reaction("Samvaad Reply", reply, api.EMOJIS[0])
		self.assertRaises(frappe.PermissionError, api.delete_message, "Samvaad Thread", name)
		frappe.set_user(self.coordinator)
		self.assertRaises(frappe.PermissionError, api.delete_message, "Samvaad Reply", reply)
		frappe.set_user(self.volunteer)
		api.delete_message("Samvaad Reply", reply)
		self.assertFalse(frappe.db.exists("Samvaad Reaction", {"reference_name": reply}))
		self.assertEqual(frappe.db.get_value("Samvaad Thread", name, "reply_count"), 0)
		frappe.set_user("Administrator")
		api.delete_message("Samvaad Thread", name)
		self.assertFalse(frappe.db.exists("Samvaad Thread", name))

	def test_edits_are_marked(self):
		name = self.post(self.lead, [self.state])
		frappe.set_user(self.volunteer)
		reply = api.add_reply(name, "<p>first</p>")
		self.assertIsNone(reply["editedAt"])
		self.assertIsNone(api.update_message("Samvaad Reply", reply["id"], "<p>first</p>")["editedAt"])
		thread = api.get_thread(name)
		self.assertIsNone(thread["editedAt"])
		self.assertIsNone(thread["replies"][0]["editedAt"])
		self.assertIsNotNone(api.update_message("Samvaad Reply", reply["id"], "<p>second</p>")["editedAt"])
		frappe.set_user("Administrator")
		frappe.get_doc("Samvaad Thread", name).update({"reply_policy": "posters"}).save()
		frappe.set_user(self.lead)
		self.assertIsNone(api.get_thread(name)["editedAt"])
		api.update_message("Samvaad Thread", name, "<p>changed</p>")
		thread = api.get_thread(name)
		self.assertIsNotNone(thread["editedAt"])
		self.assertIsNotNone(thread["replies"][0]["editedAt"])
