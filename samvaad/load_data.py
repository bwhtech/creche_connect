import random
import statistics
import time
from collections import defaultdict

import frappe
from frappe.database.sequence import get_next_val, set_next_val
from frappe.utils import add_to_date, now_datetime

from samvaad import api

DOMAIN = "load.samvaad.local"
DAYS = 180
FIRST = [
	"Asha",
	"Ravi",
	"Meena",
	"Suresh",
	"Geeta",
	"Arun",
	"Pooja",
	"Manoj",
	"Lakshmi",
	"Deepak",
	"Kiran",
	"Sunita",
]
LAST = [
	"Sahu",
	"Patil",
	"Yadav",
	"Netam",
	"Kumar",
	"Joshi",
	"Verma",
	"Ekka",
	"Reddy",
	"Singh",
	"Minj",
	"Pawar",
]
TOPICS = [
	"Attendance register for {m}",
	"Training day for new volunteers in {m}",
	"Books and slates reached the centres",
	"Monthly report due on the 5th",
	"Centre closed for the {m} holidays",
	"Parents meeting this Saturday",
	"Learning levels after the {m} test",
	"Travel allowance claims for {m}",
]
LINES = [
	"Please share this with everyone in your area.",
	"The new forms are in the Resources section.",
	"Reply here if your centre has a problem.",
	"Most centres finished on time, a few are still pending.",
	"We will discuss this in the next review call.",
	"Thank you for the quick work last week.",
	"Send photos of the centre with your report.",
	"Noted, I will tell the volunteers today.",
	"Two of our centres need more books.",
	"Done for my block.",
]
MONTHS = ["June", "July", "August", "September", "October", "November"]
ROLES = [
	("Block", "Field volunteer"),
	("Block", "Block coordinator"),
	("District", "District coordinator"),
	("District", "Program manager"),
	("State", "State program manager"),
]
ROLE_WEIGHTS = [70, 10, 8, 7, 5]


def _row(owner, at):
	return {"owner": owner, "modified_by": owner, "creation": at, "modified": at}


def _insert(doctype, rows):
	if rows:
		fields = list(rows[0])
		frappe.db.bulk_insert(doctype, fields, [[r[f] for f in fields] for r in rows], chunk_size=5000)


def _members(count):
	places = frappe.get_all("Samvaad Place", fields=["name", "kind"])
	by_kind = {k: [p.name for p in places if p.kind == k] for k in ("State", "District", "Block")}
	users, members, now = [], [], now_datetime()
	for i in range(count):
		kind, designation = random.choices(ROLES, weights=ROLE_WEIGHTS)[0]
		email = f"m{i}@{DOMAIN}"
		first, last = random.choice(FIRST), random.choice(LAST)
		full_name = f"{first} {last}"
		users.append(
			{
				"name": email,
				"email": email,
				"first_name": first,
				"last_name": last,
				"full_name": full_name,
				"user_type": "Website User",
				"enabled": 1,
				**_row("Administrator", now),
			}
		)
		members.append(
			{
				"name": email,
				"user": email,
				"full_name": full_name,
				"designation": designation,
				"place": random.choice(by_kind[kind]),
				"can_post": int(designation != "Field volunteer"),
				**_row("Administrator", now),
			}
		)
	_insert("User", users)
	_insert("Samvaad Member", members)
	return frappe.get_all("Samvaad Member", fields=["user", "place", "designation", "can_post"])


def make(members: int = 2000, threads: int = 5000, avg_replies: int = 8, seed: int = 7):
	random.seed(seed)
	everyone = _members(members)
	posters = [m for m in everyone if m.can_post and m.place and m.user.endswith(DOMAIN)]
	places = frappe.get_all("Samvaad Place", fields=["name", "parent_place"])
	tags = frappe.get_all("Samvaad Tag", pluck="name")
	below = {p.name: [m for m in everyone if api.in_place(m.place, p.name)] for p in places}
	children = defaultdict(list)
	for p in places:
		children[p.parent_place].append(p.name)

	rows = defaultdict(list)
	thread_id = get_next_val("Samvaad Thread")
	reply_id = get_next_val("Samvaad Reply")
	now = now_datetime()

	def react(doctype, name, users, at):
		for user in random.sample(users, min(len(users), random.choice([0, 0, 1, 2, 4]))):
			rows["Samvaad Reaction"].append(
				{
					"name": frappe.generate_hash(length=10),
					"reference_doctype": doctype,
					"reference_name": str(name),
					"emoji": random.choice(api.EMOJIS),
					"user": user,
					**_row(user, at),
				}
			)

	for name in range(thread_id, thread_id + threads):
		author = random.choice(posters)
		place = random.choice([author.place, *children[author.place]])
		designations = (
			[random.choice(["Field volunteer", "Block coordinator"])] if random.random() < 0.1 else []
		)
		policy = random.choices(["everyone", "posters", "none"], weights=[70, 20, 10])[0]
		created = add_to_date(now, minutes=-random.randint(10, DAYS * 24 * 60))
		audience = [m for m in below[place] if not designations or m.designation in designations]
		users = [m.user for m in audience]
		repliers = (
			[m.user for m in audience if policy == "everyone" or m.can_post] if policy != "none" else []
		)
		last, count = created, 0
		for _i in range(min(int(random.expovariate(1 / avg_replies)), avg_replies * 6) if repliers else 0):
			last = add_to_date(last, minutes=random.randint(1, 600))
			if last > now:
				break
			user = random.choice(repliers)
			rows["Samvaad Reply"].append(
				{
					"name": reply_id,
					"thread": name,
					"content": f"<p>{random.choice(LINES)}</p>",
					**_row(user, last),
				}
			)
			react("Samvaad Reply", reply_id, users, last)
			reply_id += 1
			count += 1
		ack = int(random.random() < 0.15)
		rows["Samvaad Thread"].append(
			{
				"name": name,
				"title": random.choice(TOPICS).format(m=random.choice(MONTHS)),
				"content": "".join(f"<p>{line}</p>" for line in random.sample(LINES, 3)),
				"reply_policy": policy,
				"ack_required": ack,
				"reply_count": count,
				"last_activity": last,
				**_row(author.user, created),
			}
		)
		for column, values in (
			("place", [place]),
			("designation", designations),
			("tag", random.sample(tags, random.randint(0, min(2, len(tags))))),
		):
			for idx, value in enumerate(values, 1):
				rows[f"Samvaad Thread {column.title()}"].append(
					{
						"name": frappe.generate_hash(length=10),
						"parent": name,
						"parenttype": "Samvaad Thread",
						"parentfield": column + "s",
						"idx": idx,
						column: value,
						**_row(author.user, created),
					}
				)
		react("Samvaad Thread", name, users, created)
		minutes_since = max(1, int((now - created).total_seconds() // 60))
		for user in {author.user, *random.sample(users, int(len(users) * random.uniform(0.2, 0.9)))}:
			seen = add_to_date(created, minutes=random.randint(0, minutes_since))
			key = {"name": f"{name}-{user}", "thread": name, "user": user, **_row(user, seen)}
			rows["Samvaad Thread Visit"].append({**key, "last_visit": seen})
			if ack and user != author.user and random.random() < 0.6:
				rows["Samvaad Acknowledgement"].append(key)

	set_next_val("Samvaad Thread", thread_id + threads - 1, is_val_used=True)
	set_next_val("Samvaad Reply", reply_id - 1, is_val_used=True)
	for doctype, data in rows.items():
		_insert(doctype, data)
	frappe.db.commit()
	return {doctype: len(data) for doctype, data in rows.items()} | {"Samvaad Member": members}


def clear():
	owner = ["like", f"%@{DOMAIN}"]
	threads = f"select name from `tabSamvaad Thread` where owner like '%@{DOMAIN}'"
	replies = f"select name from `tabSamvaad Reply` where thread in ({threads})"
	frappe.db.sql(
		f"delete from `tabSamvaad Reaction` where reference_doctype = 'Samvaad Reply' and reference_name in ({replies})"
	)
	frappe.db.sql(
		f"delete from `tabSamvaad Reaction` where reference_doctype = 'Samvaad Thread' and reference_name in ({threads})"
	)
	for doctype in ("Samvaad Reply", "Samvaad Thread Visit", "Samvaad Acknowledgement"):
		frappe.db.sql(f"delete from `tab{doctype}` where thread in ({threads})")
	for doctype in ("Samvaad Thread Place", "Samvaad Thread Designation", "Samvaad Thread Tag"):
		frappe.db.sql(
			f"delete from `tab{doctype}` where parenttype = 'Samvaad Thread' and parent in ({threads})"
		)
	frappe.db.delete("Samvaad Thread", {"owner": owner})
	frappe.db.delete("Samvaad Member", {"user": owner})
	frappe.db.delete("User", {"name": owner})
	frappe.db.commit()


def _time(fn, user, runs):
	sql, calls, times = frappe.db.sql, [0], []

	def counted(*args, **kwargs):
		calls[0] += 1
		return sql(*args, **kwargs)

	frappe.db.sql = counted
	try:
		for _i in range(runs):
			frappe.set_user(user)
			frappe.local.request_cache.clear()
			frappe.db.value_cache.clear()
			calls[0] = 0
			start = time.perf_counter()
			fn()
			times.append((time.perf_counter() - start) * 1000)
	finally:
		del frappe.db.sql
	return round(statistics.median(times), 1), calls[0]


def measure(runs: int = 7):
	def pick(designation):
		return frappe.db.get_value(
			"Samvaad Member", {"user": ["like", f"%@{DOMAIN}"], "designation": designation}
		)

	who = {
		"national (anita)": "anita@samvaad.local",
		"state (rahul)": "rahul@samvaad.local",
		"district coordinator": pick(designation="District coordinator"),
		"block volunteer": pick(designation="Field volunteer"),
	}
	tag = frappe.db.sql(
		"select tag from `tabSamvaad Thread Tag` group by tag order by count(*) desc limit 1"
	)[0][0]
	report = []
	for label, user in who.items():
		frappe.set_user(user)
		first = api.get_threads()
		visible = api.get_counts()["total"]
		calls = {
			"get_boot": api.get_boot,
			"get_threads": api.get_threads,
			"get_threads unread": lambda: api.get_threads(filter="unread"),
			f"get_threads tag={tag}": lambda: api.get_threads(tag=tag),
			"get_counts": api.get_counts,
		}
		if first["cursor"]:
			calls["get_threads page 2"] = lambda: api.get_threads(cursor=first["cursor"])
		if first["threads"]:
			busiest = max(first["threads"], key=lambda t: t["replyCount"])
			calls[f"get_thread ({busiest['replyCount']} replies)"] = lambda: api.get_thread(busiest["id"])
		for name, fn in calls.items():
			ms, queries = _time(fn, user, runs)
			report.append({"user": label, "visible": visible, "call": name, "ms": ms, "queries": queries})
	frappe.set_user("Administrator")
	for r in report:
		print(
			f"{r['user']:<22} {r['visible']:>6} visible  {r['call']:<34} {r['ms']:>8} ms  {r['queries']:>3} queries"
		)
