import frappe
from frappe.utils import get_system_timezone

no_cache = 1


def get_context(context):
	if frappe.session.user == "Guest":
		frappe.local.flags.redirect_location = "/login?redirect-to=" + frappe.local.request.path
		raise frappe.Redirect
	context.boot = frappe._dict(
		csrf_token=frappe.sessions.get_csrf_token(),
		site_name=frappe.local.site,
		system_timezone=get_system_timezone(),
	)
	return context
