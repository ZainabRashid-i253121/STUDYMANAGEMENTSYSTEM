# Implementation Log — Implementation Loop Steps 4–14

S01–S03, cleanup, and gap-fix used HITL; S04 used AFK/delegated execution after the user approved deterministic rules. Human review remains required before S04 acceptance/integration. `plan.md` v0.2 remains the authoritative plan (see `PLAN_UPDATE_NOTES.md` for suggested updates).

| Step | Implementation Loop activity | S01 | S02 | S03 | Cleanup | Gap-fix | S04 | S05 |
|---:|---|---|---|---|---|---|---|---|
| 4 | Follow the Implementation Loop for the slice | `docs/slices/S01.md` | `docs/slices/S02.md` | `docs/slices/S03.md` | `docs/slices/CLEANUP.md` | `docs/slices/GAPFIX.md` | `docs/slices/S04.md` | S05 workflow record (this log) |
| 5 | Select the next prioritized vertical slice | plan-v02 §6 (S01 first) | plan-v02 §6 (S02 second) | plan-v02 §6 (S03 third) | not a plan slice; added after S03 | triggered by plan-v02 comparison | plan-v03 §6 (S04 fourth) | plan-v03 reference; S05 (Person 2) |
| 6 | Load only the relevant project context | S01.md — relevant context | S02.md — relevant context | S03.md — relevant context | CLEANUP.md — relevant context | GAPFIX.md — relevant context | S04.md — relevant context | PRD, architecture, AGENTS, ADRs, plan-v03, existing code |
| 7 | Confirm/refine acceptance criteria and basic checks | S01.md — acceptance criteria | S02.md — acceptance criteria | S03.md — acceptance criteria | CLEANUP.md — acceptance criteria | GAPFIX.md — acceptance criteria | S04.md — user-approved timestamp/conflict criteria | User-approved S05 criteria; AC-07 deferred |
| 8 | Choose execution mode | HITL | HITL | HITL | HITL | HITL | AFK/delegated; deterministic approved rules, human review retained | AFK; user-approved rules, human review retained |
| 9 | Let the AI agent implement the slice | foundation, events, domain rules | authentication and routes | task dashboard and completion | cleanup fixes | gap-fix changes | Data_Access, Domain_Rules, Task_Management, External_Integration, dashboard, tests | Priority implementation, persistence/interface/dashboard updates, S05 tests |
| 10 | Run relevant checks/tests | 19 tests passed at original review | cleanup route tests | 28 tests passed at original review | 76 tests passed | 122 tests passed when originally run | 100 targeted tests passed; full suite blocked by missing Flask in execution environment | User-reported local results: 8 S05 tests passed; 141 full-suite tests passed; no failures |
| 11 | Human review: Accept, Revise, or Reject | Revise, then Accepted | Accepted | Accepted; later gaps recorded | Revise, then Accepted | Pending human review | Pending human review | **ACCEPT**; core S05 accepted with AC-07 deferred |
| 12 | Iterate with the AI if required | Revised after identified gaps | no revision recorded | gaps addressed in gap-fix | corrected test expectation | gap-fix round | pending reviewer feedback | No further S05 revision requested; AC-07 assigned to Schedule slice |
| 13 | Integrate the approved slice | integrated | integrated | integrated | integrated | pending approval | pending human acceptance and coordination with Person 1 | **Not integrated**; integration intentionally deferred |
| 14 | Update plan and affected artefacts | README and plan notes | README and plan notes | README and plan notes | README | README and plan notes | plan-v03, ADR-006, AGENTS, architecture, README, S04 record | This S05 workflow log only; no plan, code, or unrelated slice changes |

## This gap-fix round
It was triggered by a review of the code against plan.md v0.2 (and AGENTS.md) that found: no event foundation (S01), email/password validation outside Domain Rules (S01), a required deadline, a terminal Completed status, an invented in-progress status, no filter and no guidance, an unapproved manual task form, and overdue marking outside S03 scope. These are fixed as listed in `slices/GAPFIX.md`. **Outcome: pending human review.**

## Facts recorded in this log
- HITL for all slices; S01 first delivery Revise (no Domain Rules, only a users table, no module interfaces, no tests) then Accepted; S02 Accepted; S03 Accepted at 28 tests; the cleanup round had one test expecting `/logout` to return 400 instead of the real 302, corrected, then Accepted at 76 tests; the plan.md comparison found the gaps fixed in this round.

## Human review fields
Human reviewer: TO BE FILLED BY HUMAN  
Review date: TO BE FILLED BY HUMAN  
Personal review notes: TO BE FILLED BY HUMAN

## S04 implementation record
S04 was implemented in the isolated project copy using AFK/delegated execution after the user approved the conflict definition, timezone policy, import-only initiation, and ADR-006 ownership. The targeted S04 and non-Flask regression suites passed: 100 tests. The complete suite could not be collected in this execution environment because Flask is not installed; the project requirements include Flask, and installation was unavailable due to network restrictions. Human review and integration remain pending. See `docs/slices/S04.md`.

## S05 implementation and final acceptance record

- Execution mode: AFK, using the user's explicitly approved S05 decisions.
- Final human review: **ACCEPT** (user's decision; this does not assert wider group approval).
- Acceptance scope: core S05 functionality accepted. The user reported local test results of **8 S05-specific tests passed** and **141 full-suite tests passed**, with no failures. These are user-reported local results, not tests rerun during this log update.
- AC-07 limitation: the scheduling-review flag for insufficient study time is **deferred to the Schedule slice**. The existing system does not provide the study-duration information needed to assess insufficient study time. S05 leaves priority unchanged and does **not** implement or claim to implement the scheduling-review flag.
- Acceptance criteria: AC-01–AC-06 and AC-08–AC-12 accepted as met for the core S05 implementation; AC-07 deferred as stated above.
- Scope: no unrelated slices were modified as part of this acceptance-log update. S01–S04 and S09 were not changed.
- Integration: not started; the accepted S05 work remains separate pending the planned coordination with the other group slices. No commit or push was performed.
- Review date: 2026-11-27 (recorded date).


## S09 implementation record — AFK

- Human scope decision: **APPROVED** for AFK implementation; this records the user's approval and does not assert wider group approval.
- Implementation scope: reminder preferences, deadline and Scheduled Study Session reminder configuration, reusable personal presets derived from previously selected offsets, browser notification permission handling, accessible in-app fallback, immediate page-load polling, 30-second polling, cross-tab claims, task deadline/completion event consumers, skipped-reminder notices, delivery failure recording/retry, and authenticated user isolation.
- PRD traceability: FR-14 and AC-FR-14.1–14.8; BR-08; OQ-38, OQ-39, OQ-40, OQ-41, OQ-42 and OQ-43; architecture §§5, 7, 8 and 10; ADR-003, ADR-005 and accepted ADR-006; AGENTS.md §§1, 3, 5, 9–13.
- Notification channel: browser Notification API plus accessible in-app fallback, satisfying the PRD browser-notification requirement and architecture/ADR-006 in-app notification boundary. No external push service is introduced.
- Scheduling: browser checks immediately on page load and polls every 30 seconds. No separate background scheduler is introduced. Browser-closed delivery remains limited (OQ-38).
- Reminder times: custom times are supported. Reusable personal presets are derived from offsets previously configured by that user; no fixed preset durations were specified in the supplied project documents.
- Delivery retry: failures are recorded and remain eligible on a subsequent browser poll. No fixed maximum attempt count or separate retry interval is configured; these policy values remain unresolved (OQ-42). The generic Events processor's provisional G-12 policy is separate and unchanged.
- Event integration: existing `task.deadline_changed` and `task.completion_changed` events are consumed. Event polling supports a `user_id` filter so an authenticated user's browser poll does not process another user's events. The supplied Schedule module has no S08 rescheduling event name/payload; session-rescheduling reminder updates are deferred until that contract is provided. No event contract was invented and Schedule was not modified.
- Delayed reminders: already-passed reminders are marked `skipped` and generate dismissible in-app notices. Reminders more than one polling interval late are skipped rather than delivered stale.
- Deferred: OQ-38 browser-closed delivery beyond browser capabilities; OQ-41 reminders for Scheduled Study Sessions associated with completed tasks; S08 session-rescheduling consumer pending its event contract.
- Excluded: task deletion and task-deletion cancellation; Scheduled Study Session deletion and deletion-triggered cancellation.
- Date-only deadlines: reminder configuration requires a timestamp deadline; no time of day is invented for legacy date-only deadlines.
- Scope protection: S04 and accepted S05 implementation files were preserved; no Person 1 integration, commit, or push was performed.
- Validation: `pytest -q tests/test_s09_reminders.py` — **18 passed**. Three authenticated Flask route tests were added in `tests/test_s09_routes.py` but could not be executed in this environment because Flask is unavailable. Relevant non-Flask regression command `pytest -q --ignore=tests/test_cleanup_routes.py --ignore=tests/test_s03_dashboard.py --ignore=tests/test_s09_routes.py -k 'not dashboard_displays_priority_and_separate_conflict_flag'` — **128 passed, 1 deselected**. S04/S05 focused regression — **18 passed, 1 deselected**. Python compilation, Jinja template parsing, and `node --check static/reminders.js` passed.
- Full suite: `pytest -q` could not complete collection because Flask is not installed in this execution environment (three collection errors: existing cleanup routes, existing S03 dashboard, and new S09 route tests). Installing `requirements.txt` was attempted but network access was unavailable. No test assertion failures were observed in the executed suites; S09 Flask route tests remain unexecuted here and should be run locally with the declared Flask dependency installed.
- Final human review: pending user review. No commit, push, or integration was performed.
