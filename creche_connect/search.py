from typing import ClassVar

import frappe
from frappe.search.sqlite_search import SQLiteSearch
from frappe.query_builder import Criterion
from frappe.utils import add_days, escape_html, now_datetime

from creche_connect.api import Thread, ThreadPlace, ThreadTag, feed_query, get_me, thread_ids


class CrecheConnectSearch(SQLiteSearch):
	INDEX_NAME = "crecheconnect_search.db"
	BUILD_VOCABULARY = False

	INDEX_SCHEMA: ClassVar[dict] = {
		"text_fields": ["title", "content"],
		"metadata_fields": ["doctype", "name", "thread", "owner", "modified"],
	}

	INDEXABLE_DOCTYPES: ClassVar[dict] = {
		"CrecheConnect Thread": {"fields": ["name", "title", "content", "owner", "modified"]},
		"CrecheConnect Reply": {"fields": ["name", "content", "owner", "modified", "thread"]},
	}

	def __init__(self, tags: list | None = None, places: list | None = None, since=None):
		super().__init__()
		self.tags = tags
		self.places = places
		self.since = since

	def get_search_filters(self):
		query = feed_query(get_me())
		if self.tags:
			query = query.where(Thread.name.isin(thread_ids(ThreadTag).where(ThreadTag.tag.isin(self.tags))))
		if self.places:
			inside = [(ThreadPlace.place == p) | ThreadPlace.place.like(f"{p}-%") for p in self.places]
			query = query.where(Thread.name.isin(thread_ids(ThreadPlace).where(Criterion.any(inside))))
		if self.since:
			query = query.where(Thread.last_activity >= self.since)
		visible = query.select(Thread.name).run(pluck=True)
		return {"thread": [str(name) for name in visible]}

	def _prepare_fts_query(self, query):
		return " ".join('"{}"*'.format(term.replace('"', '""')) for term in query.split())

	def prepare_document(self, doc):
		document = super().prepare_document(doc)
		if document:
			document["thread"] = str(doc.get("thread") or doc.name)
		return document


def marked(text: str) -> str:
	return escape_html(text).replace("&lt;mark&gt;", "<mark>").replace("&lt;/mark&gt;", "</mark>")


@frappe.whitelist(methods=["POST"])
def search(
	query: str,
	tags: list[str] | None = None,
	authors: list[str] | None = None,
	places: list[str] | None = None,
	days: int | None = None,
) -> dict:
	since = add_days(now_datetime(), -days) if days else None
	found = CrecheConnectSearch(tags, places, since).search(query.strip(), filters={"owner": authors} if authors else None)
	hits = [h for h in found["results"] if not since or h["modified"] >= since.timestamp()]
	titles = {
		str(name): title
		for name, title in frappe.get_all(
			"CrecheConnect Thread",
			filters={"name": ["in", list({h["thread"] for h in hits})]},
			fields=["name", "title"],
			as_list=True,
		)
	}
	return {
		"results": [
			{
				"id": hit["id"],
				"thread": hit["thread"],
				"reply": str(hit["name"]) if hit["doctype"] == "CrecheConnect Reply" else None,
				"title": marked(hit["title"]) if hit["doctype"] == "CrecheConnect Thread" else escape_html(titles[hit["thread"]]),
				"snippet": marked(hit["content"]),
				"authorId": hit["author"],
				"at": hit["modified"],
			}
			for hit in hits
			if hit["thread"] in titles
		],
		"duration": found["summary"]["duration"],
	}
