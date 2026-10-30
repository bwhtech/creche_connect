from typing import Literal

import frappe
from frappe import _
from frappe.query_builder import DocType, Order
from frappe.query_builder.functions import Cast_, Count
from frappe.rate_limiter import rate_limit
from frappe.utils import cint, get_fullname, now_datetime
from frappe.utils.caching import request_cache

Thread = DocType("Samvaad Thread")
ThreadPlace = DocType("Samvaad Thread Place")
ThreadDesignation = DocType("Samvaad Thread Designation")
ThreadTag = DocType("Samvaad Thread Tag")
Visit = DocType("Samvaad Thread Visit")
Acknowledgement = DocType("Samvaad Acknowledgement")

PAGE_SIZE = 30
MAX_PAGE_SIZE = 300
REPLY_PAGE_SIZE = 50
MAX_CONTENT_LENGTH = 50_000
ADMIN_ROLES = {"System Manager", "Samvaad Admin"}
EMOJIS = ["👍", "❤️", "🙏", "🎉", "👏", "😮"]
TAG_COLORS = ["blue", "green", "amber", "violet", "red"]
limit_posts = rate_limit(limit=30, seconds=60, ip_based=False, user_based=True)
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
	"edited_at",
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


def can_acknowledge(me, thread) -> bool:
	return bool(thread.ack_required) and thread.owner != me.user and matches(me, thread)


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
		"Samvaad Thread", filters=filters, fields=THREAD_FIELDS, order_by="last_activity desc, name desc"
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
	my_visits = dict(
		frappe.get_all(
			"Samvaad Thread Visit",
			filters={"thread": ["in", names], "user": me.user},
			fields=["thread", "last_visit"],
			as_list=True,
		)
	)
	seen = dict(
		frappe.qb.from_(Visit)
		.join(Thread)
		.on(Thread.name == Visit.thread)
		.select(Visit.thread, Count("*"))
		.where(Visit.thread.isin(names) & (Visit.user != Thread.owner))
		.groupby(Visit.thread)
		.run()
	)
	reactions = reactions_for("Samvaad Thread", names)

	def unread(t):
		if t.owner == me.user and not t.reply_count:
			return False
		last = my_visits.get(t.name)
		return not last or t.last_activity > last

	def needs_ack(t):
		return can_acknowledge(me, t) and me.user not in acks.get(t.name, [])

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
			"seenCount": seen.get(t.name, 0),
			"reactions": reactions.get(t.name, {}),
			"createdAt": t.creation,
			"editedAt": t.edited_at,
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
		"editedAt": r.edited_at,
		"body": r.content,
		"reactions": reactions or {},
	}


def check_content_length(content: str | None):
	if len(content or "") > MAX_CONTENT_LENGTH:
		frappe.throw(
			_("This message is too long. Shorten it, or add long documents under Resources and link to them."),
			title=_("Message too long"),
		)


def check_only_author_edits(doc, *fields):
	if not doc.is_new() and doc.owner != frappe.session.user and any(doc.has_value_changed(f) for f in fields):
		frappe.throw(_("Only the author can edit this message"), frappe.PermissionError)


def get_visible_thread(name: str, me):
	threads = load_threads({"name": name})
	if not threads:
		frappe.throw(_("This thread was removed"), frappe.DoesNotExistError)
	if not can_see(me, threads[0]):
		frappe.throw(_("You can't see this thread"), frappe.PermissionError)
	return threads[0]


def touch_visit(thread: str, user: str):
	now = now_datetime()
	(
		frappe.qb.into(Visit)
		.columns("name", "thread", "user", "last_visit", "owner", "modified_by", "creation", "modified")
		.insert(f"{thread}-{user}", thread, user, now, user, user, now, now)
		.on_duplicate_key_update(Visit.last_visit, now)
		.on_duplicate_key_update(Visit.modified, now)
		.run()
	)


def audience_users(places: list, designations: list) -> list[str]:
	filters = {"designation": ["in", designations]} if designations else {}
	if set(places) & root_places():
		return frappe.get_all("Samvaad Member", filters=filters, pluck="user")
	or_filters = [f for p in places for f in (["place", "=", p], ["place", "like", f"{p}-%"])]
	return frappe.get_all("Samvaad Member", filters=filters, or_filters=or_filters, pluck="user")


def notify_audience(thread: str):
	frappe.enqueue(
		"samvaad.api.send_activity",
		queue="short",
		enqueue_after_commit=True,
		thread=str(thread),
		sender=frappe.session.user,
	)


def send_activity(thread: str, sender: str):
	doc = frappe.get_doc("Samvaad Thread", thread)
	users = set(audience_users([p.place for p in doc.places], [d.designation for d in doc.designations]))
	for user in (users | {doc.owner}) - {sender}:
		frappe.publish_realtime("samvaad_activity", {"thread": thread}, user=user)


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


def thread_ids(table, column="parent"):
	return frappe.qb.from_(table).select(Cast_(table[column], "unsigned"))


def thread_key():
	return Cast_(Thread.name, "varchar")


def in_audience(me):
	designated = thread_ids(ThreadDesignation)
	designation_ok = Thread.name.notin(designated)
	if me.designation:
		designation_ok |= Thread.name.isin(designated.where(ThreadDesignation.designation == me.designation))
	places = thread_ids(ThreadPlace)
	return (
		Thread.name.isin(places.where(ThreadPlace.place.isin(ancestors(me.place) or [""]))) & designation_ok
	)


def feed_query(me, filter: str | None = None, tag: str | None = None):
	query = frappe.qb.from_(Thread)
	if filter == "mine":
		query = query.where(Thread.owner == me.user)
	else:
		query = query.where((Thread.owner == me.user) | in_audience(me))
	if filter == "unread":
		query = (
			query.left_join(Visit)
			.on((Visit.thread == thread_key()) & (Visit.user == me.user))
			.where(Visit.last_visit.isnull() | (Thread.last_activity > Visit.last_visit))
			.where((Thread.owner != me.user) | (Thread.reply_count > 0))
		)
	elif filter == "ack":
		acked = thread_ids(Acknowledgement, "thread").where(Acknowledgement.user == me.user)
		query = query.where((Thread.ack_required == 1) & (Thread.owner != me.user) & Thread.name.notin(acked))
	if tag:
		tagged = thread_ids(ThreadTag).where(ThreadTag.tag == tag)
		query = query.where(Thread.name.isin(tagged))
	return query


def count(query) -> int:
	return query.select(Count("*")).run()[0][0]


@frappe.whitelist(methods=["GET"])
def get_threads(
	filter: Literal["unread", "ack", "mine"] | None = None,
	tag: str | None = None,
	cursor: str | None = None,
	limit: int = PAGE_SIZE,
) -> dict:
	me = get_me()
	size = min(max(cint(limit), PAGE_SIZE), MAX_PAGE_SIZE)
	query = (
		feed_query(me, filter, tag)
		.select(Thread.name, Thread.last_activity)
		.orderby(Thread.last_activity, order=Order.desc)
		.orderby(Thread.name, order=Order.desc)
		.limit(size + 1)
	)
	if cursor:
		at, _sep, name = cursor.rpartition("|")
		if not at:
			frappe.throw(_("Invalid cursor"))
		query = query.where(
			(Thread.last_activity < at) | ((Thread.last_activity == at) & (Thread.name < cint(name)))
		)
	rows = query.run()
	page = rows[:size]
	threads = load_threads({"name": ["in", [r[0] for r in page]]}) if page else []
	return {
		"threads": serialize(threads, me),
		"cursor": f"{page[-1][1]}|{page[-1][0]}" if len(rows) > size else None,
	}


@frappe.whitelist(methods=["GET"])
def get_counts(filter: Literal["unread", "ack", "mine"] | None = None) -> dict:
	me = get_me()
	tags = (
		feed_query(me, filter)
		.join(ThreadTag)
		.on(ThreadTag.parent == thread_key())
		.select(ThreadTag.tag, Count("*"))
		.groupby(ThreadTag.tag)
		.run()
	)
	counts = {"unread": count(feed_query(me, "unread")), "ack": count(feed_query(me, "ack"))}
	return {**counts, "total": counts.get(filter) or count(feed_query(me, filter)), "tags": dict(tags)}


def load_replies(thread: str, before: int | None = None) -> dict:
	filters = {"thread": thread}
	if before:
		filters["name"] = ["<", before]
	replies = frappe.get_all(
		"Samvaad Reply",
		filters=filters,
		fields=["name", "owner", "content", "creation", "edited_at"],
		order_by="name desc",
		limit=REPLY_PAGE_SIZE + 1,
	)
	page = replies[:REPLY_PAGE_SIZE][::-1]
	reactions = reactions_for("Samvaad Reply", [str(r.name) for r in page]) if page else {}
	return {
		"replies": [serialize_reply(r, reactions.get(str(r.name))) for r in page],
		"hasOlder": len(replies) > REPLY_PAGE_SIZE,
	}


@frappe.whitelist(methods=["GET"])
def get_thread(name: str) -> dict:
	me = get_me()
	doc = get_visible_thread(name, me)
	thread = serialize([doc], me)[0]
	thread["seenBy"] = frappe.get_all(
		"Samvaad Thread Visit", filters={"thread": name, "user": ["!=", doc.owner]}, pluck="user"
	)
	thread.update(load_replies(name))
	return thread


@frappe.whitelist(methods=["GET"])
def get_replies(thread: str, before: int) -> dict:
	get_visible_thread(thread, get_me())
	return load_replies(thread, before)


@frappe.whitelist(methods=["POST"])
def mark_read(name: str):
	me = get_me()
	get_visible_thread(name, me)
	touch_visit(name, me.user)


@frappe.whitelist(methods=["POST"])
@limit_posts
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
@limit_posts
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
	if not can_acknowledge(me, doc):
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
def update_message(
	doctype: Literal["Samvaad Thread", "Samvaad Reply"], name: str, content: str, title: str | None = None
) -> dict:
	get_me()
	doc = frappe.get_doc(doctype, name)
	doc.content = content
	if doctype == "Samvaad Thread" and title is not None:
		doc.title = title.strip()
	doc.save(ignore_permissions=True)
	return {"title": doc.get("title"), "body": doc.content, "editedAt": doc.edited_at}


@frappe.whitelist(methods=["POST"])
def delete_message(doctype: Literal["Samvaad Thread", "Samvaad Reply"], name: str):
	if frappe.db.get_value(doctype, name, "owner") != frappe.session.user and not get_me().is_admin:
		frappe.throw(_("Only the author or an admin can delete this message"), frappe.PermissionError)
	frappe.delete_doc(doctype, name, ignore_permissions=True)


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
