# Enhanced Multi-Athlete Calorie Calculation System - Final Implementation

## Overview
This prompt enhances the existing calorie calculation system to support multiple athletes with robust handling of missing data. The system gracefully degrades from research-grade accuracy (83%) to basic estimates (50%) based on available data.

## Key Requirements

### 1. Multi-Athlete Architecture from Day One

#### Update Data Models
```python
# src/core/models.py - ADD athlete_id to existing models

class Workout(BaseModel):
    # ... existing fields ...
    athlete_id: str = Field(..., description="Unique athlete identifier")
    # ... rest of fields ...

class BiometricReading(BaseModel):
    # ... existing fields ...
    athlete_id: str = Field(..., description="Unique athlete identifier")
    # ... rest of fields ...

class Athlete(BaseModel):
    """Core athlete profile - NEW MODEL"""
    athlete_id: str = Field(..., description="Unique identifier")
    name: str = Field(..., description="Athlete name")
    email: Optional[str] = Field(None, description="Contact email")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    active: bool = Field(True, description="Whether athlete is active")
    
# Update UserProfile to link with athlete
class UserProfile(BaseModel):
    # Change user_id to athlete_id
    athlete_id: str = Field(..., description="Links to athlete record")
    # ... rest of existing fields ...
```

#### Database Schema Updates
```sql
-- Add athlete_id to existing tables
ALTER TABLE workouts ADD COLUMN athlete_id TEXT NOT NULL DEFAULT 'default';
ALTER TABLE biometrics ADD COLUMN athlete_id TEXT NOT NULL DEFAULT 'default';

-- Create indexes for performance
CREATE INDEX idx_workouts_athlete ON workouts(athlete_id, start_time DESC);
CREATE INDEX idx_biometrics_athlete ON biometrics(athlete_id, date DESC);

-- Create athletes table
CREATE TABLE IF NOT EXISTS athletes (
    athlete_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT UNIQUE,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Update user_profiles to athlete_profiles
ALTER TABLE user_profiles RENAME TO athlete_profiles;
ALTER TABLE athlete_profiles RENAME COLUMN user_id TO athlete_id;

-- Multi-athlete data sources
CREATE TABLE IF NOT EXISTS athlete_data_sources (
    athlete_id TEXT NOT NULL,
    source_name TEXT NOT NULL,
    auth_token TEXT,
    refresh_token TEXT,
    expires_at TIMESTAMP,
    last_sync TIMESTAMP,
    PRIMARY KEY (athlete_id, source_name),
    FOREIGN KEY (athlete_id) REFERENCES athletes(athlete_id)
);

-- Per-athlete calibration
CREATE TABLE IF NOT EXISTS athlete_calorie_calibration (
    athlete_id TEXT NOT NULL,
    sport_category TEXT NOT NULL,
    calibration_factor REAL DEFAULT 1.0,
    sample_count INTEGER DEFAULT 0,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (athlete_id, sport_category)
);
```

### 2. Robust Missing Data Handling

The existing `EnhancedCalorieCalculator` already handles missing data well, but we need to enhance it for multi-athlete support:

```python
class MultiAthleteCalorieCalculator(EnhancedCalorieCalculator):
    """Enhanced calculator with multi-athlete support and robust defaults"""
    
    def __init__(self, database_path: str):
        super().__init__(database_path)
        self.athlete_profiles_cache = {}
        self.calibration_cache = {}
        
    def calculate_for_athlete(self, workout: Workout, athlete_id: Optional[str] = None) -> CalorieCalculationResult:
        """
        Calculate calories for specific athlete with graceful degradation
        
        Handles missing data by falling back through calculation methods:
        1. Direct calories from device (95% accuracy)
        2. Power/kilojoules (90% accuracy)
        3. HR + personal profile (83% accuracy)
        4. HR + default profile (75% accuracy)
        5. MET + personal profile (70% accuracy)
        6. MET + default profile (60% accuracy)
        7. Distance estimate (50% accuracy)
        """
        # Use athlete_id from workout if not provided
        if not athlete_id:
            athlete_id = getattr(workout, 'athlete_id', 'default')
        
        # Try to load athlete profile, fall back to defaults
        athlete_profile = self._get_or_create_athlete_profile(athlete_id)
        
        # Get athlete-specific calibration
        calibration_factor = self._get_calibration_factor(athlete_id, workout.sport)
        
        # Calculate using parent class enhanced method
        result = super().calculate_enhanced(workout, athlete_profile)
        
        # Apply athlete-specific calibration
        if calibration_factor != 1.0:
            result.calories = int(result.calories * calibration_factor)
            result.factors['calibration_factor'] = calibration_factor
            result.factors['athlete_id'] = athlete_id
        
        # Store result for future calibration if device provided calories
        if workout.calories and result.method != "direct_strava":
            self._update_calibration(athlete_id, workout.sport, workout.calories, result.calories)
        
        return result
    
    def _get_or_create_athlete_profile(self, athlete_id: str) -> UserProfile:
        """Get athlete profile with intelligent defaults for missing data"""
        
        # Check cache first
        if athlete_id in self.athlete_profiles_cache:
            return self.athlete_profiles_cache[athlete_id]
        
        # Try to load from database
        profile = self._load_athlete_profile(athlete_id)
        
        if not profile:
            # Create minimal profile with smart defaults
            profile = self._create_minimal_profile(athlete_id)
        
        # Fill in missing data with estimates
        profile = self._enhance_profile_with_estimates(profile, athlete_id)
        
        # Cache for performance
        self.athlete_profiles_cache[athlete_id] = profile
        
        return profile
    
    def _create_minimal_profile(self, athlete_id: str) -> UserProfile:
        """Create minimal profile when no data exists"""
        
        # Try to estimate from recent workouts
        estimates = self._estimate_from_workout_history(athlete_id)
        
        return UserProfile(
            athlete_id=athlete_id,
            age=estimates.get('age', 35),  # Conservative default
            gender=estimates.get('gender', 'male'),
            weight_kg=estimates.get('weight', 70.0),
            activity_level=estimates.get('activity_level', 'moderate')
        )
    
    def _estimate_from_workout_history(self, athlete_id: str) -> Dict[str, Any]:
        """Estimate athlete characteristics from their workout patterns"""
        
        estimates = {}
        
        try:
            with sqlite3.connect(self.database_path) as conn:
                # Estimate activity level from workout frequency
                cursor = conn.execute("""
                    SELECT COUNT(*) as workout_count,
                           AVG(duration) as avg_duration,
                           AVG(heart_rate_avg) as avg_hr
                    FROM workouts
                    WHERE athlete_id = ? AND start_time > date('now', '-30 days')
                """, (athlete_id,))
                
                row = cursor.fetchone()
                if row:
                    workout_count = row[0]
                    if workout_count > 20:
                        estimates['activity_level'] = 'very_active'
                    elif workout_count > 12:
                        estimates['activity_level'] = 'active'
                    elif workout_count > 6:
                        estimates['activity_level'] = 'moderate'
                    else:
                        estimates['activity_level'] = 'light'
                
                # Try to get weight from recent biometric readings
                cursor = conn.execute("""
                    SELECT value FROM biometrics
                    WHERE athlete_id = ? AND metric_type = 'weight'
                    ORDER BY date_value DESC LIMIT 1
                """, (athlete_id,))
                
                row = cursor.fetchone()
                if row:
                    estimates['weight'] = row[0]
                    
        except Exception as e:
            self.logger.warning(f"Could not estimate athlete data: {e}")
        
        return estimates
    
    def _enhance_profile_with_estimates(self, profile: UserProfile, athlete_id: str) -> UserProfile:
        """Fill in missing profile data with intelligent estimates"""
        
        # Estimate VO2max from workout performance if missing
        if not profile.vo2max:
            vo2max_estimate = self._estimate_vo2max_from_workouts(athlete_id, profile)
            if vo2max_estimate:
                profile.vo2max = vo2max_estimate
        
        # Estimate resting HR from morning readings if missing
        if not profile.resting_hr:
            resting_hr = self._estimate_resting_hr(athlete_id)
            if resting_hr:
                profile.resting_hr = resting_hr
        
        return profile
    
    def _update_calibration(self, athlete_id: str, sport: str, actual_calories: int, 
                           predicted_calories: int):
        """Update athlete-specific calibration factor"""
        
        if predicted_calories <= 0:
            return
        
        ratio = actual_calories / predicted_calories
        
        # Sanity check - ignore outliers
        if ratio < 0.5 or ratio > 2.0:
            self.logger.warning(f"Ignoring outlier calibration ratio: {ratio}")
            return
        
        try:
            with sqlite3.connect(self.database_path) as conn:
                conn.execute("""
                    INSERT INTO athlete_calorie_calibration 
                    (athlete_id, sport_category, calibration_factor, sample_count, last_updated)
                    VALUES (?, ?, ?, 1, CURRENT_TIMESTAMP)
                    ON CONFLICT(athlete_id, sport_category) DO UPDATE SET
                        calibration_factor = (calibration_factor * sample_count + ?) / (sample_count + 1),
                        sample_count = sample_count + 1,
                        last_updated = CURRENT_TIMESTAMP
                """, (athlete_id, sport, ratio, ratio))
                
            # Update cache
            cache_key = f"{athlete_id}:{sport}"
            self.calibration_cache[cache_key] = ratio
            
        except Exception as e:
            self.logger.error(f"Failed to update calibration: {e}")
```

### 3. Handle Various Data Source Limitations

```python
class DataSourceAdapter:
    """Adapt various data sources to provide consistent data"""
    
    @staticmethod
    def normalize_workout_data(workout: Dict[str, Any], source: str) -> Dict[str, Any]:
        """Normalize workout data from different sources"""
        
        normalized = {}
        
        # Map source-specific fields to standard fields
        field_mappings = {
            'strava': {
                'id': 'external_id',
                'start_date': 'start_time',
                'elapsed_time': 'duration',
                'type': 'sport',
                'average_heartrate': 'heart_rate_avg',
                'max_heartrate': 'heart_rate_max',
                'total_elevation_gain': 'elevation_gain',
                'kilojoules': 'kilojoules'
            },
            'garmin': {
                'activityId': 'external_id',
                'startTimeLocal': 'start_time',
                'duration': 'duration',
                'activityType': 'sport',
                'averageHR': 'heart_rate_avg',
                'maxHR': 'heart_rate_max',
                'elevationGain': 'elevation_gain',
                'calories': 'calories'
            },
            'apple_health': {
                'identifier': 'external_id',
                'startDate': 'start_time',
                'duration': 'duration',
                'workoutActivityType': 'sport',
                'averageHeartRate': 'heart_rate_avg',
                'activeEnergyBurned': 'calories'
            }
        }
        
        mapping = field_mappings.get(source, {})
        
        for source_field, standard_field in mapping.items():
            if source_field in workout:
                normalized[standard_field] = workout[source_field]
        
        # Handle missing duration by calculating from start/end times
        if 'duration' not in normalized and 'start_time' in normalized and 'end_time' in workout:
            start = datetime.fromisoformat(normalized['start_time'])
            end = datetime.fromisoformat(workout['end_time'])
            normalized['duration'] = int((end - start).total_seconds())
        
        # Estimate missing heart rate from perceived exertion
        if 'heart_rate_avg' not in normalized and 'perceived_exertion' in workout:
            # Rough estimate: RPE 6-20 scale maps to 60-200 HR
            rpe = workout['perceived_exertion']
            normalized['heart_rate_avg'] = 60 + (rpe * 10)
        
        return normalized
```

### 4. API Integration Updates

```python
# Update CLI for multi-athlete support
@app.command()
def add_athlete(name: str, email: Optional[str] = None, 
                age: Optional[int] = None, gender: Optional[str] = None,
                weight_kg: Optional[float] = None):
    """Add a new athlete to the system"""
    athlete_id = str(uuid.uuid4())
    
    # Create athlete record
    athlete = Athlete(
        athlete_id=athlete_id,
        name=name,
        email=email
    )
    
    # Create minimal profile if data provided
    if age and gender and weight_kg:
        profile = UserProfile(
            athlete_id=athlete_id,
            age=age,
            gender=gender,
            weight_kg=weight_kg
        )
        # Save profile to database
    
    print(f"Created athlete: {name} (ID: {athlete_id})")

@app.command()
def calculate_calories(athlete_id: str, start_date: str, end_date: str):
    """Calculate calories for an athlete's workouts"""
    calculator = MultiAthleteCalorieCalculator(database_path)
    
    # Get workouts for athlete
    workouts = get_athlete_workouts(athlete_id, start_date, end_date)
    
    results = []
    for workout in workouts:
        result = calculator.calculate_for_athlete(workout, athlete_id)
        results.append({
            'date': workout.start_time,
            'sport': workout.sport,
            'duration': workout.duration,
            'calories': result.calories,
            'method': result.method,
            'confidence': result.confidence
        })
    
    # Display results
    print(f"Calculated calories for {len(workouts)} workouts")
    print(f"Average confidence: {np.mean([r['confidence'] for r in results]):.2f}")
```

### 5. Graceful Degradation Examples

```python
# Example 1: Full data available (83% accuracy)
workout_full = Workout(
    athlete_id="athlete_123",
    sport="Run",
    duration=3600,
    heart_rate_avg=155,
    distance=10000,
    elevation_gain=100
)
profile_full = UserProfile(
    athlete_id="athlete_123",
    age=30, gender="male", weight_kg=75,
    vo2max=50, resting_hr=55, max_hr=190
)
# Result: Uses Keytel formula with all parameters

# Example 2: Only basic data (60% accuracy)
workout_basic = Workout(
    athlete_id="athlete_456",
    sport="Soccer",
    duration=5400  # Only duration known
)
# No profile exists - system creates default
# Result: Uses MET calculation with estimated profile

# Example 3: Partial HR data (70% accuracy)
workout_partial = Workout(
    athlete_id="athlete_789",
    sport="WeightTraining",
    duration=3600,
    heart_rate_avg=125  # Have HR but no user profile
)
# Result: Uses HR formula with default age/gender assumptions
```

### 6. Configuration for Missing Data Tolerance

```yaml
# config/calorie_calculation.yml
calculation_settings:
  min_confidence_threshold: 0.5  # Don't return results below 50% confidence
  
  # Fallback defaults when data missing
  defaults:
    age: 35  # Conservative middle age
    gender_distribution: 0.7  # 70% male assumption for unknown
    weight_kg: 70  # Global average
    height_cm: 170
    resting_hr: 70
    
  # Method preferences by data availability
  method_priority:
    - direct_device_calories
    - power_kilojoules
    - heart_rate_personal
    - heart_rate_estimated
    - met_intensity_adjusted
    - met_basic
    - distance_estimated
    
  # Calibration settings
  calibration:
    min_samples_required: 5  # Need 5 workouts before applying calibration
    outlier_threshold: 0.5  # Ignore calibrations outside 50-200% range
    exponential_smoothing_alpha: 0.1  # How quickly to adapt
```

## Testing Strategy

1. **Unit Tests** - Test each calculation method with missing data
2. **Integration Tests** - Test multi-athlete scenarios
3. **Validation Tests** - Compare against known research data
4. **Degradation Tests** - Verify graceful fallback through methods

## Key Benefits

1. **Multi-Athlete Ready** - No migration needed later
2. **Robust to Missing Data** - Works with minimal information
3. **Improves Over Time** - Learns from each athlete's data
4. **Transparent** - Shows confidence and method used
5. **Research-Based** - Uses validated formulas when possible

This implementation ensures the system works for any athlete with any amount of data, while maximizing accuracy when full data is available.