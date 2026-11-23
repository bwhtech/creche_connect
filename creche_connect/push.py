import json
from urllib.parse import urlparse

import frappe
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
from frappe import _
from frappe.desk.notifications import extract_mentions
from frappe.utils import get_fullname, strip_html
from frappe.utils.password import get_decrypted_password, set_encrypted_password
from py_vapid import Vapid
from py_vapid.utils import b64urlencode
from pywebpush import WebPushException, webpush

from creche_connect.api import thread_audience

SUBSCRIPTION = "CrecheConnect Push Subscription"
VAPID_KEY = (SUBSCRIPTION, "vapid", "private_key")
PUSH_HOSTS = ("fcm.googleapis.com", "push.apple.com", "push.services.mozilla.com", "notify.windows.com")


def ensure_vapid_key():
	if not get_decrypted_password(*VAPID_KEY, raise_exception=False):
		key = Vapid()
		key.generate_keys()
		raw = b64urlencode(key.private_key.private_numbers().private_value.to_bytes(32))
		set_encrypted_password(SUBSCRIPTION, "vapid", raw, "private_key")


def vapid() -> Vapid:
	return Vapid.from_raw(get_decrypted_password(*VAPID_KEY).encode())


@frappe.whitelist(methods=["GET"])
def get_public_key() -> str:
	return b64urlencode(vapid().public_key.public_bytes(Encoding.X962, PublicFormat.UncompressedPoint))


@frappe.whitelist(methods=["POST"])
def subscribe(subscription: dict):
	endpoint = subscription.get("endpoint") or ""
	url = urlparse(endpoint)
	host = (url.hostname or "").rstrip(".").lower()
	if url.scheme != "https" or not any(host == h or host.endswith(f".{h}") for h in PUSH_HOSTS):
		frappe.throw(_("This device can't receive notifications"))
	frappe.db.delete(SUBSCRIPTION, {"endpoint": endpoint})
	frappe.get_doc(
		{"doctype": SUBSCRIPTION, "user": frappe.session.user, "endpoint": endpoint, "subscription": subscription}
	).insert(ignore_permissions=True)


@frappe.whitelist(methods=["POST"])
def unsubscribe(endpoint: str):
	frappe.db.delete(SUBSCRIPTION, {"endpoint": endpoint, "user": frappe.session.user})


def push(bodies: dict, title: str, url: str):
	subscriptions = [
		s for s in frappe.get_all(SUBSCRIPTION, fields=["name", "user", "subscription"]) if s.user in bodies
	]
	if not subscriptions:
		return
	key = vapid()
	for s in subscriptions:
		try:
			webpush(
				json.loads(s.subscription),
				json.dumps({"title": title, "body": bodies[s.user], "url": url}),
				vapid_private_key=key,
				vapid_claims={"sub": f"mailto:noreply@{frappe.local.site}"},
				ttl=86400,
				timeout=10,
			)
		except WebPushException as e:
			if e.response is not None and e.response.status_code in (404, 410):
				frappe.db.delete(SUBSCRIPTION, s.name)
			else:
				frappe.log_error("CrecheConnect push failed")


def preview(html: str | None) -> str:
	return strip_html(html or "").strip()[:200] or _("Sent a picture, audio or video")


def queue(job: str, name):
	frappe.enqueue(f"creche_connect.push.{job}", enqueue_after_commit=True, name=str(name))


def thread_created(name: str):
	if not frappe.db.count(SUBSCRIPTION):
		return
	thread = frappe.get_doc("CrecheConnect Thread", name)
	body = f"{get_fullname(thread.owner)}: {preview(thread.content)}"
	push(dict.fromkeys(thread_audience(thread) - {thread.owner}, body), thread.title, f"/c/threads/{name}")


def reply_created(name: str):
	if not frappe.db.count(SUBSCRIPTION):
		return
	reply = frappe.get_doc("CrecheConnect Reply", name)
	thread = frappe.get_doc("CrecheConnect Thread", reply.thread)
	author, text = get_fullname(reply.owner), preview(reply.content)
	bodies = {thread.owner: f"{author}: {text}"}
	if mentioned := set(extract_mentions(reply.content or "")):
		mention = _("{0} mentioned you: {1}").format(author, text)
		bodies |= dict.fromkeys(mentioned & (thread_audience(thread) | {thread.owner}), mention)
	bodies.pop(reply.owner, None)
	push(bodies, thread.title, f"/c/threads/{thread.name}?reply={name}")
