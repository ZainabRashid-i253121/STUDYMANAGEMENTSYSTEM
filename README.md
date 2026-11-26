# Study Management System

## 1. Project Overview

The Study Management System is intended to help Ms. Arooj organize academic tasks and deadlines, prioritize tasks according to deadline proximity, and maintain a Flexible Study Schedule that accommodates her available time.

The system is also intended to support task-completion tracking, reminders for academic deadlines and scheduled study sessions, and recording the time spent studying each task. Importing academic tasks and checking imported information for updates are within the documented scope, subject to external-source feasibility.

The system supports organization and planning. It does not take responsibility for academic performance, make academic decisions on the user's behalf, act as the official source of academic deadlines, or assess academic work.

## 2. Intended User

The current PRD identifies Ms. Arooj as the intended user. The architecture and agent guidance describe a single **Registered User** role. Users are intended to access their own protected records. Administrative functionality is not part of the documented product scope.

## 3. Planned Product Capabilities

The following capabilities are documented in `PRD.md`. They describe intended product behavior, not completed implementation.

- Import academic tasks and available deadlines from an external source, subject to feasibility investigation.
- View academic tasks and available deadlines together, including tasks with missing deadline information.
- Update task deadlines and identify deadline conflicts for user review.
- Prioritize tasks according to deadline proximity and the prioritization rules still to be agreed.
- Create, view, and adjust a Study Schedule using deadlines and user availability.
- Create and update availability information used by the Study Schedule.
- Check for updates to imported academic tasks and deadlines.
- Mark tasks as Completed or Incomplete, record completion dates, distinguish completion status in the task list, and filter by status.
- Configure one or more reminders for academic deadlines and Scheduled Study Sessions. The intended delivery channel remains unresolved because PRD FR-14 specifies browser notifications, while `architecture.md` and ADR-006 specify in-app notifications.
- Use a Study Timer for selected tasks, including starting, pausing, resuming, and stopping it.
- Save completed timed study periods as Recorded Study Sessions and display total recorded study time per task.
- Support desktop and mobile browser access within the compatibility scope that remains to be defined.

**Product boundaries:** Manual task creation and task deletion are not supported under the current product scope in PRD v1.2. Completed tasks are retained and keep their original deadlines. Completed tasks are excluded from Task Priority calculations and future Study Schedule generation or adjustment. Whether Scheduled Study Sessions may be deleted remains unresolved under PRD OQ-43. Whether Recorded Study Sessions may be corrected, deleted, or manually created remains unresolved under PRD OQ-46; these capabilities are not assumed to be supported.

## 4. Proposed Architecture

`architecture.md` describes a **Layered Modular Monolithic Architecture**, initially deployed as a single application. The proposed structure separates presentation, business logic, and data-access responsibilities. The architecture describes a centralized relational database and defined internal service interfaces and events for module communication.

**Approval status:** The architecture document and ADR-001 through ADR-006 record the architectural choices as **Proposed**. They must not be represented as finally approved decisions.

### 4.1 Layers and Major Components

| Layer / component | Documented responsibility |
|---|---|
| Presentation Layer / UI | User-facing dashboard and interactions with system capabilities. |
| Business Layer | Contains the business modules and shared Domain Rules component. |
| Authentication and Authorization Module | Centralized authentication, authorization, and protected-access boundary. |
| Task Management Module | Owns accepted academic task records, deadlines, completion status and dates; performs Study Timer operations; owns Recorded Study Sessions and total recorded study time. |
| Priority Module | Task Priority responsibilities. |
| Schedule Management Module | User availability information, Study Schedule, and Scheduled Study Sessions. Whether Scheduled Study Sessions may be deleted remains unresolved in PRD OQ-43. |
| Reminder Module | Reminder preferences, configurations, and pending reminders for academic deadlines and Scheduled Study Sessions; updates pending reminders after rescheduling and cancels pending academic-deadline reminders when a task is marked Completed. The delivery channel is unresolved; see Section 4.4. |
| External Integration and Synchronization Module | Communication with external academic sources, import/update checks, ownership of staged imported information, and synchronization logs. |
| Shared Domain Rules component | Validates state-changing operations and staged imports, enforces documented domain invariants, and identifies potential deadline conflicts for user review. It does not decide official academic deadlines, is not a separate business module, and owns no persistent business records. |
| Data Access Layer | Controlled access to the centralized relational database. |

The architecture distinguishes a **Scheduled Study Session** (a planned session in the Study Schedule) from a **Recorded Study Session** (a completed timed study period). They are separate concepts with different documented ownership: Schedule Management owns Scheduled Study Sessions; Task Management owns Recorded Study Sessions.

### 4.2 Documented Boundaries and Constraints

- The application is proposed to be initially deployed as one application.
- Desktop and mobile browser access is within the product scope.
- External academic-source communication belongs to the External Integration and Synchronization Module.
- Database communication is handled through the Data Access Layer.
- Modules are expected to use defined interfaces rather than access another module's internal implementation or private persistence directly.
- Protected operations pass through the Authentication and Authorization boundary.
- Domain Rules is the shared Business Layer component for validating state-changing operations, validating staged imports, enforcing documented invariants, and identifying potential deadline conflicts for user review. It does not decide official academic deadlines.
- Cross-module dependent updates use events and eventual consistency as described in the proposed architecture and ADRs.
- Reminder delivery is a documented inconsistency: PRD FR-14 specifies browser notifications, while `architecture.md` and ADR-006 specify in-app notifications. This README does not choose between them or claim that both channels are supported. Browser-closed behavior, delivery failures, and retry details also retain the limitations/open questions recorded in the PRD and architecture.

### 4.3 Data Ownership

The proposed architecture and ADR-006 define the following ownership boundaries. These are documented proposed architectural allocations, not finally approved decisions:

| Information | Proposed owner / responsibility |
|---|---|
| Staged imported task information and synchronization logs | External Integration and Synchronization |
| Accepted application task records, deadlines, completion status, and completion dates | Task Management |
| User accounts, authentication information, and role assignments | Authentication and Authorization |
| User availability information, Study Schedule, and Scheduled Study Sessions | Schedule Management |
| Recorded Study Sessions and total recorded study time | Task Management |
| Task Priority | Priority |
| Reminder preferences, configurations, and pending reminders | Reminder |

The imported-task lifecycle is: External Integration stages imported information; Domain Rules validates it; Task Management accepts validated information and owns the resulting application task records. Staged records and synchronization logs remain owned by External Integration.

Domain Rules is a shared Business Layer component, not a business module or persistent-data owner. It validates state-changing operations and staged imports, enforces documented domain invariants, and identifies potential deadline conflicts for user review. It does not decide the official academic deadline or make academic decisions on the user's behalf.

### 4.4 Scope Conflicts and Unresolved Decisions

The following matters are intentionally recorded without inventing a resolution:

- **Task deletion:** Unsupported in the current product scope under PRD v1.2. `architecture.md` and ADR-006 nevertheless describe task deletion responsibilities and related reminder events. The PRD scope is stated here; the conflicting proposed architecture descriptions remain unmodified and require documentation alignment.
- **Scheduled Study Session deletion (PRD OQ-43):** Unresolved. This README does not describe session deletion as either supported or unsupported. The architecture and ADR-006 assign deletion responsibility to Schedule Management, but that proposed behavior is not treated as an approved product capability.
- **Recorded Study Session correction, deletion, and manual creation (PRD OQ-46):** Unresolved. This README does not claim that any of these operations are supported.
- **Reminder delivery channel:** Unresolved due to conflicting documents. PRD FR-14 specifies browser notifications; `architecture.md` and ADR-006 specify in-app notifications. This README does not choose between these descriptions or claim that both are supported.
- **Deadline conflicts:** `architecture.md` and ADR-006 assign Domain Rules responsibility for identifying potential deadline conflicts and flagging them for user review. Domain Rules does not determine the official academic deadline.
- **Other documented open questions:** Reminder behavior when the browser is closed, notification availability, retry limits, and related edge cases remain subject to the PRD's open questions.

**Cross-document alignment note:** `AGENTS (1).md` contains older instructions that conflict with the ownership allocations and Domain Rules responsibility recorded in `architecture.md` and ADR-006. PRD FR-16 also says availability ownership is not assigned, while the proposed architecture and ADR-006 assign it to Schedule Management. The clarifications recorded in this README reflect the resolutions supplied for this README update only. `AGENTS (1).md`, `PRD.md`, `architecture.md`, and the ADRs have not been changed; their remaining inconsistencies must be aligned through the project's document-approval process before implementation guidance is treated as consistent.

## 5. Current Implementation Status

**Implementation has not started.** The project is currently in **Stage 2 — Validate & Plan** of Deliverable 4.

The PRD, architecture, AGENTS guidance, and ADRs describe requirements, proposed architecture, constraints, and instructions for future implementation. They are not evidence that the application or its features have been built.

The following implementation details are therefore not yet verified and are intentionally not specified here:

- Programming language, framework, and their versions.
- Database product and database configuration.
- External academic source and integration technology.
- Authentication provider or implementation mechanism.
- Dependencies and package installation steps.
- Environment variables and configuration values.
- Source-code directory structure.
- Application installation and execution commands.
- Test framework, test commands, and test results.
- Hosting, deployment, and operational instructions.

These sections should be completed only after implementation decisions and repository contents provide verifiable information. No installation, execution, testing, or deployment commands are supplied at this stage.

## 6. Requirements, Architecture, and Agent Documentation

The following files are the current supplied project documents. Their filenames are preserved as they exist in the provided project workspace.

- [`PRD.md`](PRD.md) — product purpose, scope, functional and non-functional requirements, business rules, constraints, main flows, edge cases, open questions, and requirement status.
- [`architecture.md`](architecture.md) — proposed architecture, architectural drivers, components, boundaries, interactions, data responsibilities, constraints, and open decisions.
- [`AGENTS (1).md`](AGENTS%20%281%29.md) — guidance for future AI coding agents, including product intent, architectural boundaries, module responsibilities, dependency rules, invariants, human-approval requirements, and ADR compliance.

### 6.1 Architecture Decision Records

All supplied ADRs are marked **Proposed**.

- [`ADR-001-architecture-style(1).md`](ADR-001-architecture-style%281%29.md) — proposed architectural style.
- [`ADR-002-data-persistence(1).md`](ADR-002-data-persistence%281%29.md) — proposed data persistence, transaction, backup, and recovery approach.
- [`ADR-003-authentication-boundary(1).md`](ADR-003-authentication-boundary%281%29.md) — proposed authentication and authorization boundary.
- [`ADR-004-external-integration(1).md`](ADR-004-external-integration%281%29.md) — proposed external academic-source integration and import staging.
- [`ADR-005-module-communication(1).md`](ADR-005-module-communication%281%29.md) — proposed communication between system modules.
- [`ADR-006-module-responsibilities.md`](ADR-006-module-responsibilities.md) — proposed module responsibilities, Domain Rules, and data ownership.

The PRD is a **Revised Draft (v1.2)**. Its document status says final approval is pending and that FR-13 to FR-16 and related changes remain subject to group validation. Open questions and unresolved decisions remain recorded in the PRD and architecture documents; this README does not resolve them.

## 7. Installation, Execution, Testing, and Deployment

**To be completed after implementation.**

No verified installation, execution, testing, or deployment instructions are available while implementation has not started. Add these instructions only when the project’s actual technology choices, configuration, repository structure, and validated commands are available.
