app_name = "meeting_intelligence"
app_title = "Meeting Intelligence"
app_publisher = "Dhanaa Lakshmi"
app_description = "Frappe application that transforms raw meeting data into measurable business intelligence"
app_email = "dhanaalakshminarayanan@gmail.com"
app_license = "mit"

doc_events = {
	"Meeting Session": {
		"on_update": "meeting_intelligence.meeting_intelligence.doctype.meeting_participant.meeting_participant.update_metrics_on_session_change",
		"on_trash": "meeting_intelligence.meeting_intelligence.doctype.meeting_participant.meeting_participant.update_metrics_on_session_change",
	},
	"Decision Log": {
		"on_update": "meeting_intelligence.meeting_intelligence.doctype.decision_log.decision_log.update_session_decision_count",
		"on_trash": "meeting_intelligence.meeting_intelligence.doctype.decision_log.decision_log.update_session_decision_count_on_trash",
	},
	"Action Item": {
		"on_update": "meeting_intelligence.meeting_intelligence.doctype.action_item.action_item.update_session_action_count",
		"on_trash": "meeting_intelligence.meeting_intelligence.doctype.action_item.action_item.update_session_action_count_on_trash",
	},
}

scheduler_events = {
	"daily": [
		"meeting_intelligence.tasks.mark_overdue_action_items",
		"meeting_intelligence.tasks.update_ghost_scores",
		"meeting_intelligence.tasks.send_overdue_reminders",
	],
	"weekly": [
		"meeting_intelligence.tasks.zombie_decision_scan",
		"meeting_intelligence.tasks.send_manager_digest",
	],
}
