app_name = "crecheconnect"
app_title = "CrecheConnect"
app_publisher = "BWH"
app_description = "Audience-targeted threads for field programmes"
app_email = "vishwajeet@bwh.tech"
app_license = "mit"

use_json_request_body = True
export_python_type_annotations = True
require_type_annotated_api_methods = True

add_to_apps_screen = [
	{"name": "crecheconnect", "logo": "/assets/crecheconnect/logo.svg", "title": "CrecheConnect", "route": "/c"}
]

website_route_rules = [{"from_route": "/c/<path:app_path>", "to_route": "c"}]
website_redirects = [{"source": "/", "target": "/c"}]

sqlite_search = ["crecheconnect.search.CrecheConnectSearch"]
