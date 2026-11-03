import frappe
from frappe.utils import add_to_date, now_datetime

PASSWORD = "crecheconnect123"

GEO = [
	(
		"CG",
		"Chhattisgarh",
		"green",
		[
			(
				"JSP",
				"Jashpur",
				[
					("KNK", "Kunkuri"),
					("PTH", "Pathalgaon"),
					("BGC", "Bagicha"),
					("KSB", "Kansabel"),
					("DLD", "Duldula"),
					("FRS", "Farsabahar"),
				],
			),
			("RPR", "Raipur", [("ABP", "Abhanpur"), ("ARG", "Arang"), ("TLD", "Tilda"), ("DRS", "Dharsiwa")]),
			(
				"BSP",
				"Bilaspur",
				[("MST", "Masturi"), ("TKP", "Takhatpur"), ("KTA", "Kota"), ("BLH", "Bilha")],
			),
			("BST", "Bastar", [("JDP", "Jagdalpur"), ("BSN", "Bastanar"), ("LHD", "Lohandiguda")]),
			("SRG", "Surguja", [("AMB", "Ambikapur"), ("LDR", "Lundra"), ("MNP", "Mainpat")]),
			("KRB", "Korba", [("KTG", "Katghora"), ("PAL", "Pali"), ("PDU", "Podi-Uproda")]),
		],
	),
	(
		"MP",
		"Madhya Pradesh",
		"red",
		[
			("BPL", "Bhopal", [("PHN", "Phanda"), ("BRS", "Berasia")]),
			("IDR", "Indore", [("MHW", "Mhow"), ("DPL", "Depalpur"), ("SNW", "Sanwer")]),
			("JBP", "Jabalpur", [("PNG", "Panagar"), ("SHR", "Sihora"), ("KDM", "Kundam")]),
			("GWL", "Gwalior", [("BTW", "Bhitarwar"), ("DBR", "Dabra")]),
			("MDL", "Mandla", [("BCH", "Bichhiya"), ("NNP", "Nainpur"), ("NRN", "Narayanganj")]),
		],
	),
	(
		"MH",
		"Maharashtra",
		"amber",
		[
			("PUN", "Pune", [("HVL", "Haveli"), ("MLS", "Mulshi")]),
			("NSK", "Nashik", [("SNR", "Sinnar"), ("IGP", "Igatpuri")]),
		],
	),
	(
		"UP",
		"Uttar Pradesh",
		"blue",
		[
			("LKO", "Lucknow", [("MLH", "Malihabad"), ("MHG", "Mohanlalganj")]),
			("STP", "Sitapur", [("BSW", "Biswan"), ("MMD", "Mahmudabad")]),
		],
	),
	(
		"BR",
		"Bihar",
		"violet",
		[
			("PAT", "Patna", [("PHL", "Phulwari"), ("DNP", "Danapur")]),
			("GAY", "Gaya", [("BDG", "Bodh Gaya"), ("SHG", "Sherghati")]),
		],
	),
	("KA", "Karnataka", "red", [("MYS", "Mysuru", [("HNS", "Hunsur"), ("NJG", "Nanjangud")])]),
	("TN", "Tamil Nadu", "blue", [("MDU", "Madurai", [("MLR", "Melur"), ("USL", "Usilampatti")])]),
]

DESIGNATIONS = [
	("National director", 1),
	("Head of operations", 1),
	("State program manager", 0),
	("District coordinator", 0),
	("Program manager", 0),
	("Block coordinator", 0),
	("Field volunteer", 0),
]

USERS = [
	("anita", "Anita Rao", "National director", ""),
	("vikram", "Vikram Sethi", "Head of operations", ""),
	("anil", "Anil Sahu", "State program manager", "CG"),
	("rahul", "Rahul Patil", "State program manager", "MH"),
	("kavya", "Kavya Reddy", "State program manager", "KA"),
	("amit", "Amit Mishra", "State program manager", "UP"),
	("sanjay", "Sanjay Bhagat", "District coordinator", "CG-JSP"),
	("ramesh", "Ramesh Minj", "Program manager", "CG-JSP"),
	("neha", "Neha Tirkey", "Block coordinator", "CG-JSP-KNK"),
	("vinod", "Vinod Painkra", "Block coordinator", "CG-JSP-PTH"),
	("kavita", "Kavita Ekka", "Field volunteer", "CG-JSP-BGC"),
	("sushma", "Sushma Lakra", "Field volunteer", "CG-JSP-KNK"),
	("pradeep", "Pradeep Verma", "District coordinator", "CG-RPR"),
	("shalini", "Shalini Dewangan", "Field volunteer", "CG-RPR-ARG"),
	("manish", "Manish Kaushik", "District coordinator", "CG-BSP"),
	("rina", "Rina Patel", "Block coordinator", "CG-BSP-MST"),
	("dilip", "Dilip Sahu", "Field volunteer", "CG-BSP-TKP"),
	("lata", "Lata Kashyap", "District coordinator", "CG-BST"),
	("somaru", "Somaru Baghel", "Block coordinator", "CG-BST-BSN"),
	("jyoti", "Jyoti Netam", "Field volunteer", "CG-BST-JDP"),
	("ajay", "Ajay Singh", "Program manager", "CG-SRG"),
	("sunil", "Sunil Paikra", "Field volunteer", "CG-SRG-MNP"),
	("kamla", "Kamla Kanwar", "Block coordinator", "CG-KRB-KTG"),
	("rupa", "Rupa Tirkey", "Field volunteer", "CG-JSP-KSB"),
	("alok", "Alok Tiwari", "State program manager", "MP"),
	("swati", "Swati Chouhan", "District coordinator", "MP-BPL"),
	("rakesh", "Rakesh Yadav", "Program manager", "MP-IDR"),
	("pinky", "Pinky Malviya", "Block coordinator", "MP-IDR-MHW"),
	("naresh", "Naresh Patel", "Block coordinator", "MP-JBP-SHR"),
	("savitri", "Savitri Dhurve", "Field volunteer", "MP-MDL-BCH"),
	("gopal", "Gopal Kushwaha", "Field volunteer", "MP-GWL-DBR"),
	("preeti", "Preeti Uikey", "Field volunteer", "MP-MDL-NNP"),
	("priya", "Priya Kulkarni", "District coordinator", "MH-PUN"),
	("sneha", "Sneha Joshi", "District coordinator", "MH-NSK"),
	("kiran", "Kiran More", "Program manager", "MH-PUN"),
	("deepak", "Deepak Shinde", "Block coordinator", "MH-NSK-SNR"),
	("sunita", "Sunita Pawar", "Field volunteer", "MH-PUN-HVL"),
	("asha", "Asha Jadhav", "Field volunteer", "MH-NSK-IGP"),
	("arjun", "Arjun Gowda", "District coordinator", "KA-MYS"),
	("farhan", "Farhan Ali", "District coordinator", "UP-LKO"),
	("suresh", "Suresh Yadav", "Block coordinator", "UP-STP-BSW"),
	("manoj", "Manoj Singh", "Field volunteer", "UP-STP-BSW"),
	("imran", "Imran Shaikh", "Field volunteer", "UP-LKO-MLH"),
	("lakshmi", "Lakshmi Iyer", "District coordinator", "TN-MDU"),
	("ravi", "Ravi Kumar", "District coordinator", "BR-PAT"),
	("pooja", "Pooja Sharma", "Block coordinator", "BR-GAY-BDG"),
	("meena", "Meena Devi", "Field volunteer", "BR-GAY-BDG"),
	("rekha", "Rekha Kumari", "Field volunteer", "BR-PAT-PHL"),
	("gita", "Gita Rani", "Field volunteer", "BR-GAY-SHG"),
]
POSTERS = {
	"anita",
	"vikram",
	"anil",
	"rahul",
	"kavya",
	"amit",
	"sanjay",
	"ramesh",
	"pradeep",
	"priya",
	"sneha",
	"arjun",
	"farhan",
	"lakshmi",
	"ravi",
	"alok",
	"swati",
}

TAGS = [
	("Enrolment", "green"),
	("Reporting", "violet"),
	("Training", "blue"),
	("Logistics", "amber"),
	("Urgent", "red"),
	("Field stories", "green"),
	("Budget", "violet"),
]

RESOURCES = [
	(
		"Volunteer onboarding course",
		"Course",
		"https://example.org/courses/onboarding",
		"6 short lessons, about 40 minutes",
		1,
	),
	(
		"How to run your first class",
		"Video",
		"https://example.org/videos/first-class",
		"12 minute walkthrough",
		1,
	),
	(
		"Attendance app guide",
		"Document",
		"https://example.org/docs/attendance-app",
		"PDF, Hindi and English",
		1,
	),
	("Reporting portal", "Link", "https://example.org/portal", "Weekly enrolment reports", 1),
	("Teaching with songs", "Video", "https://example.org/videos/songs", "8 minutes, from the Gaya team", 0),
	(
		"Learner progress card template",
		"Document",
		"https://example.org/docs/progress-card",
		"Printable A4",
		0,
	),
]

THREADS = [
	{
		"title": "Q3 enrolment drive: targets and reporting format",
		"author": "anita",
		"ago": 190,
		"places": ["IN"],
		"designations": ["State program manager", "District coordinator"],
		"policy": "everyone",
		"ack": True,
		"acks": ["kavya", "priya", "farhan", "lakshmi"],
		"seen": ["kavya", "priya", "farhan", "lakshmi", "rahul", "arjun"],
		"tags": ["Enrolment", "Reporting"],
		"reactions": {"👍": ["kavya", "priya", "farhan", "sneha"], "🙏": ["lakshmi"]},
		"body": "<p>Team, the Q3 enrolment drive starts on <strong>1 November</strong>. Each state has a target in the sheet shared last week.</p><p>What I need from every coordinator:</p><ul><li>Weekly enrolment numbers by district, every Monday before 11 AM</li><li>One line on blockers, if any</li><li>Photos from at least two centres</li></ul><p>Please acknowledge so I know this reached you.</p>",
		"replies": [
			(
				"kavya",
				170,
				"<p>Karnataka is on board. Can we report learners enrolled in the pilot centres separately?</p>",
				{},
			),
			(
				"anita",
				160,
				"<p>Yes, add a separate column for pilot centres. Good call.</p>",
				{"👍": ["kavya"]},
			),
			(
				"priya",
				120,
				"<p>Maharashtra will send the first report on Monday. Nashik is still short of two volunteers.</p>",
				{},
			),
			(
				"farhan",
				95,
				"<p>For UP, can the Monday deadline move to 2 PM? Block-level data reaches us late in the morning.</p>",
				{},
			),
			(
				"lakshmi",
				40,
				"<p>Tamil Nadu has translated the reporting format. Sharing it here in case others need a regional version.</p>",
				{},
			),
		],
	},
	{
		"title": "Monsoon schedule change for Pune and Nashik centres",
		"author": "rahul",
		"ago": 300,
		"places": ["MH-PUN", "MH-NSK"],
		"designations": ["District coordinator", "Program manager", "Block coordinator"],
		"policy": "everyone",
		"seen": ["priya", "sneha", "deepak", "kiran"],
		"tags": ["Logistics", "Urgent"],
		"reactions": {"👍": ["deepak", "kiran"]},
		"body": "<p>Because of the heavy rain alerts, evening classes at Pune and Nashik centres move to <strong>4–6 PM</strong> from tomorrow until the end of the month.</p><p>District officers, please inform the centre heads today.</p>",
		"replies": [
			(
				"deepak",
				280,
				"<p>Informed all 14 centres in Nashik. Two centres have no power backup, so 4 PM works better for them anyway.</p>",
				{},
			),
			("sneha", 250, "<p>Pune done. Will share attendance after the first week.</p>", {}),
		],
	},
	{
		"title": "New attendance app rollout: training on 20 October",
		"author": "vikram",
		"ago": 60 * 26,
		"places": ["IN"],
		"designations": ["Block coordinator"],
		"policy": "none",
		"ack": True,
		"acks": ["deepak"],
		"seen": ["deepak", "pooja"],
		"tags": ["Training"],
		"reactions": {"👍": ["deepak", "pooja", "neha"]},
		"body": "<p>We are replacing paper attendance registers with the new attendance app across all districts.</p><ul><li><strong>Training:</strong> 20 October, 11 AM, online</li><li><strong>Who:</strong> every district officer</li><li><strong>Bring:</strong> your login, sent by SMS today</li></ul><p>Replies are off for this announcement. Please send questions to your state lead.</p>",
	},
	{
		"title": "Field visit checklist for Lucknow division",
		"author": "amit",
		"ago": 60 * 5,
		"places": ["UP-LKO", "UP-STP"],
		"policy": "everyone",
		"seen": ["farhan", "suresh", "imran"],
		"tags": ["Reporting"],
		"body": "<p>The ministry team visits Lucknow division next week. Use this checklist for every centre:</p><ul><li>Attendance register up to date</li><li>Learner progress cards filled</li><li>Reading material visible and stocked</li></ul><p>Reply here with anything you need from the state office.</p>",
		"replies": [
			(
				"suresh",
				220,
				"<p>Sitapur centres need 40 more progress cards. Can the state office send them by Thursday?</p>",
				{},
			),
			(
				"farhan",
				200,
				"<p>Suresh, I will pick them up from Lucknow tomorrow and drop them at Sitapur.</p>",
				{},
			),
		],
	},
	{
		"title": "Volunteer kit distribution this Saturday",
		"author": "priya",
		"ago": 60 * 8,
		"places": ["MH-PUN"],
		"policy": "everyone",
		"seen": ["sneha", "deepak", "sunita", "asha", "kiran"],
		"tags": ["Logistics"],
		"reactions": {"🎉": ["sunita", "asha"], "👍": ["deepak"]},
		"body": "<p>Kits (bag, slate, two primers, chalk) are ready at the district offices. Volunteers, please collect yours on <strong>Saturday between 10 AM and 1 PM</strong>.</p>",
		"replies": [
			(
				"deepak",
				420,
				"<p>Nashik office will stay open till 3 PM for volunteers coming from far villages.</p>",
				{},
			),
			("sunita", 380, "<p>Thank you. I will collect for the two volunteers in my village too.</p>", {}),
		],
	},
	{
		"title": "Budget review prep for the ministry meeting",
		"author": "anita",
		"ago": 60 * 30,
		"places": ["IN"],
		"designations": ["National director", "Head of operations"],
		"policy": "everyone",
		"seen": ["vikram"],
		"tags": ["Budget"],
		"body": "<p>Vikram, let's finalise the state-wise spend summary by Wednesday. I will take the outcomes section.</p>",
		"replies": [
			(
				"vikram",
				60 * 29,
				"<p>On it. I will have the draft in the shared folder by Tuesday evening.</p>",
				{},
			)
		],
	},
	{
		"title": "Weekly story share: what worked this week?",
		"author": "ravi",
		"ago": 60 * 4,
		"places": ["BR"],
		"policy": "everyone",
		"seen": ["pooja", "meena", "gita"],
		"tags": ["Field stories"],
		"reactions": {"❤️": ["meena", "gita", "rekha"], "👏": ["pooja"]},
		"body": "<p>Share one thing that worked in your class this week. A small win counts too. Photos welcome.</p>",
		"replies": [
			(
				"meena",
				200,
				"<p>We used songs to teach the alphabet. Even the older women joined in and stayed back after class.</p>",
				{"❤️": ["ravi", "pooja", "gita"], "👏": ["rekha"]},
			),
			(
				"pooja",
				150,
				"<p>Lovely, Meena. Gaya block started evening classes after the harvest and attendance doubled.</p>",
				{},
			),
		],
	},
	{
		"title": "Primer reprint: send your district counts",
		"author": "kavya",
		"ago": 60 * 20,
		"places": ["IN"],
		"designations": ["District coordinator", "Block coordinator"],
		"policy": "posters",
		"seen": ["arjun", "priya", "deepak"],
		"tags": ["Logistics", "Reporting"],
		"body": "<p>The printer can deliver 5,000 primers by the 25th. Coordinators who run a field team, reply with your district counts. Replies are limited to keep the numbers clean.</p>",
		"replies": [
			("priya", 60 * 18, "<p>Pune 900, Nashik 700.</p>", {}),
			("ravi", 60 * 17, "<p>Patna 600, Gaya 850.</p>", {}),
		],
	},
	{
		"title": "Thank you, volunteers: 1 lakh learners reached",
		"author": "anita",
		"ago": 60 * 48,
		"places": ["IN"],
		"designations": ["Field volunteer"],
		"policy": "none",
		"seen": ["meena", "sunita", "rekha", "asha"],
		"tags": ["Field stories"],
		"reactions": {
			"❤️": ["meena", "sunita", "rekha", "asha", "gita", "kavita"],
			"🎉": ["imran", "manoj"],
			"🙏": ["sushma"],
		},
		"body": "<p>This month the program crossed <strong>1,00,000 learners</strong>. That is your work, one class at a time. Thank you.</p>",
	},
	{
		"title": "Jashpur coordinators: monthly review on Friday",
		"author": "anil",
		"ago": 75,
		"places": ["CG-JSP"],
		"designations": ["District coordinator", "Block coordinator", "Program manager"],
		"policy": "everyone",
		"ack": True,
		"acks": ["sanjay"],
		"seen": ["sanjay", "ramesh"],
		"tags": ["Reporting", "Urgent"],
		"reactions": {"👍": ["sanjay", "ramesh"]},
		"body": "<p>Monthly review for Jashpur is on <strong>Friday at 3 PM</strong> at the district office.</p><ul><li>Block coordinators: bring centre-wise attendance for September</li><li>Program manager: status of the Bagicha centre that has no teacher</li></ul><p>Acknowledge so I can book the hall.</p>",
		"replies": [
			(
				"sanjay",
				60,
				"<p>Confirmed. I will join from Kunkuri if the road to Jashpur is still closed.</p>",
				{},
			),
			(
				"neha",
				30,
				"<p>Kunkuri attendance sheet is ready. Two centres are still on paper registers.</p>",
				{"🙏": ["anil"]},
			),
		],
	},
	{
		"title": "Kunkuri centres reopen on Monday",
		"author": "ramesh",
		"ago": 60 * 6,
		"places": ["CG-JSP-KNK"],
		"policy": "everyone",
		"seen": ["sushma"],
		"tags": ["Logistics"],
		"reactions": {"🎉": ["sushma", "neha", "kavita"]},
		"body": "<p>Repairs after the flood are done. All Kunkuri centres reopen on <strong>Monday</strong>. Volunteers, please tell your learners.</p>",
		"replies": [
			("sushma", 60 * 5, "<p>I will tell the women in my village today. Many were asking.</p>", {})
		],
	},
]


def email(uid: str) -> str:
	return f"{uid}@crecheconnect.local"


def ago(minutes: int):
	return add_to_date(now_datetime(), minutes=-minutes)


def insert(doc: dict):
	return frappe.get_doc(doc).insert(ignore_permissions=True, ignore_if_duplicate=True)


def make_demo():
	# Frappe keeps a given owner and creation only during a patch.
	frappe.flags.in_patch = True
	make_places()
	for seniority, (name, national) in enumerate(DESIGNATIONS):
		if not frappe.db.exists("CrecheConnect Designation", name):
			insert(
				{
					"doctype": "CrecheConnect Designation",
					"designation_name": name,
					"seniority": seniority,
					"is_national": national,
				}
			)
	make_users()
	for name, color in TAGS:
		if not frappe.db.exists("CrecheConnect Tag", name):
			insert({"doctype": "CrecheConnect Tag", "tag_name": name, "color": color})
	if not frappe.db.count("CrecheConnect Resource"):
		for title, kind, url, description, pinned in RESOURCES:
			insert(
				{
					"doctype": "CrecheConnect Resource",
					"title": title,
					"kind": kind,
					"url": url,
					"description": description,
					"pinned": pinned,
				}
			)
	if not frappe.db.count("CrecheConnect Thread"):
		for t in THREADS:
			make_thread(t)
	frappe.flags.in_patch = False
	frappe.db.commit()


def make_places():
	if frappe.db.exists("CrecheConnect Place", "IN"):
		return
	insert(
		{
			"doctype": "CrecheConnect Place",
			"place_name": "All India",
			"kind": "Country",
			"code": "IN",
			"color": "violet",
		}
	)
	for code, name, color, districts in GEO:
		insert(
			{
				"doctype": "CrecheConnect Place",
				"place_name": name,
				"kind": "State",
				"code": code,
				"parent_place": "IN",
				"color": color,
			}
		)
		for dcode, dname, blocks in districts:
			district = insert(
				{
					"doctype": "CrecheConnect Place",
					"place_name": dname,
					"kind": "District",
					"code": dcode,
					"parent_place": code,
					"color": color,
				}
			)
			for bcode, bname in blocks:
				insert(
					{
						"doctype": "CrecheConnect Place",
						"place_name": bname,
						"kind": "Block",
						"code": bcode,
						"parent_place": district.name,
						"color": color,
					}
				)


def make_users():
	for uid, full_name, designation, place in USERS:
		user = email(uid)
		if not frappe.db.exists("User", user):
			first, _sep, last = full_name.partition(" ")
			doc = frappe.get_doc(
				{
					"doctype": "User",
					"email": user,
					"first_name": first,
					"last_name": last,
					"user_type": "System User" if uid == "anita" else "Website User",
					"send_welcome_email": 0,
					"new_password": PASSWORD,
				}
			)
			doc.flags.no_welcome_mail = True
			doc.insert(ignore_permissions=True)
			if uid == "anita":
				doc.add_roles("CrecheConnect Admin")
		if not frappe.db.exists("CrecheConnect Member", user):
			insert(
				{
					"doctype": "CrecheConnect Member",
					"user": user,
					"designation": designation,
					"place": place or None,
					"can_post": uid in POSTERS,
				}
			)


def react(doctype: str, name, reactions: dict, at):
	for emoji, uids in reactions.items():
		for uid in uids:
			insert(
				{
					"doctype": "CrecheConnect Reaction",
					"reference_doctype": doctype,
					"reference_name": name,
					"emoji": emoji,
					"user": email(uid),
					"owner": email(uid),
					"creation": at,
				}
			)


def make_thread(t: dict):
	created = ago(t["ago"])
	thread = insert(
		{
			"doctype": "CrecheConnect Thread",
			"title": t["title"],
			"content": t["body"],
			"owner": email(t["author"]),
			"creation": created,
			"last_activity": created,
			"places": [{"place": p} for p in t["places"]],
			"designations": [{"designation": d} for d in t.get("designations", [])],
			"tags": [{"tag": tag} for tag in t["tags"]],
			"reply_policy": t["policy"],
			"ack_required": int(t.get("ack", False)),
		}
	)
	last = created
	for uid, minutes, body, reactions in t.get("replies", []):
		last = ago(minutes)
		reply = insert(
			{
				"doctype": "CrecheConnect Reply",
				"thread": thread.name,
				"content": body,
				"owner": email(uid),
				"creation": last,
			}
		)
		react("CrecheConnect Reply", reply.name, reactions, last)
	react("CrecheConnect Thread", thread.name, t.get("reactions", {}), created)
	for uid in t.get("acks", []):
		insert(
			{
				"doctype": "CrecheConnect Acknowledgement",
				"thread": thread.name,
				"user": email(uid),
				"owner": email(uid),
			}
		)
	for uid in {t["author"], *t["seen"]}:
		insert(
			{
				"doctype": "CrecheConnect Thread Visit",
				"thread": thread.name,
				"user": email(uid),
				"last_visit": last,
				"owner": email(uid),
				"creation": last,
			}
		)
