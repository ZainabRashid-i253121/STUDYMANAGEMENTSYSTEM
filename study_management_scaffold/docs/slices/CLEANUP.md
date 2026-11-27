# Cleanup round — shared validators and import idempotency

## Slice ID and name
CLEANUP — not a slice in plan.md v0.2; a refinement round on S01–S03 that was added during implementation.

## Requirement IDs covered
Supports S01 (Domain Rules as the validation gateway, module interfaces) and S02/S03 route test coverage. No new PRD requirement is claimed.

## Goal and scope
Move more validation into Domain Rules, make staged-import acceptance idempotent, and add Flask route tests. (The round also added an in-progress "Start" action, which the gap-fix round later removed because plan S03 defines only Completed and Incomplete.)

## Relevant context only
`app.py`, `Domain_Rules/__init__.py`, `Task_Management/__init__.py`, `Schedule/__init__.py`, `Reminder/__init__.py`, `External_Integration/__init__.py`, `Priority/__init__.py`, `Data_Access/database.py`, `tests/test_domain_rules.py`, `tests/test_module_interfaces.py`, `tests/test_cleanup_routes.py`, `README.md`.

## Dependencies and decision gates
| Gate | Status |
|---|---|
| G-01 | PROVISIONAL (see S01). |
| G-04 (import duplicates/retries) | **OPEN** — `accept_staged_import` idempotency is a technical safeguard, not an approved import policy (S06). |
| Scope | Schedule, Reminder, External_Integration and Priority belong to S07, S09, S06 and S05; their service code exists early. |

## Acceptance criteria and basic checks
- [x] `Domain_Rules` validates time range, day of week, ISO reminder date/time, reminder status and optional course length; Schedule, Reminder and Task Management raise `DomainRuleError` for them.
- [x] `accept_staged_import` returns the same task on repeated acceptance and creates only one task.
- [x] Route tests cover registration, login, logout and CSRF behavior (including `/logout` redirecting with the session kept when the token is missing).
- [~] "Start" action and `Priority.deadline_distances` dashboard batching — delivered in this round, then removed/unused after the gap-fix round (see `GAPFIX.md`).

## Execution mode
HITL. Reason: unresolved decision gates and foundation risk required a human review stop after each slice.

## Tests that verify it
- `tests/test_domain_rules.py`: `test_valid_time_ranges`, `test_invalid_time_ranges`, `test_valid_day_of_week`, `test_invalid_day_of_week`, `test_valid_reminder_datetime`, `test_invalid_reminder_datetime`, `test_valid_reminder_status`, `test_invalid_reminder_status`, `test_optional_course_validation`, `test_course_maximum_length`.
- `tests/test_module_interfaces.py`: `test_accept_staged_import_twice_creates_only_one_task`, `test_new_domain_rules_are_used_by_schedule_reminder_and_task_services`, `test_priority_batch_distances_uses_supplied_task_list`.
- `tests/test_cleanup_routes.py`: `test_register_success`, `test_register_duplicate_email`, `test_register_short_password`, `test_login_success_and_wrong_password`, `test_logout`, `test_public_post_routes_reject_missing_csrf`, `test_authenticated_post_routes_reject_missing_csrf`.

## Code / commit reference
TO BE FILLED BY HUMAN

## Implementation owner(s)
TO BE FILLED BY HUMAN

## Review outcome and iterations
- First review: **Revise** — one test (`test_authenticated_post_routes_reject_missing_csrf`) expected `/logout` to return 400 without a CSRF token; the real behavior is a 302 redirect that does not log the user out.
- Iteration: the test was corrected; then **Accepted** at 76 passing tests.

## Remaining limitations and follow-up work
- Early service code for S05, S06, S07 and S09 modules is outside the three assigned slices and still needs its own slice review.
- Availability ownership: the code places `availability` under Schedule (plan/ADR-006 summary), but `AGENTS.md` says ownership must not be assigned until the architecture is updated (OI-06 / G-14).

Human reviewer: TO BE FILLED BY HUMAN  
Review date: TO BE FILLED BY HUMAN  
Personal review notes: TO BE FILLED BY HUMAN
