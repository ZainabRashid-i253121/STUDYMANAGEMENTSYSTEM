# Gap-fix round — alignment with plan.md v0.2

## Slice ID and name
GAPFIX — corrective round on S01 and S03 (and S02 validation), triggered by a review of the code against plan.md v0.2 and AGENTS.md.

## Requirement IDs covered
S01: ADR-005, ADR-006, ADR-001/002 (event foundation, Domain Rules gateway). S03: FR-02, FR-13, NFR-01, BR-06; plan §10 warning 5 (manual task entry).

## Goal and scope
Fix only the gaps found: A1 event foundation, A2 email/password in Domain Rules, B1 optional deadlines, B2 Completed/Incomplete with revert, B3 filter, B4 guidance, B5 overdue marking removed, B6 manual entry behind a flag, B7 tests, C1–C5 documentation. No features from S04–S12 were added.

## Relevant context only
`Data_Access/database.py`, `Data_Access/event_store.py`, `Events/`, `Domain_Rules/`, `Task_Management/`, `Authentication/`, `Priority/`, `app.py`, `templates/`, `tests/`, `README.md`, `docs/`.

## Dependencies and decision gates
| Gate | Status |
|---|---|
| G-01 | PROVISIONAL (event mechanism; `AGENTS.md` conflict noted). |
| G-08 | PROVISIONAL (completion date on reversion; default list view). |
| G-12 | PROVISIONAL (retry interval and maximum attempts). |
| G-14 / OI-01 | OPEN (manual task entry; behind `ALLOW_MANUAL_TASK_ENTRY`, default off). |
| G-05 | Missing-deadline priority behavior undecided: Priority skips tasks without a deadline and invents nothing. |

## Acceptance criteria and basic checks
- [x] A1 `events` and `processed_events` tables, `Events` module, unique event ids, duplicate prevention, retry then failure with `last_error`, PROVISIONAL constants, `task.completion_changed` published in the task transaction.
- [x] A2 email/password validation in Domain Rules with unchanged behavior and messages.
- [x] B1 nullable deadline with a data-preserving rebuild migration; empty deadline allowed, invalid non-empty deadline rejected; "Missing deadline information"; undated tasks sorted last; Priority/Schedule/Reminder/External_Integration do not crash.
- [x] B2 statuses are `incomplete`/`completed`; old rows migrated; revert supported; double complete/incomplete rejected; completion date cleared on reversion (PROVISIONAL).
- [x] B3 filter links and `?status=` handling. B4 guidance. B5 overdue marking removed from the dashboard (Priority module kept, unused by the dashboard).
- [x] B6 `ALLOW_MANUAL_TASK_ENTRY` (env `STUDY_MANAGEMENT_ALLOW_MANUAL_TASK_ENTRY=1`); form hidden and `POST /tasks` returns 404 when off; `create_task` service remains.
- [x] B7 tests updated and added (listed in `S01.md` and `S03.md`).
- [x] C1–C5 documentation (this file, `PLAN_UPDATE_NOTES.md`, slice records, log, README).

## Execution mode
HITL. Reason: unresolved decision gates and foundation risk required a human review stop after each slice.

## Tests that verify it
See `tests/test_events.py`, `tests/test_s03_dashboard.py`, `tests/test_database.py` (`test_init_db_rebuilds_legacy_tasks_table_and_keeps_data`, `test_init_db_migration_is_idempotent`), `tests/test_module_interfaces.py` (`test_modules_do_not_crash_on_tasks_without_deadline`) and `tests/test_domain_rules.py`. Changed existing tests: `test_pending_to_completed_is_valid` became `test_incomplete_to_completed_is_valid` and the transition test now uses `incomplete` (statuses changed); the start-action tests in `tests/test_cleanup_routes.py` were replaced by completion-toggle tests (the Start action was removed); the old overdue and in-progress dashboard assertions in `tests/test_s03_dashboard.py` were replaced (those features were removed); `test_init_db_creates_required_tables` now also expects the event tables; the CSRF route test lists the new `/incomplete` route instead of `/start`.

## Code / commit reference
TO BE FILLED BY HUMAN

## Implementation owner(s)
TO BE FILLED BY HUMAN

## Review outcome and iterations
Outcome: pending human review. Triggered by comparing the delivered code with plan.md v0.2, which found the gaps fixed here.

## Remaining limitations and follow-up work
- Provisional behaviors (G-01, G-08, G-12) and the open manual-entry decision need group decisions.
- `AGENTS.md` says the supplied documents do not establish an event mechanism while plan S01 requires an event foundation; this conflict must be resolved by the group (G-14).
- Schedule, Reminder, External_Integration and Priority service code exists early (they belong to S07, S09, S06, S05).
- G-01 and G-02 technology and authentication choices were made by the AI and are not yet group-approved.

Human reviewer: TO BE FILLED BY HUMAN  
Review date: TO BE FILLED BY HUMAN  
Personal review notes: TO BE FILLED BY HUMAN
