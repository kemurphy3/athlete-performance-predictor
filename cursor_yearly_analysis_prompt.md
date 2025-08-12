# Single-Click Yearly Analysis Script - Implementation Prompt

## Objective
Create a command-line script that generates comprehensive fitness insights for the past year with a single command, combining Strava activities with VeSync biometric data.

## Script Requirements

### 1. Core Functionality
```python
# Usage: python analyze_year.py [--athlete-id ATHLETE_ID] [--days DAYS]
# Default: Analyzes past 365 days for default athlete
```

### 2. Data Collection Phase
- Automatically sync all configured data sources
- Handle missing credentials gracefully
- Show progress indicators during sync
- Fall back to cached data if sync fails

### 3. Analysis Components

#### A. Performance Metrics
```python
performance_metrics = {
    'fitness_progression': calculate_fitness_trend(),  # CTL/ATL/TSB
    'pace_improvements': analyze_pace_changes(),
    'endurance_gains': measure_endurance_progress(),
    'strength_gains': analyze_power_metrics(),
    'consistency_score': calculate_workout_consistency()
}
```

#### B. Health Indicators
```python
health_indicators = {
    'resting_hr_trend': analyze_resting_hr(),
    'recovery_metrics': calculate_recovery_quality(),
    'weight_changes': track_weight_from_vesync(),
    'body_composition': analyze_body_metrics(),
    'sleep_quality': estimate_from_morning_hr()  # If available
}
```

#### C. Training Load Analysis
```python
training_load = {
    'acute_load': calculate_7day_load(),
    'chronic_load': calculate_28day_load(),
    'load_ratio': acute_load / chronic_load,
    'injury_risk': assess_injury_risk_level(),
    'fatigue_score': estimate_current_fatigue()
}
```

#### D. Sport-Specific Insights

**For Soccer:**
```python
soccer_insights = {
    'sprint_analysis': {
        'sprint_count': estimate_from_hr_spikes(),
        'high_intensity_minutes': time_above_85_percent_hr(),
        'recovery_between_sprints': analyze_hr_recovery_periods()
    },
    'movement_patterns': {
        'steady_jog_time': time_in_zone2(),
        'explosive_efforts': count_hr_accelerations(),
        'positional_estimate': guess_from_hr_patterns()
    },
    'match_readiness': calculate_match_fitness()
}
```

**For Running:**
```python
running_insights = {
    'pace_zones': analyze_pace_distribution(),
    'vo2max_estimate': estimate_from_pace_hr_relationship(),
    'race_predictions': {
        '5k': predict_5k_time(),
        '10k': predict_10k_time(),
        'half_marathon': predict_half_time()
    },
    'training_balance': assess_easy_vs_hard_ratio()
}
```

### 4. AI-Style Insights Generation

```python
def generate_ai_insights(metrics):
    insights = []
    
    # Training Load Insights
    if metrics['training_load']['injury_risk'] > 0.7:
        insights.append({
            'type': 'warning',
            'title': 'High Injury Risk Detected',
            'message': f"Your training load has increased {metrics['load_increase']}% "
                      f"in the past 2 weeks. Consider a recovery week.",
            'recommendation': 'Reduce volume by 30% this week or add 2 rest days'
        })
    
    # Fitness Improvement
    if metrics['fitness_progression']['improvement'] > 10:
        insights.append({
            'type': 'achievement',
            'title': 'Significant Fitness Gains',
            'message': f"Your fitness has improved {metrics['fitness_progression']['improvement']}% "
                      f"over the past 3 months!",
            'recommendation': 'Maintain current training rhythm'
        })
    
    # Recovery Needs
    if metrics['health_indicators']['resting_hr_elevated']:
        insights.append({
            'type': 'health',
            'title': 'Elevated Resting Heart Rate',
            'message': 'Your resting HR is 5+ bpm above normal',
            'recommendation': 'Take an easy day or rest day today'
        })
    
    return insights
```

### 5. Output Formats

#### Console Output (Pretty)
```
🏃 FITNESS YEAR IN REVIEW - 2024
════════════════════════════════════════════

📊 OVERALL STATISTICS
├─ Total Workouts: 287
├─ Total Time: 312.5 hours
├─ Total Distance: 2,847 km
├─ Calories Burned: 187,432
└─ Consistency: 78% (5.5 workouts/week)

💪 FITNESS PROGRESSION
├─ VO2max Estimate: 48 → 52 (+8.3%)
├─ FTP Estimate: 245W → 265W (+8.2%)
└─ Resting HR: 58 → 55 (-5.2%)

⚡ PERFORMANCE HIGHLIGHTS
├─ Fastest 5K: 19:32 (Oct 15)
├─ Longest Run: 21.1 km (Nov 3)
└─ Best Soccer Match: 92 min, 843 cal

⚠️  ATTENTION NEEDED
├─ Injury Risk: MODERATE (load ratio: 1.4)
├─ Fatigue Level: HIGH
└─ Recommended Action: 2-3 easy days

🎯 PERSONALIZED RECOMMENDATIONS
1. Your running pace has improved 6% - consider signing up for a race
2. Add 1 strength training session per week for injury prevention
3. Your Tuesday/Thursday pattern is working well - keep it up!
```

#### JSON Report (Detailed)
```json
{
  "period": {
    "start": "2023-12-01",
    "end": "2024-12-01"
  },
  "athlete": {
    "id": "athlete_123",
    "name": "John Doe"
  },
  "summary_stats": {...},
  "performance_metrics": {...},
  "health_indicators": {...},
  "training_load": {...},
  "sport_specific": {...},
  "ai_insights": [...],
  "recommendations": [...],
  "raw_data": {
    "monthly_breakdown": [...],
    "weekly_patterns": [...],
    "workout_distribution": {...}
  }
}
```

### 6. Implementation Details

#### Use Existing Infrastructure
```python
from src.core.multi_athlete_calorie_calculator import MultiAthleteCalorieCalculator
from src.core.data_ingestion import DataIngestionOrchestrator
from src.connectors import get_connector

async def main():
    # Initialize components
    orchestrator = DataIngestionOrchestrator(DB_PATH)
    calculator = MultiAthleteCalorieCalculator(DB_PATH)
    
    # Get athlete profile
    athlete_id = args.athlete_id or 'default'
    profile = await orchestrator.get_athlete_profile(athlete_id)
    
    # Sync data
    await orchestrator.sync_all_sources(start_date, end_date)
    
    # Run analysis
    metrics = await analyze_year_data(athlete_id)
    
    # Generate insights
    insights = generate_ai_insights(metrics)
    
    # Display results
    display_pretty_output(metrics, insights)
    save_json_report(metrics, insights)
```

#### Key Calculations

**Fitness Trend (CTL/ATL):**
```python
def calculate_fitness_trend(workouts):
    # Chronic Training Load (42-day average)
    ctl = calculate_exponential_average(workouts, 42)
    
    # Acute Training Load (7-day average)
    atl = calculate_exponential_average(workouts, 7)
    
    # Training Stress Balance
    tsb = ctl - atl
    
    return {
        'fitness': ctl,
        'fatigue': atl,
        'form': tsb
    }
```

**Injury Risk Assessment:**
```python
def assess_injury_risk(load_ratio, fatigue_score, recovery_quality):
    risk_score = 0
    
    # Load ratio component (40%)
    if load_ratio > 1.5:
        risk_score += 0.4
    elif load_ratio > 1.3:
        risk_score += 0.3
    elif load_ratio > 1.1:
        risk_score += 0.2
    
    # Fatigue component (30%)
    risk_score += (fatigue_score * 0.3)
    
    # Recovery component (30%)
    risk_score += ((1 - recovery_quality) * 0.3)
    
    return {
        'score': risk_score,
        'level': 'HIGH' if risk_score > 0.7 else 'MODERATE' if risk_score > 0.4 else 'LOW'
    }
```

### 7. Error Handling

```python
try:
    results = await sync_data()
except CredentialsError:
    print("⚠️  Missing credentials. Using cached data...")
    results = load_cached_data()
except NetworkError:
    print("⚠️  Network error. Using offline analysis...")
    results = analyze_local_data()
```

### 8. Testing Requirements

1. Test with various data availability scenarios
2. Verify calculations match research formulas
3. Test with multiple athletes
4. Validate injury risk predictions
5. Ensure graceful degradation

### 9. Future Enhancements

- Email report delivery
- Comparison with previous years
- Goal setting for next year
- Export to training platforms
- Integration with coaching tools

This script should provide immediate value while building on the existing multi-athlete infrastructure.