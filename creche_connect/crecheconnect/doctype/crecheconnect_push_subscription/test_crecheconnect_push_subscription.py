# Copyright (c) 2026, BWH and Contributors
# See license.txt

import json
from unittest.mock import MagicMock, patch

import frappe
from frappe.tests import IntegrationTestCase
from pywebpush import WebPushException

from creche_connect import api, push
from creche_connect.crecheconnect.doctype.crecheconnect_thread.test_crecheconnect_thread import (
	insert,
	member,
	place,
)

IGNORE_TEST_RECORD_DEPENDENCIES = ["User", "CrecheConnect Place", "CrecheConnect Designation"]


def device(user: str) -> dict:
	return {"endpoint": f"https://fcm.googleapis.com/fcm/send/{user}", "keys": {"p256dh": "x", "auth": "y"}}


class IntegrationTestCrecheConnectPush(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		root = frappe.db.get_value("CrecheConnect Place", {"kind": "Country"}) or place("Country", "IN")
		cls.state = place("State", "TX", root)
		cls.district = place("District", "DST", cls.state)
		block = place("Block", "BLK", cls.district)
		for i, name in enumerate(["Test lead", "Test coordinator", "Test volunteer"]):
			insert({"doctype": "CrecheConnect Designation", "designation_name": name, "seniority": 100 + i})
		cls.lead = member("lead", "Test lead", cls.state, can_post=True)
		cls.coordinator = member("coordinator", "Test coordinator", cls.district, can_post=True)
		cls.volunteer = member("volunteer", "Test volunteer", block)
		cls.outsider = member("outsider", "Test volunteer", place("State", "TY", root))
		push.ensure_vapid_key()
		for user in (cls.lead, cls.coordinator, cls.volunteer, cls.outsider):
			frappe.set_user(user)
			push.subscribe(device(user))
		frappe.set_user("Administrator")

	def tearDown(self):
		frappe.set_user("Administrator")

	def post(self, user: str, places: list) -> str:
		frappe.set_user(user)
		return api.create_thread("Test thread", "<p>Hello</p>", places)["name"]

	def pushes(self, job, name) -> dict:
		with patch("creche_connect.push.webpush") as webpush:
			job(name)
		return {call.args[0]["endpoint"].rsplit("/", 1)[1]: json.loads(call.args[1]) for call in webpush.call_args_list}

	def test_new_thread_reaches_its_audience_but_not_its_author(self):
		thread = self.post(self.coordinator, [self.district])
		sent = self.pushes(push.thread_created, thread)
		self.assertEqual(set(sent), {self.volunteer})
		self.assertEqual(sent[self.volunteer]["url"], f"/c/threads/{thread}")

	def test_reply_reaches_the_author_and_mentioned_people_only(self):
		thread = self.post(self.lead, [self.state])
		mention = "".join(
			f'<span class="mention" data-type="mention" data-id="{u}" data-label="x">@x</span>'
			for u in (self.volunteer, self.outsider)
		)
		frappe.set_user(self.coordinator)
		reply = api.add_reply(thread, f"<p>{mention} see this</p>")["id"]
		sent = self.pushes(push.reply_created, reply)
		self.assertEqual(set(sent), {self.lead, self.volunteer})
		self.assertIn("mentioned you", sent[self.volunteer]["body"])
		self.assertNotIn("mentioned you", sent[self.lead]["body"])

	def test_group_mention_reaches_that_designation_in_the_audience(self):
		thread = self.post(self.lead, [self.state])
		frappe.set_user(self.coordinator)
		group = '<span class="mention" data-type="mention" data-id="designation:Test volunteer" data-label="Test volunteer">@x</span>'
		reply = api.add_reply(thread, f"<p>{group} please submit</p>")["id"]
		sent = self.pushes(push.reply_created, reply)
		self.assertEqual(set(sent), {self.lead, self.volunteer})
		self.assertIn("mentioned you", sent[self.volunteer]["body"])
		frappe.set_user(self.volunteer)
		self.assertIn(thread, [t["id"] for t in api.get_threads(filter="mentions")["threads"]])

	def test_followers_get_every_reply_and_muted_people_only_mentions(self):
		thread = self.post(self.lead, [self.state])
		frappe.set_user(self.volunteer)
		api.set_notify(thread, "Follow")
		frappe.set_user(self.outsider)
		with self.assertRaises(frappe.PermissionError):
			api.set_notify(thread, "Follow")
		frappe.set_user(self.lead)
		api.set_notify(thread, "Mute")
		frappe.set_user(self.coordinator)
		reply = api.add_reply(thread, "<p>Done</p>")["id"]
		self.assertEqual(set(self.pushes(push.reply_created, reply)), {self.volunteer})
		mention = f'<span class="mention" data-type="mention" data-id="{self.lead}" data-label="x">@x</span>'
		reply = api.add_reply(thread, f"<p>{mention} please check</p>")["id"]
		self.assertEqual(set(self.pushes(push.reply_created, reply)), {self.volunteer, self.lead})

	def test_reshare_to_team_reaches_the_new_people(self):
		thread = api.create_thread("Test thread", "<p>Hello</p>", [self.state], designations=["Test coordinator"])["name"]
		frappe.set_user(self.coordinator)
		api.toggle_reshare(thread, "Please read", places=[self.district])
		sent = self.pushes(push.reshare_created, f"{thread}-{self.coordinator}")
		self.assertEqual(set(sent), {self.volunteer})
		self.assertIn("reshared: Please read", sent[self.volunteer]["body"])

	def test_expired_device_is_forgotten(self):
		thread = self.post(self.coordinator, [self.district])
		gone = WebPushException("gone", response=MagicMock(status_code=410))
		with patch("creche_connect.push.webpush", side_effect=gone):
			push.thread_created(thread)
		self.assertFalse(frappe.db.exists(push.SUBSCRIPTION, {"user": self.volunteer}))
		frappe.set_user(self.volunteer)
		push.subscribe(device(self.volunteer))

	def test_only_real_push_services_are_accepted(self):
		frappe.set_user(self.volunteer)
		for endpoint in (
			"https://example.com/x",
			"http://fcm.googleapis.com/x",
			"https://fcm.googleapis.com.evil.io/x",
			"https://evil.io\\@fcm.googleapis.com/x",
			"https://fcm.googleapis.com:8443/x",
		):
			with self.assertRaises(frappe.ValidationError):
				push.subscribe({"endpoint": endpoint, "keys": {}})

	def test_device_moves_to_whoever_signs_in_on_it(self):
		frappe.set_user(self.outsider)
		push.subscribe(device(self.volunteer))
		owners = frappe.get_all(push.SUBSCRIPTION, {"endpoint": f"https://fcm.googleapis.com/fcm/send/{self.volunteer}"}, pluck="user")
		self.assertEqual(owners, [self.outsider])
		frappe.set_user(self.volunteer)
		push.subscribe(device(self.volunteer))
