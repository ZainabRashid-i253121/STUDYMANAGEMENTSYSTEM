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

Tests have not been run for this S07 work. No test results are claimed.

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
