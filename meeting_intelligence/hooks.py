app_name = "meeting_intelligence"
app_title = "Meeting Intelligence"
app_publisher = "Dhanaa Lakshmi"
app_description = "Frappe application that transforms raw meeting data into measurable business intelligence"
app_email = "dhanaalakshminarayanan@gmail.com"
app_license = "mit"

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "meeting_intelligence",
# 		"logo": "/assets/meeting_intelligence/logo.png",
# 		"title": "Meeting Intelligence",
# 		"route": "/meeting_intelligence",
# 		"has_permission": "meeting_intelligence.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/meeting_intelligence/css/meeting_intelligence.css"
# app_include_js = "/assets/meeting_intelligence/js/meeting_intelligence.js"

# include js, css files in header of web template
# web_include_css = "/assets/meeting_intelligence/css/meeting_intelligence.css"
# web_include_js = "/assets/meeting_intelligence/js/meeting_intelligence.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "meeting_intelligence/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "meeting_intelligence/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# automatically load and sync documents of this doctype from downstream apps
# importable_doctypes = [doctype_1]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "meeting_intelligence.utils.jinja_methods",
# 	"filters": "meeting_intelligence.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "meeting_intelligence.install.before_install"
# after_install = "meeting_intelligence.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "meeting_intelligence.uninstall.before_uninstall"
# after_uninstall = "meeting_intelligence.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "meeting_intelligence.utils.before_app_install"
# after_app_install = "meeting_intelligence.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "meeting_intelligence.utils.before_app_uninstall"
# after_app_uninstall = "meeting_intelligence.utils.after_app_uninstall"

# Build
# ------------------
# To hook into the build process

# after_build = "meeting_intelligence.build.after_build"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "meeting_intelligence.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
# 	}
# }

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"meeting_intelligence.tasks.all"
# 	],
# 	"daily": [
# 		"meeting_intelligence.tasks.daily"
# 	],
# 	"hourly": [
# 		"meeting_intelligence.tasks.hourly"
# 	],
# 	"weekly": [
# 		"meeting_intelligence.tasks.weekly"
# 	],
# 	"monthly": [
# 		"meeting_intelligence.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "meeting_intelligence.install.before_tests"

# Extend DocType Class
# ------------------------------
#
# Specify custom mixins to extend the standard doctype controller.
# extend_doctype_class = {
# 	"Task": "meeting_intelligence.custom.task.CustomTaskMixin"
# }

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "meeting_intelligence.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "meeting_intelligence.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["meeting_intelligence.utils.before_request"]
# after_request = ["meeting_intelligence.utils.after_request"]

# Job Events
# ----------
# before_job = ["meeting_intelligence.utils.before_job"]
# after_job = ["meeting_intelligence.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"meeting_intelligence.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

# Translation
# ------------
# List of apps whose translatable strings should be excluded from this app's translations.
# ignore_translatable_strings_from = []

