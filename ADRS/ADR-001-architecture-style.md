# ADR-001: Selection of Architectural Style

**Status:** Proposed

## Context

The Study Management System supports task and deadline management, deadline-conflict identification, task prioritization, Study Schedule management, external integration, reminders, and study-time recording. It must provide clear separation of responsibilities while remaining manageable for the current project scope.

Architectural drivers include maintainability, separation of responsibilities, external integration, data consistency, security, reliability, and browser compatibility.

## Alternatives Considered

1. Traditional Monolithic Architecture
2. Microservices Architecture
3. Layered Modular Monolithic Architecture

## Decision

The proposed architectural style is **Layered Modular Monolithic Architecture**. The application is organized into presentation, business, and data-access layers. Business responsibilities are divided into modules with defined ownership and interfaces. The application is initially deployed as one application.

## Rationale

Traditional Monolithic Architecture was rejected because it provides less explicit modular separation, which could make the system harder to maintain, test, and extend as functionality grows.

Microservices Architecture was rejected because it introduces additional inter-service communication, distributed transaction, deployment, and recovery complexity. That complexity is unnecessary for the current scale and project scope.

Layered Modular Monolithic Architecture was selected because it balances modularity, maintainability, reliability, and development simplicity. It allows the team to isolate responsibilities, including external integration, without introducing independently deployed services or additional infrastructure. A separate External Integration module is a logical module within the monolith, not a separate service.

## Trade-offs / Consequences

- Provides clear separation of presentation, business logic, and data access.
- Supports module-level development and testing.
- Keeps deployment and system management straightforward.
- Requires disciplined module boundaries and service interfaces.
- All modules remain part of one application; a major application-level failure may affect the whole system.
- Independent deployment and scaling of modules are not supported.
