# S07 — User Availability and Study Schedule: Workflow Evidence

## Slice information

- **Slice:** S07 — User Availability and Study Schedule creation/viewing
- **Responsible member:** Person 3
- **Implementation mode:** AFK (Away-from-Keyboard)
- **Reason:** This project uses AFK implementation for the assigned slice.
- **Requirement references:** PRD FR-06 / AC-FR-06.1–06.2; FR-16 / AC-FR-16.1–16.3; plan-v03 S07; architecture §§5–8; ADR-005 and ADR-006.
- **Working branch:** `person3-s07`; `main` is unchanged.

## Context reviewed

The implementation reuses the existing Schedule, Task Management, Authentication, Data Access, and Priority interfaces and the existing availability and study-session tables. Availability and scheduled sessions remain owned by Schedule Management; tasks and user estimates remain owned by Task Management.

## Selected implementation rules

- Study-duration estimates are entered by the user per task and stored as positive whole minutes.
- Higher-priority tasks are allocated first. Equal-priority tasks are ordered by nearest deadline; ties preserve Task Management's existing list order.
- Sessions are allocated chronologically inside saved weekly availability.
- A task may span available periods. The generator commits sessions for a task only when its full estimate fits by its deadline; otherwise it leaves that task unscheduled and preserves the time for later tasks.
- Completed tasks are excluded. Tasks without an estimate, deadline, or determinable priority remain unscheduled. The planning horizon runs from the supplied/current date through the latest eligible task deadline.
- Existing future scheduled sessions are preserved and count as occupied time; their duration counts toward the task estimate on subsequent generation requests. Schedule adjustment remains S08 scope.
- No availability time is double-counted when saved periods overlap.
- When priority and deadline are both equal, the existing Task Management list order is preserved. Tasks with Undetermined priority remain unscheduled because the priority interface supplies no rank for them.

## Implementation status

Availability entry, update, and viewing; task estimate entry; schedule generation; and a user-scoped schedule view are implemented. Generation uses the Priority and Task Management service interfaces and writes all generated sessions in one Data Access transaction. The scheduler does not adjust or delete existing sessions. Tasks without deadlines or with undetermined priority remain unscheduled, per the user's edge-case decision.

## Tests added

- Availability updates are user-scoped.
- Task study-duration estimates persist, are user-scoped, and reject non-positive or non-integer values.
- Authenticated schedule views show the signed-in user's sessions and associated task titles.
- Generation covers priority/deadline order, chronological placement, splitting across slots, insufficient availability without overbooking, missing estimates/deadlines, and completed-task exclusion.
- Routes cover authentication and CSRF for availability, duration, and generation operations; database migration coverage checks the new nullable column on existing task tables.

## Validation status

At the initial implementation handoff, tests had not yet been run. The subsequent environment setup and successful test run are recorded below.

## Stage 4 testing and verification attempt — 2026-11-28

The S07 verification step was attempted on the committed S07 implementation (`f462f72`). The following commands were issued from `study_management_scaffold/`:

| Command | Actual result |
|---|---|
| `pytest -q tests/test_s07_schedule.py` | Did not start: PowerShell reported `pytest` was not recognized. No tests were collected or run. |
| `pytest -q tests/test_database.py tests/test_module_interfaces.py` | Did not start for the same missing `pytest` executable. No tests were collected or run. |
| `pytest -q tests/test_s05_priority.py tests/test_s03_dashboard.py` | Did not start for the same missing `pytest` executable. No tests were collected or run. |
| `git show --check --oneline HEAD` | Passed for commit `f462f72`; no whitespace errors were reported. |
| `git diff --check` | Passed; no whitespace errors were reported. |

`python`, `python3`, `py`, and `pytest` were not available in the shell or the checked project virtual-environment path. There were no code corrections or test retests because the test runner did not start. These results indicate an environment blocker, not a passing or failing S07 test suite. S07 is **not marked accepted**. Verification notes were recorded on the separate `person3-s07-verify` branch; `main` was not modified.

## Python environment setup and successful retest — 2026-11-28

- Repository inspection found no Python version pin, `pyproject.toml`, or existing virtual environment. `study_management_scaffold/requirements.txt` is the dependency source and lists only Flask and pytest.
- Installed the signed Python 3.14.10 64-bit Windows runtime per-user from the official Python Software Foundation installer. Its Authenticode signature validated successfully.
- Created `study_management_scaffold/.venv` with Python 3.14.10 and installed only `requirements.txt` dependencies. Installed top-level versions: Flask 3.1.3 and pytest 9.2.0, with their required transitive packages.
- Initial test attempts failed before collection because Python/pytest were absent. Environment setup resolved that blocker; no S07 code changes or corrections were needed.

Successful test command, run from `study_management_scaffold/`:

```powershell
\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider tests/test_s07_schedule.py tests/test_database.py tests/test_module_interfaces.py tests/test_s05_priority.py tests/test_s03_dashboard.py
```

Actual result: **64 passed in 17.72 seconds**. This covers S07 duration persistence/validation and ownership, availability create/update, schedule viewing, priority/deadline order, slot allocation and splitting, insufficient-time handling, missing estimate/deadline behavior, completed-task exclusion, database migration, module interfaces, and the related Priority/dashboard regressions. No test failures occurred, so no code correction or subsequent retest was required. S07 remains pending human review and is **not marked accepted**. Setup and test-log changes are on `person3-s07-verify`; `main` was not modified, committed, or pushed.

## Human review and targeted revision — 2026-11-28

- **Original human review decision:** REVISE. The reviewer accepted AC1–AC4 and the logged 64-test result, and requested correction/evidence for Undetermined priority handling, Data Access boundary interpretation, stale S07 validation documentation, and an actual application walkthrough. This decision is preserved; no final Accept/Reject decision has been made.
- **Finding 1 — Undetermined priority:** Added `test_schedule_generation_leaves_undetermined_priority_unscheduled` to `study_management_scaffold/tests/test_s07_schedule.py`. It supplies an `Undetermined` result at the Priority service boundary and verifies the task remains unscheduled and no session is persisted. Scheduler behavior already filters to ranked High/Medium/Low tasks; no production-code correction was necessary.
- **Finding 2 — Data Access boundary:** Reviewed architecture §§5–8, ADR-002, ADR-005 and ADR-006 against `Schedule`, `Task_Management`, `Priority`, and `Data_Access`. Schedule imports `Data_Access.connection_scope` for connection lifecycle and transaction handling and only queries or changes Schedule-owned availability/session tables. Cross-module task and priority data is obtained through Task Management and Priority service interfaces. However, SQL statements are written in the Schedule business module; `connection_scope` yields a raw SQLite connection rather than a query/repository interface. This matches the established persistence pattern used by Task Management and Priority, but the literal architecture rule “Only Data Access communicates directly with the database” can be read more strictly. No S07-only refactor was made because this is a shared project-wide boundary ambiguity, and moving Schedule alone to a new repository pattern would make the architecture inconsistent. The strict boundary interpretation remains for human/team clarification; no cross-owner table access was found.
- **Finding 3 — stale validation note:** Updated `study_management_scaffold/docs/slices/S07.md` with the recorded 64-test result and pending final human review. Clarified in this log that the “not yet run” statement describes the initial implementation handoff and is superseded by later actual results.
- **Finding 4 — manual application verification:** The browser walkthrough could not be completed visually. `cua.getState()` reported `Browsers: Error: The browser access host is unavailable`; native Chrome windows were reported minimized, and launching Chrome through the computer-use interface returned `accessibility window-opened handler did not become ready`. As a separate application-level check, a temporary local Flask instance used a disposable SQLite database outside the repository. Authenticated HTTP requests to the app created a Saturday 09:00–11:00 availability period, updated it to 09:00–12:00, generated a schedule, and fetched the rendered schedule page. Responses showed the updated availability and both session titles/times: High Priority 09:00–10:30, then Medium Priority 10:30–11:30, both on 2026-11-28 and inside the saved slot. This verifies the application route/render flow, but is not a successful browser-based visual walkthrough.
- **Focused test and retest:** Ran from `study_management_scaffold/`: `\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider tests/test_s07_schedule.py tests/test_database.py tests/test_module_interfaces.py tests/test_s05_priority.py tests/test_s03_dashboard.py`. Actual result after adding the Undetermined-priority test: **65 passed in 11.45s**. The new focused case monkeypatches the Priority interface to return `Undetermined` and asserts the task is returned unscheduled with no persisted session. No test failures or implementation corrections were required.
- **Branch/history:** Work is being performed on the already checked-out branch `main` because the reviewer instructed not to switch branches. No branch switch, commit, or push is being made.
- **S07 status:** REVISE remains the human decision. S07 is not accepted.
