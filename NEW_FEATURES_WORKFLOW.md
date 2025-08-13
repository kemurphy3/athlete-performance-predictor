# New Features Workflow Guide

## Overview
This document provides step-by-step instructions for using the three new features implemented in your Athlete Performance Predictor project. Follow these workflows in order to ensure proper setup and functionality.

---

## 🚨 **CRITICAL: Database Schema Update Required**

**Before using any new features, you MUST update your database schema to support multi-athlete functionality.**

### Step 1: Database Migration
```bash
# Navigate to your project directory
cd /c/Users/kemur/Git/athlete-performance-predictor

# Run the database migration to add athlete_id columns
python -m src.cli db migrate
```

**If this fails, you may need to manually update your database schema. See troubleshooting section below.**

---

## 🔥 **Feature 1: Enhanced Multi-Athlete Calorie System**

### What It Does
- Calculates calories for multiple athletes
- Gracefully degrades when data is missing
- Provides calibration and estimation capabilities

### How to Use
```bash
# Basic calorie calculation for default athlete
python -m src.cli analyze calories

# Calculate for specific athlete
python -m src.cli analyze calories --athlete-id "athlete_001"

# Calculate with custom date range
python -m src.cli analyze calories --start-date "2024-01-01" --end-date "2024-12-31"
```

### Expected Output
- Calorie calculations for each athlete
- Data quality indicators
- Calibration factors
- Estimation confidence levels

---

## 📊 **Feature 2: Single-Click Yearly Analysis Script**

### What It Does
- Comprehensive yearly fitness review
- Performance metrics analysis
- Health and training load assessment
- AI-generated insights and recommendations

### How to Use
```bash
# Basic yearly analysis (default athlete, past 365 days)
python analyze_year.py

# Verbose output for debugging
python analyze_year.py --verbose

# Custom athlete and time period
python analyze_year.py --athlete-id "athlete_001" --days 180
```

### Expected Output
- Console summary with key metrics
- JSON report saved to `data/reports/`
- Performance trends and patterns
- Injury risk assessment
- Personalized recommendations

### Troubleshooting Common Issues

#### Issue 1: "get_connector() missing 1 required positional argument: 'config'"
**Cause:** The connector initialization is missing configuration parameters.

**Solution:**
```bash
# Check if you have environment variables set
cat .env

# If .env is missing, copy from template
cp env_template.txt .env

# Edit .env with your API keys
notepad .env
```

**Required Environment Variables:**
```bash
STRAVA_CLIENT_ID=your_strava_client_id
STRAVA_CLIENT_SECRET=your_strava_client_secret
STRAVA_REFRESH_TOKEN=your_strava_refresh_token
VESYNC_EMAIL=your_vesync_email
VESYNC_PASSWORD=your_vesync_password
```

#### Issue 2: "no such column: athlete_id"
**Cause:** Database schema hasn't been updated for multi-athlete support.

**Solution:**
```bash
# Force database recreation (WARNING: This will delete existing data)
python -m src.cli db reset

# Or manually add columns (advanced users only)
python -c "
import sqlite3
conn = sqlite3.connect('data/fitness_data.db')
cursor = conn.cursor()
cursor.execute('ALTER TABLE workouts ADD COLUMN athlete_id TEXT DEFAULT \"default\"')
cursor.execute('ALTER TABLE biometrics ADD COLUMN athlete_id TEXT DEFAULT \"default\"')
cursor.execute('CREATE TABLE IF NOT EXISTS athletes (id TEXT PRIMARY KEY, name TEXT, created_at TIMESTAMP)')
cursor.execute('CREATE TABLE IF NOT EXISTS athlete_profiles (athlete_id TEXT PRIMARY KEY, age INTEGER, weight REAL, height REAL, activity_level TEXT)')
conn.commit()
conn.close()
print('Database schema updated successfully')
"
```

#### Issue 3: "Analysis failed: 'acwr_ratio'"
**Cause:** Missing data prevents calculation of training load metrics.

**Solution:**
```bash
# Check if you have workout data
python -c "
import sqlite3
conn = sqlite3.connect('data/fitness_data.db')
cursor = conn.cursor()
cursor.execute('SELECT COUNT(*) FROM workouts')
print(f'Total workouts: {cursor.fetchone()[0]}')
cursor.execute('SELECT COUNT(*) FROM biometrics')
print(f'Total biometrics: {cursor.fetchone()[0]}')
conn.close()
"

# If no data, sync from your data sources first
python -m src.cli sync strava
python -m src.cli sync vesync
```

---

## 🎯 **Feature 3: AI-Powered Fitness Dashboard**

### What It Does
- Interactive Streamlit dashboard with 5 tabs
- AI-powered insights and Q&A
- Real-time data visualization
- Comprehensive fitness analytics

### How to Use
```bash
# Launch the dashboard
python launch_dashboard.py

# Or launch directly with Streamlit
streamlit run src/visualization/ai_dashboard.py

# Launch with custom port
streamlit run src/visualization/ai_dashboard.py --server.port 8502
```

### Dashboard Tabs
1. **Overview:** Summary metrics and key insights
2. **Performance:** Training load, pace trends, heart rate zones
3. **Health:** Weight, body composition, resting heart rate
4. **AI Insights:** Automated analysis and recommendations
5. **Ask AI:** Interactive Q&A with your fitness data

### Expected Behavior
- Dashboard opens in your default browser
- Real-time data loading and visualization
- Interactive charts and filters
- AI-generated insights and recommendations

### Troubleshooting Dashboard Issues

#### Issue 1: "ModuleNotFoundError: No module named 'streamlit'"
**Solution:**
```bash
pip install streamlit plotly pandas numpy
```

#### Issue 2: Dashboard loads but shows no data
**Solution:**
```bash
# Check database connection
python -c "
import sqlite3
try:
    conn = sqlite3.connect('data/fitness_data.db')
    print('Database connection successful')
    conn.close()
except Exception as e:
    print(f'Database connection failed: {e}')
"

# Verify data exists
python -c "
import sqlite3
conn = sqlite3.connect('data/fitness_data.db')
cursor = conn.cursor()
cursor.execute('SELECT name FROM sqlite_master WHERE type=\"table\"')
tables = cursor.fetchall()
print('Available tables:', [t[0] for t in tables])
conn.close()
"
```

---

## 🔧 **Complete Setup Workflow**

### Step-by-Step Setup
```bash
# 1. Navigate to project directory
cd /c/Users/kemur/Git/athlete-performance-predictor

# 2. Install/update dependencies
pip install -r requirements.txt

# 3. Set up environment variables
cp env_template.txt .env
# Edit .env with your API keys

# 4. Update database schema
python -m src.cli db migrate

# 5. Sync data from sources
python -m src.cli sync strava
python -m src.cli sync vesync

# 6. Test calorie system
python -m src.cli analyze calories

# 7. Test yearly analysis
python analyze_year.py --verbose

# 8. Launch dashboard
python launch_dashboard.py
```

---

## 📋 **Troubleshooting Checklist**

- [ ] Environment variables configured in `.env`
- [ ] Database schema updated (athlete_id columns exist)
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] Data sources synced successfully
- [ ] Database contains workout and biometric data
- [ ] No Python import errors
- [ ] API keys are valid and working

---

## 🆘 **Getting Help**

If you encounter issues not covered in this guide:

1. **Check the logs:** Look for error messages in the console output
2. **Verify data:** Ensure your database contains the expected data
3. **Test components:** Try each feature individually to isolate issues
4. **Check dependencies:** Verify all required packages are installed
5. **Review environment:** Confirm API keys and configuration are correct

---

## 📊 **Expected Results**

After successful setup, you should have:
- ✅ Multi-athlete calorie calculations working
- ✅ Yearly analysis generating comprehensive reports
- ✅ Interactive dashboard with real-time data
- ✅ AI-powered insights and recommendations
- ✅ Seamless data flow between all components

This workflow ensures you can systematically test and troubleshoot each feature while building toward a fully functional athlete performance prediction system.
