# Study Management System — S01–S04

## Technology and setup
- Python, Flask, SQLite (`sqlite3`), and pytest for tests.
- No ORM or additional runtime libraries are used.

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python app.py
```
Open `http://127.0.0.1:5000/`. Set `STUDY_MANAGEMENT_SECRET_KEY` to a long random secret for a persistent deployment. Set `SESSION_COOKIE_SECURE=1` behind HTTPS. Do not use Flask's development server in production.

Run tests from the project root with `pytest -q`.

## Persistence
`Data_Access.database.init_db()` creates the complete schema idempotently:
- `users` — account records (Authentication).
- `tasks` — task records and completion state.
- `study_sessions` — scheduled study sessions, optionally linked to an owned task.
- `reminders` — user-owned deadline, Scheduled Study Session, and legacy reminders with delivery state.
- `reminder_preferences` — user-level enable/disable preferences for deadline and session reminders.
- `reminder_notices` — dismissible user-specific notices for skipped reminders.
- `availability` — weekly user availability (Monday=0 through Sunday=6).
- `staged_imports` and `sync_logs` — externally imported data remains staged until accepted.
- `events` and `processed_events` — in-application event records and duplicate-prevention records (PROVISIONAL pending G-01/G-12; see *Event foundation*).

Every user-owned table has a `user_id` foreign key to `users`. Connections enable `PRAGMA foreign_keys=ON`. The task/session/reminder/import relationships use composite foreign keys where applicable to prevent cross-user task references. The default database file is `instance/study_management.db`. `tasks.deadline` remains the date-compatible field; `tasks.deadline_at` stores an optional timezone-aware deadline timestamp normalized to UTC. Existing date-only values are preserved with `deadline_at = NULL` (no time is invented). Task status is `incomplete` or `completed`. `staged_imports.deadline_at` preserves timestamp values while imported data is staged. Databases created by earlier code are migrated automatically by `init_db()` (old task statuses are normalized; legacy reminder rows are preserved while the reminder delivery schema is extended).

## Domain Rules
`Domain_Rules` is the shared validation boundary and raises `DomainRuleError` for: missing/overlong task titles, invalid non-empty ISO deadlines (an empty deadline is allowed through `validate_optional_deadline`), unknown statuses, disallowed status transitions, invalid email/password at registration, the time/day/reminder/course validators, and timezone-aware deadline timestamps. It normalizes deadline instants to UTC and identifies conflicts when two or more tasks for the same user share the exact instant. Task statuses are `incomplete` and `completed`: a task can be marked completed and reverted to incomplete; completing a completed task (or marking an incomplete task incomplete) is rejected. Maximum title length is 200 characters.

## Public module interfaces and communication
Modules expose service functions from their package `__init__.py`; callers must use these functions rather than importing another module's private helpers or querying its tables.

```text
UI / app.py
  ├── Authentication ──> Domain_Rules (email/password validation)
  │                 └──> Data_Access
  └── Task_Management ──> Domain_Rules
                     ├──> Events (publish task.completion_changed and task.deadline_changed in the same transaction)
                     └──> Data_Access

Events ────────────────> Data_Access (event_store; all event SQL lives there)

Priority ──────────────> Task_Management public API
Schedule ──────────────> Task_Management public API (optional task link)
         └─────────────> Data_Access
Reminder ──────────────> Task_Management public API (optional task link)
         └─────────────> Data_Access
External_Integration ──> Domain_Rules (validate staged data)
                    ├──> Task_Management public API (accept import / update imported deadline)
                    └──> Data_Access (its own staged imports/logs)
```

### Service APIs
- `Task_Management`: `create_task` (date-only or optional timezone-aware `deadline_at`), `get_task`, `list_tasks(user_id, status=None)`, `update_task_deadline(user_id, task_id, deadline_at)`, `update_study_duration(user_id, task_id, study_duration_minutes)`, `transition_task_status` (`completed` / `incomplete`), `get_completion_summary`.
- `Events` (S01 foundation infrastructure, not a business module): `publish_event`, `register_handler`, `process_pending_events` (optionally scoped by `user_id`), `list_events`, `get_event`.
- `Priority`: `deadline_distance` and `deadline_distances` (return factual days-until-deadline; tasks without a deadline are skipped; priority bands/weights are not assumed without an approved rule).
- `Schedule`: `set_availability`, `update_availability`, `list_availability`, `generate_study_schedule`, `schedule_study_session`, `list_study_sessions`.
- `Reminder`: `create_reminder`, `list_reminders`, `update_reminder_status`, `get_preferences`, `update_preferences`, `claim_due_reminders`, `complete_delivery`, `list_notices`, and `dismiss_notice`. Reminder presets are user-specific offsets reused from previously configured reminders; no fixed preset durations are specified by the project documents.
- `External_Integration`: `stage_import` (date-only or timezone-aware timestamp), `list_staged_imports`, `accept_staged_import`, `update_imported_task_deadline` (S06 integration hook), `record_sync_result`.

All persistence operations go through `Data_Access`. Cross-module task lookups and creation use `Task_Management` public service functions. Imported information is owned by External Integration while staged; accepting it creates a task through Task Management.

## Authentication and authorization (S02)
Registration/login/logout and the sole automatically assigned role (`Registered User`) remain in `Authentication`. Passwords are salted PBKDF2-HMAC-SHA256 hashes, not plaintext. `/dashboard` is protected. Authentication initialization is preserved; `app.py` now calls `init_db()` before `init_auth()` so referenced tables exist.

## User-data isolation
Every service query for user-owned records includes `user_id = ?`. Never trust a user ID supplied by a browser request; pass the authenticated session's user ID. Cross-module calls also include that user ID, and linked task references are checked through the Task Management public API and reinforced by composite foreign keys. Task deletion is not exposed by the current service interface.

## Event foundation (S01, PROVISIONAL pending G-01 / G-12)
Plan S01 requires an event publication/consumption foundation with unique event identifiers, duplicate prevention, retry handling and failure logging. `Events` provides a small database-backed, in-application version: `publish_event(..., db=connection)` joins the caller's transaction (a rejected operation commits no event); every event has a unique `event_id`; `processed_events` guarantees a handler runs at most once per event; failures store `last_error`, count `attempts`, and become `failed` after `EVENT_MAX_ATTEMPTS`; events with no registered handler stay `pending`. `Task_Management` publishes `task.completion_changed` and `task.deadline_changed`. Reminder consumes these events to cancel pending deadline reminders on task completion and recalculate pending reminder times after deadline changes. The Schedule module in this project version does not yet expose an S08 rescheduling event contract, so session-rescheduling reminder updates remain deferred. Event retry interval and maximum attempts (`EVENT_RETRY_INTERVAL_SECONDS`, `EVENT_MAX_ATTEMPTS`) remain provisional (G-12); reminder-delivery retries are separately recorded by Reminder and retried on a subsequent browser polling pass without a fixed attempt cap.

## Scope notes
- The priority module deliberately reports deadline distance only. No priority categories, weights, or thresholds were specified in this implementation request, so none are invented.
- The schema and services provide foundation-level operations, not a complete user interface for all modules.
- Email verification, password reset, MFA, login throttling, external provider adapters, and production deployment hardening are outside this skeleton.


## S03 — Task dashboard and completion tracking
The login-protected `/dashboard` shows only the signed-in user's tasks (title, course, deadline, status, completion timestamp), earliest deadline first. Tasks **without a deadline remain visible**, are marked *Missing deadline information* and are listed after dated tasks (FR-02). A short *How to use this dashboard* section gives guidance for the implemented features (NFR-01).

- **Completion:** `POST /tasks/<id>/complete` and `POST /tasks/<id>/incomplete` (CSRF-protected, session `user_id` only, 404 for another user's task, `DomainRuleError` shown as a flash message). Completing never deletes the task or changes its deadline (BR-06). *PROVISIONAL pending G-08:* reverting to incomplete clears `completed_at`, and the default list view is "all".
- **Filter:** `GET /dashboard?status=all|incomplete|completed` (unknown values fall back to `all`), using `Task_Management.list_tasks(user_id, status)`.
- **Progress:** `Task_Management.get_completion_summary(user_id)` returns total, incomplete, completed and completion percentage (no calculation in the template).
- **Manual task entry is NOT an approved requirement** (plan OI-01 / G-14; `AGENTS.md`). The dashboard "Add task" form and `POST /tasks` are behind `ALLOW_MANUAL_TASK_ENTRY` (default **off**; `POST /tasks` then returns 404). For local development/demo set `STUDY_MANAGEMENT_ALLOW_MANUAL_TASK_ENTRY=1`. `Task_Management.create_task` remains available as a service function (used by imports).
- No overdue marking and no priority levels on the dashboard (Priority belongs to slice S05).

## S07 — User availability and Study Schedule

The authenticated `/schedule` page lets a user save and update weekly availability and view their saved Scheduled Study Sessions. Availability periods and sessions are always scoped to the signed-in user. The task dashboard accepts a positive whole-minute study-duration estimate for each task; estimates are stored as `tasks.study_duration_minutes`, owned and updated through Task Management. Existing databases gain the nullable column through the `init_db()` migration, so imported or older tasks remain available until the user supplies an estimate.

Schedule generation uses the user's estimates, existing Task Management and Priority interfaces, and saved availability. It processes higher-priority tasks first and uses the nearer deadline to break equal-priority ties. It places sessions chronologically within availability periods, splitting estimates across periods when needed. Tasks without an estimate, deadline, or determinable priority, and tasks whose full estimate cannot fit by the deadline, remain unscheduled. Existing sessions are preserved and treated as occupied time; schedule adjustment remains S08 scope. See `docs/slices/S07.md` for details.

### S03 routes and module communication
```text
Browser
  └── Flask routes in app.py (login + CSRF + session user_id)
       ├── Task_Management.list_tasks / transition_task_status / get_completion_summary
       │    ├── Domain_Rules validation
       │    ├── Events.publish_event (same transaction)
       │    └── Data_Access connection_scope (all SQL; user_id scoped)
       └── Task_Management.create_task (only when ALLOW_MANUAL_TASK_ENTRY is on)
```

## Cleanup round — shared validators and import idempotency (the task start action was later removed)

### Task start action (superseded)
The cleanup round added an in-progress `Start` action. It was **removed in the gap-fix round** because plan S03 defines only Completed and Incomplete statuses.

### Shared Domain_Rules validators
`Domain_Rules` now provides these reusable validators, all raising `DomainRuleError` on invalid input:
- `validate_time_range(start_time, end_time)`: strict 24-hour `HH:MM` values and start earlier than end.
- `validate_day_of_week(day_of_week)`: integer 0–6 (Monday–Sunday; booleans are rejected).
- `validate_iso_datetime(remind_at)`: ISO date/time with both date and time components.
- `validate_reminder_status(status)`: `pending`, `delivering`, `delivered`, `dismissed`, `cancelled`, or `skipped`.
- `validate_course(course)`: optional text, trimmed, maximum 100 characters; blank becomes `None`.

Task Management validates course values. Schedule validates availability/session dates, time ranges, and day-of-week values. Reminder validates reminder timestamps and statuses. Domain validation failures from these services use `DomainRuleError` rather than plain `ValueError`.

### Staged-import acceptance safety
Task Management supports an optional internal `source_import_id` idempotency key, backed by a unique `(user_id, source_import_id)` index. External Integration still creates tasks only through `Task_Management.create_task`. Repeated or concurrent acceptance attempts therefore resolve to the same task instead of creating duplicates. The import row is conditionally changed from `staged` to `accepted`, and only the caller that performs that state change writes the acceptance log. `init_db()` adds the idempotency column/index to existing S01–S03 databases as well as new databases.

### Dashboard query efficiency
`Priority.deadline_distances(user_id, tasks=...)` calculates distances for a task list already fetched by Task Management. The dashboard no longer uses it (overdue marking was removed in the gap-fix round); the interface remains available for slice S05.

### Updated tests
The test suite now includes:
- All earlier S01/S02/S03 tests.
- New Domain_Rules valid/invalid cases for time ranges, weekdays, reminder ISO date/time, reminder statuses, and optional course length.
- Service-level checks that Schedule, Reminder, and Task Management use `DomainRuleError` for these invalid values.
- A repeated staged-import acceptance test confirming only one task is created.
- Flask test-client coverage for registration success/duplicate/short password, login success/wrong password, logout, CSRF rejection on every POST route, and (after the gap-fix round) completion toggling and cross-user 404.

Run the complete suite from this directory with `pytest -q`.

## Gap-fix round (comparison with plan.md v0.2)
A review of the code against `plan.md` v0.2 and `AGENTS.md` found gaps in S01 and S03; this round fixed only those gaps: event foundation (A1), Domain Rules as the single validation gateway for email/password (A2), optional deadlines (B1), Completed/Incomplete statuses and revert (B2), filter (B3), guidance (B4), overdue marking removed (B5), manual task entry behind a flag (B6), tests (B7) and documentation (C1-C5). Outcome: pending human review. Run `pytest -q` from this directory; the full suite is 122 tests.

## Development process

Implementation followed the course Implementation Loop for each vertical slice, using HITL execution and a human review stop between slices. Records (following plan.md section 8.1) are kept in:

- [Plan update notes](docs/PLAN_UPDATE_NOTES.md) (changes to make to the authoritative `plan.md`; this project does not replace it)
- [S01 — Application foundation](docs/slices/S01.md)
- [S02 — Authentication and authorization](docs/slices/S02.md)
- [S03 — Task dashboard and completion tracking](docs/slices/S03.md)
- [Cleanup round](docs/slices/CLEANUP.md)
- [Gap-fix round](docs/slices/GAPFIX.md)
- [Implementation log — loop steps 4–14](docs/IMPLEMENTATION_LOG.md)

Human reviewer, review date, owners, commit references and personal review notes are intentionally left for the human to complete in each record.


## S04 — Deadline management and conflict identification
Imported deadline updates use `External_Integration.update_imported_task_deadline`, which delegates to `Task_Management.update_task_deadline`. S06 remains responsible for discovering and matching external updates; this S04 interface expects S06 to supply the already-matched task ID. Timestamps must be ISO 8601 with an explicit UTC offset and are stored in UTC. Domain Rules flags every same-user task sharing that exact instant. The dashboard displays the conflict flag for review; no automatic resolution is performed. Successful changes publish `task.deadline_changed` transactionally.

S04 tests: `pytest -q tests/test_s04_deadline_management.py`.

## S09 — Reminder preferences and delivery

Reminder preferences and pending reminders are owned by `Reminder`. The dashboard supports user-level enable/disable settings, deadline/session categories, custom reminder times, and reusable personal presets derived from offsets the user has previously configured (the PRD does not specify fixed preset durations). Deadline reminders require a timestamp deadline; date-only legacy deadlines do not have an approved time of day and are not assigned one. Scheduled-session event times are converted from the browser's local time to UTC when a reminder is configured.

The browser helper checks immediately on page load and polls every 30 seconds. It uses the native browser Notification API when permission is granted and an accessible in-app fallback otherwise. Server-side claims prevent two tabs from claiming the same reminder simultaneously; unacknowledged claims become eligible again after the 30-second claim lease. Skipped reminders create dismissible in-app notices. Task deadline-change and completion events are consumed through the existing Events interface.

Delivery failures are recorded and remain retryable on a subsequent poll. No maximum delivery-attempt count or separate retry interval is configured; those policy values remain unresolved. The existing generic Events processor retains its separate provisional G-12 retry settings. Browser-closed delivery remains limited; no push service or separate background scheduler is used. Scheduled-session rescheduling remains deferred until S08 supplies its event name and payload. Reminders for sessions linked to completed tasks remain deferred. Task deletion and scheduled-session deletion/cancellation are not implemented.
