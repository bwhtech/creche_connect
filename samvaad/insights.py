from collections import Counter, defaultdict
from typing import Literal

import frappe
from frappe.utils import add_days, get_first_day_of_week, getdate, now_datetime

from samvaad.api import ADMIN_ROLES, MEMBER_FIELDS, load_threads, matches

PERIODS = {"7d": (7, "day"), "30d": (30, "day"), "90d": (91, "week")}


def rate(part: int, whole: int) -> float:
	return part / whole if whole else 0


def window_stats(start, end, members) -> dict:
	threads = load_threads({"creation": ["between", [start, end]]})
	audience = {t.name: {m.user for m in members if matches(m, t)} for t in threads}
	in_threads = {"thread": ["in", list(audience) or [""]]}
	visits = frappe.get_all("Samvaad Thread Visit", filters=in_threads, fields=["thread", "user", "creation"])
	acks = frappe.get_all("Samvaad Acknowledgement", filters=in_threads, fields=["thread", "user"])
	replies = frappe.get_all("Samvaad Reply", filters=in_threads, fields=["name", "thread"], as_list=True)
	reply_thread = {str(name): thread for name, thread in replies}
	reactions = frappe.get_all(
		"Samvaad Reaction",
		filters={
			"reference_name": ["in", [*audience, *reply_thread] or [""]],
			"creation": ["between", [start, end]],
		},
		fields=["reference_doctype", "reference_name", "user"],
	)
	for r in reactions:
		r.thread = (
			r.reference_name
			if r.reference_doctype == "Samvaad Thread"
			else reply_thread.get(r.reference_name)
		)
	reactions = [r for r in reactions if r.thread in audience]

	reached = set().union(*audience.values())
	ack_due = [u for t in threads if t.ack_required for u in audience[t.name] - {t.owner}]
	acked = [a.user for a in acks if a.user in audience[a.thread]]
	return {
		"threads": threads,
		"audience": audience,
		"visits": visits,
		"reactions": reactions,
		"reached": reached,
		"seen": {v.user for v in visits if v.user in audience[v.thread]},
		"ack_due": ack_due,
		"acked": acked,
	}


def kpis(stats) -> dict:
	return {
		"threads": len(stats["threads"]),
		"reached": len(stats["reached"]),
		"seenRate": rate(len(stats["seen"]), len(stats["reached"])),
		"ackRate": rate(len(stats["acked"]), len(stats["ack_due"])),
		"reactions": len(stats["reactions"]),
	}


def region_of(place: str | None, depth: int) -> str | None:
	parts = (place or "").split("-")
	return "-".join(parts[:depth]) if len(parts) >= depth else None


def region_stats(stats, members, depth: int) -> dict:
	by_user = {m.user: region_of(m.place, depth) for m in members}

	def count(users):
		return Counter(by_user.get(u) for u in users)

	reach, seen = count(stats["reached"]), count(stats["seen"])
	ack_due, acked = count(stats["ack_due"]), count(stats["acked"])
	reactions = count(r.user for r in stats["reactions"])
	threads = Counter(
		code for t in stats["threads"] for code in {by_user[u] for u in stats["audience"][t.name]}
	)
	return {
		code: {
			"reach": reach[code],
			"seenRate": rate(seen[code], reach[code]),
			"ackRate": rate(acked[code], ack_due[code]),
			"reactions": reactions[code],
			"threads": threads[code],
		}
		for code in set(reach) | set(reactions)
		if code
	}


@frappe.whitelist(methods=["GET"])
def get_insights(period: Literal["7d", "30d", "90d"] = "30d") -> dict:
	frappe.only_for(list(ADMIN_ROLES))
	days, step = PERIODS[period]
	end = now_datetime()
	start = add_days(end, -days)
	members = frappe.get_all("Samvaad Member", fields=MEMBER_FIELDS)
	current = window_stats(start, end, members)

	districts = defaultdict(list)
	for code, d in sorted(region_stats(current, members, 2).items(), key=lambda x: -x[1]["reach"]):
		districts[region_of(code, 1)].append({"id": code, **d})

	thread_tags = {t.name: t.tags for t in current["threads"]}
	tags = Counter(tag for r in current["reactions"] for tag in thread_tags.get(r.thread, []))
	designation_of = {m.user: m.designation or "National staff" for m in members}
	designations = Counter(designation_of[u] for u in current["reached"])

	def bucket_of(day):
		return day if step == "day" else get_first_day_of_week(day)

	openers, visitors = defaultdict(set), defaultdict(set)
	for v in current["visits"]:
		openers[bucket_of(getdate(v.creation))].add(v.user)
		visitors[v.thread].add(v.user)
	last = bucket_of(getdate(end))
	gap = 1 if step == "day" else 7
	buckets = [add_days(last, -gap * i) for i in reversed(range(days // gap))]

	per_thread = Counter(r.thread for r in current["reactions"])
	top = []
	for t in sorted(current["threads"], key=lambda t: per_thread[t.name], reverse=True)[:5]:
		audience = current["audience"][t.name]
		if per_thread[t.name]:
			top.append(
				{
					"id": t.name,
					"title": t.title,
					"tags": t.tags,
					"reactions": per_thread[t.name],
					"seenRate": rate(len(visitors[t.name] & audience), len(audience)),
				}
			)

	return {
		"kpis": kpis(current),
		"previous": kpis(window_stats(add_days(start, -days), start, members)),
		"states": region_stats(current, members, 1),
		"districts": districts,
		"topics": [{"tag": tag, "reactions": n} for tag, n in tags.most_common()],
		"designations": [{"name": d, "people": n} for d, n in designations.most_common()],
		"engagement": [{"date": b.strftime("%-d %b"), "people": len(openers[b])} for b in buckets],
		"step": step,
		"topThreads": top,
	}
