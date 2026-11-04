from typing import ClassVar, Literal

import frappe
from frappe.search.sqlite_search import SQLiteSearch
from frappe.utils import escape_html

from creche_connect.api import Thread, ThreadTag, feed_query, get_me, thread_ids


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

	def __init__(self, tags: list | None = None):
		super().__init__()
		self.tags = tags

	def get_search_filters(self):
		query = feed_query(get_me())
		if self.tags:
			query = query.where(Thread.name.isin(thread_ids(ThreadTag).where(ThreadTag.tag.isin(self.tags))))
		visible = query.select(Thread.name).run(pluck=True)
		return {"thread": [str(name) for name in visible]}

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
	types: list[Literal["CrecheConnect Thread", "CrecheConnect Reply"]] | None = None,
) -> dict:
	filters = {field: values for field, values in (("owner", authors), ("doctype", types)) if values}
	found = CrecheConnectSearch(tags).search(query.strip(), filters=filters)
	hits = found["results"]
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
