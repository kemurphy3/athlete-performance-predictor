# 🚀 **Complete Usage Guide - Athlete Performance Predictor**

## **Quick Start - One-Click Analysis**

### **🎯 The "Click and Go" Script**
**File**: `analyze_my_fitness.py`  
**Purpose**: Complete fitness analysis with one command  
**Command**: `python analyze_my_fitness.py`

**What It Does**:
- ✅ Loads all your Strava and VeSync data
- ✅ Calculates training load and injury risk
- ✅ Analyzes movement patterns and sprint detection
- ✅ Generates ML-based predictions
- ✅ Creates comprehensive report
- ✅ Saves results to timestamped file

**Output**: Complete analysis report with key insights and recommendations

---

## **📊 Interactive Dashboard**

### **🎨 Streamlit Dashboard**
**File**: `streamlit_app.py`  
**Purpose**: Interactive web interface for real-time analysis  
**Command**: `streamlit run streamlit_app.py`

**Features**:
- 📁 **File Upload**: Drag & drop your fitness data
- 🔬 **Real-Time Analysis**: Live processing with progress bars
- 📈 **Interactive Charts**: Zoom, pan, and hover on Plotly visualizations
- 📋 **Export Options**: PDF reports, CSV data, Excel files
- ⚙️ **Settings**: Customize analysis parameters

**Navigation**:
1. **📊 Dashboard**: Overview and quick stats
2. **🔬 Analysis**: Detailed ML analysis and injury risk
3. **📈 Visualizations**: Interactive charts and trends
4. **📋 Reports**: Generate and export reports
5. **⚙️ Settings**: Configure system preferences

---

## **🤖 Advanced ML Features**

### **🧠 Machine Learning Models**
**File**: `ml_models.py`  
**Purpose**: Advanced injury prediction and biomechanical analysis

**Key Capabilities**:
- **Injury Risk Prediction**: Ensemble models (XGBoost, Random Forest, Gradient Boosting)
- **Biomechanical Asymmetry**: Detects imbalances using research-based thresholds
- **Confidence Intervals**: Bootstrap-based uncertainty quantification
- **SHAP Explainability**: Understand why predictions are made

**Usage**: Automatically integrated into main analysis

---

## **📡 Data Collection**

### **📱 VeSync Integration**
**File**: `vesync_data_collector.py`  
**Purpose**: Collect data from smart scales, sleep trackers, and environmental sensors

**What It Collects**:
- ⚖️ **Body Composition**: Weight, body fat, muscle mass, hydration
- 😴 **Sleep Data**: Duration, quality, deep/REM sleep
- 🌡️ **Environmental**: Air quality, humidity, temperature

**Command**: `python vesync_data_collector.py`

---

## **🔧 Step-by-Step Usage Workflow**

### **Step 1: Initial Setup**
```bash
# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp env_template.txt .env
# Edit .env with your VeSync and Strava credentials
```

### **Step 2: Collect Data**
```bash
# Collect VeSync data (smart scales, sleep, etc.)
python vesync_data_collector.py

# Your Strava data should already be in data/activities.csv
```

### **Step 3: Run Analysis**
```bash
# Option 1: One-click comprehensive analysis
python analyze_my_fitness.py

# Option 2: Interactive dashboard
streamlit run streamlit_app.py
```

### **Step 4: Review Results**
- 📄 **Text Report**: Generated automatically with timestamp
- 📊 **Interactive Charts**: Available in Streamlit dashboard
- 📈 **Export Options**: PDF, CSV, Excel formats

---

## **🎯 Feature-Specific Usage**

### **🏃 Movement Pattern Analysis**
**New Feature**: Automatically detects sprint patterns and training style

**What It Analyzes**:
- **Sprint Detection**: Identifies high-intensity efforts using pace and heart rate
- **Training Style**: Determines if you're doing steady-state vs. interval training
- **Movement Efficiency**: Calculates speed-to-heart-rate ratios
- **Pace Variability**: Measures consistency between training sessions

**How It Works**:
1. **Pace Analysis**: Converts pace to speed, detects >8 mph efforts
2. **Heart Rate Zones**: Categorizes intensity using your max HR
3. **Duration Patterns**: Identifies short, intense efforts
4. **Rolling Averages**: Smooths data to detect trends

**Example Output**:
```json
{
  "sprint_patterns": {
    "summary": {
      "sprint_frequency": "25%",
      "training_style": "Interval",
      "recommendation": "Good balance of sprint and recovery runs"
    }
  }
}
```

### **⚡ Sprint Pattern Detection**
**Purpose**: Identify when you're doing high-intensity training

**Detection Methods**:
1. **Speed Threshold**: >8 mph (7:30 min/mile pace)
2. **Heart Rate Zones**: Zone 4-5 (>80% max HR)
3. **Duration Analysis**: Short, intense efforts
4. **Combined Scoring**: Multi-factor intensity assessment

**Recommendations**:
- **Low Sprint Frequency**: Add 1-2 sprint sessions per week
- **High Sprint Frequency**: Ensure adequate recovery
- **Balanced**: Maintain current training structure

---

## **📊 Data Requirements**

### **Minimum Data for Analysis**
- **Activities**: At least 10 activities with dates and types
- **GPS Data**: Distance, duration, and pace information
- **Heart Rate**: Average heart rate for intensity analysis
- **Time Range**: At least 4 weeks of data for trends

### **Optimal Data for Best Results**
- **Activities**: 3+ months of consistent data
- **VeSync Integration**: Body composition and sleep tracking
- **Heart Rate Zones**: Resting and max HR configured
- **Activity Types**: Mix of running, cycling, and other sports

---

## **🚨 Troubleshooting**

### **Common Issues**

**"No GPS activities found"**
- Ensure activities have 'type' column with 'Run', 'Ride', or 'Walk'
- Check that 'distance_miles' column exists and has values > 0

**"ML assessment unavailable"**
- Install required packages: `pip install xgboost shap scikit-learn`
- Check that your data has sufficient features for ML analysis

**"VeSync connection failed"**
- Verify credentials in `.env` file
- Ensure devices are online in VeSync app
- Check internet connection

### **Performance Issues**
- **Slow Analysis**: Use smaller date ranges for initial testing
- **Memory Issues**: Close other applications during analysis
- **Dashboard Lag**: Reduce data size or use text analysis instead

---

## **🎯 Best Practices**

### **For Optimal Results**
1. **Regular Data Collection**: Run VeSync collector daily
2. **Consistent Activity Logging**: Log all workouts in Strava
3. **Heart Rate Monitoring**: Use HR monitor during activities
4. **Regular Analysis**: Run analysis weekly for trend tracking

### **Training Recommendations**
1. **Monitor ACWR**: Keep acute:chronic workload ratio 0.8-1.3
2. **Recovery Tracking**: Pay attention to sleep and body composition
3. **Sprint Training**: Include 1-2 sprint sessions per week
4. **Asymmetry Monitoring**: Address imbalances before they become injuries

---

## **🔮 Advanced Usage**

### **Custom Analysis**
```python
from analyze_my_fitness import FitnessAnalyzer

# Create custom analyzer
analyzer = FitnessAnalyzer()

# Run specific analyses
movement_patterns = analyzer.analyze_movement_patterns()
sprint_patterns = analyzer.detect_sprint_patterns()
injury_risk = analyzer.assess_injury_risk_ml(analyzer.activities)
```

### **Integration with Other Tools**
- **Jupyter Notebooks**: Import functions for custom analysis
- **API Development**: Use classes as backend for web services
- **Data Pipeline**: Integrate with ETL processes
- **Monitoring Systems**: Set up automated analysis schedules

---

## **📞 Getting Help**

### **When You Need Support**
1. **Check This Guide**: Most questions answered here
2. **Review Error Messages**: Clear error descriptions provided
3. **Check Data Quality**: Ensure your data meets requirements
4. **Review Logs**: Detailed logging for troubleshooting

### **Next Steps**
1. **Start Simple**: Use `analyze_my_fitness.py` first
2. **Explore Dashboard**: Try Streamlit for interactive experience
3. **Customize Profile**: Update athlete profile in the script
4. **Regular Analysis**: Make this part of your training routine

---

## **🎉 You're Ready!**

**Start Here**: `python analyze_my_fitness.py`  
**Explore More**: `streamlit run streamlit_app.py`  
**Customize**: Edit athlete profile in the script  
**Track Progress**: Run analysis weekly for trends  

**Your fitness data is about to reveal insights you never knew existed!** 🏃‍♂️💪
