from typing import Literal

import frappe
from frappe import _
from frappe.utils import cint, get_fullname, now_datetime
from frappe.utils.caching import request_cache

ADMIN_ROLES = {"System Manager", "Samvaad Admin"}
EMOJIS = ["👍", "❤️", "🙏", "🎉", "👏", "😮"]
TAG_COLORS = ["blue", "green", "amber", "violet", "red"]
MEMBER_FIELDS = ["user", "full_name", "designation", "place", "can_post"]
THREAD_FIELDS = [
	"name",
	"title",
	"content",
	"owner",
	"reply_policy",
	"ack_required",
	"last_activity",
	"reply_count",
	"creation",
]


def is_admin(user: str | None = None) -> bool:
	return bool(ADMIN_ROLES & set(frappe.get_roles(user)))


def get_me():
	user = frappe.session.user
	me = frappe.db.get_value("Samvaad Member", user, MEMBER_FIELDS, as_dict=True)
	admin = is_admin(user)
	if not me:
		if not admin:
			frappe.throw(
				_("You are not a Samvaad member yet. Ask an admin to add you."), frappe.PermissionError
			)
		me = frappe._dict(user=user, full_name=get_fullname(user), designation=None, place=None, can_post=1)
	me.is_admin = admin
	return me


@request_cache
def root_places() -> set[str]:
	return set(frappe.get_all("Samvaad Place", filters={"kind": "Country"}, pluck="name"))


def in_place(member_place: str | None, place: str) -> bool:
	member_place = member_place or ""
	return place in root_places() or member_place == place or member_place.startswith(place + "-")


def ancestors(place: str | None) -> list[str]:
	parts = (place or "").split("-") if place else []
	return [*root_places(), *("-".join(parts[: i + 1]) for i in range(len(parts)))]


def matches(member, thread) -> bool:
	return any(in_place(member.place, p) for p in thread.places) and (
		not thread.designations or member.designation in thread.designations
	)


def can_see(me, thread) -> bool:
	return thread.owner == me.user or matches(me, thread)


def can_reply(me, thread) -> bool:
	if not can_see(me, thread):
		return False
	if thread.owner == me.user or thread.reply_policy == "everyone":
		return True
	return thread.reply_policy == "posters" and bool(me.can_post)


def group_by(rows, key, value):
	out = {}
	for row in rows:
		out.setdefault(row[key], []).append(row[value])
	return out


def reactions_for(doctype: str, names: list) -> dict:
	rows = frappe.get_all(
		"Samvaad Reaction",
		filters={"reference_doctype": doctype, "reference_name": ["in", names]},
		fields=["reference_name", "emoji", "user"],
		order_by="creation asc",
	)
	out = {}
	for r in rows:
		out.setdefault(r.reference_name, {}).setdefault(r.emoji, []).append(r.user)
	return out


def load_threads(filters) -> list:
	threads = frappe.get_all(
		"Samvaad Thread", filters=filters, fields=THREAD_FIELDS, order_by="last_activity desc"
	)
	if not threads:
		return []
	for t in threads:
		t.name = str(t.name)
	names = [t.name for t in threads]
	child = {}
	for doctype, field in (
		("Samvaad Thread Place", "place"),
		("Samvaad Thread Designation", "designation"),
		("Samvaad Thread Tag", "tag"),
	):
		rows = frappe.get_all(
			doctype,
			filters={"parenttype": "Samvaad Thread", "parent": ["in", names]},
			fields=["parent", field],
			order_by="idx asc",
		)
		child[field] = group_by(rows, "parent", field)
	for t in threads:
		t.places = child["place"].get(t.name, [])
		t.designations = child["designation"].get(t.name, [])
		t.tags = child["tag"].get(t.name, [])
	return threads


def serialize(threads, me) -> list:
	if not threads:
		return []
	names = [t.name for t in threads]
	acks = group_by(
		frappe.get_all(
			"Samvaad Acknowledgement", filters={"thread": ["in", names]}, fields=["thread", "user"]
		),
		"thread",
		"user",
	)
	visits = frappe.get_all(
		"Samvaad Thread Visit", filters={"thread": ["in", names]}, fields=["thread", "user", "last_visit"]
	)
	seen = group_by(visits, "thread", "user")
	my_visits = {v.thread: v.last_visit for v in visits if v.user == me.user}
	reactions = reactions_for("Samvaad Thread", names)

	def unread(t):
		if t.owner == me.user and not t.reply_count:
			return False
		last = my_visits.get(t.name)
		return not last or t.last_activity > last

	def needs_ack(t):
		return (
			bool(t.ack_required)
			and t.owner != me.user
			and me.user not in acks.get(t.name, [])
			and matches(me, t)
		)

	return [
		{
			"id": t.name,
			"title": t.title,
			"body": t.content or "",
			"authorId": t.owner,
			"geo": {"places": t.places, "designations": t.designations},
			"tags": t.tags,
			"policy": t.reply_policy,
			"ackRequired": bool(t.ack_required),
			"acks": acks.get(t.name, []),
			"seenBy": [u for u in seen.get(t.name, []) if u != t.owner],
			"reactions": reactions.get(t.name, {}),
			"createdAt": t.creation,
			"lastActivity": t.last_activity,
			"replyCount": cint(t.reply_count),
			"unread": unread(t),
			"canReply": can_reply(me, t),
			"needsAck": needs_ack(t),
		}
		for t in threads
	]


def serialize_reply(r, reactions=None) -> dict:
	return {
		"id": str(r.name),
		"authorId": r.owner,
		"at": r.creation,
		"body": r.content,
		"reactions": reactions or {},
	}


def get_visible_thread(name: str, me):
	threads = load_threads({"name": name})
	if not threads or not can_see(me, threads[0]):
		frappe.throw(_("You can't see this thread"), frappe.PermissionError)
	return threads[0]


def touch_visit(thread: str, user: str):
	name = f"{thread}-{user}"
	if frappe.db.exists("Samvaad Thread Visit", name):
		frappe.db.set_value("Samvaad Thread Visit", name, "last_visit", now_datetime())
	else:
		frappe.get_doc(
			{"doctype": "Samvaad Thread Visit", "thread": thread, "user": user, "last_visit": now_datetime()}
		).insert(ignore_permissions=True, ignore_if_duplicate=True)


def audience_users(places: list, designations: list) -> list[str]:
	filters = {"designation": ["in", designations]} if designations else {}
	if set(places) & root_places():
		return frappe.get_all("Samvaad Member", filters=filters, pluck="user")
	or_filters = [f for p in places for f in (["place", "=", p], ["place", "like", f"{p}-%"])]
	return frappe.get_all("Samvaad Member", filters=filters, or_filters=or_filters, pluck="user")


def notify_audience(thread):
	users = set(
		audience_users([p.place for p in thread.places], [d.designation for d in thread.designations])
	)
	for user in (users | {thread.owner}) - {frappe.session.user}:
		frappe.publish_realtime(
			"samvaad_activity", {"thread": str(thread.name)}, user=user, after_commit=True
		)


def get_member(user: str) -> dict:
	member = frappe.db.get_value("Samvaad Member", user, MEMBER_FIELDS, as_dict=True)
	member.is_admin = is_admin(user)
	return member


@frappe.whitelist(methods=["GET"])
def get_boot() -> dict:
	me = get_me()
	members = frappe.get_all("Samvaad Member", fields=MEMBER_FIELDS, order_by="full_name asc")
	admins = set(
		frappe.get_all(
			"Has Role",
			filters={
				"parenttype": "User",
				"role": ["in", list(ADMIN_ROLES)],
				"parent": ["in", [m.user for m in members]],
			},
			pluck="parent",
		)
	)
	for m in members:
		m.is_admin = m.user in admins
	return {
		"me": me,
		"members": members,
		"places": frappe.get_all(
			"Samvaad Place",
			fields=["name", "place_name", "kind", "parent_place", "color"],
			order_by="name asc",
		),
		"designations": frappe.get_all(
			"Samvaad Designation", fields=["name", "seniority", "is_national"], order_by="seniority asc"
		),
		"tags": frappe.get_all("Samvaad Tag", fields=["name", "color"], order_by="creation asc"),
		"resources": frappe.get_all(
			"Samvaad Resource",
			fields=["name", "title", "kind", "url", "description", "pinned"],
			order_by="creation asc",
		),
		"emojis": EMOJIS,
	}


@frappe.whitelist(methods=["GET"])
def get_threads() -> list:
	me = get_me()
	names = set(
		frappe.get_all(
			"Samvaad Thread Place",
			filters={"parenttype": "Samvaad Thread", "place": ["in", ancestors(me.place)]},
			pluck="parent",
		)
	)
	names |= {str(n) for n in frappe.get_all("Samvaad Thread", filters={"owner": me.user}, pluck="name")}
	if not names:
		return []
	return serialize([t for t in load_threads({"name": ["in", list(names)]}) if can_see(me, t)], me)


@frappe.whitelist(methods=["GET"])
def get_thread(name: str) -> dict:
	me = get_me()
	thread = serialize([get_visible_thread(name, me)], me)[0]
	replies = frappe.get_all(
		"Samvaad Reply",
		filters={"thread": name},
		fields=["name", "owner", "content", "creation"],
		order_by="creation asc",
	)
	reactions = reactions_for("Samvaad Reply", [str(r.name) for r in replies]) if replies else {}
	thread["replies"] = [serialize_reply(r, reactions.get(str(r.name))) for r in replies]
	return thread


@frappe.whitelist(methods=["POST"])
def mark_read(name: str):
	me = get_me()
	get_visible_thread(name, me)
	touch_visit(name, me.user)


@frappe.whitelist(methods=["POST"])
def create_thread(
	title: str,
	content: str,
	places: list,
	designations: list | None = None,
	tags: list | None = None,
	reply_policy: Literal["everyone", "posters", "none"] = "everyone",
	ack_required: bool = False,
) -> dict:
	me = get_me()
	if not me.can_post:
		frappe.throw(_("You can't start threads"), frappe.PermissionError)
	if not places:
		frappe.throw(_("Pick at least one place"))
	if me.place and any(p in root_places() or not in_place(p, me.place) for p in places):
		frappe.throw(
			_("You can only post to {0} and places below it").format(frappe.bold(me.place)),
			frappe.PermissionError,
		)
	tag_names = list(dict.fromkeys(ensure_tag(t) for t in tags or []))
	thread = frappe.get_doc(
		{
			"doctype": "Samvaad Thread",
			"title": title.strip(),
			"content": content,
			"places": [{"place": p} for p in places],
			"designations": [{"designation": d} for d in designations or []],
			"tags": [{"tag": t} for t in tag_names],
			"reply_policy": reply_policy,
			"ack_required": cint(ack_required),
		}
	).insert(ignore_permissions=True)
	touch_visit(thread.name, me.user)
	return {
		"name": str(thread.name),
		"tags": frappe.get_all("Samvaad Tag", filters={"name": ["in", tag_names]}, fields=["name", "color"]),
	}


def ensure_tag(name: str) -> str:
	name = name.strip()
	existing = frappe.db.get_value("Samvaad Tag", name)
	if existing:
		return existing
	color = TAG_COLORS[frappe.db.count("Samvaad Tag") % len(TAG_COLORS)]
	return (
		frappe.get_doc({"doctype": "Samvaad Tag", "tag_name": name, "color": color})
		.insert(ignore_permissions=True)
		.name
	)


@frappe.whitelist(methods=["POST"])
def add_reply(thread: str, content: str) -> dict:
	me = get_me()
	if not can_reply(me, get_visible_thread(thread, me)):
		frappe.throw(_("You can't reply to this thread"), frappe.PermissionError)
	reply = frappe.get_doc({"doctype": "Samvaad Reply", "thread": thread, "content": content}).insert(
		ignore_permissions=True
	)
	touch_visit(thread, me.user)
	return serialize_reply(reply)


@frappe.whitelist(methods=["POST"])
def acknowledge(thread: str):
	me = get_me()
	doc = get_visible_thread(thread, me)
	if not doc.ack_required or not matches(me, doc):
		frappe.throw(_("This thread doesn't ask you to acknowledge it"))
	frappe.get_doc({"doctype": "Samvaad Acknowledgement", "thread": thread, "user": me.user}).insert(
		ignore_permissions=True, ignore_if_duplicate=True
	)


@frappe.whitelist(methods=["POST"])
def toggle_reaction(doctype: Literal["Samvaad Thread", "Samvaad Reply"], name: str, emoji: str):
	if emoji not in EMOJIS:
		frappe.throw(_("Unsupported reaction"))
	me = get_me()
	thread = name if doctype == "Samvaad Thread" else frappe.db.get_value("Samvaad Reply", name, "thread")
	get_visible_thread(thread, me)
	key = {"reference_doctype": doctype, "reference_name": name, "emoji": emoji, "user": me.user}
	existing = frappe.db.get_value("Samvaad Reaction", key)
	if existing:
		frappe.delete_doc("Samvaad Reaction", existing, ignore_permissions=True)
	else:
		frappe.get_doc({"doctype": "Samvaad Reaction", **key}).insert(ignore_permissions=True)


@frappe.whitelist(methods=["POST"])
def save_member(
	email: str,
	full_name: str,
	designation: str,
	place: str | None = None,
	can_post: bool = False,
	is_new: bool = False,
) -> dict:
	frappe.only_for(list(ADMIN_ROLES))
	exists = frappe.db.exists("Samvaad Member", email)
	if is_new and exists:
		frappe.throw(_("{0} is already a member").format(frappe.bold(email)), frappe.DuplicateEntryError)
	first_name, _sep, last_name = full_name.strip().partition(" ")
	if frappe.db.exists("User", email):
		user = frappe.get_doc("User", email)
		user.update({"first_name": first_name, "last_name": last_name})
	else:
		user = frappe.get_doc(
			{
				"doctype": "User",
				"email": email,
				"first_name": first_name,
				"last_name": last_name,
				"user_type": "Website User",
				"send_welcome_email": 0,
			}
		)
	user.save(ignore_permissions=True)
	member = (
		frappe.get_doc("Samvaad Member", email)
		if exists
		else frappe.get_doc({"doctype": "Samvaad Member", "user": email})
	)
	member.update({"designation": designation, "place": place or None, "can_post": cint(can_post)})
	member.save(ignore_permissions=True)
	return get_member(email)
