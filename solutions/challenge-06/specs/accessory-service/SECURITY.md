# Service Security Notes

Detail the threat model and controls unique to this service. Align with global requirements from `../../platform/SECURITY.md` and note any deviations.

## Threat Model Snapshot

| Asset              | Threat                           | Mitigation                                       |
| ------------------ | -------------------------------- | ------------------------------------------------ |
| **Accessory Data** | Unauthorized access/modification | (Future) AuthZ; Currently public for demo.       |
| **Cosmos DB**      | Key leakage                      | Managed Identity (Production); Env vars (Local). |
| **API**            | DDoS / Abuse                     | Container Apps scaling; Cosmos DB limits.        |

## Controls Checklist
- [x] **Authentication**: None (Public API).
- [x] **Secrets**:
    -   Production: Managed Identity (Workload Identity).
    -   Local: `.env` file (not committed).
- [x] **Data**: Stored in Cosmos DB (Encrypted at rest by default).
- [x] **Transport**: HTTPS enforced.

## Testing & Monitoring
-   **Scans**: GitHub Advanced Security (future).
-   **Monitoring**: Application Insights (requests, exceptions, dependencies).

## Exceptions
-   **Public API**: The service is currently unauthenticated for workshop/demo simplicity.
