"""Application entry point for the Study Management System."""
import os
import secrets

from flask import Flask, abort, flash, jsonify, redirect, render_template, request, session, url_for

from Data_Access.database import init_db
from Domain_Rules import TASK_STATUSES, DomainRuleError
from Priority import prioritize_tasks
import Events
from Reminder import (
    create_reminder, get_preferences, update_preferences, list_reminders,
    list_reminder_presets, register_event_handlers, claim_due_reminders,
    complete_delivery, list_notices, dismiss_notice, POLL_INTERVAL_SECONDS,
)
from Schedule import (
    generate_study_schedule, list_availability, list_study_sessions,
    set_availability, update_availability,
)
from Task_Management import (
    create_task,
    get_task,
    get_completion_summary,
    list_tasks,
    transition_task_status,
    update_study_duration,
)

from Authentication import (
    authenticate_user,
    current_user,
    init_auth,
    login_required,
    new_csrf_token,
    register_user,
    validate_csrf_token,
)


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.update(
        SECRET_KEY=os.environ.get("STUDY_MANAGEMENT_SECRET_KEY") or secrets.token_hex(32),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=os.environ.get("SESSION_COOKIE_SECURE", "0") == "1",
        # OPEN DECISION (plan OI-01 / G-14, AGENTS.md): manual task creation is NOT an
        # approved requirement. Off by default; set
        # STUDY_MANAGEMENT_ALLOW_MANUAL_TASK_ENTRY=1 only for local development/demo.
        ALLOW_MANUAL_TASK_ENTRY=os.environ.get(
            "STUDY_MANAGEMENT_ALLOW_MANUAL_TASK_ENTRY", "0") == "1",
    )
    if test_config:
        app.config.update(test_config)

    init_db()
    init_auth()
    register_event_handlers()

    @app.context_processor
    def inject_csrf_token():
        return {"csrf_token": new_csrf_token}

    @app.get("/")
    def home():
        return redirect(url_for("dashboard") if current_user() else url_for("login"))

    @app.route("/register", methods=["GET", "POST"])
    def register():
        if current_user():
            return redirect(url_for("dashboard"))
        if request.method == "POST":
            if not validate_csrf_token(request.form.get("csrf_token")):
                flash("Your form session expired. Please try again.", "error")
                return render_template("register.html"), 400
            try:
                user_id = register_user(
                    request.form.get("email", ""),
                    request.form.get("password", ""),
                )
                session.clear()
                session["user_id"] = user_id
                flash("Account created successfully.", "success")
                return redirect(url_for("dashboard"))
            except ValueError as exc:
                flash(str(exc), "error")
        return render_template("register.html")

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if current_user():
            return redirect(url_for("dashboard"))
        if request.method == "POST":
            if not validate_csrf_token(request.form.get("csrf_token")):
                flash("Your form session expired. Please try again.", "error")
                return render_template("login.html"), 400
            user = authenticate_user(
                request.form.get("email", ""),
                request.form.get("password", ""),
            )
            if user is None:
                flash("Email or password is incorrect.", "error")
            else:
                session.clear()
                session["user_id"] = user["id"]
                flash("You are now logged in.", "success")
                return redirect(url_for("dashboard"))
        return render_template("login.html")

    @app.post("/logout")
    @login_required
    def logout():
        if not validate_csrf_token(request.form.get("csrf_token")):
            flash("Your form session expired. Please try again.", "error")
            return redirect(url_for("dashboard"))
        session.clear()
        flash("You have been logged out.", "success")
        return redirect(url_for("login"))

    @app.get("/dashboard")
    @login_required
    def dashboard():
        user = current_user()
        user_id = session["user_id"]
        # PROVISIONAL pending G-08: the default task-list view is undecided; "all" is used.
        requested = request.args.get("status", "all")
        status_filter = requested if requested in TASK_STATUSES else "all"
        all_tasks = prioritize_tasks(user_id, tasks=list_tasks(user_id))
        tasks = all_tasks if status_filter == "all" else [
            task for task in all_tasks if task["status"] == status_filter
        ]
        summary = get_completion_summary(user_id)
        preferences = get_preferences(user_id)
        reminders = list_reminders(user_id)
        notices = list_notices(user_id)
        sessions = list_study_sessions(user_id)
        deadline_presets = list_reminder_presets(user_id, "deadline")
        session_presets = list_reminder_presets(user_id, "session")
        return render_template(
            "dashboard.html", user=user, tasks=tasks, summary=summary,
            status_filter=status_filter, reminder_tasks=all_tasks, preferences=preferences, reminders=reminders,
            notices=notices, sessions=sessions, deadline_presets=deadline_presets,
            session_presets=session_presets, poll_interval=POLL_INTERVAL_SECONDS,
            manual_entry_enabled=app.config["ALLOW_MANUAL_TASK_ENTRY"],
        )

    @app.get("/schedule")
    @login_required
    def schedule_page():
        user_id = session["user_id"]
        availability = list_availability(user_id)
        sessions = list_study_sessions(user_id)
        for study_session in sessions:
            task_id = study_session.get("task_id")
            task = get_task(user_id, task_id) if task_id is not None else None
            study_session["task_title"] = task["title"] if task else None
        return render_template(
            "schedule.html",
            user=current_user(),
            availability=availability,
            sessions=sessions,
            weekdays=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
        )

    @app.post("/schedule/generate")
    @login_required
    def create_study_schedule():
        if not validate_csrf_token(request.form.get("csrf_token")):
            abort(400)
        try:
            result = generate_study_schedule(session["user_id"])
        except DomainRuleError as exc:
            flash(str(exc), "error")
            return redirect(url_for("schedule_page"))
        if result["session_ids"]:
            flash(
                f"Schedule created with {len(result['session_ids'])} study session(s). "
                f"{len(result['unscheduled_task_ids'])} task(s) remain unscheduled.",
                "success",
            )
        elif result["unscheduled_task_ids"]:
            flash(
                f"No new sessions were created. {len(result['unscheduled_task_ids'])} task(s) "
                "remain unscheduled; check their estimates, priorities, deadlines, and availability.",
                "error",
            )
        else:
            flash("No new sessions were needed; existing sessions were preserved.", "success")
        return redirect(url_for("schedule_page"))

    @app.post("/availability")
    @login_required
    def add_availability():
        if not validate_csrf_token(request.form.get("csrf_token")):
            abort(400)
        try:
            set_availability(
                session["user_id"],
                request.form.get("day_of_week", type=int),
                request.form.get("start_time", ""),
                request.form.get("end_time", ""),
            )
            flash("Availability saved.", "success")
        except DomainRuleError as exc:
            flash(str(exc), "error")
        return redirect(url_for("schedule_page"))

    @app.post("/availability/<int:availability_id>")
    @login_required
    def edit_availability(availability_id):
        if not validate_csrf_token(request.form.get("csrf_token")):
            abort(400)
        try:
            updated_id = update_availability(
                session["user_id"], availability_id,
                request.form.get("day_of_week", type=int),
                request.form.get("start_time", ""),
                request.form.get("end_time", ""),
            )
        except DomainRuleError as exc:
            flash(str(exc), "error")
            return redirect(url_for("schedule_page"))
        if updated_id is None:
            abort(404)
        flash("Availability updated.", "success")
        return redirect(url_for("schedule_page"))

    @app.post("/tasks")
    @login_required
    def add_task():
        if not app.config["ALLOW_MANUAL_TASK_ENTRY"]:
            abort(404)  # manual task entry is not an approved requirement (OI-01)
        if not validate_csrf_token(request.form.get("csrf_token")):
            abort(400)
        try:
            create_task(
                session["user_id"],
                request.form.get("title", ""),
                request.form.get("deadline", ""),
                request.form.get("course", "").strip() or None,
            )
            flash("Task added successfully.", "success")
        except DomainRuleError as exc:
            flash(str(exc), "error")
        return redirect(url_for("dashboard"))

    @app.post("/tasks/<int:task_id>/incomplete")
    @login_required
    def incomplete_task(task_id):
        if not validate_csrf_token(request.form.get("csrf_token")):
            abort(400)
        user_id = session["user_id"]
        try:
            updated_task = transition_task_status(user_id, task_id, "incomplete")
        except DomainRuleError as exc:
            flash(str(exc), "error")
            return redirect(url_for("dashboard"))
        if updated_task is None:
            abort(404)
        flash("Task marked as incomplete.", "success")
        return redirect(url_for("dashboard"))

    @app.post("/tasks/<int:task_id>/complete")
    @login_required
    def complete_task(task_id):
        if not validate_csrf_token(request.form.get("csrf_token")):
            abort(400)
        user_id = session["user_id"]
        try:
            updated_task = transition_task_status(user_id, task_id, "completed")
        except DomainRuleError as exc:
            flash(str(exc), "error")
            return redirect(url_for("dashboard"))
        if updated_task is None:
            # The service scopes the lookup/update by user_id; foreign tasks are indistinguishable.
            abort(404)
        flash("Task marked as completed.", "success")
        return redirect(url_for("dashboard"))

    @app.post("/tasks/<int:task_id>/study-duration")
    @login_required
    def save_study_duration(task_id):
        if not validate_csrf_token(request.form.get("csrf_token")):
            abort(400)
        try:
            task = update_study_duration(
                session["user_id"], task_id,
                request.form.get("study_duration_minutes", type=int),
            )
        except DomainRuleError as exc:
            flash(str(exc), "error")
            return redirect(url_for("dashboard"))
        if task is None:
            abort(404)
        flash("Study-duration estimate saved.", "success")
        return redirect(url_for("dashboard"))


    @app.post("/reminder-preferences")
    @login_required
    def save_reminder_preferences():
        if not validate_csrf_token(request.form.get("csrf_token")):
            abort(400)
        update_preferences(
            session["user_id"],
            enabled=request.form.get("enabled") == "on",
            deadline_enabled=request.form.get("deadline_enabled") == "on",
            session_enabled=request.form.get("session_enabled") == "on",
        )
        flash("Reminder preferences updated.", "success")
        return redirect(url_for("dashboard"))

    @app.post("/reminders")
    @login_required
    def add_reminder():
        if not validate_csrf_token(request.form.get("csrf_token")):
            abort(400)
        user_id = session["user_id"]
        target_type = request.form.get("target_type")
        if target_type not in {"deadline", "session"}:
            abort(400)
        task_id = request.form.get("task_id", type=int) if target_type == "deadline" else None
        session_id = request.form.get("session_id", type=int) if target_type == "session" else None
        event_at = request.form.get("event_at") or None
        remind_at = request.form.get("remind_at") or None
        preset_offset = request.form.get("preset_offset_seconds", type=int)
        if preset_offset is not None:
            if task_id is not None:
                task = get_task(user_id, task_id)
                event_at = task.get("deadline_at") if task else None
            if not event_at:
                flash("The event time is unavailable; a reminder cannot be created.", "error")
                return redirect(url_for("dashboard"))
            from datetime import datetime, timedelta, timezone
            event_time = datetime.fromisoformat(event_at.replace("Z", "+00:00"))
            remind_at = (event_time - timedelta(seconds=preset_offset)).astimezone(timezone.utc).isoformat()
        if not remind_at:
            flash("Choose a custom reminder time or a saved preset.", "error")
            return redirect(url_for("dashboard"))
        try:
            create_reminder(
                user_id, remind_at, task_id=task_id, session_id=session_id,
                event_at=event_at, message=request.form.get("message", "").strip() or None,
            )
            flash("Reminder saved.", "success")
        except DomainRuleError as exc:
            flash(str(exc), "error")
        return redirect(url_for("dashboard"))

    @app.get("/api/reminders/poll")
    @login_required
    def poll_reminders():
        # Consume only events already published by their owning modules.
        user_id = session["user_id"]
        Events.process_pending_events(user_id=user_id)
        return jsonify({
            "reminders": claim_due_reminders(user_id),
            "notices": list_notices(user_id),
        })

    @app.post("/api/reminders/<int:reminder_id>/delivery")
    @login_required
    def acknowledge_reminder_delivery(reminder_id):
        if not validate_csrf_token(request.headers.get("X-CSRF-Token")):
            abort(400)
        payload = request.get_json(silent=True) or {}
        updated = complete_delivery(
            session["user_id"], reminder_id, payload.get("claim_token", ""),
            success=bool(payload.get("success")), error=payload.get("error"),
        )
        return jsonify({"updated": updated}), (200 if updated else 409)

    @app.post("/api/reminder-notices/<int:notice_id>/dismiss")
    @login_required
    def dismiss_reminder_notice(notice_id):
        if not validate_csrf_token(request.headers.get("X-CSRF-Token")):
            abort(400)
        return jsonify({"dismissed": dismiss_notice(session["user_id"], notice_id)})

    @app.get("/health")
    def health_check():
        return {"status": "running"}, 200

    return app


if __name__ == "__main__":
    application = create_app()
    # Debug mode is disabled by default; enable only in local development.
    application.run(debug=os.environ.get("FLASK_DEBUG", "0") == "1")
