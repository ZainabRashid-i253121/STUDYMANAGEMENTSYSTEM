# Plan update notes (for the authoritative plan.md)

This file does **not** replace `plan.md`. It lists changes the team should make to `plan.md` through its normal review process. Nothing here changes a requirement, ADR or gate status.

## 1. Version history row (plan §9)
Add a row, for example: `v0.3 | Slice status after implementation of S01–S03 and a gap-fix round; provisional behaviors recorded.`

## 2. Slice status (member 1)
| Slice | Status to record |
|---|---|
| S01 | Implemented with PROVISIONAL event mechanism and technology choices; pending final human review. |
| S02 | Implemented with PROVISIONAL authentication choices (G-02); pending final human review. |
| S03 | Implemented with PROVISIONAL G-08 behavior; manual entry behind a flag (OI-01 open); pending final human review. |

## 3. Gates that still need a group decision
- **G-01** — approve (or replace) Flask, SQLite, pytest and the database-backed event mechanism. `AGENTS.md` §5 says the documents do not establish an event mechanism, while plan S01 requires event foundations: resolve this conflict under G-14.
- **G-02** — approve the authentication mechanism, password policy (currently 8 characters minimum), session handling and rate limiting.
- **G-08** — confirm the default task-list view ("all"), completion date on reversion (currently cleared), and completion effects on priority/scheduling/reminders.
- **G-12** — set the event retry interval (currently 60 s) and maximum attempts (currently 3); backup policy (S12).
- **G-13** — define measurable usability and compatibility targets.
- **G-14 / OI-01** — decide whether manual task entry is in scope; today it exists only behind `ALLOW_MANUAL_TASK_ENTRY` (default off). Also decide what happens if external import is infeasible.
- **G-15 / OI-08** — define user-visible behavior for delayed/failed events and who may inspect failed events.
- **OI-06** — availability ownership: code follows plan/ADR-006 (Schedule), while `AGENTS.md` says do not assign ownership yet.

## 4. Scope notes to record
- Early service code exists for Priority (S05), Schedule (S07), Reminder (S09) and External_Integration (S06); it should be reviewed when those slices start.
- Status vocabulary: tasks are `incomplete`/`completed` (FR-13). `AGENTS.md` uses the word "pending" for incomplete tasks; the code uses `incomplete`.
- The slice completion record (plan §8.1) fields for owner, commit reference and reviewer are left "TO BE FILLED BY HUMAN" in `docs/slices/`.


## 5. S04 plan update (plan-v03.md)
A new versioned plan file, `plan-v03.md`, preserves `plan-v02.md` and records the S04 decisions: ADR-006 Accepted; Domain Rules owns conflict identification; imported data initiates deadline updates; exact same-user UTC-normalized instants are conflicts; timezone-aware timestamps require an explicit offset; existing date-only values remain unchanged. S04 uses AFK/delegated execution and awaits human review. S05/S06/S08/S09 remain responsible for priority, external update discovery/matching, schedule, and reminder reactions respectively.
