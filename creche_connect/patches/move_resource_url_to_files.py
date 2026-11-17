import frappe


def execute():
	if not frappe.db.has_column("CrecheConnect Resource", "url"):
		return
	resource = frappe.qb.DocType("CrecheConnect Resource")
	for r in (
		frappe.qb.from_(resource)
		.select(resource.name, resource.url)
		.where(resource.url.isnotnull())
		.run(as_dict=True)
	):
		frappe.get_doc(
			{
				"doctype": "CrecheConnect Resource File",
				"parenttype": "CrecheConnect Resource",
				"parentfield": "files",
				"parent": r.name,
				"idx": 1,
				"url": r.url,
			}
		).db_insert()
