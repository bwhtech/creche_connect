app_name = "samvaad"
app_title = "Samvaad"
app_publisher = "BWH"
app_description = "Audience-targeted threads for field programmes"
app_email = "vishwajeet@bwh.tech"
app_license = "mit"

use_json_request_body = True
export_python_type_annotations = True
require_type_annotated_api_methods = True

add_to_apps_screen = [
	{"name": "samvaad", "logo": "/assets/samvaad/logo.svg", "title": "Samvaad", "route": "/samvaad"}
]

website_route_rules = [{"from_route": "/samvaad/<path:app_path>", "to_route": "samvaad"}]
