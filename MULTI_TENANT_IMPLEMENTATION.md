# MULTI-TENANT ADAPTIVE PLATFORM IMPLEMENTATION GUIDE

## CURSOR IMPLEMENTATION PROMPT

Build a multi-tenant fitness platform with OAuth integrations, dedup engine, web dashboard, conversational AI with adaptive intelligence, and real-time workout modification. Transform the existing single-athlete codebase into a production-ready SaaS with intelligent adaptation capabilities.

### CORE PHILOSOPHY: ADAPTIVE INTELLIGENCE

The platform learns from each user interaction to provide increasingly personalized fitness guidance. It adapts to:
- User preferences and communication style
- Life events and schedule changes
- Real-time performance during workouts
- Long-term patterns and progress
- Equipment availability and constraints

### GAPS & RISKS (RESOLVE FIRST)

**Must-Have (Missing)**
1. **Data retention limits** - Test: Auto-delete after 730 days unless user opts for longer
2. **Provider rate limit handling** - Test: Graceful degradation at 80% quota with user alerts
3. **Concurrent sync conflicts** - Test: Parallel syncs don't corrupt; last-write-wins with conflict log
4. **BLOCKED: 3rd-party passwords** - Never collect. OAuth-only. Mark providers without OAuth as unsupported
5. **Webhook signature validation** - Test: Reject unsigned/invalid Strava webhooks
6. **Conversation context limits** - Test: Maintain 10k token context with intelligent pruning
7. **Real-time adaptation safety** - Test: Never exceed user's specified heart rate zones
8. **Privacy-preserving learning** - Test: User preferences never leak across tenants

**Should-Have**
1. **Progressive data loading** - Paginate at 100 records; virtual scroll for 10k+ items
2. **Travel timezone handling** - Store workout timezone; convert display based on user pref
3. **Recovery source precedence** - WHOOP > Oura > Garmin for HRV/sleep
4. **Chat token budgets** - 10k context window with intelligent summarization
5. **Export format compliance** - Support TCX/FIT/GPX exports
6. **Adaptive UI components** - Interface adjusts based on user interaction patterns
7. **Life event detection** - Automatically detect schedule changes from calendar integration

### ARCHITECTURE

**Services:**
- API: FastAPI with async SQLAlchemy, Pydantic v2
- Worker: Celery with Redis broker, priority queues
- Frontend: Next.js 14 with TypeScript, TanStack Query
- Database: Postgres 15 with row-level security, TimescaleDB for time-series
- Cache: Redis for sessions, summaries, rate limits, conversation context
- Storage: S3-compatible for exports, backups, voice recordings
- Real-time: WebSockets for live workout modifications
- AI: Claude API for conversational AI, local models for real-time adaptation

**Modules:**
```
src/
  auth/          # Argon2id, JWT with rotation, OAuth flows
  connectors/    # Per-provider OAuth + sync logic
  dedup/         # Merge engine with field-level provenance
  models/        # SQLAlchemy + Pydantic schemas
  api/           # FastAPI routes with tenant isolation
  workers/       # Celery tasks for sync, analysis
  chat/          # Conversational AI with context management
  adaptation/    # Real-time workout modification engine
  learning/      # User preference learning system
  life_events/   # Calendar integration and event detection
  frontend/      # Next.js dashboard with adaptive UI
tests/           # Pytest with 90% coverage target
```

### DATA MODELS

```python
# Core entities with tenant isolation
User: id, email, password_hash, tenant_id, created_at, mfa_secret
Athlete: id, user_id, name, profile_data, settings, adaptation_preferences
Source: id, athlete_id, provider, oauth_tokens_encrypted, last_sync, status
Workout: id, athlete_id, source_id, external_ids[], start_time_utc, sport, metrics{}, provenance{}, quality_score, adaptation_log[]
BiometricReading: id, athlete_id, source_id, date, type, value, unit, confidence
SyncJob: id, source_id, status, started_at, completed_at, error_details

# Adaptive Intelligence Models
UserPreference: id, athlete_id, category, preference_key, value, confidence, learned_at, source
ConversationContext: id, athlete_id, session_id, messages[], summary, created_at, updated_at
AdaptationHistory: id, athlete_id, workout_id, adaptation_type, original_plan, modified_plan, reason, outcome
LifeEvent: id, athlete_id, event_type, start_date, end_date, impact_level, adaptation_rules
WorkoutModification: id, workout_id, timestamp, metric, original_value, new_value, reason
LearningInsight: id, athlete_id, insight_type, data{}, confidence, created_at, validated

# Chat and Voice
ChatSession: id, athlete_id, started_at, ended_at, mode (text/voice), satisfaction_score
ChatMessage: id, session_id, role, content, tools_used[], latency_ms, token_count
VoiceTranscript: id, message_id, audio_url, transcript, confidence, duration_seconds

# Dedup keys
DeduplicationKey: workout_hash(external_id + start_time + duration + sport)
```

### API ENDPOINTS

```
# Authentication
POST   /auth/register         # Email/password with Argon2id
POST   /auth/login           # Returns JWT + refresh token
POST   /auth/magic-link      # Send 6-digit code via email
GET    /auth/oauth/{provider}/authorize
GET    /auth/oauth/{provider}/callback

# Source Management
GET    /api/sources          # List connected sources
POST   /api/sources/{provider}/connect
DELETE /api/sources/{id}     # Revoke + delete data
POST   /api/sources/{id}/sync # Trigger manual sync

# Workouts
GET    /api/workouts         # Paginated, filtered by date/sport/source
GET    /api/workouts/{id}    # Full details with provenance
PUT    /api/workouts/{id}    # Manual edits with audit log
POST   /api/workouts/{id}/adapt # Real-time workout modification

# Biometrics & Analysis
GET    /api/biometrics       # HRV, weight, sleep trends
GET    /api/analysis/load    # ACWR, TRIMP, TSS calculations
GET    /api/analysis/adaptation-insights # User-specific patterns

# Conversational AI
POST   /api/chat             # AI analysis with adaptive responses
GET    /api/chat/history     # Previous conversations
POST   /api/chat/voice       # Voice input processing
WS     /api/chat/stream      # Real-time conversation streaming

# User Preferences & Learning
GET    /api/preferences      # Learned user preferences
PUT    /api/preferences/{id} # Manual preference override
GET    /api/adaptations/history # Past workout adaptations
POST   /api/adaptations/feedback # User feedback on adaptations

# Life Events
GET    /api/life-events      # Detected and manual events
POST   /api/life-events      # Manual event entry
PUT    /api/life-events/{id} # Update event details
POST   /api/calendar/connect # Connect calendar for auto-detection

# Real-time Adaptation
WS     /api/workout/live     # Live workout data streaming
POST   /api/workout/start    # Begin adaptive workout session
POST   /api/workout/end      # Complete workout with summary

# Export & Account
POST   /api/export           # Generate CSV/Parquet/TCX
DELETE /api/account          # Full GDPR deletion
```

### CONVERSATIONAL AI INFRASTRUCTURE

```python
class AdaptiveConversationManager:
    def __init__(self, athlete_id: str):
        self.athlete_id = athlete_id
        self.context_manager = ContextManager(max_tokens=10000)
        self.preference_engine = PreferenceEngine(athlete_id)
        self.adaptation_engine = AdaptationEngine(athlete_id)
    
    async def process_message(self, message: str, mode: str = "text") -> ConversationResponse:
        # 1. Load user context and preferences
        context = await self.context_manager.get_context(self.athlete_id)
        preferences = await self.preference_engine.get_preferences()
        
        # 2. Detect intent and required tools
        intent = await self.detect_intent(message, context)
        
        # 3. Handle different conversation types
        if intent.type == "workout_modification":
            return await self.handle_workout_adaptation(message, context, preferences)
        elif intent.type == "life_event":
            return await self.handle_life_event(message, context)
        elif intent.type == "analysis":
            return await self.handle_analysis(message, context, preferences)
        
        # 4. Learn from interaction
        await self.preference_engine.learn_from_interaction(message, response)
        
        return response
    
    async def handle_workout_adaptation(self, message: str, context: Context, preferences: Preferences):
        # Extract constraints (e.g., "I only have 35 minutes")
        constraints = await self.extract_constraints(message)
        
        # Get current workout plan
        workout = await self.get_todays_workout(self.athlete_id)
        
        # Apply intelligent adaptation
        adapted_workout = await self.adaptation_engine.adapt_workout(
            workout, constraints, preferences
        )
        
        # Generate conversational response
        response = await self.generate_adaptive_response(
            original=workout,
            adapted=adapted_workout,
            reason=constraints,
            style=preferences.communication_style
        )
        
        return response
```

### REAL-TIME WORKOUT MODIFICATION ENGINE

```python
class WorkoutAdaptationEngine:
    def __init__(self):
        self.safety_monitor = SafetyMonitor()
        self.performance_tracker = PerformanceTracker()
        self.adaptation_strategies = AdaptationStrategies()
    
    async def adapt_workout(self, workout: Workout, constraints: Dict, preferences: UserPreferences) -> AdaptedWorkout:
        # 1. Validate constraints against safety limits
        safe_constraints = self.safety_monitor.validate(constraints, workout)
        
        # 2. Select adaptation strategy based on workout type and constraints
        strategy = self.select_strategy(workout, safe_constraints, preferences)
        
        # 3. Apply adaptations
        if constraints.get("time_limit"):
            workout = await self.adapt_for_time(workout, constraints["time_limit"], strategy)
        
        if constraints.get("equipment_available"):
            workout = await self.adapt_for_equipment(workout, constraints["equipment_available"])
        
        if constraints.get("fatigue_level"):
            workout = await self.adapt_for_fatigue(workout, constraints["fatigue_level"])
        
        # 4. Ensure workout maintains training stimulus
        workout = await self.optimize_training_effect(workout, preferences)
        
        # 5. Add adaptation metadata
        workout.adaptation_log.append({
            "timestamp": datetime.utcnow(),
            "constraints": constraints,
            "strategy": strategy.name,
            "modifications": self.get_modifications(original, workout)
        })
        
        return workout
    
    async def adapt_for_time(self, workout: Workout, time_limit: int, strategy: Strategy) -> Workout:
        """The 35-minute problem: Intelligently compress workouts while maintaining effectiveness"""
        if strategy == Strategy.MAINTAIN_INTENSITY:
            # Reduce volume, keep intensity
            return self.compress_intervals(workout, time_limit)
        elif strategy == Strategy.MAINTAIN_VOLUME:
            # Increase density, reduce rest
            return self.reduce_rest_periods(workout, time_limit)
        elif strategy == Strategy.HYBRID:
            # Smart mix based on workout phase
            return self.hybrid_compression(workout, time_limit)
```

### USER PREFERENCE LEARNING SYSTEM

```python
class PreferenceLearningEngine:
    def __init__(self, athlete_id: str):
        self.athlete_id = athlete_id
        self.preference_store = PreferenceStore()
        self.pattern_detector = PatternDetector()
        self.confidence_threshold = 0.8
    
    async def learn_from_interaction(self, interaction: Interaction) -> List[LearnedPreference]:
        learned = []
        
        # 1. Communication style learning
        if interaction.type == "message":
            style = self.detect_communication_style(interaction)
            await self.update_preference("communication_style", style, interaction)
        
        # 2. Workout preference learning
        if interaction.type == "workout_feedback":
            preferences = self.extract_workout_preferences(interaction)
            for pref in preferences:
                await self.update_preference(f"workout_{pref.type}", pref.value, interaction)
        
        # 3. Schedule pattern learning
        if interaction.type == "calendar_sync" or interaction.type == "workout_completed":
            patterns = await self.pattern_detector.detect_schedule_patterns(self.athlete_id)
            for pattern in patterns:
                if pattern.confidence > self.confidence_threshold:
                    await self.update_preference(f"schedule_{pattern.type}", pattern.value, pattern)
        
        # 4. Equipment preference learning
        if interaction.type == "equipment_selection":
            await self.update_preference("preferred_equipment", interaction.equipment, interaction)
        
        return learned
    
    async def update_preference(self, key: str, value: Any, source: Any):
        existing = await self.preference_store.get(self.athlete_id, key)
        
        if existing:
            # Bayesian update of confidence
            new_confidence = self.bayesian_update(existing.confidence, source.confidence)
            if new_confidence > existing.confidence:
                await self.preference_store.update(self.athlete_id, key, value, new_confidence)
        else:
            await self.preference_store.create(self.athlete_id, key, value, source.confidence)
```

### LIFE EVENT ADAPTATION FEATURES

```python
class LifeEventAdapter:
    def __init__(self):
        self.event_detector = EventDetector()
        self.impact_analyzer = ImpactAnalyzer()
        self.plan_adjuster = PlanAdjuster()
    
    async def detect_and_adapt(self, athlete_id: str) -> List[Adaptation]:
        # 1. Detect life events from multiple sources
        calendar_events = await self.detect_from_calendar(athlete_id)
        behavior_events = await self.detect_from_behavior(athlete_id)
        explicit_events = await self.get_user_reported_events(athlete_id)
        
        all_events = self.merge_events(calendar_events, behavior_events, explicit_events)
        
        adaptations = []
        for event in all_events:
            # 2. Analyze impact on training
            impact = await self.impact_analyzer.analyze(event, athlete_id)
            
            # 3. Create adaptations
            if event.type == "travel":
                adaptations.extend(await self.adapt_for_travel(event, impact))
            elif event.type == "work_deadline":
                adaptations.extend(await self.adapt_for_stress(event, impact))
            elif event.type == "illness":
                adaptations.extend(await self.adapt_for_recovery(event, impact))
            elif event.type == "race":
                adaptations.extend(await self.adapt_for_competition(event, impact))
        
        # 4. Apply adaptations to training plan
        await self.plan_adjuster.apply_adaptations(athlete_id, adaptations)
        
        return adaptations
```

### FRONTEND COMPONENTS FOR ADAPTIVE UI

```typescript
// Chat Interface Component
interface ChatInterfaceProps {
  athleteId: string;
  mode: 'text' | 'voice';
  onAdaptation: (adaptation: WorkoutAdaptation) => void;
}

export const AdaptiveChatInterface: React.FC<ChatInterfaceProps> = ({ athleteId, mode, onAdaptation }) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isListening, setIsListening] = useState(false);
  const { preferences } = useUserPreferences(athleteId);
  const { sendMessage, streamResponse } = useChatAPI();
  
  const handleMessage = async (content: string) => {
    const userMessage = { role: 'user', content, timestamp: new Date() };
    setMessages([...messages, userMessage]);
    
    const response = await streamResponse(content, {
      athleteId,
      preferences,
      context: messages
    });
    
    // Handle workout adaptations
    if (response.type === 'workout_adaptation') {
      onAdaptation(response.adaptation);
    }
    
    setMessages([...messages, userMessage, response.message]);
  };
  
  return (
    <div className={`chat-interface ${preferences.ui_density}`}>
      <MessageList messages={messages} preferences={preferences} />
      {mode === 'voice' ? (
        <VoiceInput onTranscript={handleMessage} isListening={isListening} />
      ) : (
        <TextInput onSubmit={handleMessage} suggestions={preferences.quick_responses} />
      )}
      <AdaptationPreview currentAdaptation={currentAdaptation} />
    </div>
  );
};

// Workout Adaptation UI Component
export const WorkoutAdaptationUI: React.FC<{ workout: Workout }> = ({ workout }) => {
  const [constraints, setConstraints] = useState<Constraints>({});
  const [adaptedWorkout, setAdaptedWorkout] = useState<Workout | null>(null);
  const { adaptWorkout } = useAdaptationAPI();
  
  const handleTimeConstraint = (minutes: number) => {
    setConstraints({ ...constraints, time_limit: minutes });
  };
  
  const handleAdapt = async () => {
    const result = await adaptWorkout(workout.id, constraints);
    setAdaptedWorkout(result);
  };
  
  return (
    <div className="workout-adaptation-panel">
      <h3>Adapt Today's Workout</h3>
      
      <ConstraintInput
        label="Available Time"
        value={constraints.time_limit}
        onChange={handleTimeConstraint}
        presets={[20, 35, 45, 60]}
      />
      
      <EquipmentSelector
        available={constraints.equipment_available}
        onChange={(equipment) => setConstraints({ ...constraints, equipment_available: equipment })}
      />
      
      <FatigueSlider
        value={constraints.fatigue_level}
        onChange={(level) => setConstraints({ ...constraints, fatigue_level: level })}
      />
      
      <Button onClick={handleAdapt}>Adapt Workout</Button>
      
      {adaptedWorkout && (
        <AdaptationComparison
          original={workout}
          adapted={adaptedWorkout}
          reason={constraints}
        />
      )}
    </div>
  );
};

// Life Event Calendar Integration
export const LifeEventCalendar: React.FC = () => {
  const { events, addEvent, updateEvent } = useLifeEvents();
  const { adaptations } = useTrainingAdaptations();
  
  return (
    <Calendar
      events={events}
      adaptations={adaptations}
      onEventAdd={addEvent}
      onEventEdit={updateEvent}
      renderEvent={(event) => (
        <EventCard
          event={event}
          impact={event.training_impact}
          adaptations={adaptations.filter(a => a.event_id === event.id)}
        />
      )}
    />
  );
};
```

### SYNC JOBS WITH ADAPTIVE LEARNING

```python
@celery.task(bind=True, max_retries=3)
def sync_source_with_learning(self, source_id):
    # 1. Check rate limits (Redis counter)
    # 2. Refresh OAuth token if needed
    # 3. Fetch delta since last_sync with pagination
    # 4. Normalize units, timezones
    # 5. Run dedup with field precedence
    # 6. Store with provenance tracking
    # 7. Extract patterns for preference learning
    patterns = extract_workout_patterns(new_workouts)
    await preference_engine.learn_from_patterns(source.athlete_id, patterns)
    # 8. Update last_sync, clear cache
    # 9. Handle failures with exponential backoff
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

### AI CHAT IMPLEMENTATION WITH ADAPTATION

```python
async def handle_adaptive_chat(query: str, athlete_id: str) -> ChatResponse:
    # 1. Load user preferences and context
    preferences = await preference_engine.get_preferences(athlete_id)
    context = await context_manager.get_context(athlete_id)
    
    # 2. Try domain tools with adaptation awareness (< 2s)
    tools_result = await run_adaptive_analysis_tools(query, athlete_id, preferences)
    if tools_result.confidence > 0.8:
        response = format_adaptive_response(tools_result, preferences)
        await learn_from_response(query, response, athlete_id)
        return response
    
    # 3. RAG over athlete summaries and adaptations (< 5s)
    rag_result = await search_athlete_context_with_adaptations(query, athlete_id)
    if rag_result.confidence > 0.7:
        response = format_adaptive_response(rag_result, preferences, citations=rag_result.sources)
        await learn_from_response(query, response, athlete_id)
        return response
    
    # 4. Web search with adaptation context (60s cap)
    if FEATURE_WEB_SEARCH_ENABLED:
        with timeout(60):
            web_result = await search_web_with_context(query, context)
            if web_result:
                response = format_adaptive_response(web_result, preferences, citations=web_result.urls)
                await learn_from_response(query, response, athlete_id)
                return response
    
    # 5. Fallback with learning
    fallback_response = ChatResponse(
        text="I don't have enough information to answer that question right now, but I'm learning. Could you tell me more about what you're looking for?",
        confidence=0.0,
        tools_used=["domain", "rag", "web"],
        follow_up_questions=generate_clarifying_questions(query, context)
    )
    await learn_from_response(query, fallback_response, athlete_id)
    return fallback_response
```

### SECURITY REQUIREMENTS (ENHANCED)

1. **OAuth tokens**: Encrypt with Fernet, store key in env
2. **Tenant isolation**: Every query includes `WHERE athlete_id IN (user's athletes)`
3. **Session security**: Secure, HttpOnly, SameSite cookies; 24h expiry
4. **Rate limits**: 100 req/min per user, 10 syncs/hour per source
5. **Audit log**: Track admin actions, exports, deletions, adaptations
6. **Input validation**: Pydantic for all inputs; SQL injection prevention
7. **CORS**: Whitelist frontend origin only
8. **CSP headers**: Strict policy preventing XSS
9. **Preference privacy**: User preferences encrypted at rest, never shared
10. **Voice data**: Temporary storage only, auto-delete after processing

### EDGE CASES & ERROR HANDLING (ENHANCED)

1. **Expired OAuth token**: Auto-refresh; if refresh fails, mark source as needs_reauth
2. **Provider API down**: Exponential backoff with jitter; max 5 retries over 24h
3. **Duplicate workouts**: Merge by precedence; store all external_ids
4. **Unit mismatches**: Normalize to metric; store original_unit field
5. **Clock skew**: Normalize to UTC; detect >24h drift and flag
6. **Partial data**: Use available fields; mark quality_score lower
7. **PII in logs**: Redact emails, names; use user_id only
8. **Chat timeout**: Hard stop at 60s; return helpful fallback
9. **Empty states**: "Connect a source to get started" CTAs
10. **Webhook replay**: Idempotent processing; track event_id
11. **Adaptation conflicts**: User preference overrides automatic adaptations
12. **Voice recognition failure**: Fallback to text input with retry option
13. **Context overflow**: Intelligent summarization maintains key information
14. **Life event conflicts**: Manual resolution UI for overlapping events

### TESTS & ACCEPTANCE CRITERIA (ENHANCED)

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
def test_preference_learning():
    # Preferences update with Bayesian confidence
def test_workout_adaptation():
    # 60min workout -> 35min maintains training effect
def test_context_management():
    # 10k tokens maintained with smart pruning
def test_life_event_detection():
    # Calendar events correctly impact training
```

**Integration Tests**
```python
def test_strava_oauth_flow():
    # Mock OAuth endpoints, verify token storage
def test_sync_with_rate_limit():
    # Hit rate limit, verify backoff behavior
def test_webhook_validation():
    # Invalid signature -> 401 response
def test_adaptive_chat_flow():
    # Chat learns and adapts responses over time
def test_real_time_adaptation():
    # WebSocket updates during live workout
def test_preference_persistence():
    # Learned preferences survive restarts
```

**E2E Tests (Playwright)**
```
- Register -> Connect Strava -> Sync -> View workouts
- Chat "What was my longest run?" -> Get accurate answer
- Chat "I only have 35 minutes today" -> Get adapted workout
- Voice input -> Transcription -> Adaptive response
- Add life event -> See training adaptations
- Complete workout -> Preference learning -> Better next recommendation
- Export data -> Download includes adaptation history
- Delete source -> Verify data removed but preferences retained
```

**Load Tests**
- 100 concurrent users, 10k workouts each
- API p95 < 200ms for workout list
- Sync job completes < 5min for 1000 activities
- Chat response < 10s for complex queries
- Real-time adaptation < 100ms latency
- Preference learning < 500ms per interaction

**Chaos Tests**
1. **Tenant isolation breach**: Attempt cross-tenant reads via API fuzzing
2. **Token leakage**: Grep logs for OAuth tokens during high load
3. **Dedup corruption**: Parallel syncs of same athlete, verify no data loss
4. **Clock drift**: Set device time +48h, verify workout placement
5. **Provider cutoff**: Drop connections mid-sync, verify partial success
6. **Preference corruption**: Conflicting preferences don't crash system
7. **Context overflow**: System gracefully handles 100k+ token conversations
8. **Adaptation loops**: Prevent infinite adaptation cycles

### COST & LATENCY GUARDRAILS (ENHANCED)

**Sync Jobs**
- Budget: $0.10/user/month for API calls
- Enforce: Track calls in Redis; pause at 80% monthly quota
- Alert: Email user at 90% quota

**AI Chat & Adaptation**
- Budget: $1.00/user/month for LLM tokens
- Enforce: 10k token context; 200 queries/day limit
- Cache: Common questions and adaptations for 24h
- Alert: "Daily limit reached" after 200 queries
- Local models: Use for real-time adaptations to reduce costs

**Voice Processing**
- Budget: $0.50/user/month for transcription
- Enforce: 60min/day voice input limit
- Optimize: Local wake word detection

**Monitoring**
```python
metrics.histogram('sync.duration', duration, tags={'provider': provider})
metrics.increment('chat.adaptation_rate', tags={'type': 'time_constraint'})
metrics.histogram('preference.learning_time', duration, tags={'category': category})
metrics.gauge('websocket.active_connections', connection_count)
if latency > 10:
    alerts.send('Chat latency exceeded 10s', context)
if adaptation_time > 100:
    alerts.send('Real-time adaptation slow', context)
```

### UNKNOWN UNKNOWNS (MITIGATIONS)

1. **Provider API changes**: Version detection; feature flags for risky endpoints
2. **GDPR audits**: Data flow diagram; retention policy docs; deletion verification
3. **Biometric accuracy**: Disclaimer on all health metrics; links to studies
4. **Timezone database**: Use pytz with auto-updates; fallback to UTC
5. **OAuth provider downtime**: Cached auth for 1h; backup magic links
6. **AI hallucinations**: Fact-checking layer for health claims
7. **Voice privacy concerns**: Clear data handling policy; opt-in only
8. **Adaptation liability**: Medical disclaimers; conservative safety margins

### IMPLEMENTATION STEPS (UPDATED)

1. **Database Migration**
   - Add tenant_id to all tables
   - Create users, athletes, sources tables
   - Add preference and adaptation tables
   - Add TimescaleDB for time-series data
   - Add RLS policies
   - Test: No cross-tenant queries possible

2. **Authentication System**
   - Implement Argon2id password hashing
   - JWT with refresh tokens
   - Magic link email flow
   - Voice authentication support
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
   - Pattern extraction for learning
   - Test: Queue, execute, retry, fail

5. **Deduplication Engine**
   - Fuzzy matching algorithm
   - Field-level precedence
   - Provenance tracking
   - Test: Exact, fuzzy, conflict cases

6. **Conversational AI Infrastructure**
   - Claude API integration
   - Context management system
   - Preference-aware responses
   - Voice transcription pipeline
   - Test: Text, voice, context overflow

7. **Adaptation Engine**
   - Time-based adaptations (35-minute problem)
   - Equipment-based modifications
   - Fatigue-aware adjustments
   - Safety monitoring
   - Test: All adaptation scenarios

8. **Preference Learning System**
   - Bayesian confidence updates
   - Pattern detection algorithms
   - Privacy-preserving storage
   - Test: Learning accuracy, no leaks

9. **Life Event Integration**
   - Calendar API connectors
   - Event detection algorithms
   - Impact analysis engine
   - Plan adjustment logic
   - Test: Detection accuracy, adaptations

10. **API Layer**
    - FastAPI with auth middleware
    - Tenant isolation on all routes
    - WebSocket support for real-time
    - Pagination, filtering
    - Test: CRUD with auth, no leaks

11. **Frontend Dashboard**
    - Next.js with TypeScript
    - TanStack Query for caching
    - Chart.js for visualizations
    - Adaptive UI components
    - Voice input interface
    - Test: All user flows

12. **Real-time Features**
    - WebSocket infrastructure
    - Live workout tracking
    - Real-time adaptations
    - Test: Latency, reliability

13. **Observability**
    - Structured logging with Loguru
    - Prometheus metrics
    - Sentry error tracking
    - Adaptation analytics
    - Test: Logs clean, metrics flow

14. **Security Hardening**
    - OWASP scan
    - Penetration test
    - PII audit
    - Voice data security
    - Test: No vulnerabilities, no PII leaks

### DELIVERABLES

Working multi-tenant adaptive platform with:
- User registration and OAuth source connections
- Automatic sync with deduplication
- Web dashboard showing workouts and trends
- Conversational AI with voice support and adaptive responses
- Real-time workout modification engine
- User preference learning system
- Life event adaptation features
- Full test coverage and monitoring
- Production-ready security and privacy

All Must-Have and Should-Have requirements integrated. No 3rd-party passwords. Intelligent 35-minute workout adaptations. Privacy-preserving preference learning. Chaos tests passing.

## RED TEAM SCENARIOS (ENHANCED)

### 1. Multi-Tenant Isolation Attack
**Scenario**: Malicious user attempts to access other tenants' data via:
- SQL injection in workout filters
- JWT tampering to change tenant_id
- GraphQL query depth attacks
- Race conditions during user creation
- Preference leakage across tenants

**Detection**: Anomaly detection on access patterns, honeypot data
**Mitigation**: Parameterized queries, JWT signature validation, query depth limits, transaction isolation, encrypted preferences

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
- Manipulate preference learning
- Cause harmful workout adaptations

**Detection**: Token usage spikes, prompt pattern analysis, adaptation safety checks
**Mitigation**: Input sanitization, strict medical filters, rate limiting, RAG access controls, adaptation bounds

### 5. Calorie Estimation Manipulation
**Scenario**: Attacker provides inputs to:
- Generate unrealistic calorie burns
- Exploit formula edge cases (negative values)
- Cause integer overflows
- Create liability via bad recommendations

**Detection**: Statistical anomaly detection on outputs
**Mitigation**: Input bounds checking, output sanity limits, medical disclaimers

### 6. Voice Data Exfiltration
**Scenario**: Attacker attempts to:
- Access other users' voice recordings
- Extract PII from transcripts
- Replay voice commands
- Spoof voice authentication

**Detection**: Access pattern monitoring, voice fingerprinting
**Mitigation**: Immediate deletion after processing, transcript sanitization, replay protection

### 7. Adaptation Attack
**Scenario**: Malicious adaptations to:
- Cause injury through excessive intensity
- Exploit safety boundary conditions
- Create adaptation loops
- Corrupt preference learning

**Detection**: Safety monitoring, adaptation pattern analysis
**Mitigation**: Hard safety limits, manual override, adaptation history audit

## FEATURE FLAGS (ENHANCED)

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
  
  # AI & Adaptation
  FEATURE_WEB_SEARCH_ENABLED: false  # Enable after safety review
  FEATURE_ADVANCED_LLM: true  # Claude for conversations
  FEATURE_CHAT_HISTORY: true
  FEATURE_VOICE_INPUT: true
  FEATURE_REAL_TIME_ADAPTATION: true
  FEATURE_PREFERENCE_LEARNING: true
  FEATURE_LIFE_EVENT_DETECTION: true
  FEATURE_35_MINUTE_ADAPTATION: true
  
  # Providers
  FEATURE_GARMIN_CONNECT: true
  FEATURE_WHOOP_API: false  # Pending API access
  FEATURE_APPLE_HEALTH: false  # Requires mobile app
  FEATURE_GOOGLE_CALENDAR: true
  FEATURE_OUTLOOK_CALENDAR: true
```

## MONITORING DASHBOARDS (ENHANCED)

### System Health
- API latency p50/p95/p99
- Worker queue depth
- Database connection pool
- Redis memory usage
- Error rate by endpoint
- WebSocket connection count
- Voice processing queue

### Business Metrics
- Daily active users
- Sources connected per user
- Sync success rate by provider
- Chat satisfaction score
- Data quality scores
- Adaptation usage rate
- Preference learning effectiveness
- Voice input usage

### Security Metrics
- Failed auth attempts
- OAuth refresh failures
- Tenant isolation violations
- Rate limit hits
- Suspicious query patterns
- Voice replay attempts
- Adaptation safety triggers

### AI & Learning Metrics
- Chat response times
- Adaptation success rate
- Preference learning accuracy
- Context management efficiency
- Voice transcription accuracy
- Life event detection rate
- 35-minute adaptation usage

## DEPLOYMENT CHECKLIST (ENHANCED)

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
- [ ] Voice data policies approved
- [ ] Medical disclaimers reviewed
- [ ] Adaptation safety tested

### Launch Day
- [ ] Database migrations applied
- [ ] TimescaleDB configured
- [ ] Redis cache warmed
- [ ] Worker queues empty
- [ ] Health checks passing
- [ ] WebSocket infrastructure ready
- [ ] Voice pipeline tested
- [ ] Canary deployment successful
- [ ] Rollback plan ready
- [ ] Support team briefed
- [ ] Status page updated

### Post-Launch
- [ ] Monitor error rates
- [ ] Check provider quotas
- [ ] Review user feedback
- [ ] Analyze performance metrics
- [ ] Track adaptation usage
- [ ] Measure learning effectiveness
- [ ] Update documentation
- [ ] Plan next iteration

## CURSOR USAGE NOTES

To implement this adaptive system:

1. Start with the database migration including preference tables
2. Build auth before any other features
3. Implement conversational AI infrastructure early
4. Test adaptation engine with safety bounds
5. Ensure preference learning preserves privacy
6. Implement WebSocket support for real-time features
7. Add voice support as progressive enhancement

## IMPLEMENTATION TIMELINE (12 WEEKS)

### Week 1-2: Foundation & Multi-Tenancy
**Goal**: Database, auth, basic API structure

**Tasks**:
1. Set up PostgreSQL with row-level security
2. Add TimescaleDB for time-series data
3. Create all data models including adaptive intelligence tables
4. Implement authentication (JWT, OAuth prep)
5. Basic FastAPI structure with tenant isolation
6. Set up Redis for caching and sessions

**Test**: Can create users, authenticate, and maintain tenant isolation

### Week 3-4: Provider Integrations
**Goal**: Connect Strava, begin dedup engine

**Tasks**:
1. Implement OAuth flow for Strava
2. Create sync job infrastructure with Celery
3. Build basic deduplication engine
4. Set up webhook handling
5. Create source precedence logic
6. Implement rate limiting

**Test**: Can connect Strava, sync workouts, handle duplicates

### Week 5-6: Core Dashboard & Analytics
**Goal**: Basic web UI with workout display

**Tasks**:
1. Next.js setup with TypeScript
2. Authentication flow in frontend
3. Basic workout list and detail views
4. Simple analytics charts
5. Responsive design foundation
6. Initial loading states and error handling

**Test**: Can view synced workouts in clean UI

### Week 7-8: Adaptive Intelligence Core
**Goal**: Implement workout adaptation engine

**Tasks**:
1. Build workout modification engine
2. Implement 35-minute problem solver
3. Create adaptation strategies (intensity/volume/hybrid)
4. Add safety monitoring system
5. Build adaptation UI components
6. Create real-time preview system

**Test**: Can adapt 60-min workout to 35-min with maintained effectiveness

### Week 9-10: Conversational AI & Learning
**Goal**: Add chat interface and preference learning

**Tasks**:
1. Integrate Claude API for conversations
2. Build context management system (10k tokens)
3. Implement preference learning engine
4. Create Bayesian confidence updates
5. Add pattern detection for schedules
6. Build chat UI with streaming responses

**Test**: Chat learns user preferences and adapts responses

### Week 11-12: Life Events & Polish
**Goal**: Complete adaptive features, prepare for launch

**Tasks**:
1. Calendar integration for life events
2. Automatic training plan adjustments
3. Voice input support (progressive enhancement)
4. WebSocket for real-time adaptations
5. Comprehensive error handling
6. Performance optimization
7. Security audit
8. Documentation

**Test**: Full adaptive cycle works end-to-end

## DAILY DEVELOPMENT WORKFLOW (7am Start)

### Morning Session (7:00-8:00am)
**Focus**: New feature development when mind is fresh

Example daily tasks:
- Monday: Database schema for new feature
- Tuesday: API endpoint implementation
- Wednesday: Frontend component creation
- Thursday: Integration testing
- Friday: Code review and refactoring

### Evening Session (7:30-9:30pm)
**Focus**: Testing, debugging, learning

Example tasks:
- Write tests for morning's code
- Debug issues found during day
- Research next day's implementation
- Update documentation
- Push code for review

### Quick Wins First
Start each feature with the simplest working version:
1. Hardcoded MVP (30 min)
2. Basic dynamic version (1 hour)
3. Full implementation (2-3 hours)
4. Polish and optimize (1 hour)

## CRITICAL PATH FEATURES

**Must Have for Beta**:
1. ✅ Multi-tenant auth
2. ✅ Strava sync
3. ✅ Basic deduplication
4. ✅ Workout list/detail views
5. ✅ 35-minute adaptation
6. ✅ Basic chat interface
7. ✅ Preference learning (basic)

**Can Add Later**:
- Additional providers (Garmin, WHOOP)
- Voice input
- Complex life event handling
- Advanced analytics
- Mobile app
- Coach portal

## COMMON PITFALLS TO AVOID

1. **Over-engineering early**: Start simple, iterate
2. **Perfect UI too soon**: Function over form initially
3. **Too many providers**: Nail Strava first
4. **Complex AI before basics**: Get core working first
5. **Ignoring tests**: Test as you go, not later
6. **Analysis paralysis**: Ship working code daily

## CURSOR PROMPTS FOR EACH PHASE

### Phase 1 Prompt:
"Create PostgreSQL schema with row-level security for multi-tenant fitness platform. Include User, Athlete, Workout, Source, and UserPreference tables. Add FastAPI endpoints for auth using JWT."

### Phase 2 Prompt:
"Implement Strava OAuth integration with token refresh. Create Celery task for syncing workouts. Build deduplication engine that merges workouts within 5-minute window."

### Phase 3 Prompt:
"Create Next.js dashboard showing workout list with infinite scroll. Add workout detail page with charts using Recharts. Implement responsive design with Tailwind."

### Phase 4 Prompt:
"Build workout adaptation engine that can compress 60-minute workout to 35 minutes while maintaining training effect. Create three strategies: maintain intensity, maintain volume, and hybrid."

### Phase 5 Prompt:
"Integrate Claude API for conversational UI. Implement preference learning system with Bayesian confidence updates. Create chat interface with streaming responses."

## SUCCESS METRICS BY WEEK

- Week 2: 5 test users can create accounts
- Week 4: 100 workouts synced successfully
- Week 6: Dashboard loads in <2 seconds
- Week 8: 35-minute adaptation used 50+ times
- Week 10: AI responds intelligently to 80% of queries
- Week 12: Ready for 50-user beta launch

Remember: Ship something every single day. Progress > Perfection.

---

This guide incorporates adaptive intelligence throughout while maintaining security and data integrity. The 35-minute problem is a core feature, not an edge case.