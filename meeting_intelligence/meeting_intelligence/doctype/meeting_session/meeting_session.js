// Copyright (c) 2026, Dhanaa Lakshmi and contributors
// For license information, please see license.txt

frappe.ui.form.on("Meeting Session", {
    refresh(frm) {
    frm.trigger("render_meeting_snapshot");

        if (!frm.is_new()) {
            frm.add_custom_button("Meeting Snapshot", () => {
                frm.trigger("show_meeting_snapshot");
            });
        }
    },

    duration_minutes(frm) {
        frm.trigger("render_meeting_snapshot");
    },

    agenda_followed(frm) {
        frm.trigger("render_meeting_snapshot");
    },

    attendees_add(frm) {
        frm.trigger("render_meeting_snapshot");
    },

    attendees_remove(frm) {
        frm.trigger("render_meeting_snapshot");
    },

    render_meeting_snapshot(frm) {
        if (frm.is_new()) return;

        const score = frm.doc.health_score || 0;
        const label = frm.doc.health_label || "Not calculated";
        const cost = frm.doc.meeting_cost || 0;
        const decisions = frm.doc.decisions_count || 0;
        const actions = frm.doc.open_actions_count || 0;

        frm.dashboard.set_headline(
            `Health: ${label} · Score: ${score}/100 · Cost: ${cost.toFixed(2)}`
        );

        frm.dashboard.add_indicator(
            `Decisions: ${decisions}`,
            decisions ? "green" : "orange"
        );

        frm.dashboard.add_indicator(
            `Open Actions: ${actions}`,
            actions ? "orange" : "green"
        );

        if (frm.doc.has_monologue) {
            frm.dashboard.add_indicator("Monologue Detected", "red");
        }
    },

    show_meeting_snapshot(frm) {
        const score = frm.doc.health_score || 0;
        const label = frm.doc.health_label || "Not calculated";
        const cost = frm.doc.meeting_cost || 0;

        const dialog = new frappe.ui.Dialog({
            title: "Meeting Intelligence Snapshot",
            fields: [
                {
                    fieldtype: "HTML",
                    fieldname: "snapshot"
                }
            ]
        });

        dialog.fields_dict.snapshot.$wrapper.html(`
            <div style="padding: 10px 0;">
                <h3>${label}</h3>
                <p><strong>Health Score:</strong> ${score}/100</p>
                <p><strong>Meeting Cost:</strong> ${cost.toFixed(2)}</p>
                <p><strong>Decisions:</strong> ${frm.doc.decisions_count || 0}</p>
                <p><strong>Open Actions:</strong> ${frm.doc.open_actions_count || 0}</p>
                <p><strong>Monologue:</strong> ${
                    frm.doc.has_monologue ? "Detected" : "Not detected"
                }</p>
            </div>
        `);

        dialog.show();
    }

});
