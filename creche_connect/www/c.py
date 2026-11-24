import frappe
from frappe.core.api.file import get_max_file_size
from frappe.translate import get_translations_from_apps, get_user_translations
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
		max_file_size=get_max_file_size(),
		lang=frappe.local.lang,
		translations=get_translations_from_apps(frappe.local.lang, ["creche_connect"])
		| get_user_translations(frappe.local.lang),
		socketio_port=frappe.conf.socketio_port if frappe._dev_server else None,
	)
	return context
