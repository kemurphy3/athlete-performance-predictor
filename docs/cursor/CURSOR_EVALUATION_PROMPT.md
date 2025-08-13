# Cursor Evaluation & Enhancement Prompt

## Context
I've created a one-click fitness analysis script (`analyze_my_fitness.py`) that provides AI insights for athletes. Please evaluate this script and enhance it with the following requirements:

## Evaluation Criteria

### 1. Code Quality
- Add comprehensive type hints throughout
- Improve error handling and edge cases
- Add proper logging instead of print statements
- Ensure 90%+ test coverage potential
- Add docstrings in Google style

### 2. ML/AI Enhancements
- Implement actual ML models instead of rule-based logic
- Add the biomechanical asymmetry detection from research
- Include confidence intervals for all predictions
- Add SHAP values for explainability
- Implement the LSTM injury prediction model

### 3. Performance Optimizations
- Add caching for expensive calculations
- Implement async data loading
- Optimize pandas operations
- Add progress bars for long operations
- Enable parallel processing where applicable

### 4. Feature Additions
- **HRV Integration**: Add HRV analysis if data available
- **Sleep Analysis**: Correlate sleep with performance
- **Weather Impact**: Add weather data integration
- **Video Analysis**: Add placeholder for video upload and analysis
- **Export Options**: PDF reports, CSV data, API endpoints

### 5. Visualization Improvements
- Create more interactive Plotly dashboards
- Add biomechanical asymmetry visualizations
- Include confidence bands on predictions
- Add comparative analysis (vs other athletes)
- Create printable PDF reports

### 6. Production Readiness
- Add CLI arguments for different modes
- Create configuration file support
- Add data validation with Pydantic
- Implement proper logging with rotating files
- Add monitoring and metrics collection

## Specific Enhancements Needed

### 1. Replace Rule-Based Injury Risk
Current:
```python
def _assess_injury_risk(self, ratio: float) -> str:
    if ratio > 1.5:
        return "🔴 HIGH RISK"
```

Should be:
```python
def _assess_injury_risk(self, athlete_data: pd.DataFrame) -> Tuple[float, Dict[str, float]]:
    """ML-based injury risk with confidence intervals"""
    # Use ensemble model
    # Return probability and confidence
    # Include SHAP explanations
```

### 2. Add Biomechanical Asymmetry
```python
def calculate_asymmetry_metrics(self) -> Dict[str, float]:
    """Calculate biomechanical asymmetries from activity data"""
    # SLCMJ asymmetry
    # Hamstring imbalance
    # Stride length differences
    # Power output asymmetry
```

### 3. Implement Real ML Models
```python
class InjuryPredictor:
    def __init__(self):
        self.ensemble = self._load_pretrained_models()
        
    def predict(self, features: np.ndarray) -> InjuryRiskPrediction:
        # LSTM for temporal patterns
        # XGBoost for tabular data
        # Ensemble combination
        # Confidence intervals
```

### 4. Add Interactive Dashboard
```python
def create_streamlit_app():
    """Create full Streamlit application"""
    st.title("🏃 Athlete Performance Analyzer")
    
    # File upload
    # Real-time analysis
    # Interactive visualizations
    # Export functionality
    # Historical comparisons
```

### 5. Performance Metrics
Add these calculations:
- VO2max estimation from running data
- Lactate threshold estimation
- Running economy trends
- Power-to-weight ratios
- Fatigue index calculations

### 6. Soccer-Specific Enhancements
```python
def analyze_soccer_performance(self) -> SoccerMetrics:
    """Advanced soccer analytics"""
    # Sprint count detection
    # High-intensity running distance
    # Acceleration/deceleration loads
    # Position-specific metrics
    # Recovery between games
```

## Testing Requirements

Create comprehensive tests:
```python
# tests/test_fitness_analyzer.py
class TestFitnessAnalyzer:
    def test_injury_prediction_accuracy(self):
        # Test model achieves >85% accuracy
        
    def test_asymmetry_detection(self):
        # Test biomechanical calculations
        
    def test_nutrition_recommendations(self):
        # Validate macro calculations
        
    def test_api_performance(self):
        # Ensure <50ms response times
```

## Documentation Needs

1. Add README section on how to use the script
2. Create API documentation
3. Add example notebooks
4. Include sample data for testing
5. Create video tutorial

## Performance Benchmarks

Ensure the enhanced version meets:
- Analysis completes in <5 seconds for 1 year of data
- Memory usage <500MB
- API responses <50ms
- 90%+ test coverage
- Works with missing data gracefully

## Deliverables

1. Enhanced `analyze_my_fitness.py` with all improvements
2. New `ml_models.py` with injury prediction models
3. `streamlit_app.py` for interactive dashboard
4. Comprehensive test suite
5. Updated documentation

Please evaluate the current implementation and provide these enhancements while maintaining the user-friendly "click and go" nature of the script.