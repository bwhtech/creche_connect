import frappe
from frappe.website.page_renderers.base_renderer import BaseRenderer
from werkzeug.wrappers import Response


class ServiceWorker(BaseRenderer):
	def can_render(self):
		return self.path == "crecheconnect-sw.js"

	def render(self):
		with open(frappe.get_app_path("creche_connect", "sw.js")) as f:
			return Response(f.read(), content_type="text/javascript", headers={"Cache-Control": "no-cache"})
