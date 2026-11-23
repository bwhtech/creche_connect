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
		for endpoint in ("https://example.com/x", "http://fcm.googleapis.com/x", "https://fcm.googleapis.com.evil.io/x"):
			with self.assertRaises(frappe.ValidationError):
				push.subscribe({"endpoint": endpoint, "keys": {}})

	def test_device_moves_to_whoever_signs_in_on_it(self):
		frappe.set_user(self.outsider)
		push.subscribe(device(self.volunteer))
		owners = frappe.get_all(push.SUBSCRIPTION, {"endpoint": f"https://fcm.googleapis.com/fcm/send/{self.volunteer}"}, pluck="user")
		self.assertEqual(owners, [self.outsider])
		frappe.set_user(self.volunteer)
		push.subscribe(device(self.volunteer))
