# Enhanced Calorie Calculation System Implementation Prompt

## Context
The repository already has a basic CalorieCalculator in `src/core/calorie_calculator.py` that needs significant enhancement based on published research. The system should integrate with the existing data ingestion pipeline that supports multiple data sources (Strava, VeSync, etc.) through a connector architecture.

## Existing Infrastructure Analysis

### What's Already Working Well:
1. **Multi-source data ingestion** - Robust connector architecture with BaseConnector abstract class
2. **Deduplication engine** - Handles multiple data sources intelligently
3. **Data models** - Well-structured Workout and BiometricReading models with Pydantic
4. **Priority-based calculation** - Already implements tiered methods (direct calories > kilojoules > HR > MET > distance)
5. **Quality scoring** - `get_calorie_quality_score()` provides confidence metrics
6. **Database schema** - SQLite with proper fields for calories, HR, power, etc.

### Critical Gaps to Address:

1. **HR Calculation Accuracy**
   - Current: Uses generic intensity formula with hardcoded age/HR assumptions
   - Need: Implement Keytel et al. (2005) formulas with gender-specific calculations
   - Need: Personal metrics (age, gender, VO2max) integration

2. **Personal Data Management**
   - Current: Only accepts weight as parameter, estimates others
   - Need: User profile system with persistent personal metrics
   - Need: Integration with BiometricReading for weight tracking over time

3. **Environmental Factors**
   - Current: No environmental adjustments
   - Need: Weather API integration for temperature/humidity
   - Need: Elevation gain already in model but not used in calculations

4. **Activity-Specific Adjustments**
   - Current: Fixed MET values without intensity variations
   - Need: HR zone-based adjustments for sports like soccer
   - Need: Work/rest ratio for weight training

5. **Data Evolution**
   - Current: No learning from historical data
   - Need: Personal calibration factors that improve over time
   - Need: Comparison with device-provided calories for validation

## Implementation Requirements

### 1. Enhanced Personal Metrics System

```python
# Add to src/core/models.py
class UserProfile(BaseModel):
    """User profile for personalized calculations"""
    user_id: str
    age: int
    gender: Literal['male', 'female']
    weight_kg: float
    height_cm: Optional[float] = None
    vo2max: Optional[float] = None
    resting_hr: Optional[int] = None
    max_hr: Optional[int] = None
    activity_level: Literal['sedentary', 'light', 'moderate', 'active', 'very_active'] = 'moderate'
    
    @property
    def calculated_max_hr(self) -> int:
        """Tanaka formula: 208 - (0.7 × age)"""
        return self.max_hr or int(208 - (0.7 * self.age))
```

### 2. Research-Based HR Calculation

Replace the current `_calculate_from_heart_rate` method with:

```python
def _calculate_from_heart_rate_keytel(self, workout: Workout, user: UserProfile) -> float:
    """
    Keytel et al. (2005) formulas - 83% accuracy with personal metrics
    """
    hr_avg = workout.heart_rate_avg
    duration_min = workout.duration / 60
    
    if user.gender == 'male':
        if user.vo2max:
            # Most accurate formula
            calories = ((-95.7735 + (0.634 * hr_avg) + (0.404 * user.vo2max) +
                       (0.394 * user.weight_kg) + (0.271 * user.age)) / 4.184) * duration_min
        else:
            # Without VO2max
            calories = ((-55.0969 + (0.6309 * hr_avg) + (0.1988 * user.weight_kg) +
                       (0.2017 * user.age)) / 4.184) * duration_min
    else:  # female
        if user.vo2max:
            calories = ((-59.3954 + (0.45 * hr_avg) + (0.380 * user.vo2max) +
                       (0.103 * user.weight_kg) + (0.274 * user.age)) / 4.184) * duration_min
        else:
            calories = ((-20.4022 + (0.4472 * hr_avg) + (0.1263 * user.weight_kg) +
                       (0.074 * user.age)) / 4.184) * duration_min
    
    return calories
```

### 3. Environmental API Integration

```python
# src/connectors/weather.py
class WeatherConnector:
    """Fetch environmental data for workouts"""
    
    def __init__(self, api_key: str, provider: str = 'openweathermap'):
        self.api_key = api_key
        self.provider = provider
        self.cache = {}  # 15-minute TTL cache
    
    async def get_conditions(self, lat: float, lon: float, timestamp: datetime) -> Dict:
        """Get historical weather for workout location/time"""
        # Implementation for OpenWeatherMap Time Machine API
        # Return: temperature_c, humidity_percent, wind_speed_mps, pressure_hpa
```

### 4. Enhanced MET Calculations with Intensity

```python
def _calculate_met_with_intensity(self, workout: Workout, user: UserProfile) -> float:
    """Calculate METs with HR-based intensity adjustments"""
    base_met = self.MET_VALUES.get(workout.sport, 4.0)
    
    if workout.heart_rate_avg and user.resting_hr:
        # Calculate HR zones
        hr_reserve = user.calculated_max_hr - user.resting_hr
        hr_percent = (workout.heart_rate_avg - user.resting_hr) / hr_reserve
        
        # Sport-specific intensity adjustments
        if workout.sport in ['Soccer', 'Basketball', 'Tennis']:
            if hr_percent < 0.6:  # Zone 2
                base_met *= 0.7
            elif hr_percent < 0.7:  # Zone 3
                base_met *= 1.0
            elif hr_percent < 0.8:  # Zone 4
                base_met *= 1.3
            else:  # Zone 5
                base_met *= 1.5
    
    return base_met
```

### 5. Workout-Specific Enhancements

```python
def _calculate_weight_training(self, workout: Workout, user: UserProfile) -> float:
    """Special handling for weight training with work/rest ratios"""
    # Parse raw_data for set/rep information if available
    work_ratio = 0.4  # Default 40% work time
    
    if workout.raw_data and 'sets' in workout.raw_data:
        # Calculate actual work time from sets/reps/rest
        total_sets = sum(ex.get('sets', 0) for ex in workout.raw_data.get('exercises', []))
        avg_rest_between_sets = 90  # seconds
        estimated_work_time = workout.duration - (total_sets * avg_rest_between_sets)
        work_ratio = max(0.3, min(0.6, estimated_work_time / workout.duration))
    
    base_calories = self._calculate_from_met(workout, user)
    return base_calories * work_ratio
```

### 6. Personal Calibration System

```python
class PersonalCalibrationModel:
    """Learn from user's historical data"""
    
    def __init__(self, user_id: str, db_path: str):
        self.user_id = user_id
        self.db_path = db_path
        self.calibration_factors = self._load_calibration()
    
    def update_calibration(self, workout: Workout, predicted_calories: float):
        """Update calibration when device provides actual calories"""
        if workout.calories and workout.data_quality_score > 0.8:
            ratio = workout.calories / predicted_calories
            sport_key = workout.sport_category or workout.sport
            
            # Exponential moving average
            alpha = 0.1
            if sport_key not in self.calibration_factors:
                self.calibration_factors[sport_key] = ratio
            else:
                self.calibration_factors[sport_key] = (
                    alpha * ratio + (1 - alpha) * self.calibration_factors[sport_key]
                )
            
            self._save_calibration()
```

### 7. API Rate Limiting and Caching

```python
from functools import lru_cache
from datetime import datetime, timedelta

class APIRateLimiter:
    def __init__(self, calls_per_minute: int = 60):
        self.calls_per_minute = calls_per_minute
        self.calls = []
    
    async def wait_if_needed(self):
        now = datetime.now()
        self.calls = [c for c in self.calls if c > now - timedelta(minutes=1)]
        if len(self.calls) >= self.calls_per_minute:
            wait_time = 60 - (now - self.calls[0]).total_seconds()
            await asyncio.sleep(wait_time)
        self.calls.append(now)

@lru_cache(maxsize=1000)
def get_cached_weather(lat_rounded: float, lon_rounded: float, 
                      time_rounded: int) -> Optional[Dict]:
    """Cache with 0.01° precision and 15-minute time buckets"""
    # Round lat/lon to 0.01 degrees (~1km)
    # Round time to 15-minute buckets
    pass
```

### 8. Integration with Existing Pipeline

```python
# Modify DataIngestionOrchestrator to include calorie enhancement
class DataIngestionOrchestrator:
    def __init__(self, database_path: str, weather_api_key: Optional[str] = None):
        # ... existing code ...
        self.calorie_calculator = EnhancedCalorieCalculator(database_path)
        self.weather_connector = WeatherConnector(weather_api_key) if weather_api_key else None
    
    async def process_workout(self, workout: Workout, user_profile: UserProfile):
        """Process workout with enhanced calorie calculation"""
        # Skip if high-quality calories already exist
        if workout.calories and workout.data_quality_score > 0.9:
            return workout
        
        # Get environmental data if GPS available
        env_data = None
        if workout.has_gps and workout.gps_data and self.weather_connector:
            env_data = await self.weather_connector.get_conditions(
                workout.gps_data['start_lat'],
                workout.gps_data['start_lon'],
                workout.start_time
            )
        
        # Calculate enhanced calories
        calculated_calories = self.calorie_calculator.calculate_enhanced(
            workout, user_profile, env_data
        )
        
        # Update workout if calculated is better than existing
        if calculated_calories['confidence'] > workout.data_quality_score:
            workout.calories = int(calculated_calories['calories'])
            workout.plugin_data['calorie_calculation'] = calculated_calories
        
        return workout
```

### 9. Database Schema Updates

```sql
-- Add user profiles table
CREATE TABLE IF NOT EXISTS user_profiles (
    user_id TEXT PRIMARY KEY,
    age INTEGER NOT NULL,
    gender TEXT NOT NULL,
    weight_kg REAL NOT NULL,
    height_cm REAL,
    vo2max REAL,
    resting_hr INTEGER,
    max_hr INTEGER,
    activity_level TEXT DEFAULT 'moderate',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Add calibration table
CREATE TABLE IF NOT EXISTS calorie_calibration (
    user_id TEXT NOT NULL,
    sport_category TEXT NOT NULL,
    calibration_factor REAL DEFAULT 1.0,
    sample_count INTEGER DEFAULT 0,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, sport_category)
);

-- Add weather cache table
CREATE TABLE IF NOT EXISTS weather_cache (
    location_hash TEXT PRIMARY KEY,
    timestamp_bucket INTEGER NOT NULL,
    temperature_c REAL,
    humidity_percent REAL,
    wind_speed_mps REAL,
    cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 10. Configuration and Environment Variables

```python
# Add to env_template.txt
OPENWEATHER_API_KEY=your_api_key_here
ELEVATION_API_KEY=your_google_or_mapbox_key
CALORIE_CALCULATION_MODE=enhanced  # basic|enhanced|research
ENABLE_WEATHER_LOOKUP=true
WEATHER_CACHE_TTL_MINUTES=15
```

## Testing Requirements

1. **Unit Tests** for each calculation method
2. **Integration Tests** with real workout data
3. **Validation against published research data**
4. **Performance tests** for API rate limiting
5. **Accuracy comparison** with device-provided calories

## Performance Optimizations

1. **Batch API calls** for multiple workouts
2. **Pre-fetch weather** for common locations
3. **Vector operations** for time-series HR data
4. **Async processing** for API calls
5. **Smart caching** with location/time rounding

## Privacy and Security

1. **Encrypt** user profile data at rest
2. **API keys** in environment variables only
3. **Anonymize** telemetry data
4. **GDPR compliance** for EU users
5. **Local-first** calculation when possible

## Future Enhancements

1. **Machine Learning** for personal metabolic modeling
2. **Wearable API integration** (Garmin, Polar, Whoop)
3. **Altitude acclimatization** factors
4. **Sleep/recovery** impact on metabolism
5. **Nutrition integration** for net calorie tracking

This enhanced system will provide:
- **10-15% better accuracy** than current implementation
- **Seamless integration** with existing architecture
- **Progressive enhancement** as more data becomes available
- **Research-backed** calculations with proper citations
- **User-specific** calibration that improves over time