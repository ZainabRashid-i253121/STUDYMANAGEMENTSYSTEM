# ADR-004: External Academic Source Integration and Import Staging

**Status:** Proposed

## Context

FR-01 requires support for importing academic tasks and available deadlines from an external source, subject to feasibility investigation. FR-08 requires checking for updates to imported tasks and deadlines. Failed or incomplete imports must not be reported as successful.

The external academic source has not yet been selected. The architecture must isolate external communication and define the lifecycle of imported information before it becomes an accepted application task.

## Alternatives Considered

1. Implement external integration directly inside Task Management.
2. Create a separate External Integration and Synchronization Module.
3. Rely exclusively on manual task entry without external integration.

## Decision

The proposed decision is to create a separate **External Integration and Synchronization Module** within the application.

The module will:
- Communicate with external academic sources.
- Import tasks and check for updates.
- Own and store staged imported task information before it is accepted as an application task.
- Maintain synchronization logs, including attempts, retries, and partial outcomes.
- Report failed or incomplete imports accurately and never present them as successful.

The import lifecycle is:

1. External Integration retrieves and stages source data.
2. External Integration submits staged data and synchronization outcomes to Domain Rules for validation.
3. Domain Rules validates the data against applicable system invariants.
4. After successful validation, Task Management accepts the imported task and becomes the owner of the accepted task record.
5. External Integration retains responsibility for its staging records and synchronization log.

External Integration does not apply business rules or write directly to database tables. The external source and synchronization mechanism will be selected after feasibility investigation.

## Rationale

A separate module isolates external communication from internal task management and provides a clear place for import staging, synchronization, and integration failure handling.

Manual-only entry was rejected as a replacement because it would not satisfy FR-01's requirement to support external task importing, subject to feasibility. Manual entry may remain a complementary way to add tasks; it is not an equivalent substitute for the required integration capability.

## Trade-offs / Consequences

- Separates external integration from internal business logic.
- Defines ownership of staged data before task acceptance.
- Allows Domain Rules to validate imported information before Task Management accepts it.
- Adds a module and service interfaces.
- The system depends on the availability and accessibility of the external source.
- External platform selection, authentication, duplicate handling, partial update behavior, cancellation handling, and retry details remain open.
