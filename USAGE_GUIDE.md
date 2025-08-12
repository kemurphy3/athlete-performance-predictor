# 🚀 **Complete Usage Guide - Multi-Source Fitness Data Platform**

## **Quick Start - New CLI System**

### **🎯 The New Command-Line Interface**
**Entry Point**: `python -m src.cli --help`  
**Purpose**: Unified interface for all platform features  
**Architecture**: Multi-source data ingestion with intelligent deduplication

**What It Does**:
- ✅ Connects to multiple fitness data sources (Strava, Garmin, Fitbit, WHOOP, Oura, Withings)
- ✅ Intelligently deduplicates overlapping workout and biometric records
- ✅ Provides ML-based injury prediction and performance analysis
- ✅ Exports clean data to Parquet, CSV, or feeds into analysis pipeline
- ✅ Works with any subset of connectors configured

---

## **🔌 Data Source Connectors**

### **📱 Available Data Sources**
The platform supports multiple fitness data sources that can be configured independently:

#### **Strava API** (Required for existing functionality)
- **What**: Running, cycling, swimming activities
- **Setup**: OAuth2 authentication with client ID and secret
- **Data**: GPS routes, heart rate, power, cadence, elevation

#### **Garmin Connect**
- **What**: Comprehensive fitness and health data
- **Setup**: Username/password or OAuth authentication
- **Data**: Activities, biometrics, sleep, stress, body composition

#### **Fitbit**
- **What**: Activity tracking and health monitoring
- **Setup**: OAuth2 with client ID and secret
- **Data**: Steps, heart rate, sleep, exercise, nutrition

#### **WHOOP**
- **What**: Advanced recovery and strain tracking
- **Setup**: API key authentication
- **Data**: Strain, recovery, sleep, HRV, respiratory rate

#### **Oura Ring**
- **What**: Sleep and recovery optimization
- **Setup**: Personal access token
- **Data**: Sleep stages, readiness, activity, HRV

#### **Withings**
- **What**: Smart scales and health monitors
- **Setup**: OAuth2 with client ID and secret
- **Data**: Weight, body composition, blood pressure, sleep

#### **VeSync** (Legacy integration)
- **What**: Smart scales and environmental sensors
- **Setup**: Username/password authentication
- **Data**: Body composition, air quality, temperature

---

## **⚙️ Configuration & Setup**

### **Step 1: Environment Configuration**
```bash
# Copy the template
copy env_template.txt .env

# Edit .env with your API credentials
# Only fill in the sources you want to use
```

### **Step 2: Required Credentials**
```bash
# Minimum setup (Strava only)
STRAVA_CLIENT_ID=your_strava_client_id
STRAVA_CLIENT_SECRET=your_strava_client_secret
STRAVA_REFRESH_TOKEN=your_strava_refresh_token

# Optional: Add more sources as you get access
GARMIN_USERNAME=your_garmin_username
GARMIN_PASSWORD=your_garmin_password
FITBIT_CLIENT_ID=your_fitbit_client_id
WHOOP_API_KEY=your_whoop_api_key
OURA_ACCESS_TOKEN=your_oura_token
```

### **Step 3: Security Keys**
```bash
# Generate encryption key (32 bytes, base64 encoded)
python -c "import base64; import os; print(base64.b64encode(os.urandom(32)).decode())"

# Generate JWT secret (32 bytes, hex encoded)
python -c "import secrets; print(secrets.token_hex(32))"
```

---

## **🚀 Core Commands**

### **🔐 Authentication Management**
```bash
# List configured data sources
python -m src.cli auth --list

# Authenticate with specific source
python -m src.cli auth garmin
python -m src.cli auth fitbit
python -m src.cli auth whoop
```

### **📡 Data Synchronization**
```bash
# Sync all configured sources
python -m src.cli sync

# Sync last 30 days
python -m src.cli sync --days 30

# Sync specific sources only
python -m src.cli sync --source garmin,strava

# Force refresh of all data
python -m src.cli sync --force
```

### **🔬 Analysis & ML**
```bash
# Run comprehensive fitness analysis
python -m src.cli analyze

# Run analysis with specific plugin
python -m src.cli analyze --plugin ball_sports

# Custom date range analysis
python -m src.cli analyze --start-date 2024-01-01 --end-date 2024-12-31
```

### **📤 Data Export**
```bash
# Export to Parquet (recommended)
python -m src.cli export --format parquet

# Export to CSV
python -m src.cli export --format csv --output fitness_data.csv

# Export specific data types
python -m src.cli export --format parquet --type workouts
python -m src.cli export --format parquet --type biometrics
```

### **📊 System Status**
```bash
# Check sync status and data summaries
python -m src.cli status

# View data source health
python -m src.cli status --detailed

# Check database statistics
python -m src.cli status --database
```

---

## **🎯 Feature-Specific Usage**

### **🏃 Movement Pattern Analysis**
**New Feature**: Automatically detects sprint patterns and training style from GPS and heart rate data

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

### **⚡ Sprint Pattern Detection**
**Purpose**: Identify when you're doing high-intensity training

**Detection Methods**:
1. **Speed Threshold**: >8 mph (7:30 min/mile pace)
2. **Heart Rate Zones**: Zone 4-5 (>80% max HR)
3. **Duration Analysis**: Short, intense efforts
4. **Combined Scoring**: Multi-factor intensity assessment

### **🧠 ML Injury Prediction**
**New Feature**: Ensemble-based injury risk assessment with confidence intervals

**Models Used**:
- **XGBoost**: High-performance gradient boosting
- **Random Forest**: Robust ensemble method
- **Gradient Boosting**: Additional ensemble diversity
- **Ensemble Combination**: Weighted voting for final predictions

**Features**:
- **Biomechanical Asymmetry**: SLCMJ, hamstring, knee valgus, Y-balance, hip rotation
- **Training Load**: Acute:Chronic Workload Ratio (ACWR) with ML enhancement
- **Confidence Intervals**: Bootstrap-based uncertainty quantification
- **SHAP Explainability**: Understand why predictions are made

---

## **📊 Data Requirements**

### **Minimum Data for Analysis**
- **Activities**: At least 10 activities with dates and types
- **GPS Data**: Distance, duration, and pace information
- **Heart Rate**: Average heart rate for intensity analysis
- **Time Range**: At least 4 weeks of data for trends

### **Optimal Data for Best Results**
- **Activities**: 3+ months of consistent data
- **Multi-Source Integration**: Combine Strava + Garmin + Fitbit + WHOOP
- **Heart Rate Zones**: Resting and max HR configured
- **Activity Types**: Mix of running, cycling, and other sports

### **Data Quality Features**
- **Automatic Deduplication**: Removes overlapping records from multiple sources
- **Data Validation**: Pydantic models ensure data integrity
- **Quality Scoring**: Each record gets a 0-1 quality score
- **Source Precedence**: Higher quality sources take priority when merging

---

## **🚨 Troubleshooting**

### **Common Issues**

**"No data sources configured"**
- Check your `.env` file has at least one data source configured
- Verify API credentials are correct
- Test connection with `python -m src.cli auth --list`

**"Authentication failed for [source]"**
- Verify API credentials in `.env` file
- Check if the service is experiencing downtime
- Ensure your account has API access enabled

**"ML assessment unavailable"**
- Install required packages: `pip install -r requirements.txt`
- Check that your data has sufficient features for ML analysis
- Verify database connection and data availability

**"Database connection failed"**
- Check if `data/` directory exists
- Ensure SQLite is working on your system
- Verify file permissions

### **Performance Issues**
- **Slow Analysis**: Use smaller date ranges for initial testing
- **Memory Issues**: Close other applications during analysis
- **Sync Timeouts**: Increase timeout values in `.env` file

---

## **🎯 Best Practices**

### **For Optimal Results**
1. **Regular Data Collection**: Run sync daily or weekly
2. **Consistent Activity Logging**: Log all workouts in your primary platform
3. **Multi-Source Integration**: Combine data from multiple sources for comprehensive analysis
4. **Regular Analysis**: Run analysis weekly for trend tracking

### **Training Recommendations**
1. **Monitor Training Load**: Keep acute:chronic workload ratio 0.8-1.3
2. **Recovery Tracking**: Pay attention to sleep and body composition
3. **Sprint Training**: Include 1-2 sprint sessions per week
4. **Asymmetry Monitoring**: Address imbalances before they become injuries

---

## **🔮 Advanced Usage**

### **Plugin System**
```bash
# Enable ball sports analysis (soccer, basketball, etc.)
python -m src.cli analyze --plugin ball_sports

# Custom plugin development
# Create plugins in src/plugins/ directory
```

### **Custom Analysis**
```python
from src.core.data_ingestion import DataIngestionOrchestrator
from src.ml.ml_models import InjuryRiskPredictor

# Create orchestrator
orchestrator = DataIngestionOrchestrator()

# Get your data
workouts = orchestrator.get_workouts()
biometrics = orchestrator.get_biometrics()

# Run custom analysis
predictor = InjuryRiskPredictor()
risk_assessment = predictor.predict_injury_risk(workouts, biometrics)
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
1. **Start Simple**: Use `python -m src.cli sync` first
2. **Explore Analysis**: Try `python -m src.cli analyze` for insights
3. **Add Sources**: Gradually add more data sources as you get access
4. **Regular Analysis**: Make this part of your training routine

---

## **🎉 You're Ready!**

**Start Here**: `python -m src.cli --help`  
**Sync Data**: `python -m src.cli sync`  
**Get Insights**: `python -m src.cli analyze`  
**Export Data**: `python -m src.cli export --format parquet`  

**Your multi-source fitness data platform is ready to provide insights you never knew existed!** 🏃‍♂️💪

---

## **🔄 Migration from Old System**

### **If You Have Existing Data**
1. **Backup**: Copy your existing `data/` directory
2. **Run Migration**: `python -m src.cli migrate` (when implemented)
3. **Verify**: Check data integrity with `python -m src.cli status`
4. **Clean Up**: Remove old CSV files after verification

### **What's Changed**
- **New Architecture**: `src/` directory structure
- **Database**: SQLite instead of CSV files
- **Multi-Source**: Support for multiple fitness platforms
- **CLI Interface**: Unified command-line interface
- **Deduplication**: Automatic handling of overlapping data
