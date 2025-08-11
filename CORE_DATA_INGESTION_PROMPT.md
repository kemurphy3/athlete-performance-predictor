# Core Data Ingestion System for Athlete Performance Predictor

Enhance the athlete-performance-predictor with a comprehensive data ingestion system as its core functionality, replacing the current limited Strava/VeSync integration.

## Architecture Overview

Transform the current data layer into a robust multi-source ingestion system:

```
athlete-performance-predictor/
├── src/
│   ├── core/
│   │   ├── data_ingestion.py      # Main orchestrator
│   │   ├── models.py              # Enhanced data models
│   │   └── deduplication.py       # Dedup logic
│   ├── connectors/                # API connectors
│   │   ├── base.py               # Abstract connector
│   │   ├── strava.py             # Enhanced Strava
│   │   ├── garmin.py             # New Garmin connector
│   │   ├── whoop.py              # New WHOOP connector
│   │   ├── oura.py               # New Oura connector
│   │   └── ...                   # Other connectors
│   ├── ml/                       # Existing ML models
│   ├── analysis/                 # Core fitness analysis
│   └── plugins/                  # Sport-specific plugins
│       └── ball_sports/          # Optional ball sports module
```

## Core Data Models

Replace the current basic activity model with comprehensive schemas:

```python
# src/core/models.py

class Workout(BaseModel):
    """Universal workout model for all activities"""
    # Identity
    workout_id: str  # Deterministic hash
    
    # Temporal
    start_time: datetime
    end_time: datetime
    duration: int  # seconds
    
    # Activity classification
    sport: str  # Raw sport name from source
    sport_category: SportCategory  # Enum: ENDURANCE, STRENGTH, BALL_SPORT, MIXED
    
    # Core metrics (available for most activities)
    distance: Optional[float]  # meters
    calories: Optional[int]
    heart_rate_avg: Optional[int]
    heart_rate_max: Optional[int]
    elevation_gain: Optional[float]
    
    # Advanced metrics (when available)
    power_avg: Optional[float]  # watts
    cadence_avg: Optional[int]
    training_load: Optional[float]
    perceived_exertion: Optional[int]
    
    # Source tracking
    source: DataSource  # Enum: GARMIN, STRAVA, WHOOP, etc.
    external_ids: Dict[str, str]  # {source: id}
    raw_data: Optional[Dict]  # Preserve source-specific fields
    
    # Data quality
    has_gps: bool = False
    has_power: bool = False
    data_quality_score: float  # 0-1 based on available metrics

class BiometricReading(BaseModel):
    """Daily biometric measurements"""
    date: date
    metric_type: MetricType  # weight, hrv, resting_hr, sleep_hours
    value: float
    unit: str
    source: DataSource
    confidence: float  # For averaged/estimated values
```

## Enhanced CLI (Main Entry Point)

Replace the current scattered scripts with a unified CLI:

```bash
# Authentication
python -m athlete_performance_predictor auth garmin
python -m athlete_performance_predictor auth --list  # Show configured sources

# Data synchronization
python -m athlete_performance_predictor sync  # Sync all configured sources
python -m athlete_performance_predictor sync --days 90 --source garmin,strava

# Analysis (existing functionality enhanced)
python -m athlete_performance_predictor analyze  # Run fitness analysis
python -m athlete_performance_predictor analyze --plugin ball_sports  # With plugin

# Export
python -m athlete_performance_predictor export --format parquet
python -m athlete_performance_predictor export --format report --output fitness_report.pdf

# Status
python -m athlete_performance_predictor status  # Show data summary
```

## Connector Implementation

Each connector inherits from a base class and implements standard methods:

```python
# src/connectors/base.py
class BaseConnector(ABC):
    """Abstract base for all data source connectors"""
    
    @abstractmethod
    async def authenticate(self) -> bool:
        """Handle OAuth or API key authentication"""
        
    @abstractmethod
    async def fetch_workouts(self, start_date: date, end_date: date) -> List[Workout]:
        """Fetch workouts in date range"""
        
    @abstractmethod
    async def fetch_biometrics(self, start_date: date, end_date: date) -> List[BiometricReading]:
        """Fetch biometric data"""
        
    def transform_to_canonical(self, raw_data: Dict) -> Workout:
        """Transform source-specific format to canonical model"""
```

## Deduplication Engine

Implement intelligent deduplication in the core:

```python
# src/core/deduplication.py
class DeduplicationEngine:
    """Smart deduplication across multiple sources"""
    
    PRECEDENCE_ORDER = [
        DataSource.GARMIN,  # Most detailed GPS/sensor data
        DataSource.WHOOP,   # Best recovery metrics
        DataSource.STRAVA,  # Good social features
        DataSource.OURA,    # Best sleep data
        # ... others
    ]
    
    def deduplicate_workouts(self, workouts: List[Workout]) -> List[Workout]:
        """
        Three-tier matching:
        1. Exact external_id match
        2. Temporal + distance matching
        3. GPS route similarity (if available)
        """
        
    def merge_workout_data(self, duplicates: List[Workout]) -> Workout:
        """Intelligently merge data from multiple sources"""
        # Take base from highest precedence
        # Fill missing fields from other sources
        # Average conflicting biometrics
```

## Integration with Existing ML Pipeline

Enhance the current ML models with richer data:

```python
# src/ml/ml_models.py (enhancement)
class InjuryPredictor:
    def prepare_features(self, workouts: List[Workout], biometrics: List[BiometricReading]) -> pd.DataFrame:
        """Enhanced feature extraction with multi-source data"""
        features = pd.DataFrame()
        
        # Existing features
        features['training_load'] = self._calculate_training_load(workouts)
        features['acute_chronic_ratio'] = self._calculate_acwr(workouts)
        
        # New multi-source features
        features['sleep_quality'] = self._extract_sleep_metrics(biometrics)
        features['hrv_trend'] = self._calculate_hrv_trend(biometrics)
        features['cross_training_variety'] = self._calculate_sport_diversity(workouts)
        
        return features
```

## Plugin System for Sport-Specific Analysis

Create an optional plugin architecture:

```python
# src/plugins/base.py
class AnalysisPlugin(ABC):
    """Base class for sport-specific analysis plugins"""
    
    @abstractmethod
    def can_analyze(self, workout: Workout) -> bool:
        """Check if this plugin applies to the workout"""
        
    @abstractmethod
    def analyze(self, workout: Workout) -> Dict[str, Any]:
        """Perform sport-specific analysis"""

# src/plugins/ball_sports/analyzer.py
class BallSportsPlugin(AnalysisPlugin):
    """GPS-based analysis for soccer, basketball, etc."""
    
    def can_analyze(self, workout: Workout) -> bool:
        return workout.sport_category == SportCategory.BALL_SPORT and workout.has_gps
        
    def analyze(self, workout: Workout) -> Dict[str, Any]:
        # Sprint detection
        # Acceleration patterns
        # Field coverage heatmaps
        # Return sport-specific metrics
```

## Database Schema

Upgrade from simple CSV to proper database:

```sql
-- SQLite schema for local storage
CREATE TABLE workouts (
    workout_id TEXT PRIMARY KEY,
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    sport TEXT,
    sport_category TEXT,
    distance REAL,
    duration INTEGER,
    -- ... other fields
    raw_data JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE biometrics (
    id INTEGER PRIMARY KEY,
    date DATE,
    metric_type TEXT,
    value REAL,
    source TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE sync_metadata (
    source TEXT,
    last_sync TIMESTAMP,
    sync_status TEXT
);
```

## Configuration

Centralize all configuration:

```python
# .env
# Core settings
DATABASE_URL=sqlite:///data/athlete.db
LOG_LEVEL=INFO

# API Credentials (all optional)
GARMIN_USERNAME=
GARMIN_PASSWORD=
STRAVA_CLIENT_ID=
STRAVA_CLIENT_SECRET=
WHOOP_API_KEY=
OURA_ACCESS_TOKEN=

# Feature flags
ENABLE_GPS_ANALYSIS=true
ENABLE_PLUGINS=true
AUTO_DEDUPLICATE=true
```

## Error Handling and Logging

Implement robust error handling throughout:

```python
import structlog
logger = structlog.get_logger()

class DataIngestionOrchestrator:
    async def sync_all_sources(self):
        """Sync data from all configured sources"""
        results = {}
        
        for source in self.configured_sources:
            try:
                connector = self.get_connector(source)
                workouts = await connector.fetch_workouts(...)
                results[source] = {"status": "success", "count": len(workouts)}
                logger.info("sync_completed", source=source, count=len(workouts))
            except RateLimitError as e:
                results[source] = {"status": "rate_limited", "retry_after": e.retry_after}
                logger.warning("rate_limit_hit", source=source)
            except Exception as e:
                results[source] = {"status": "error", "error": str(e)}
                logger.error("sync_failed", source=source, error=str(e))
                
        return results
```

## Testing Strategy

Comprehensive test coverage:

```python
# tests/test_connectors.py
@pytest.mark.asyncio
async def test_garmin_connector():
    """Test Garmin data fetching and transformation"""
    
# tests/test_deduplication.py
def test_cross_source_deduplication():
    """Test deduplication across multiple sources"""
    
# tests/test_plugins.py
def test_plugin_loading():
    """Test dynamic plugin loading and execution"""
```

## Migration Path

For existing users:
1. Preserve current Strava/VeSync data
2. Migrate to new database schema
3. Re-run deduplication with enhanced logic
4. Maintain backwards compatibility with existing analysis

This architecture makes data ingestion the core strength of athlete-performance-predictor while keeping sport-specific features modular and optional. The system works great for any athlete while offering advanced features when relevant.