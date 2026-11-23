app_name = "creche_connect"
app_title = "CrecheConnect"
app_publisher = "BWH"
app_description = "Audience-targeted threads for field programmes"
app_email = "vishwajeet@bwh.tech"
app_license = "mit"

use_json_request_body = True
export_python_type_annotations = True
require_type_annotated_api_methods = True

add_to_apps_screen = [
	{"name": "creche_connect", "logo": "/assets/creche_connect/logo.svg", "title": "CrecheConnect", "route": "/c"}
]

website_route_rules = [{"from_route": "/c/<path:app_path>", "to_route": "c"}]
page_renderer = ["creche_connect.service_worker.ServiceWorker"]
has_permission = {
	"CrecheConnect Resource": "creche_connect.crecheconnect.doctype.crecheconnect_resource.crecheconnect_resource.has_permission"
}
permission_query_conditions = {
	"CrecheConnect Resource": "creche_connect.crecheconnect.doctype.crecheconnect_resource.crecheconnect_resource.permission_query_conditions"
}
website_redirects = [{"source": "/", "target": "/c"}]

sqlite_search = ["creche_connect.search.CrecheConnectSearch"]

doc_events = {"File": {"before_insert": "creche_connect.files.check_audio_size"}}
