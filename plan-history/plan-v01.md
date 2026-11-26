# plan.md — Study Management System Implementation Plan

**Project:** Group #7 — Study Management System
**Stage:** 2 — Validate & Plan
**Plan version:** v0.2 (validated planning baseline) — see Section 9
**Status:** Validated planning baseline for Stage 2. Open decisions remain explicitly gated; this plan does not approve or resolve them. It introduces no new requirements, features, or architectural decisions.

**Source documents (read in full for this plan):** `final-prd.md` (PRD v1.2), `architecture.md`, `AGENTS.md`, `ADR-002` to `ADR-006`.
**Not supplied:** `ADR-001-architecture-style.md`. Its decision (Layered Modular Monolith, single initial deployment) is taken from `architecture.md` §4 and `AGENTS.md` §2 only.

**Conventions used in this plan**
- Requirement IDs (FR-xx, NFR-xx, BR-xx, PC-xx, AC-FR-xx.y, OQ-xx, EC-xx) are the PRD's own. Their wording is not changed here.
- `G-xx` = a **decision gate**: an unresolved matter that must be decided by the project team before the affected slice (or the affected part of it) can start. Gates are defined in Section 2.3.
- `OI-xx` = an additional open issue found while planning that the documents do not settle (Section 2.4).
- `C-xx` = a cross-check finding about an inconsistency between documents (Appendix A).
- Slice IDs are `S01` to `S27`.
- ADRs and the PRD retain their recorded status (ADRs: **Proposed**; PRD: **v1.2 draft, final approval pending**; FR-13 and FR-15 retain their pending-validation status). The project team has instructed that these documents be treated as the source of truth for planning; this plan does not describe any proposed decision as formally approved.

---

## 1. Product Objective

The Study Management System gives Ms. Arooj, the intended user, one web application — usable in desktop and mobile browsers — for organizing and following her academic work (PRD §1.1, §1.2). The product aims to:

1. Keep academic task and deadline information **accurate and up to date** (BR-02).
2. **Display** academic tasks and available deadlines in one place (FR-02).
3. **Prioritize** tasks according to agreed deadline-based rules (FR-05, BR-01).
4. Support **changes to deadlines** and flag **deadline conflicts** for the user's review (FR-03, FR-04).
5. Provide a **Flexible Study Schedule** that accommodates available time and adjusts when deadlines, priorities, or availability change (FR-06, FR-07, FR-09).
6. **Import** academic tasks and deadlines from an external academic source (subject to feasibility) and check them for updates (FR-01, FR-08).
7. **Track task completion** while preserving tasks and their original deadlines (FR-13, BR-06).
8. Deliver **in-app reminders** for deadlines and Scheduled Study Sessions at user-configured times (FR-14).
9. **Record study time** per task without automatically changing Task Priority or deadlines (FR-15, BR-07).
10. Let the user **explicitly delete** tasks and Scheduled Study Sessions (FR-16, BR-09).
11. Restrict each Registered User to their own private records (NFR-03) and support backup and recovery (NFR-04).

The system is an organizational and planning aid. It does not take responsibility for academic performance, make academic decisions, act as the official source of deadlines, or assess academic work (BR-03 to BR-05; PC-01 to PC-04). No slice in this plan may contradict these boundaries.

---

## 2. Implementation Assumptions and Open Issues

### 2.1 Authority and status of the source documents

- The PRD is the source for requirement wording, acceptance criteria, business rules, edge cases, and open questions. `architecture.md` and ADR-002 to ADR-006 are the source for structure, ownership, and communication.
- Where `AGENTS.md` differs from PRD v1.2, `architecture.md`, or ADR-006, this plan follows the PRD/architecture/ADRs **and flags the difference** rather than silently reconciling it (AGENTS.md §11, step 5). All such differences are listed in Appendix A and must be cleared under gate **G-14** before Stage 4 work on the affected slices.
- Where `AGENTS.md` states a behavior as decided that the PRD still lists as open (e.g., completed tasks excluded from priority/scheduling), this plan treats the behavior as **open** and gates it (see G-08, G-09, G-10). It is not planned as established behavior.

### 2.2 Assumptions extracted from the documents

| ID | Assumption | Source |
|---|---|---|
| A-01 | The system is a Layered Modular Monolith (Presentation, Business, Data Access), deployed initially as a single application. Modules are responsibility boundaries, not separately deployed services. | architecture §4, §10; AGENTS §2 (ADR-001 not supplied) |
| A-02 | Persistence uses one centralized relational database, logically organized by module ownership. The database product is not selected. | ADR-002 |
| A-03 | Operations within one domain use database transactions. Cross-module dependent updates use events and eventual consistency; no distributed transactions. | ADR-002, ADR-005 |
| A-04 | One role exists: **Registered User**, assigned automatically at registration. Users access only their own records. No Administrator role or functionality. Authorization is enforced at protected service interfaces and data retrieval, not only in the UI. | ADR-003; PRD NFR-03, OQ-51 |
| A-05 | Data ownership follows ADR-006 §1: Task Management owns tasks, deadlines, completion status/date, task deletion, Recorded Study Sessions, and total recorded study time; Priority owns Task Priority; Schedule Management owns availability, the Study Schedule, Scheduled Study Sessions, and session deletion; Reminder owns reminder preferences/configurations/pending reminders; Authentication and Authorization owns users, authentication information, and role assignments; External Integration owns staged imported task information and the synchronization log. **AGENTS.md conflicts with the availability allocation and several other allocations; affected work remains gated by G-14 until the source documents are reconciled.** | ADR-006 §1; architecture §8; AGENTS §6; C-01–C-11 |
| A-06 | Domain Rules is a shared Business Layer component (not a module) and the single enforcer of domain invariants. Every state-changing operation is validated by Domain Rules before the Data Access commit. Read-only queries may use Data Access directly, subject to authentication, authorization, and ownership. | ADR-006 §3; architecture §6 |
| A-07 | Domain Rules identifies deadline conflicts and flags them for user review. It does not decide the official deadline. | ADR-006 §3; architecture §6.11 |
| A-08 | Import lifecycle: External Integration stages data → Domain Rules validates data and synchronization outcome → Task Management accepts and becomes owner of the accepted task → External Integration keeps staging records and the sync log. External Integration neither applies business rules nor writes directly to database tables. Only External Integration talks to the external source. | ADR-004; ADR-006 §4 |
| A-09 | Service calls are used for immediate responses, information retrieval, and operation requests. Events notify interested modules after a successful operation. Events carry unique identifiers; failed processing is retried under a predefined policy (interval and maximum attempts set during implementation); events failing past the limit are logged; an authorized operator or maintenance process investigates and initiates recovery. No Administrator role is introduced for this. | ADR-005 |
| A-10 | Reminders are in-app notifications, triggered by a background scheduling mechanism. Delivery while the application is closed depends on the deployment environment's background-processing capability and is not guaranteed. No other delivery channel is assumed. | PRD FR-14; ADR-006 §5; architecture §7, §9 |
| A-11 | Recorded Study Sessions (Task Management; historical) are distinct from Scheduled Study Sessions (Schedule Management; planned). Reminder associations apply to tasks/deadlines and Scheduled Study Sessions only, never to Recorded Study Sessions. | ADR-006 §2, §5 |
| A-12 | After a successful task rescheduling or deletion, Task Management notifies Reminder; after a successful Scheduled Study Session rescheduling or deletion, Schedule Management notifies Reminder (events). | ADR-005; ADR-006 §5; architecture §7 |
| A-13 | Task information flows Task Management → Priority (service call). Schedule Management retrieves task information from Task Management through its service interface. Priority makes priorities available to Schedule Management (architecture §7 "Priority → Schedule Management"). Recorded study time is never an input to Task Priority or deadlines. | architecture §6.10, §7; ADR-005 |
| A-14 | Priority data is persisted (ADR-002 lists priorities among stored data); the owner is Priority. | ADR-002 Context; ADR-006 §1 |
| A-15 | The only task-creation path documented as supported is import followed by acceptance (A-08). `AGENTS.md` states manual task creation is not supported; the PRD defines "Manual Task Entry" in its glossary but has no functional requirement for it (see C-10, OI-01). No manual-entry slice is planned. During development, test fixtures place tasks into Task Management through the same accept-validated-task interface used by import. | AGENTS §1; PRD §3; ADR-004 |
| A-16 | No programming language, framework, database product, hosting platform, authentication mechanism or provider, event technology, background-processing technology, or test framework is established. None is chosen in this plan. | architecture §10; AGENTS §7 |
| A-17 | No repository was supplied. Before each Stage 4 slice, the implementing agent must inspect the actual repository and follow its existing structure, naming, and test conventions (AGENTS §9). | AGENTS §9 |
| A-18 | The slice priorities (Section 4) are **planning proposals** based on dependency order, PRD scope, and risk. The PRD does not assign priorities to requirements. | This plan |

### 2.3 Decision gates (unresolved issues that affect implementation)

A slice listed under "Blocks" must not implement the affected behavior until the gate is decided through the project's review process and the source document is updated. Where a slice can proceed without the gated part, the slice's acceptance criteria say so.

| Gate | Unresolved matter | PRD / document references | Blocks |
|---|---|---|---|
| G-01 | Technology selections: language, framework, database product, hosting/deployment, background-processing mechanism, event mechanism, test framework. Must be proposed to and approved by the team. | ADR-002; architecture §10, §13; AGENTS §7, §10 | S01 (start), S04, S18, S26, all slices indirectly |
| G-02 | Authentication mechanism, password/credential handling, session management, any external provider. | ADR-003; NFR-03; OQ-28 | S02 |
| G-03 | External academic source selection and feasibility; external authentication method. | OQ-01, OQ-05; EC-11; FR-01 | S10, S11, S12 |
| G-04 | Import behavior: duplicates, completeness determination, cancelled/disappearing imported tasks, outdated-information communication, partial updates and retries. | OQ-02, OQ-03, OQ-04, OQ-06, OQ-07; EC-02, EC-10, EC-12 | S10 (duplicates), S11 (completeness, partial), S12 |
| G-05 | Prioritization rules: exact BR-01 rules, equal-deadline handling, tasks without deadlines, representation of unclear outcomes. | BR-01; OQ-08, OQ-14, OQ-15, OQ-16; EC-03, EC-05 | S05 (ordering of undated tasks), S07 |
| G-06 | Deadline changes and conflicts: what is a valid change; what qualifies as a conflict; disputed values; update timing relative to review; effect of conflicts on priority/scheduling. | OQ-09 to OQ-13, OQ-18; EC-04 | S08 (validity), S09, S12 |
| G-07 | Scheduling rules: the "agreed scheduling rules" referenced by FR-06/07/09 are **not contained in any supplied document**; availability data format; missing/outdated availability, insufficient time, overlaps, missed sessions, automatic vs user-approved adjustment, preserved session details, FR-07 vs FR-09 distinction. | FR-06, FR-07, FR-09; OQ-17, OQ-19 to OQ-25; EC-06 to EC-09, EC-13 | S13 (availability format), S14, S15, S16 |
| G-08 | Task completion: default list view and filter options; whether Completed tasks participate in priority/schedule generation; completion-date behavior when reverted; handling of already scheduled sessions when a task is Completed. | OQ-35, OQ-36, OQ-37; EC-15, EC-16 | S06, S07, S14 |
| G-09 | Reminders: reminder-time choices (preset/custom) and multiple reminders per event; passed reminder times; reminders for Completed tasks; delivery-failure handling; verification of the selected deployment's background-processing capability. | OQ-38, OQ-39, OQ-40, OQ-41, OQ-42; EC-17, EC-18, EC-19, EC-26 | S17, S18 |
| G-10 | Study Timer: concurrent timers; interrupted timers (browser closed/connection lost); correction/deletion/manual creation of Recorded Study Sessions; timer behavior on Completed/deleted tasks; relation to Scheduled Study Sessions; date for sessions spanning midnight. | OQ-44 to OQ-49; EC-20 to EC-22, EC-24 | S20, S21, S22 |
| G-11 | What happens to Recorded Study Sessions when their task is deleted. | OQ-47; EC-23; FR-16 note | S23 |
| G-12 | Backup/recovery and event-retry parameters: backup frequency and retention, failure/data-loss scenarios covered, recovery verification, retry interval, maximum attempts. | NFR-04; OQ-29, OQ-30; ADR-002, ADR-005; PRD §10.10 | S04 (retry values), S26 |
| G-13 | Quality targets and verification procedures: supported browsers/versions, security verification, response-time targets, availability target and measurement, partial-sync test approach, usability target. | NFR-01, 02, 03, 05, 06; OQ-26 to OQ-28, OQ-31 to OQ-34; EC-14 | S25 (usability target), S27 |
| G-14 | Reconcile all cross-document conflicts C-01 to C-11 in Appendix A, including the availability and deadline-conflict ownership conflicts, and decide the manual-task-entry gap (OI-01). Update the authoritative PRD/architecture/ADR/AGENTS documents through team review before implementing affected behavior. | PRD v1.2; architecture; ADR-004; ADR-006; AGENTS §11; Appendix A | Start of Stage 4 for all affected slices |
| G-15 | User-visible behavior when a cross-module event is delayed or fails, and the operational recovery procedure. | EC-25; PRD §10.10; ADR-005 | S04 (user-visible part), S19, S23, S24, S26 |

### 2.4 Additional open issues found while planning

These are matters the supplied documents do not settle. They are **not** decided here.

| ID | Open issue | Affects |
|---|---|---|
| OI-01 | **No documented way to create tasks other than import.** If external import proves infeasible (G-03), the product has no task source. The PRD glossary defines Manual Task Entry; no FR supports it; ADR-004 says manual entry "may remain a complementary way to add tasks"; AGENTS.md says it is not supported. Team decision needed. | S05, S10 |
| OI-02 | **Who initiates a deadline change** (user edit, imported-update, or both) is not stated in FR-03 / Flow 3. This plan covers user-initiated change in S08 and import-initiated change in S12; confirmation needed. | S08, S12 |
| OI-03 | **How Schedule Management learns of deadline/priority changes** is not specified (architecture lists events only toward Reminder). This plan assumes only the documented service-call paths (A-13) and requires confirmation of the trigger mechanism. | S16 |
| OI-04 | **Effect of task deletion on dependent data** is not specified: the task's Priority data (owned by Priority), any Scheduled Study Sessions referencing the task, and an imported task's staging record (a deleted imported task might re-enter on the next update check). Only reminder cancellation is specified. | S23 |
| OI-05 | **Effect of deleting a Scheduled Study Session** on schedule adjustment (does deletion trigger re-adjustment?) is not specified. | S24 |
| OI-06 | **Availability has no standalone requirement ID, and its ownership is inconsistent across documents.** The PRD introduces availability through FR-06/FR-07; ADR-006 assigns it to Schedule Management; AGENTS.md says ownership is open and incorrectly refers to FR-16 for availability (PRD FR-16 is deletion). Do not implement the ownership allocation until G-14 is cleared and the source documents agree. | S13 |
| OI-07 | **Timer state location** (where a running/paused timer's state is held) is not specified. It interacts with OQ-45 (interrupted timers). | S20, S21 |
| OI-08 | **Operator access to the failed-event log.** ADR-005 requires an "authorized system operator or maintenance process" without an Administrator role; the access mechanism is not defined. | S04 |
| OI-09 | **Architecture diagram direction ambiguity:** the diagram shows both Task→Schedule and Schedule→Task service calls; ADR-005 and §7 describe Schedule→Task retrieval. This plan uses Schedule→Task (A-13). | S14 |
| OI-10 | **Final PRD approval is pending**, ADRs are Proposed, and FR-13/FR-15 are pending validation. Any change to these documents may require plan updates. | All |

---

## 3. Vertical Slices

**Slice rules**
- Each slice cuts through the layers it needs (UI → Authentication and Authorization → business module → Domain Rules → Data Access → database) and delivers behavior that can be run and tested. Slices S01 to S04 are **enabling slices**: they deliver verified architectural capability rather than user-visible features, and are tested through integration tests and architecture-conformance checks.
- One slice is implemented per Stage 4 prompt. A slice is never combined with another, and no prompt asks for the full product.
- Behavior covered by an open PRD question is **not** implemented until its gate is decided. Where a slice can deliver without the gated behavior, it does so and states the exclusion.
- Terms follow the PRD glossary (Study Schedule vs Scheduled Study Session vs Study Timer vs Recorded Study Session).

### Phase A — Foundations (enabling)

**S01 — Application foundation and layered walking skeleton**
- *Outcome:* A running single application with Presentation, Business, and Data Access layers, a connected relational database, domain-level transactions, an operation log, a responsive UI shell, and a runnable test harness.
- *Requirements:* NFR-04 (transactions, operation records); NFR-02/PC-06 (responsive shell); ADR-001 (via architecture), ADR-002.
- *Components:* UI shell, Data Access and Persistence, module/Domain Rules placeholders (structure only).
- *Gated by:* G-01.

**S02 — Registration, authentication, and authorization boundary**
- *Outcome:* A user can register (Registered User role assigned automatically), sign in, and reach protected operations only when authenticated and authorized; user-specific record isolation is available to all owning modules.
- *Requirements:* NFR-03; ADR-003; OQ-51 (resolved).
- *Components:* UI, Authentication and Authorization, Data Access.
- *Gated by:* G-01, G-02.

**S03 — Domain Rules validation gateway**
- *Outcome:* A single validation entry point that every state-changing operation passes through before a Data Access commit, with a demonstrable reject-and-do-not-commit path. Individual invariants are added by the slices that need them.
- *Requirements:* Architecture §6.2–6.3; ADR-006 §3; BR-06/BR-07 and import rules (added in their own slices).
- *Components:* Domain Rules, Data Access.
- *Gated by:* none beyond G-01.

**S04 — Cross-module event processing infrastructure**
- *Outcome:* Modules can publish an event after a successful operation and other modules consume it independently, with unique event identifiers, duplicate prevention, retries, failure logging, and processing records.
- *Requirements:* NFR-04; ADR-005; ADR-002 (transaction/event consistency); PRD §10.10.
- *Components:* Event processing, Data Access (event/operation records), Domain Rules (not involved in consumers' persistence).
- *Gated by:* G-01 (event mechanism), G-12 (retry values), G-15 (user-visible behavior), OI-08.

### Phase B — Task core

**S05 — Accept validated tasks and show the task/deadline dashboard**
- *Outcome:* A signed-in user sees their own academic tasks and available deadlines in one dashboard; tasks without deadlines remain visible and are marked as missing deadline information. Tasks enter Task Management only through the accept-validated-task interface (A-15).
- *Requirements:* FR-02; BR-02, BR-04; PC-05; NFR-03; NFR-02.
- *Components:* UI, Authentication and Authorization, Task Management, Domain Rules, Data Access.
- *Gated by:* G-05 (ordering of undated tasks), OI-01.

**S06 — Task completion tracking**
- *Outcome:* The user can mark a task Completed or Incomplete, the completion date is recorded, completed and pending tasks are visually distinct, and the list can be filtered by completion status. Completion never deletes a task or changes its original deadline.
- *Requirements:* FR-13; BR-02, BR-06; PC-05.
- *Components:* UI, Task Management, Domain Rules (BR-06), Data Access.
- *Gated by:* G-08 (default view/filters, completion-date on revert).

**S07 — Task Priority calculation and display**
- *Outcome:* Tasks are given a Task Priority according to deadline proximity (closer deadline → higher priority) and shown in priority order; equal-deadline tasks are not ranked by any unapproved rule.
- *Requirements:* FR-05; BR-01, BR-03; AC-FR-05.1/05.2.
- *Components:* Priority, Task Management (service call), Domain Rules, Data Access, UI.
- *Gated by:* G-05, G-08 (whether Completed tasks participate).

**S08 — Update a task deadline**
- *Outcome:* The user changes a task's deadline; a valid change is accepted, the deadline is updated, and the task's priority position is recalculated. Task Management publishes a "task rescheduled" event for Reminder.
- *Requirements:* FR-03 (AC-FR-03.1); BR-01, BR-02; Flow 3.
- *Components:* UI, Task Management, Domain Rules, Priority (service call), event infrastructure, Data Access.
- *Gated by:* G-06 (what is "valid"), OI-02.

**S09 — Identify and flag deadline conflicts**
- *Outcome:* When a deadline change creates a conflict, Domain Rules identifies it and the affected task is flagged for the user's review. The system does not decide the official deadline.
- *Requirements:* FR-04 (AC-FR-04.1); FR-03 (AC-FR-03.2); BR-04; ADR-006 §3.
- *Components:* Domain Rules, Task Management (flag state/display), UI.
- *Gated by:* G-06 — **cannot start until conflict conditions are approved.**

### Phase C — External import

**S10 — Import: stage, validate, accept**
- *Outcome:* Tasks and available deadlines are retrieved from the external source, staged, validated by Domain Rules, and accepted by Task Management so they appear in the task list; staging records and the synchronization log are owned by External Integration.
- *Requirements:* FR-01 (AC-FR-01.1); Flow 1; ADR-004; ADR-006 §4; BR-02.
- *Components:* External Integration and Synchronization, Domain Rules, Task Management, Data Access, UI.
- *Gated by:* G-03, G-04 (duplicates), G-01.

**S11 — Import failure and incomplete-import reporting**
- *Outcome:* A failed or incomplete import is recorded in the synchronization log, the user is notified, and the import is never shown as successful.
- *Requirements:* FR-01 (AC-FR-01.2, AC-FR-01.3); EC-01; ADR-004; ADR-006 §3.
- *Components:* External Integration, Domain Rules, UI.
- *Gated by:* G-03, G-04 (completeness determination, partial outcomes).

**S12 — Check imported tasks for updates**
- *Outcome:* The system checks imported tasks and deadlines for updates and routes changes through staging and Domain Rules validation before Task Management applies them; unsuccessful updates are not reported as successful.
- *Requirements:* FR-08 (AC-FR-08.1, AC-FR-08.2); Flow 7; EC-10 to EC-12; BR-02.
- *Components:* External Integration, Domain Rules, Task Management (deadline update path from S08, conflict flagging from S09), UI.
- *Gated by:* G-03, G-04, G-06, OI-02.

### Phase D — Study schedule

**S13 — User availability**
- *Outcome:* The user can create, update, and view their own availability information, owned by Schedule Management, for use by the Study Schedule.
- *Requirements:* FR-06 and FR-07 (availability input); ADR-006 §1; OI-06.
- *Components:* UI, Schedule Management, Domain Rules, Data Access.
- *Gated by:* G-07 (availability data format and granularity).

**S14 — Create and view the Study Schedule**
- *Outcome:* The system creates and displays a Study Schedule of Scheduled Study Sessions organized according to deadlines, Task Priority, and availability, under the agreed scheduling rules.
- *Requirements:* FR-06 (AC-FR-06.1, AC-FR-06.2); Flow 5; BR-03; PC-05.
- *Components:* Schedule Management, Task Management (service call), Priority (service interface), Domain Rules, Data Access, UI.
- *Gated by:* G-07, G-08 (Completed tasks), OI-09.

**S15 — Adjust the Study Schedule when availability changes**
- *Outcome:* Updating availability is reflected in the Study Schedule under the agreed adjustment rules; rescheduled sessions publish a "session rescheduled" event for Reminder.
- *Requirements:* FR-07 (AC-FR-07.1, AC-FR-07.2); Flow 6; EC-13.
- *Components:* Schedule Management, Domain Rules, event infrastructure, UI.
- *Gated by:* G-07 (automatic vs user-approved; preserved details; FR-07/FR-09 relationship).

**S16 — Adjust the Study Schedule when deadlines or priorities change**
- *Outcome:* Relevant deadline or Task Priority changes lead to schedule adjustment under the agreed scheduling rules; rescheduled sessions publish the "session rescheduled" event.
- *Requirements:* FR-09 (AC-FR-09.1, AC-FR-09.2); Flow 6.
- *Components:* Schedule Management, Task Management and Priority (service interfaces), Domain Rules, event infrastructure.
- *Gated by:* G-07, OI-03.

### Phase E — Reminders

**S17 — Reminder preferences**
- *Outcome:* The user can enable or disable reminders and configure how far in advance reminders fire for academic deadlines and for Scheduled Study Sessions; pending reminders are created from those settings. Disabled preferences suppress reminders.
- *Requirements:* FR-14 (AC-FR-14.1, 14.2, 14.3, 14.7); Flow 9; BR-08.
- *Components:* UI, Reminder, Task Management and Schedule Management (service interfaces), Domain Rules, Data Access.
- *Gated by:* G-09 (time choices; multiple reminders per event).

**S18 — In-app reminder delivery by background scheduling**
- *Outcome:* Pending reminders trigger in-app notifications at configured times using the background scheduling mechanism; delivery while the application is closed is subject to the deployment's capability.
- *Requirements:* FR-14 (AC-FR-14.4); EC-18, EC-19, EC-26; OQ-38.
- *Components:* Reminder, deployment background-processing capability, UI (in-app notification display).
- *Gated by:* G-01, G-09.

**S19 — Pending reminders follow rescheduled deadlines and sessions**
- *Outcome:* When a task deadline or a Scheduled Study Session is rescheduled, the owning module's event causes Reminder to update the corresponding pending reminder automatically.
- *Requirements:* FR-14 (AC-FR-14.5); BR-08; ADR-005; ADR-006 §5.
- *Components:* Reminder (event consumer), event infrastructure, Task Management and Schedule Management (event producers from S08, S15, S16).
- *Gated by:* G-15.

### Phase F — Study timer and recorded study time

**S20 — Start and stop a Study Timer; save a Recorded Study Session**
- *Outcome:* The user starts a Study Timer for a selected task and stops it; the completed duration and date are saved as a Recorded Study Session owned by Task Management.
- *Requirements:* FR-15 (AC-FR-15.1, 15.3, and the save portion of 15.4); Flow 10; PC-05.
- *Components:* UI, Task Management, Domain Rules (BR-07), Data Access.
- *Gated by:* G-10 (concurrency, interruption, midnight date, Completed/deleted task).

**S21 — Pause and resume a Study Timer**
- *Outcome:* The user can pause and resume a running timer; paused time is excluded from the saved duration.
- *Requirements:* FR-15 (AC-FR-15.2; paused-time portion of AC-FR-15.4).
- *Components:* UI, Task Management, Domain Rules.
- *Gated by:* G-10, OI-07.

**S22 — Total Recorded Study Time per task**
- *Outcome:* The total of saved Recorded Study Session durations is displayed per task, and recorded time is proven not to change Task Priority or deadlines.
- *Requirements:* FR-15 (AC-FR-15.5, AC-FR-15.6); BR-07.
- *Components:* UI, Task Management, Priority (non-influence check), Domain Rules.
- *Gated by:* G-10 (correction/deletion of sessions is out of this slice's behavior).

### Phase G — Explicit deletion

**S23 — Delete a task and cancel its pending reminders**
- *Outcome:* The user can explicitly delete a task; Task Management performs the deletion and, after success, notifies Reminder, which cancels associated pending reminders.
- *Requirements:* FR-16 (AC-FR-16.1, 16.2, 16.3); FR-14 (AC-FR-14.6, task part); BR-08, BR-09; Flow 11.
- *Components:* UI, Task Management, Domain Rules, event infrastructure, Reminder.
- *Gated by:* G-11, G-14 (AGENTS.md states task deletion is unsupported; C-01), G-15, OI-04.

**S24 — Delete a Scheduled Study Session and cancel its pending reminders**
- *Outcome:* The user can explicitly delete a Scheduled Study Session; Schedule Management performs the deletion and, after success, notifies Reminder, which cancels associated pending reminders.
- *Requirements:* FR-16 (AC-FR-16.4, 16.5, 16.6); FR-14 (AC-FR-14.6, session part); BR-08, BR-09; Flow 12.
- *Components:* UI, Schedule Management, Domain Rules, event infrastructure, Reminder.
- *Gated by:* G-14 (AGENTS.md lists session deletion as unresolved; C-02), G-15, OI-05.

### Phase H — Cross-cutting completion and verification

**S25 — Brief guidance for main features**
- *Outcome:* The dashboard provides brief guidance for the main features that exist at that point.
- *Requirements:* NFR-01.
- *Components:* UI.
- *Gated by:* G-13 (measurable usability target, if the team sets one).

**S26 — Scheduled backup, restoration, and reconciliation**
- *Outcome:* Persisted application data is protected by scheduled automated backups; the application database can be restored from the latest valid backup, followed by reconciliation of pending events/operations and verification of dependent module data, without re-applying completed effects.
- *Requirements:* NFR-04; ADR-002; ADR-005; PRD §10.10.
- *Components:* Data Access and Persistence, event infrastructure, External Integration (re-synchronization after restore).
- *Gated by:* G-12, G-15, G-01.

**S27 — Quality verification (compatibility, security, performance, availability)**
- *Outcome:* Documented verification of NFR-02, NFR-03, NFR-05, and NFR-06 against targets and procedures the team has defined, across all implemented slices.
- *Requirements:* NFR-02, NFR-03, NFR-05, NFR-06; PC-06, PC-07; EC-14.
- *Components:* All.
- *Gated by:* G-13 — **NFR-05 and NFR-06 verification cannot be performed until measurable targets exist.**

---

## 4. Slice Priorities and Implementation Order

### 4.1 Priority scale (planning proposal — see A-18)

| Priority | Meaning | Basis |
|---|---|---|
| **P0** | Foundation | Required by every other slice (architecture boundaries, security boundary, Domain Rules gate, events). |
| **P1** | Core product | Directly delivers the primary product purpose: view, prioritize, import, schedule (PRD §1.1, FR-01 to FR-09). |
| **P2** | Supporting scope | In-scope features added in PRD v1.1/v1.2 (completion, reminders, timer, deletion) and recovery (NFR-04). |
| **P3** | Polish | Guidance (NFR-01). |

### 4.2 Implementation sequence

Slices are implemented in the order below. **A slice whose gate is undecided is skipped, not reordered:** the next unblocked slice proceeds and the skipped slice resumes once its gate clears and it passes the pre-start check (Section 8.1). Decision gates should be put to the team early so that blocked slices do not accumulate.

| Order | Slice | Priority | Phase | Blocked by (undecided gates at plan time) |
|---|---|---|---|---|
| 1 | S01 Foundation and walking skeleton | P0 | A | G-01 |
| 2 | S02 Registration, authentication, authorization | P0 | A | G-01, G-02 |
| 3 | S03 Domain Rules validation gateway | P0 | A | — |
| 4 | S04 Event processing infrastructure | P0 | A | G-12 (values), G-15, OI-08 |
| 5 | S05 Accept validated tasks; dashboard | P1 | B | G-05 (undated ordering), OI-01 |
| 6 | S07 Task Priority calculation and display | P1 | B | G-05, G-08 |
| 7 | S08 Update a task deadline | P1 | B | G-06 (validity), OI-02 |
| 8 | S09 Deadline conflict flagging | P1 | B | G-06 |
| 9 | S10 Import: stage, validate, accept | P1 | C | G-03, G-04 |
| 10 | S11 Import failure reporting | P1 | C | G-03, G-04 |
| 11 | S12 Check imported updates | P1 | C | G-03, G-04, G-06, OI-02 |
| 12 | S13 User availability | P1 | D | G-07 |
| 13 | S14 Create and view Study Schedule | P1 | D | G-07, G-08, OI-09 |
| 14 | S06 Task completion tracking | P2 | B | G-08 |
| 15 | S15 Adjust schedule on availability change | P2 | D | G-07 |
| 16 | S16 Adjust schedule on deadline/priority change | P2 | D | G-07, OI-03 |
| 17 | S17 Reminder preferences | P2 | E | G-09 |
| 18 | S18 In-app reminder delivery | P2 | E | G-01, G-09 |
| 19 | S19 Reminders follow rescheduling | P2 | E | G-15 |
| 20 | S20 Start/stop timer; Recorded Study Session | P2 | F | G-10 |
| 21 | S21 Pause/resume timer | P2 | F | G-10, OI-07 |
| 22 | S22 Total Recorded Study Time | P2 | F | G-10 |
| 23 | S23 Delete task; cancel reminders | P2 | G | G-11, G-14, G-15, OI-04 |
| 24 | S24 Delete Scheduled Study Session; cancel reminders | P2 | G | G-14, G-15, OI-05 |
| 25 | S26 Backup, restoration, reconciliation | P2 | H | G-12, G-15 |
| 26 | S25 Brief guidance | P3 | H | G-13 (target, if set) |
| 27 | S27 Quality verification | P2 | H | G-13 |

**Sequencing rationale**
1. **Foundations first (S01–S04).** Every later slice relies on the layered structure, the authentication/authorization boundary (NFR-03), the Domain Rules gate (architecture §6.2), and event infrastructure (ADR-005).
2. **Tasks before everything that consumes them (S05–S09).** Priority, scheduling, reminders, timers, and import all depend on Task Management records. S06 (completion) is P2 and sequenced after the P1 core, but is listed before the schedule adjustments because G-08 also affects S07 and S14.
3. **Import after the task core (S10–S12).** Import feeds Task Management through the same accept interface exercised in S05, and S12 reuses the deadline update (S08) and conflict flagging (S09). Because source feasibility (G-03) is the largest external risk, the **feasibility investigation should run in parallel from the start** (see Section 8.4); the slice order is then a point of integration, not an assumption of feasibility.
4. **Schedule after Priority (S13–S16).** Scheduling needs task information, Task Priority, and availability (A-13).
5. **Reminders after Tasks and Schedule (S17–S19).** Reminder serves both deadlines and Scheduled Study Sessions, and depends on the events emitted by S08, S15, and S16.
6. **Timer after Task Management (S20–S22).** Independent of reminders and schedule; it is sequenced after the P1 core. It precedes deletion so that G-11 (Recorded Study Sessions on task deletion) can be tested against real records.
7. **Deletion after its dependents exist (S23–S24).** Deletion cancels reminders, so it follows the Reminder slices; S23 also follows the timer slices.
8. **Recovery and verification last (S25–S27).** Backup and reconciliation need the event and operation records of all earlier slices; quality verification needs the finished system.

---

## 5. Dependencies

### 5.1 Slice-to-slice dependencies

"Hard" = the slice cannot be delivered without it. "Soft" = a hook or test is deferred until the later slice exists.

| Slice | Hard dependencies | Soft dependencies / notes |
|---|---|---|
| S01 | G-01 | — |
| S02 | S01 | — |
| S03 | S01 | — |
| S04 | S01, S03 | Retry values from G-12 |
| S05 | S01, S02, S03 | Seeding of tasks via accept-validated-task interface (A-15) |
| S06 | S05, S03 | Rule "completion does not delete/alter deadline" is added to Domain Rules here |
| S07 | S05, S03 | S08 (recalculation on change); S06 (G-08 participation); S22 (non-influence proof) |
| S08 | S05, S07, S03, S04 | Event consumed later in S19 |
| S09 | S08, S03 | — |
| S10 | S05, S03, S02 | S11 (failure paths) |
| S11 | S10 | — |
| S12 | S10, S08, S09 | S11 (failure reporting reused) |
| S13 | S02, S03 | — |
| S14 | S13, S05, S07, S03 | S06 (Completed-task participation, G-08) |
| S15 | S14, S04 | Event consumed in S19 |
| S16 | S14, S08, S07, S04 | Event consumed in S19; OI-03 |
| S17 | S05, S14, S03 | S06 (reminders for Completed tasks, G-09) |
| S18 | S17 | G-01 (background processing) |
| S19 | S17, S04, S08 | S15, S16 (session reschedule producers) |
| S20 | S05, S03 | S06 (Completed-task timer behavior, G-10) |
| S21 | S20 | — |
| S22 | S20, S07 | S21 |
| S23 | S05, S04, S17 | S20–S22 (G-11); S10/S12 (OI-04) |
| S24 | S14, S04, S17 | — |
| S25 | S05 | Content reflects only slices that exist |
| S26 | S04 and all persistence-owning slices implemented to date | S10 (re-synchronization after restore) |
| S27 | All implemented slices | G-13 targets |

### 5.2 Slice-to-architecture-component dependencies

| Component (architecture §5) | Slices that depend on it |
|---|---|
| UI | S01, S02, S05–S08, S09, S10–S14, S15–S24 (user-facing slices), S25, S27 |
| Authentication and Authorization | S02 (builds it); S05–S24 (every protected operation) |
| Task Management | S05, S06, S08, S09, S10, S12, S14, S16, S17, S20–S23 |
| Priority | S07, S08, S14, S16, S22 |
| Schedule Management | S13–S16, S17, S19, S24 |
| Reminder | S17–S19, S23, S24 |
| External Integration and Synchronization | S10, S11, S12, S26 (re-sync) |
| Domain Rules | S03 (builds it); every state-changing operation in S05–S24 |
| Data Access and Persistence | S01 (builds it); all persistence; S26 |
| Event processing (ADR-005) | S04 (builds it); S08, S15, S16, S19, S23, S24, S26 |

### 5.3 Dependencies on external or environmental capabilities

| Capability | Needed by | Status |
|---|---|---|
| External academic source and its authentication | S10, S11, S12 | Not selected (G-03) |
| Deployment background-processing capability | S18 (and closed-application behavior, EC-26) | Not selected (G-01, G-09) |
| Database product, event mechanism, authentication mechanism | S01, S02, S04 | Not selected (G-01, G-02) |
| Defined quality targets | S27 | Not defined (G-13) |


---

## 6. Acceptance Criteria and Definition of Done

### 6.1 Acceptance-criteria policy

- The PRD acceptance criteria remain authoritative. This plan maps each functional slice to the exact PRD acceptance-criteria IDs; it does not rewrite their wording.
- A slice is accepted only when its applicable PRD criteria pass and the technical checks below pass.
- Where a PRD criterion depends on an unresolved decision, the slice may implement only the behavior already specified. The gated behavior must remain excluded until the relevant gate is cleared.
- For enabling slices S01–S04, which do not have direct user-facing PRD acceptance criteria, the technical checks below are the acceptance criteria.
- A test must not silently settle an open product question. If expected behavior is not defined, record the test as blocked pending the relevant gate.

### 6.2 Slice acceptance-criteria map

| Slice | PRD acceptance criteria / technical acceptance criteria |
|---|---|
| S01 | **Technical:** application starts from the documented repository run procedure; Presentation, Business, and Data Access boundaries are demonstrably separate; the application connects to the selected relational database; one representative domain transaction commits successfully and rolls back on forced failure; the responsive shell renders at the agreed desktop and mobile viewports; the existing test harness runs. Technology choices remain subject to G-01. |
| S02 | **Technical + NFR-03:** registration assigns the single Registered User role; sign-in establishes an authenticated session; unauthenticated access to a protected operation is rejected; one user's test records cannot be read or changed by another user; authorization is enforced at the protected service/data retrieval boundary, not only by hiding UI elements. Authentication details remain subject to G-02. |
| S03 | **Technical:** a state-changing operation demonstrably invokes Domain Rules before persistence; a rejected operation leaves the stored record unchanged; a permitted operation commits; read-only queries remain subject to authentication, authorization, and ownership. |
| S04 | **Technical:** a successful operation emits one uniquely identified event; the consumer processes it once; replaying the same event does not duplicate its effect; a transient failure is retried; a failure beyond the approved retry limit is logged with enough information for investigation. Retry values and user-visible failure behavior remain gated by G-12/G-15. |
| S05 | AC-FR-02.1, AC-FR-02.2. Also verify that only the authenticated user's accepted task records are shown. Task creation remains limited to the currently documented import/acceptance path until OI-01 is decided. |
| S06 | AC-FR-13.1 through AC-FR-13.6. Default list view, reversion date behavior, and effects on priority/schedule/reminders remain gated by G-08/G-09. |
| S07 | AC-FR-05.1, AC-FR-05.2. Do not rank equal-deadline tasks using an unapproved rule; missing-deadline and Completed-task handling remain gated. |
| S08 | AC-FR-03.1. Also verify that a successful change triggers the documented downstream notification path; do not decide what constitutes a valid change without G-06. |
| S09 | AC-FR-03.2, AC-FR-04.1. Do not begin conflict classification until G-06 defines conflict conditions. |
| S10 | AC-FR-01.1. Also verify staged imported data is validated before Task Management accepts it and that module ownership boundaries are respected. |
| S11 | AC-FR-01.2, AC-FR-01.3. Failure and incomplete outcomes must not be represented as successful imports. |
| S12 | AC-FR-08.1, AC-FR-08.2. Updated data must pass through staging and Domain Rules before acceptance; unresolved partial-update and cancellation behavior remains gated. |
| S13 | **Technical:** the authenticated user can create, update, and retrieve only their own availability records through Schedule Management's approved ownership/interface. Do not start until G-14 resolves the ownership conflict and G-07 approves the data format/granularity. |
| S14 | AC-FR-06.1, AC-FR-06.2. The generated Study Schedule must use only approved deadline, priority, and availability rules; unresolved schedule behavior remains gated. |
| S15 | AC-FR-07.1, AC-FR-07.2. Verify reminder-update events for successfully rescheduled sessions when the relevant event behavior is approved. |
| S16 | AC-FR-09.1, AC-FR-09.2. Verify the agreed deadline/priority change triggers the approved schedule-adjustment behavior; the trigger mechanism remains gated by OI-03/G-07. |
| S17 | AC-FR-14.1, AC-FR-14.2, AC-FR-14.3, AC-FR-14.7. Do not implement reminder-time choices or multiple-reminder behavior until G-09 is cleared. |
| S18 | AC-FR-14.4. Verify in-app notification delivery at the configured time in the selected deployment; closed-application behavior must be tested only against verified deployment capability. |
| S19 | AC-FR-14.5. Verify pending reminders update after successful task-deadline and Scheduled Study Session rescheduling events. |
| S20 | AC-FR-15.1, AC-FR-15.3, and the applicable save portion of AC-FR-15.4. Do not implement timer concurrency, interruption recovery, or Completed/deleted-task behavior until G-10 is cleared. |
| S21 | AC-FR-15.2 and the paused-time portion of AC-FR-15.4. Verify paused time is excluded from the saved duration. |
| S22 | AC-FR-15.5, AC-FR-15.6. Verify saved recorded time is displayed per task and does not modify Task Priority or deadlines. |
| S23 | AC-FR-16.1, AC-FR-16.2, AC-FR-16.3, plus AC-FR-14.6 for task reminders. Do not begin until G-11/G-14/G-15 and OI-04 are resolved for the affected behavior. |
| S24 | AC-FR-16.4, AC-FR-16.5, AC-FR-16.6, plus AC-FR-14.6 for Scheduled Study Session reminders. Do not begin until G-14/G-15 and OI-05 are resolved. |
| S25 | **NFR-01:** the dashboard contains brief guidance for each main feature that has actually been implemented; guidance does not describe unavailable or gated behavior as available. Any measurable usability target remains subject to G-13. |
| S26 | **NFR-04 / technical:** an automated backup is created according to the approved schedule; a restoration from the latest valid backup succeeds in a test environment; pending events/operations are reconciled; already-applied effects are not duplicated; dependent module data is verified. Backup frequency, retention, and recovery coverage remain subject to G-12. |
| S27 | **NFR-02, NFR-03, NFR-05, NFR-06:** produce recorded test evidence against team-approved browser, security, response-time, and availability targets. Do not claim pass/fail against targets that have not been defined. |

### 6.3 Cross-slice definition of done

A slice is complete only when all applicable items are satisfied:

1. Its scope is limited to the slice outcome and approved requirements.
2. Its dependencies and decision gates have been checked; unresolved gates are not bypassed.
3. Its implementation respects the layered architecture, module ownership, service interfaces, Domain Rules, authentication/authorization, and Data Access boundaries.
4. Applicable PRD acceptance criteria and technical checks have passing evidence.
5. Relevant failure paths and edge cases specified for that slice are tested.
6. No unrelated feature, unapproved technology, or undocumented business rule has been introduced.
7. Existing project tests and validation commands have been run where available; results are reported accurately.
8. Documentation and traceability are updated if the implementation reveals a changed dependency, decision, or requirement interpretation.
9. The slice status is updated in Section 7 and the plan history is updated in Section 9.

---

## 7. Slice Status and Progress Tracking

### 7.1 Initial status baseline

The supplied materials contain a plan draft and source documents, but no implementation repository or evidence that any slice has been implemented and accepted. Therefore every slice is recorded as **Not Started** at this baseline. This is a planning status, not a claim about work that may have happened outside the supplied materials.

Allowed statuses:
- **Not Started** — no implementation work has been accepted.
- **In Progress** — implementation has begun but the definition of done is not met.
- **Blocked** — work cannot proceed because a named gate, dependency, or source-document decision is unresolved.
- **Implemented — Pending Validation** — code exists, but acceptance evidence is incomplete.
- **Complete** — all definition-of-done checks pass and evidence is recorded.

| Slice | Initial status | Status note / blocker to check before starting |
|---|---|---|
| S01 | Not Started | G-01 technology selection |
| S02 | Not Started | S01; G-01 and G-02 |
| S03 | Not Started | S01; G-01 |
| S04 | Not Started | S01/S03; G-01, G-12, G-15, OI-08 |
| S05 | Not Started | S01–S03; G-05 and OI-01 |
| S06 | Not Started | S03/S05; G-08 and G-14 where AGENTS conflict applies |
| S07 | Not Started | S03/S05; G-05, G-08, G-14 |
| S08 | Not Started | S03/S05/S07/S04; G-06 and OI-02 |
| S09 | Not Started | S08; G-06 and G-14 (conflict-identification ownership) |
| S10 | Not Started | S02/S03/S05; G-03/G-04 and G-14 |
| S11 | Not Started | S10; G-03/G-04 |
| S12 | Not Started | S08–S10; G-03/G-04/G-06 |
| S13 | Not Started | G-07 and G-14 (availability ownership) |
| S14 | Not Started | S05/S07/S13; G-07/G-08 and OI-09 |
| S15 | Not Started | S14/S04; G-07 and G-14 |
| S16 | Not Started | S08/S14/S04; G-07 and OI-03 |
| S17 | Not Started | S05/S14; G-09 and G-14 (completed-task reminder conflict) |
| S18 | Not Started | S17; G-01/G-09 |
| S19 | Not Started | S17/S04/S08; G-15 |
| S20 | Not Started | S05/S03; G-10 and G-14 (timer concurrency/recovery conflicts) |
| S21 | Not Started | S20; G-10 and OI-07 |
| S22 | Not Started | S20/S07; G-10 |
| S23 | Not Started | S05/S04/S17/S20–S22; G-11/G-14/G-15 and OI-04 |
| S24 | Not Started | S14/S04/S17; G-14/G-15 and OI-05 |
| S25 | Not Started | S05; G-13 if a measurable usability target is required |
| S26 | Not Started | S04 and persistence-owning slices; G-01/G-12/G-15 |
| S27 | Not Started | All implemented slices; G-13 |

### 7.2 Updating status

At the end of each implementation slice, update its status and add a short evidence note (for example, test name/result, acceptance-criteria IDs passed, or the reason it remains blocked). Do not mark a slice Complete solely because code has been generated.

---

## 8. Execution Controls and Stage 4 Handoff

### 8.1 Pre-start check for every slice

Before asking an AI coding agent to implement a slice:

1. Read the current `plan.md`, `PRD.md`, `architecture.md`, `AGENTS.md`, and relevant ADRs from the repository.
2. Confirm the slice's hard dependencies are complete.
3. Check each gate and open issue listed for the slice. If unresolved, skip the slice or implement only its explicitly unblocked portion.
4. Confirm G-14 has been cleared for any slice affected by Appendix A conflicts.
5. Inspect the actual repository structure, existing code, tests, and run commands. Do not assume a language, framework, or folder structure from this plan.
6. Give the agent only one slice and its acceptance criteria at a time.
7. Require the agent to report changed files, requirements/acceptance criteria addressed, tests run and results, remaining issues, and proposed plan updates.

### 8.2 Stage 4 prompt boundary

Each implementation prompt must:
- Name exactly one slice ID and its outcome.
- Identify relevant PRD acceptance-criteria IDs and technical checks from Section 6.
- Identify dependencies, gates, and excluded behavior.
- Require compliance with AGENTS.md and the applicable ADRs.
- Prohibit implementation of unresolved behavior or additional features.
- Require tests for the approved behavior and explicit reporting of anything blocked.
- Ask the agent to update the slice status only when evidence supports the new status.

### 8.3 Change control during implementation

Update this plan when:
- A gate is resolved or a source document changes.
- A dependency or implementation order changes.
- A slice is split, combined, deferred, or descoped by an approved team decision.
- Repository inspection reveals a material implementation constraint.
- An acceptance criterion is clarified or its status changes.
- A new cross-document conflict or material open issue is discovered.

A plan update does not itself approve a requirement or architecture decision. Update the authoritative PRD, architecture, ADR, or AGENTS document through the team's review process first, then reflect the approved change here.

### 8.4 Parallel work and feasibility investigation

The external academic source feasibility investigation (G-03) may run in parallel with foundation work because it is an investigation, not implementation of S10–S12. Record the candidate source, available access method, authentication constraints, permitted data, rate/usage limits if known, and a feasibility conclusion for team review. Do not integrate with a source until the team approves it.

Decision gates may be investigated in parallel, but implementation slices must still respect their hard dependencies and unresolved blockers. Parallel investigation does not authorize parallel implementation of dependent slices.

---

## 9. Plan History and Version Control

| Version | Date | Change | Status |
|---|---|---|---|
| v0.1 | 2026-11-20 | Initial plan draft supplied for validation; contained Sections 1–5.3 only. | Superseded |
| v0.2 | 2026-11-20 | Validated planning baseline: completed acceptance-criteria mapping, initial slice-status baseline, execution controls, plan history, and cross-document conflict register; clarified unresolved conflicts and gates without deciding them. | Current |

Preserve this file as `plan.md` in the working repository. Before the next material revision, retain the current version as `plan-v02.md` (or preserve an equivalent immutable Git commit/tag) and then update `plan.md`. Continue with `plan-v03.md`, etc., for later versions. Do not overwrite the only historical copy.

---

## Appendix A — Cross-Document Conflict Register

The following are validation findings, not decisions. **G-14 remains open** until the project team reconciles the relevant source documents and updates them through the agreed review process. This plan does not choose which conflicting behavior to implement.

| ID | Conflict | Source statements | Planning treatment / affected work |
|---|---|---|---|
| C-01 | Task deletion | PRD v1.2 FR-16 explicitly supports task deletion and AC-FR-16.1–16.3; ADR-006 assigns task deletion to Task Management. AGENTS.md §§1, 3 and 8 state task deletion is not supported. | Treat PRD/ADR-006 as the recorded feature scope for planning, but do not implement until G-14 is cleared. S23 blocked. |
| C-02 | Scheduled Study Session deletion | PRD v1.2 FR-16 explicitly supports deletion and AC-FR-16.4–16.6; ADR-006 assigns deletion to Schedule Management. AGENTS.md §§1 and 3 says deletion is unresolved/not supported. | S24 blocked until G-14; do not silently choose. |
| C-03 | Reminder delivery channel | PRD v1.2 FR-14 and ADR-006 specify in-app notifications with background scheduling; AGENTS.md §1 and Reminder Module section specify browser notifications. | Plan uses in-app notifications as the PRD/ADR-006 wording, but S17–S19 must not implement the delivery channel until G-14 confirms the source documents agree. |
| C-04 | Reminders for Completed tasks | PRD OQ-41 leaves pending reminders for Completed tasks open; AGENTS.md says completing a task cancels its pending academic-deadline reminders. | Keep behavior open under G-09. Do not implement automatic cancellation on completion without an approved source update. |
| C-05 | Completed tasks in Task Priority | PRD OQ-36 leaves participation in priority calculations open; AGENTS.md Priority/Domain Rules sections say Completed tasks are excluded. | Keep behavior open under G-08. S07 must not apply the exclusion until the team resolves the conflict. |
| C-06 | Completed tasks in Study Schedule | PRD OQ-36 leaves participation in schedule generation open; AGENTS.md Schedule/Domain Rules sections say Completed tasks are excluded. | Keep behavior open under G-08. S14–S16 must not apply the exclusion until the team resolves the conflict. |
| C-07 | Concurrent Study Timers | PRD OQ-44 asks whether multiple timers may run simultaneously; AGENTS.md says multiple timers for different tasks are supported. | Keep concurrency open under G-10. S20/S21 must not assume concurrent timers until resolved. |
| C-08 | Timer recovery after interruption | PRD OQ-45 leaves browser-closure/connection-loss behavior open; AGENTS.md requires timer state and elapsed-time recovery. | Keep recovery open under G-10. Do not implement recovery as an approved requirement until resolved. |
| C-09 | User availability ownership | ADR-006 §1 assigns user availability to Schedule Management; AGENTS.md §6 says ownership is open and must not be assigned without an architecture/ADR update. | Treat ownership as conflicting, not settled. S13 remains blocked by G-14 and G-07 until architecture/AGENTS are reconciled. |
| C-10 | Manual task creation | PRD glossary defines Manual Task Entry but no FR specifies it; ADR-004 says manual entry may remain complementary; AGENTS.md says manual task creation is not supported. | Do not add a manual-entry slice. Keep OI-01 open; decide whether import is the only task source before S05/S10. |
| C-11 | Deadline-conflict identification ownership | ADR-006 §3 assigns conflict identification to Domain Rules; AGENTS.md §3 says architecture does not assign ownership and instructs agents not to assign it without approval. | Keep S09 blocked by G-14/G-06 until architecture/AGENTS and ADR-006 agree. |

### Appendix A.1 — Source-document status and missing artefact

- `final-prd.md` is PRD v1.2 updated draft; final approval remains pending. FR-13 and FR-15 retain their recorded pending-validation status unless the team separately approves them.
- The supplied ADRs are marked **Proposed**. This plan does not describe them as finally approved.
- `ADR-001-architecture-style.md` was not supplied with the source set. The Layered Modular Monolith and single-application deployment are taken from `architecture.md` and AGENTS.md only. Obtain ADR-001 before changing or claiming its full rationale/alternatives.
- The plan's status baseline is based only on the supplied documents; no implementation repository or accepted implementation evidence was supplied.
