# Advanced Calorie Calculation System Implementation Prompt

## Objective
Create a sophisticated, tiered calorie calculation system that starts with basic data and evolves as more metrics become available. The system should be accurate, scalable, and integrate with external APIs for environmental data.

## Research-Based Requirements

### Core Calculation Methods (Priority Order)
1. **Heart Rate Based** (83% accuracy when combined with personal metrics)
   - Keytel et al. (2005) formulas for male/female
   - Requires: HR, age, weight, gender, duration
   - Optional: VO2max for higher accuracy
   
2. **Power/Kilojoules** (95% accuracy)
   - Direct conversion: 1 kcal = 4.184 kJ × 0.239 (human efficiency)
   - Only available for cycling with power meters

3. **MET-Based** (70% accuracy)
   - Formula: METs × weight(kg) × hours × 1.05
   - Sport-specific MET values from Compendium of Physical Activities

4. **Distance-Based** (60% accuracy)
   - Running: ~1 kcal/kg/km (flat)
   - Cycling: ~0.5 kcal/kg/km (moderate pace)

### Tiered System Architecture

```python
class CalorieCalculationTier(Enum):
    BASIC = 1      # Only duration, weight, activity type
    STANDARD = 2   # + distance, basic personal metrics
    ADVANCED = 3   # + heart rate data
    PREMIUM = 4    # + environmental data, VO2max
    ELITE = 5      # + power data, metabolic testing
```

### Data Requirements by Tier

**Tier 1 - Basic (Always Available)**
- Activity type
- Duration
- User weight
- Returns: MET-based estimate ±25% accuracy

**Tier 2 - Standard**
- All Tier 1 data
- Distance covered
- User age, gender
- Returns: Enhanced MET + distance calculations ±20% accuracy

**Tier 3 - Advanced**
- All Tier 2 data
- Heart rate (average or time series)
- Resting HR, max HR
- Returns: HR-based calculations ±15% accuracy

**Tier 4 - Premium**
- All Tier 3 data
- Environmental data (temp, humidity, elevation)
- VO2max (estimated or tested)
- Returns: Adjusted HR calculations ±10% accuracy

**Tier 5 - Elite**
- All Tier 4 data
- Power meter data
- Metabolic testing results
- Returns: Lab-quality estimates ±5% accuracy

## API Integrations

### 1. Weather API (OpenWeatherMap or WeatherAPI)
```python
# Fetch temperature, humidity, wind speed, pressure
# Only significant impact when:
# - Temp < 10°C or > 30°C (5-10% adjustment)
# - Humidity > 60% AND Temp > 25°C (up to 15% adjustment)
# - Wind > 20 km/h for cycling/running (5-10% adjustment)
```

### 2. Elevation API (Google Elevation API or MapBox)
```python
# Calculate total elevation gain/loss
# Impact: +10 calories/kg per 100m elevation gain
# Critical for trail running, hiking, mountain biking
```

### 3. Surface Type (Optional - Diminishing Returns)
```python
# Can use Overpass API for OpenStreetMap data
# Only implement if easy, as impact is minimal:
# - Grass vs turf: 5% difference
# - Road vs trail: 10-15% difference
# - Sand/snow: 20-30% difference
```

## Implementation Requirements

### 1. Adaptive Calculation Engine
```python
class AdaptiveCalorieCalculator:
    def calculate(self, workout_data: Dict) -> CalorieResult:
        # 1. Determine available data tier
        tier = self._determine_tier(workout_data)
        
        # 2. Calculate using all available methods
        results = {}
        if tier >= Tier.BASIC:
            results['met'] = self._calculate_met(...)
        if tier >= Tier.STANDARD:
            results['distance'] = self._calculate_distance(...)
        if tier >= Tier.ADVANCED:
            results['heart_rate'] = self._calculate_hr(...)
        
        # 3. Weight results by confidence
        final_calories = self._weighted_average(results, tier)
        
        # 4. Apply environmental adjustments if available
        if tier >= Tier.PREMIUM:
            final_calories *= self._environmental_factor(...)
        
        return CalorieResult(
            calories=final_calories,
            confidence=self._tier_confidence[tier],
            method_used=self._best_method(results),
            tier=tier
        )
```

### 2. Personal Model Evolution
```python
class PersonalCalorieModel:
    """Learns from user's historical data to improve accuracy"""
    
    def __init__(self, user_id: str):
        self.calibration_factor = 1.0  # Starts neutral
        self.sport_adjustments = {}    # Sport-specific calibrations
        
    def update_from_feedback(self, predicted: float, actual: float, sport: str):
        # Rolling average calibration
        error_ratio = actual / predicted
        self.calibration_factor = 0.9 * self.calibration_factor + 0.1 * error_ratio
        
        # Sport-specific adjustments
        if sport not in self.sport_adjustments:
            self.sport_adjustments[sport] = 1.0
        self.sport_adjustments[sport] = 0.9 * self.sport_adjustments[sport] + 0.1 * error_ratio
```

### 3. Activity-Specific Formulas

**Soccer/Indoor Soccer:**
```python
# Base MET: 7.0
# Adjust for intensity using HR zones:
# - Zone 2 (60-70% HRmax): × 0.7
# - Zone 3 (70-80% HRmax): × 1.0
# - Zone 4 (80-90% HRmax): × 1.3
# - Zone 5 (90-100% HRmax): × 1.5
```

**Weight Training:**
```python
# Account for work/rest ratio
# Actual work time = total time × 0.4-0.6
# Exercise-specific METs:
exercises_mets = {
    'compound_lower': 8.0,  # squats, deadlifts
    'compound_upper': 6.0,  # bench, rows
    'isolation': 3.5,       # curls, extensions
    'core': 3.8,
    'cardio_circuits': 8.0
}
```

**Running (Treadmill vs Outdoor):**
```python
# Treadmill: Base calculation × 0.95 (no wind resistance)
# Add incline factor: + (grade × 0.9 × speed × weight)
# Trail running: Base × 1.1-1.15 (terrain factor)
```

## Error Handling & Validation

1. **Data Quality Checks:**
   - HR data: Remove outliers (< 40 or > 220 bpm)
   - Distance: Validate against duration (unrealistic speeds)
   - Environmental: Use defaults if API fails

2. **Confidence Scoring:**
   ```python
   confidence = base_confidence[tier] * data_quality_score * personal_model_confidence
   ```

3. **Fallback Strategy:**
   - Always calculate MET-based estimate as fallback
   - If APIs fail, use seasonal averages for location
   - Cache environmental data for offline use

## Testing Requirements

1. **Unit Tests:**
   - Each calculation method independently
   - Tier determination logic
   - API integration fallbacks

2. **Integration Tests:**
   - Full workout calculations at each tier
   - API timeout handling
   - Data quality edge cases

3. **Validation Dataset:**
   - Compare against known good sources (research papers)
   - Test extreme conditions (ultra-endurance, HIIT, etc.)
   - Verify environmental adjustments

## Performance Considerations

1. **API Calls:**
   - Batch requests when possible
   - Cache environmental data (15-minute TTL)
   - Pre-fetch common locations

2. **Calculation Speed:**
   - Pre-compute MET lookup tables
   - Vector operations for HR time series
   - Async API calls

## User Interface Requirements

1. **Transparency:**
   - Show which tier/method was used
   - Display confidence interval
   - Explain major adjustments (weather, elevation)

2. **Settings:**
   - Allow manual tier selection
   - Environmental data opt-in/out
   - Personal metrics management

3. **Feedback Loop:**
   - Allow users to rate accuracy
   - Compare with device readings
   - Show improvement over time

## Security & Privacy

1. **API Keys:**
   - Environment variables only
   - Rotate regularly
   - Rate limit protection

2. **Personal Data:**
   - Encrypt at rest
   - GDPR compliance
   - Anonymous analytics only

## Future Enhancements

1. **Machine Learning:**
   - Personal metabolic model
   - Activity pattern recognition
   - Fatigue factor estimation

2. **Additional Integrations:**
   - Wearable device APIs
   - Nutrition tracking
   - Recovery metrics

3. **Advanced Factors:**
   - Altitude acclimatization
   - Heat adaptation
   - Training load impact

## Summary

Build a system that:
1. Always works with minimal data (Tier 1)
2. Progressively improves with more data
3. Transparently shows confidence levels
4. Learns from individual patterns
5. Integrates environmental data when beneficial
6. Maintains high performance and reliability

The environmental APIs (weather, elevation) ARE worth implementing as they provide 10-15% accuracy improvements in relevant conditions. Surface type is optional - implement only if straightforward, as the benefit is marginal.