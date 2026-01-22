```markdown
# Service Security Notes

Detail the threat model and controls unique to this service. Align with global requirements from `../../platform/SECURITY.md` and note any deviations.

## Threat Model Snapshot

| Asset | Threat | Mitigation |
| --- | --- | --- |
| **Accessory Data** | Unauthorized access/modification | (Future) AuthZ; Currently public for demo/workshop. |
| **Cosmos DB** | Key leakage | Managed Identity (Production); Env vars (Local). |
| **API** | DDoS / Abuse | Container Apps scaling limits; Cosmos DB RU throttling. |
| **API** | Injection attacks (SQL) | Parameterized queries; Pydantic validation. |
| **Stock Data** | Data manipulation | Input validation (non-negative values); Audit logging. |

## Controls Checklist

### Authentication/Authorization
- [x] **Authentication**: None (Public API for workshop/demo purposes).
- [ ] **Authorization**: Future scope - role-based access for admin operations (create/update/delete).

### Secrets Handling
- [x] **Production**: Managed Identity (Workload Identity) for Cosmos DB access.
- [x] **Local**: `.env` file for Cosmos DB key (file not committed to source control).
- [x] **Key Rotation**: Managed Identity eliminates key rotation concerns in production.

### Data Classification
| Data Type | Classification | Encryption |
| --- | --- | --- |
| Accessory metadata | Internal/Public | Encrypted at rest (Cosmos DB default) |
| Pricing data | Internal | Encrypted at rest (Cosmos DB default) |
| Stock levels | Internal | Encrypted at rest (Cosmos DB default) |

### Transport Security
- [x] **HTTPS**: Enforced for all API endpoints.
- [x] **TLS**: Azure Container Apps handles TLS termination.

### Input Validation
- [x] **Pydantic Models**: All inputs validated with type hints and constraints.
- [x] **Enum Validation**: Type and size fields restricted to valid values.
- [x] **Length Limits**: Name (1-200 chars), description (max 2000 chars).
- [x] **Non-Negative Values**: Price and stock must be >= 0.

## Testing & Monitoring

### Security Scans
- [ ] **SAST**: GitHub Advanced Security (future).
- [ ] **Dependency Scanning**: Dependabot for Python dependencies.
- [ ] **Container Scanning**: Azure Defender for Containers (future).

### Runtime Monitoring
- [x] **Logging**: All operations logged with structured format.
- [x] **Error Tracking**: Exceptions logged with stack traces.
- [x] **Application Insights**: Request tracing, dependency calls, exceptions.

### Alerts
- [ ] **Failed Health Checks**: Alert on repeated 503 responses.
- [ ] **High Error Rate**: Alert on spike in 5xx responses.
- [ ] **RU Throttling**: Alert on Cosmos DB 429 responses.

## Query Security

### SQL Injection Prevention
The service uses dynamic SQL query building for search/filter functionality. Mitigations:

1. **Parameterized Queries**: Values are passed as parameters, not string concatenation.
2. **Enum Validation**: `type` field validated against known values before query.
3. **Pydantic Validation**: All input sanitized through Pydantic models.

### Safe Query Building Pattern
```python
# CORRECT: Build filter list dynamically
filters = []
params = []
if search:
    filters.append("(CONTAINS(c.name, @search) OR CONTAINS(c.description, @search))")
    params.append({"name": "@search", "value": search})

# Build WHERE clause only if filters exist
where_clause = " AND ".join(filters) if filters else ""
query = f"SELECT * FROM c" + (f" WHERE {where_clause}" if where_clause else "")
```

**Note**: The Cosmos DB Emulator does NOT support tautologies like `WHERE 1=1`. The service uses proper list-building patterns instead.

## Exceptions

| Exception | Owner | Expiration | Follow-up Plan |
| --- | --- | --- | --- |
| **Public API** | Backend Team | End of workshop | Implement authentication before production use. |
| **No Rate Limiting** | Backend Team | End of workshop | Add API rate limiting before production deployment. |

## Recommendations for Production

Before deploying to production with real data:

1. **Add Authentication**: Implement Azure AD / OAuth2 authentication.
2. **Add Authorization**: Role-based access control for admin operations.
3. **Enable Rate Limiting**: Protect against abuse.
4. **Audit Logging**: Log all create/update/delete operations with user identity.
5. **Enable Security Scanning**: SAST, dependency scanning, container scanning.
6. **Review Data Classification**: Ensure no sensitive data in accessory records.

```
