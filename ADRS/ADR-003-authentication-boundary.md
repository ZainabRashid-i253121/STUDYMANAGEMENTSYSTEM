# ADR-003: Authentication and Authorization Boundary

**Status:** Proposed

## Context

NFR-03 requires protected records to be accessible only to authenticated and authorized users while minimizing credential storage. Authentication and authorization responsibilities must be consistent across business modules.

The current project scope is for a single user category. Administrative functionality is not established as a system requirement.

## Alternatives Considered

1. Authentication and authorization implemented separately within each module.
2. A centralized Authentication and Authorization Module.
3. An external authentication service.

## Decision

The proposed decision is to establish a centralized **Authentication and Authorization Module** within the application.

The system will use a single **Registered User** role for the current project scope. The role is automatically assigned when a user registers. Registered users may manage their own tasks, Scheduled Study Sessions, Recorded Study Sessions, and reminders.

Access to user-specific records must be restricted so that a user cannot view or modify another user's private data. A separate Administrator role is outside the current scope. Additional roles may be introduced later if supported by approved requirements.

The specific authentication mechanism, password-handling implementation, and any external provider remain subject to further investigation.

## Rationale

Centralization avoids duplicating authentication and authorization logic across modules and provides a consistent security boundary. A single Registered User role reflects the current product scope without introducing unsupported administrative functionality.

Authorization must be enforced at protected service interfaces and data-retrieval operations, not only by hiding or showing UI features. User-specific record ownership must be checked before returning or modifying a record.

## Trade-offs / Consequences

- Provides a consistent authentication and authorization boundary.
- Reduces duplicated security logic.
- Requires all protected operations to enforce the authenticated user's identity and permissions.
- Requires user-specific record isolation across all owning modules.
- The authentication mechanism, credential-handling procedures, session management, and verification procedures require further specification.
- A future need for additional roles would require an approved scope change and corresponding authorization updates.
