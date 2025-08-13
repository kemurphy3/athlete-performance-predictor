# MULTI-TENANT PLATFORM IMPLEMENTATION GUIDE

## CURSOR IMPLEMENTATION PROMPT

Build a multi-tenant fitness platform with OAuth integrations, dedup engine, web dashboard, and AI chat. Transform the existing single-athlete codebase into a production-ready SaaS.

### GAPS & RISKS (RESOLVE FIRST)

**Must-Have (Missing)**
1. **Data retention limits** - Test: Auto-delete after 730 days unless user opts for longer
2. **Provider rate limit handling** - Test: Graceful degradation at 80% quota with user alerts
3. **Concurrent sync conflicts** - Test: Parallel syncs don't corrupt; last-write-wins with conflict log
4. **BLOCKED: 3rd-party passwords** - Never collect. OAuth-only. Mark providers without OAuth as unsupported
5. **Webhook signature validation** - Test: Reject unsigned/invalid Strava webhooks

**Should-Have**
1. **Progressive data loading** - Paginate at 100 records; virtual scroll for 10k+ items
2. **Travel timezone handling** - Store workout timezone; convert display based on user pref
3. **Recovery source precedence** - WHOOP > Oura > Garmin for HRV/sleep
4. **Chat token budgets** - 4k context window; sliding window pruning
5. **Export format compliance** - Support TCX/FIT/GPX exports

### ARCHITECTURE

**Services:**
- API: FastAPI with async SQLAlchemy, Pydantic v2
- Worker: Celery with Redis broker, priority queues
- Frontend: Next.js 14 with TypeScript, TanStack Query
- Database: Postgres 15 with row-level security
- Cache: Redis for sessions, summaries, rate limits
- Storage: S3-compatible for exports, backups

**Modules:**
```
src/
  auth/          # Argon2id, JWT with rotation, OAuth flows
  connectors/    # Per-provider OAuth + sync logic
  dedup/         # Merge engine with field-level provenance
  models/        # SQLAlchemy + Pydantic schemas
  api/           # FastAPI routes with tenant isolation
  workers/       # Celery tasks for sync, analysis
  chat/          # LLM router with tool/RAG/web fallback
  frontend/      # Next.js dashboard
tests/           # Pytest with 90% coverage target
```

### DATA MODELS

```python
# Core entities with tenant isolation
User: id, email, password_hash, tenant_id, created_at, mfa_secret
Athlete: id, user_id, name, profile_data, settings
Source: id, athlete_id, provider, oauth_tokens_encrypted, last_sync, status
Workout: id, athlete_id, source_id, external_ids[], start_time_utc, sport, metrics{}, provenance{}, quality_score
BiometricReading: id, athlete_id, source_id, date, type, value, unit, confidence
SyncJob: id, source_id, status, started_at, completed_at, error_details

# Dedup keys
DeduplicationKey: workout_hash(external_id + start_time + duration + sport)
```

### API ENDPOINTS

```
POST   /auth/register         # Email/password with Argon2id
POST   /auth/login           # Returns JWT + refresh token
POST   /auth/magic-link      # Send 6-digit code via email
GET    /auth/oauth/{provider}/authorize
GET    /auth/oauth/{provider}/callback

GET    /api/sources          # List connected sources
POST   /api/sources/{provider}/connect
DELETE /api/sources/{id}     # Revoke + delete data
POST   /api/sources/{id}/sync # Trigger manual sync

GET    /api/workouts         # Paginated, filtered by date/sport/source
GET    /api/workouts/{id}    # Full details with provenance
PUT    /api/workouts/{id}    # Manual edits with audit log

GET    /api/biometrics       # HRV, weight, sleep trends
GET    /api/analysis/load    # ACWR, TRIMP, TSS calculations

POST   /api/chat             # AI analysis with 60s timeout
GET    /api/chat/history     # Previous conversations

POST   /api/export           # Generate CSV/Parquet/TCX
DELETE /api/account          # Full GDPR deletion
```

### SYNC JOBS

```python
@celery.task(bind=True, max_retries=3)
def sync_source(self, source_id):
    # 1. Check rate limits (Redis counter)
    # 2. Refresh OAuth token if needed
    # 3. Fetch delta since last_sync with pagination
    # 4. Normalize units, timezones
    # 5. Run dedup with field precedence
    # 6. Store with provenance tracking
    # 7. Update last_sync, clear cache
    # 8. Handle failures with exponential backoff
```

### DEDUPLICATION ENGINE

```python
def deduplicate_workout(new_workout, existing_workouts):
    # Match by: external_id exact, time window ±5min, duration ±5%, sport match
    # Precedence: Garmin > Strava > Withings > Oura > WHOOP > HealthKit
    # Field-level merge: power from Garmin, GPS from Strava, etc
    # Track provenance per field for explainability
    # Return merged workout with conflict log
```

### AI CHAT IMPLEMENTATION

```python
async def handle_chat(query: str, athlete_id: str) -> ChatResponse:
    # 1. Try domain tools (< 2s)
    tools_result = await run_analysis_tools(query, athlete_id)
    if tools_result.confidence > 0.8:
        return format_response(tools_result)
    
    # 2. RAG over athlete summaries (< 5s)
    rag_result = await search_athlete_context(query, athlete_id)
    if rag_result.confidence > 0.7:
        return format_response(rag_result, citations=rag_result.sources)
    
    # 3. Web search with 60s cap
    if FEATURE_WEB_SEARCH_ENABLED:
        with timeout(60):
            web_result = await search_web(query)
            if web_result:
                return format_response(web_result, citations=web_result.urls)
    
    # 4. Fallback
    return ChatResponse(
        text="I don't know the answer to that question.",
        confidence=0.0,
        tools_used=["domain", "rag", "web"]
    )
```

### SECURITY REQUIREMENTS

1. **OAuth tokens**: Encrypt with Fernet, store key in env
2. **Tenant isolation**: Every query includes `WHERE athlete_id IN (user's athletes)`
3. **Session security**: Secure, HttpOnly, SameSite cookies; 24h expiry
4. **Rate limits**: 100 req/min per user, 10 syncs/hour per source
5. **Audit log**: Track admin actions, exports, deletions
6. **Input validation**: Pydantic for all inputs; SQL injection prevention
7. **CORS**: Whitelist frontend origin only
8. **CSP headers**: Strict policy preventing XSS

### EDGE CASES & ERROR HANDLING

1. **Expired OAuth token**: Auto-refresh; if refresh fails, mark source as needs_reauth
2. **Provider API down**: Exponential backoff with jitter; max 5 retries over 24h
3. **Duplicate workouts**: Merge by precedence; store all external_ids
4. **Unit mismatches**: Normalize to metric; store original_unit field
5. **Clock skew**: Normalize to UTC; detect >24h drift and flag
6. **Partial data**: Use available fields; mark quality_score lower
7. **PII in logs**: Redact emails, names; use user_id only
8. **Chat timeout**: Hard stop at 60s; return "I don't know"
9. **Empty states**: "Connect a source to get started" CTAs
10. **Webhook replay**: Idempotent processing; track event_id

### TESTS & ACCEPTANCE CRITERIA

**Unit Tests (pytest)**
```python
def test_dedup_exact_match():
    # Two workouts, same external_id -> merge
def test_dedup_fuzzy_match():
    # Same time ±5min, duration ±5% -> merge
def test_token_encryption():
    # Tokens encrypted at rest, decryptable
def test_tenant_isolation():
    # User A cannot see User B's data
def test_unit_conversion():
    # 10mi -> 16.09km, 150lb -> 68.04kg
```

**Integration Tests**
```python
def test_strava_oauth_flow():
    # Mock OAuth endpoints, verify token storage
def test_sync_with_rate_limit():
    # Hit rate limit, verify backoff behavior
def test_webhook_validation():
    # Invalid signature -> 401 response
```

**E2E Tests (Playwright)**
```
- Register -> Connect Strava -> Sync -> View workouts
- Chat "What was my longest run?" -> Get accurate answer
- Export data -> Download CSV with all workouts
- Delete source -> Verify data removed
```

**Load Tests**
- 100 concurrent users, 10k workouts each
- API p95 < 200ms for workout list
- Sync job completes < 5min for 1000 activities
- Chat response < 10s for complex queries

**Chaos Tests**
1. **Tenant isolation breach**: Attempt cross-tenant reads via API fuzzing
2. **Token leakage**: Grep logs for OAuth tokens during high load
3. **Dedup corruption**: Parallel syncs of same athlete, verify no data loss
4. **Clock drift**: Set device time +48h, verify workout placement
5. **Provider cutoff**: Drop connections mid-sync, verify partial success

### COST & LATENCY GUARDRAILS

**Sync Jobs**
- Budget: $0.10/user/month for API calls
- Enforce: Track calls in Redis; pause at 80% monthly quota
- Alert: Email user at 90% quota

**AI Chat**
- Budget: $0.50/user/month for LLM tokens
- Enforce: 4k token context; 100 queries/day limit
- Cache: Common questions for 24h
- Alert: "Daily limit reached" after 100 queries

**Monitoring**
```python
metrics.histogram('sync.duration', duration, tags={'provider': provider})
metrics.increment('chat.fallback_rate', tags={'reason': 'timeout'})
if latency > 10:
    alerts.send('Chat latency exceeded 10s', context)
```

### UNKNOWN UNKNOWNS (MITIGATIONS)

1. **Provider API changes**: Version detection; feature flags for risky endpoints
2. **GDPR audits**: Data flow diagram; retention policy docs; deletion verification
3. **Biometric accuracy**: Disclaimer on all health metrics; links to studies
4. **Timezone database**: Use pytz with auto-updates; fallback to UTC
5. **OAuth provider downtime**: Cached auth for 1h; backup magic links

### IMPLEMENTATION STEPS

1. **Database Migration**
   - Add tenant_id to all tables
   - Create users, athletes, sources tables
   - Add RLS policies
   - Test: No cross-tenant queries possible

2. **Authentication System**
   - Implement Argon2id password hashing
   - JWT with refresh tokens
   - Magic link email flow
   - Test: Register, login, refresh, logout

3. **OAuth Connectors (Strava first)**
   - OAuth flow with PKCE
   - Token encryption with Fernet
   - Refresh token handling
   - Test: Connect, sync, refresh, revoke

4. **Sync Worker**
   - Celery with Redis broker
   - Idempotent sync logic
   - Rate limit checking
   - Test: Queue, execute, retry, fail

5. **Deduplication Engine**
   - Fuzzy matching algorithm
   - Field-level precedence
   - Provenance tracking
   - Test: Exact, fuzzy, conflict cases

6. **API Layer**
   - FastAPI with auth middleware
   - Tenant isolation on all routes
   - Pagination, filtering
   - Test: CRUD with auth, no leaks

7. **Frontend Dashboard**
   - Next.js with TypeScript
   - TanStack Query for caching
   - Chart.js for visualizations
   - Test: Login, view data, sync

8. **AI Chat**
   - Tool router implementation
   - RAG with ChromaDB
   - Web search with timeout
   - Test: Tools, RAG, timeout, fallback

9. **Observability**
   - Structured logging with Loguru
   - Prometheus metrics
   - Sentry error tracking
   - Test: Logs clean, metrics flow

10. **Security Hardening**
    - OWASP scan
    - Penetration test
    - PII audit
    - Test: No vulnerabilities, no PII leaks

### DELIVERABLES

Working multi-tenant platform with:
- User registration and OAuth source connections
- Automatic sync with deduplication
- Web dashboard showing workouts and trends
- AI chat for analysis with citations
- Full test coverage and monitoring
- Production-ready security and privacy

All Must-Have and Should-Have requirements integrated. No 3rd-party passwords. 60s chat timeout with "I don't know" fallback. Chaos tests passing.

## RED TEAM SCENARIOS

### 1. Multi-Tenant Isolation Attack
**Scenario**: Malicious user attempts to access other tenants' data via:
- SQL injection in workout filters
- JWT tampering to change tenant_id
- GraphQL query depth attacks
- Race conditions during user creation

**Detection**: Anomaly detection on access patterns, honeypot data
**Mitigation**: Parameterized queries, JWT signature validation, query depth limits, transaction isolation

### 2. OAuth Token Exfiltration
**Scenario**: Attacker attempts to steal OAuth tokens via:
- Log injection to expose tokens
- Memory dumps during sync operations
- Side-channel timing attacks on encryption
- CSRF on OAuth callback

**Detection**: Log monitoring for token patterns, encryption timing analysis
**Mitigation**: Token redaction in logs, constant-time encryption, state parameter validation

### 3. Deduplication Data Corruption
**Scenario**: Attacker exploits dedup logic to:
- Create phantom workouts via edge cases
- Cause data loss through malicious merges
- DOS via expensive fuzzy matching
- Inject false provenance data

**Detection**: Dedup operation monitoring, data integrity checks
**Mitigation**: Strict validation, merge rollback capability, operation timeouts

### 4. AI Chat Exploitation
**Scenario**: Attacker uses chat to:
- Extract training data via prompt injection
- Bypass medical disclaimer requirements
- Consume excessive compute resources
- Access other users' summaries via RAG

**Detection**: Token usage spikes, prompt pattern analysis
**Mitigation**: Input sanitization, strict medical filters, rate limiting, RAG access controls

### 5. Calorie Estimation Manipulation
**Scenario**: Attacker provides inputs to:
- Generate unrealistic calorie burns
- Exploit formula edge cases (negative values)
- Cause integer overflows
- Create liability via bad recommendations

**Detection**: Statistical anomaly detection on outputs
**Mitigation**: Input bounds checking, output sanity limits, medical disclaimers

## FEATURE FLAGS

```yaml
# Feature flag configuration
flags:
  # Security
  FEATURE_UNSUPPORTED_PASSWORD_GRANT: false  # Never enable in prod
  FEATURE_OAUTH_PKCE: true
  FEATURE_MFA_REQUIRED: false  # Enable for enterprise
  
  # Sync
  FEATURE_WEBHOOK_SYNC: true  # Strava only initially
  FEATURE_BULK_EXPORT: true
  FEATURE_MANUAL_WORKOUT_EDIT: true
  
  # AI
  FEATURE_WEB_SEARCH_ENABLED: false  # Enable after safety review
  FEATURE_ADVANCED_LLM: false  # Use small model by default
  FEATURE_CHAT_HISTORY: true
  
  # Providers
  FEATURE_GARMIN_CONNECT: true
  FEATURE_WHOOP_API: false  # Pending API access
  FEATURE_APPLE_HEALTH: false  # Requires mobile app
```

## MONITORING DASHBOARDS

### System Health
- API latency p50/p95/p99
- Worker queue depth
- Database connection pool
- Redis memory usage
- Error rate by endpoint

### Business Metrics
- Daily active users
- Sources connected per user
- Sync success rate by provider
- Chat satisfaction score
- Data quality scores

### Security Metrics
- Failed auth attempts
- OAuth refresh failures
- Tenant isolation violations
- Rate limit hits
- Suspicious query patterns

## DEPLOYMENT CHECKLIST

### Pre-Launch
- [ ] Security audit complete
- [ ] Load tests passing
- [ ] Chaos tests passing
- [ ] GDPR compliance verified
- [ ] Provider TOS reviewed
- [ ] Backup restore tested
- [ ] Monitoring alerts configured
- [ ] Feature flags set correctly
- [ ] SSL certificates valid
- [ ] DNS configured

### Launch Day
- [ ] Database migrations applied
- [ ] Redis cache warmed
- [ ] Worker queues empty
- [ ] Health checks passing
- [ ] Canary deployment successful
- [ ] Rollback plan ready
- [ ] Support team briefed
- [ ] Status page updated

### Post-Launch
- [ ] Monitor error rates
- [ ] Check provider quotas
- [ ] Review user feedback
- [ ] Analyze performance metrics
- [ ] Update documentation
- [ ] Plan next iteration

## CURSOR USAGE NOTES

To implement this system:

1. Start with the database migration (Step 1)
2. Build auth before any other features
3. Test tenant isolation at every step
4. Use feature flags for all external integrations
5. Implement monitoring from day 1
6. Run chaos tests before each release
7. Keep security patches current
8. Document all provider quirks
9. Cache aggressively but invalidate correctly
10. Plan for 10x growth from launch

This guide should be your north star. When in doubt, prioritize security and data integrity over features.