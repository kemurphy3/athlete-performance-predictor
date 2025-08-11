# Fitpull Integration Prompt for Cursor

Build a modular data ingestion system called `fitpull` that integrates into the existing athlete-performance-predictor framework as a new data source module under `src/data/`.

## Integration Architecture

Create the fitpull module within the existing project structure:
- `src/data/fitpull/` - Main fitpull package
- `src/data/fitpull/connectors/` - API connectors for each service
- `src/data/fitpull/models/` - Pydantic data models
- `src/data/fitpull/dedup/` - Deduplication logic
- `src/data/fitpull/cli.py` - Click CLI implementation
- `src/data/fitpull/config.py` - Configuration management

The fitpull module should integrate with existing components:
- Feed data into `FitnessAnalyzer` from `src/core/analyze_my_fitness.py`
- Provide input for `InjuryPredictor` in `src/ml/ml_models.py`
- Support the Streamlit dashboard in `src/visualization/streamlit_app.py`

## Sport-Agnostic Core with Sport-Specific Modules

Design the system with three layers:

### 1. Core Fitness Module (Sport-Agnostic)
Handle universal fitness metrics:
- Workouts: duration, heart rate, calories, distance
- Biometrics: weight, HRV, sleep, resting HR
- Training load: TRIMP, acute/chronic ratios
- Recovery metrics: sleep quality, stress scores

### 2. Sport Type Detection
Implement automatic sport categorization:
- Endurance sports (running, cycling, swimming)
- Ball sports (soccer, basketball, tennis)
- Strength sports (weightlifting, CrossFit)
- Mixed sports (triathlon, obstacle racing)

### 3. Sport-Specific Analyzers
Create pluggable analyzers activated based on sport type:

```python
# src/data/fitpull/analyzers/ball_sports.py
class BallSportsAnalyzer:
    def analyze_gps_data(self, activity: Workout) -> BallSportMetrics:
        # Sprint detection (>7 m/s)
        # Acceleration/deceleration patterns
        # Change of direction frequency
        # High-intensity running distance
        # Recovery between sprints
```

## Data Models

### Enhanced Workout Model
Extend the base workout model to support sport-specific data:

```python
class Workout(BaseModel):
    # Core fields (all sports)
    workout_id: str
    start_time: datetime
    end_time: datetime
    sport: str
    sport_category: str  # endurance, ball_sport, strength, mixed
    distance: Optional[float]
    duration: int
    calories: Optional[int]
    heart_rate_avg: Optional[int]
    heart_rate_max: Optional[int]
    
    # GPS data (when available)
    gps_data: Optional[GPSData]
    route_hash: Optional[str]
    
    # Sport-specific data
    sport_specific: Optional[Dict[str, Any]]
    
    # Source tracking
    provenance: str
    external_ids: Dict[str, str]
```

### GPS Data Model for Ball Sports
```python
class GPSData(BaseModel):
    points: List[GPSPoint]
    
    def calculate_sprints(self, threshold_mps: float = 7.0) -> List[SprintEvent]:
        # Detect sprint events above threshold
        
    def calculate_accelerations(self) -> AccelerationMetrics:
        # Calculate acceleration/deceleration events
        
    def calculate_field_coverage(self) -> HeatmapData:
        # Generate positional heatmap for ball sports
```

## Connector Implementation

Each connector should detect and preserve sport-specific data:

### Garmin Connector
- Extract advanced running dynamics
- Preserve cycling power data
- Capture swimming stroke data
- Keep strength training exercise details

### Strava Connector  
- Preserve segment efforts
- Extract power data when available
- Keep kudos and social features separate
- Capture perceived exertion

### WHOOP Connector
- Focus on recovery metrics
- Strain calculations
- Sleep performance data
- Day-by-day readiness

## Integration with ML Models

Feed enriched data into existing ML pipeline:

```python
# src/ml/ml_models.py enhancement
class InjuryPredictor:
    def prepare_features(self, activities: List[Workout]) -> pd.DataFrame:
        features = self._extract_core_features(activities)
        
        # Add sport-specific features if ball sport detected
        ball_sport_activities = [a for a in activities if a.sport_category == 'ball_sport']
        if ball_sport_activities:
            features = self._add_ball_sport_features(features, ball_sport_activities)
            
        return features
```

## CLI Commands

Extend the existing CLI structure:

```bash
# Auth and sync commands
python -m src.data.fitpull auth garmin
python -m src.data.fitpull sync --all
python -m src.data.fitpull sync --source strava --days 30

# Analysis commands with sport detection
python -m src.data.fitpull analyze --detect-sport
python -m src.data.fitpull analyze --sport soccer --gps-analysis

# Export with sport-specific metrics
python -m src.data.fitpull export --include-gps --format parquet
```

## Configuration

Extend `.env` with fitpull settings:

```env
# Existing athlete-performance-predictor settings
...

# Fitpull API Credentials
GARMIN_USERNAME=
GARMIN_PASSWORD=
STRAVA_CLIENT_ID=
STRAVA_CLIENT_SECRET=
FITBIT_CLIENT_ID=
WHOOP_API_KEY=
OURA_ACCESS_TOKEN=
WITHINGS_API_KEY=

# Fitpull Settings
FITPULL_DB_PATH=./data/fitpull.db
FITPULL_DEFAULT_DAYS=30
FITPULL_ENABLE_GPS_ANALYSIS=true
FITPULL_SPORT_DETECTION_MODE=auto
```

## Deduplication Strategy

Implement smart deduplication that preserves sport-specific data:

1. Match by external_id within same source
2. For cross-source matching:
   - Time window: start_time within 5 minutes
   - Duration match: within 10%
   - Distance match: within 5% (if available)
   - Sport type must match
3. For GPS activities: route hash similarity >85%
4. Merge strategy:
   - Keep highest precedence source as primary
   - Merge unique sport-specific fields
   - Preserve GPS data from most detailed source

## Testing Requirements

Add sport-specific test cases:

```python
# tests/test_fitpull_ball_sports.py
def test_soccer_sprint_detection():
    # Test GPS analysis for soccer activity
    
def test_basketball_court_coverage():
    # Test heatmap generation for basketball

def test_sport_category_detection():
    # Test automatic sport categorization
```

## Dashboard Integration

Update Streamlit dashboard to show sport-specific insights:

```python
# src/visualization/streamlit_app.py enhancement
if st.session_state.get('sport_category') == 'ball_sport':
    st.subheader("⚽ Ball Sport Analytics")
    
    if gps_data_available:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Sprints", sprint_count)
        with col2:
            st.metric("High Intensity Distance", f"{hi_distance:.1f} km")
        with col3:
            st.metric("Max Speed", f"{max_speed:.1f} km/h")
        
        # Show field heatmap
        st.plotly_chart(create_field_heatmap(gps_data))
```

## Error Handling

Implement graceful degradation:
- If GPS data missing: skip sprint analysis, show basic metrics
- If sport detection fails: default to general fitness analysis
- If API rate limited: queue for later, continue with cached data
- Log all issues with structured logging

## Security and Privacy

- Store OAuth tokens encrypted using `cryptography` library
- Never log GPS coordinates in production
- Allow users to exclude GPS data from exports
- Implement data retention policies

Build this as a proper sub-package that enhances the existing athlete-performance-predictor without breaking current functionality. The system should intelligently adapt its analysis based on detected sport type while maintaining a clean, sport-agnostic core that works for any fitness activity.