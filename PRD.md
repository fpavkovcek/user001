# Product Requirements Document (PRD)

> Duplicate into your repository's `docs/` folder. Keep narratives concise and traceable to measurable outcomes.

## 1. Metadata
- **Product / Feature Name**: PetPal Frontend, Pet Service, Activity Service, Accessory Service
- **Author(s)**: GitHub Copilot
- **Date**: 2025-11-18
- **Revision**: v1.0
- **Status**: Draft
- **Related Docs**: README.md, backend/pet-service/README.md, backend/activity-service/README.md, infra/cosmos.bicep

## 2. Summary
PetPal needs a cohesive web experience that lets pet owners view, edit, and monitor pets alongside their activity history. This release aligns the React frontend with the Pet Service and Activity Service APIs so users can manage core pet data and log daily activities without touching underlying infrastructure. Success is measured by faster pet onboarding, richer engagement with activity timelines, and improved operational reliability of the services backing the UI.

## 3. Goals & Non-Goals
| Goals | Non-Goals |
| --- | --- |
| Unified dashboard for viewing and editing pet profiles plus recent activities and accessories. | Full e-commerce checkout, payments, or order management. |
| Reliable CRUD APIs for pets, activities, and accessories with Cosmos DB persistence. | Native mobile apps; responsive web is sufficient. |
| Capture meaningful telemetry for pet creation, activity logging, and accessory interactions. | Advanced analytics pipelines or ML-driven recommendations. |
| Provide simple, low-friction validation of accessory demand before deeper investment. | Complex inventory, warehouse, or supplier integrations. |

## 4. Success Metrics
- Reduce average time to create a pet and first activity to <3 minutes (measured via frontend telemetry funnel tracked in Application Insights).
- Achieve P95 latency <500 ms for write operations across services under emulator load tests (measured by load-test scripts owned by the backend team).
- Reach 70% engagement where daily-active users interact with both pets and activities modules (measured via frontend instrumentation dashboards maintained by product analytics).
- Within 60 days of launch, at least 40% of weekly-active users view or search accessories in a session.
- Maintain accessory catalog coverage for at least three common categories per pet type (e.g., food, enrichment, care) with no more than 10% of active items in a low-stock state.
- Reduce median time to identify and resolve low-stock accessory items to <2 working days (from first low-stock signal to being back in a healthy range).

## 5. Users & Personas
| Persona | Needs | Success Criteria |
| --- | --- | --- |
| Household Pet Owner | Quick overview of pet health, edit details, log walks/feeds, discover useful accessories. | Can add a new pet, log an activity, and view at least one relevant accessory suggestion without errors in <6 minutes. |
| Caretaker/Staff | Manage multiple pets, filter by status or date, ensure compliance logs, monitor accessory stock. | Finds any pet, activity, or accessory within 3 search/filter interactions and can identify low-stock items in <1 minute. |
| Clinic/Trainer Partner | Record structured vet/training visits tied to specific pets and recommend appropriate accessories. | Logs specialized activities with notes and timestamps and can reference a small, curated list of related accessories per pet profile. |
| Admin / Inventory Owner | Maintain a simple, accurate catalog of accessories and stock levels. | Can review, adjust, or retire accessory records in bulk without data inconsistencies being reported by staff or caretakers.

## 6. Assumptions & Constraints
- Azure Cosmos DB (NoSQL API) is the authoritative store; emulator is used locally with same schema.
- Frontend auth relies on existing GitHub OIDC integration from workshop assets; no new auth features planned.
- Services run inside container apps; scale-out relies on stateless FastAPI instances with shared Cosmos throughput.
- Regulatory scope limited to demo data (no PII/PHI), so standard workshop security posture applies.

## 7. Specification by Example
| Scenario | Given | When | Then | Automated Test? |
| --- | --- | --- | --- | --- |
| Create pet | User is on dashboard | User submits valid pet form | Pet appears on card list with health metrics | `backend/pet-service/test_api.py` |
| Filter activities | Activities exist for multiple pets | User filters by pet and date | List shows only matching activities in reverse chronological order | Add test to `backend/activity-service` (TBD) |
| Log activity from pet view | Pet detail drawer open | User submits activity modal | Activity timeline refreshes with new entry and success toast | Cypress/UI smoke test (future) |
| Browse accessories | User is on the main dashboard with accessories enabled | User opens the accessories view and filters by type | The list shows only matching accessories with name, type, price, and stock indicators, and pagination where needed | Backend + frontend tests (future) |
| Monitor low stock accessories | Accessories exist with varying stock levels | User applies a "low stock" filter | The system highlights accessories below a defined threshold so that users can quickly identify restocking needs | Backend tests validating filtering logic (future) |
| Maintain accessory catalog | Admin is authenticated with appropriate permissions | Admin creates or updates accessory details | The accessory catalog reflects the change immediately in browse/search results with no duplicate or orphaned entries | Backend tests for create/update/delete (future) |

## 8. Requirements
### Functional
1. Frontend must list pets with summary metrics and allow inline edit/create aligned with Pet Service schema.
2. Frontend must surface an activity timeline per pet and allow logging new activities via Activity Service.
3. Pet Service must expose CRUD endpoints plus search/filter with pagination.
4. Activity Service must support create/read/delete plus filtering by pet, type, and date window.
5. Both services must expose `/health` endpoints that initialize Cosmos resources and report status.
6. Accessory service must support browsing, searching, and basic management of accessories (including type, pricing, and stock level) through backend services.
7. Frontend must present an accessories experience that feels integrated with existing pet and activity workflows (for example, surfacing relevant accessories alongside pet or activity context).

### Non-Functional
- **Performance**: P95 <300 ms for reads, <500 ms for writes at workshop scale across pets, activities, and accessories; monitor RU usage.
- **Security/Privacy**: Enforce HTTPS, store secrets in environment variables or managed identity, validate payloads server-side.
- **Observability**: Structured logs include request id, RU charge, and HTTP status; propagate `traceparent` header end-to-end.
- **Accessibility**: Frontend components meet WCAG 2.1 AA keyboard and contrast requirements.

## 9. UX & Flows
- Wireframes live in `solutions/challenge-06/docs/app-full.png`; they show the dashboard layout referenced above.
- Primary journey: dashboard → create pet → view pet detail → log activity → confirm toast → updated timeline.
- Secondary journey: use filters/search on dashboard to locate specific pets/activities, leveraging query parameters to the services.
- Accessories journey: dashboard → open accessories view (or accessory panel) → browse and filter accessories → view accessory details → note items to acquire or restock.
- Cross-sell journey: from a pet or activity context, surface a small set of relevant accessories (for example, harnesses for dogs with frequent outdoor activities) that users can review without leaving their current flow.

## 9a. Accessories

### Problem & Opportunity
- Today, PetPal focuses on pets and activities but does not help users discover, organize, or reason about accessories that support pet care (toys, food, collars, bedding, grooming, etc.).
- Caretakers and staff often rely on external tools or memory to decide what accessories to use or restock, which leads to inconsistent experiences and missed engagement opportunities.
- By introducing a lightweight accessories capability, PetPal can increase stickiness (more time spent in the product), support operational tasks like stock monitoring, and lay the groundwork for future monetization without committing to full commerce flows.

### Primary Roles & Needs
- **Household Pet Owner**: Wants to quickly see which accessories are relevant for each pet (by type or activity) and to understand basic details like size, price, and whether an item is available.
- **Caretaker/Staff**: Wants a fast way to scan all accessories, filter by type or low-stock status, and ensure they have appropriate items on hand for upcoming activities or stays.
- **Admin / Inventory Owner**: Wants to maintain a simple, accurate catalog of accessories (create, update, retire) and quickly detect low-stock items so they can trigger restocking actions.

### User Stories
- As a household pet owner, I want to browse accessories by type and basic filters so that I can quickly find items that are relevant to my pet without having to leave PetPal.
- As a caretaker/staff member, I want to search and filter accessories (by type, name, and low-stock state) so that I can quickly identify what is available and what needs attention.
- As a user viewing a pet profile, I want to see a small set of suggested accessories tied to that pet’s characteristics or recent activities so that I can discover useful items in context.
- As an admin/inventory owner, I want to create, update, and retire accessories so that the catalog stays accurate and users do not see outdated or incorrect options.
- As an admin/inventory owner, I want to monitor low-stock accessories in a dedicated view so that I can trigger restocking before items become unavailable.
- As a product owner, I want to soft-launch accessories to a subset of users or as an optional dashboard panel so that we can validate demand and interaction patterns before investing in advanced features.

## 10. Dependencies
- Internal: Pet Service (FastAPI), Activity Service (FastAPI), shared Cosmos DB account/emulator, infra scripts in `start.sh`.
- Third-party: Azure Cosmos DB Emulator, GitHub authentication for frontend, Application Insights for telemetry (optional).
- Launch blockers: Verified Cosmos throughput configuration and smoke tests covering create/edit/delete flows.

## 11. Rollout Plan
- **Phase 1 (MVP)**: CRUD for pets, activity logging basic flow, service health checks wired into start scripts.
- **Phase 2 (Beta)**: Add filters, telemetry dashboards, and automated UI smoke tests.
- **Phase 3 (GA)**: Harden accessibility and latency, document runbooks, finalize autoscale thresholds. Feature flag activity validation if cross-service dependency not ready.
- Provide lightweight enablement guide in `docs/` plus update workshop instructions.

## 12. Risks & Mitigations
| Risk | Impact | Likelihood | Mitigation |
| --- | --- | --- | --- |
| Cosmos RU throttling during demos | Slower writes, degraded UX | Medium | Enable retry-after handling on frontend, monitor diagnostics, pre-provision RU burst. |
| Cross-service validation causing cascading failures | Activity logging blocked when Pet Service unavailable | Medium | Implement cached pet metadata or circuit breaker; allow eventual consistency with warning banner. |
| Accessibility gaps in new UI | Users with assistive tech blocked | Low | Include accessibility review in GA checklist and run automated audits. |

## 13. Open Questions
- What auth mechanism should the production frontend use to call the services (API key vs. managed identity gateway)?
- Do we need offline caching for the dashboard to support intermittent connectivity scenarios?
- Should Activity Service enforce pet existence synchronously or accept writes and reconcile later?

## 14. Change Log
| Date | Author | Change |
| --- | --- | --- |
| 2025-11-18 | GitHub Copilot | Initial draft aligned to template for frontend + pet + activity scope. |
