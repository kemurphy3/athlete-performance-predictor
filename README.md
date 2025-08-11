# Athlete Performance Predictor

A comprehensive fitness analytics platform that combines data from Strava activities and VeSync smart devices to provide advanced performance insights, recovery analysis, and fitness predictions.

## 🚀 Features

### Data Collection
- **Strava Integration**: Automatic collection of workout data, heart rate, GPS, and performance metrics
- **VeSync Integration**: Smart scale data (weight, body composition), sleep tracking, and environmental monitoring
- **Real-time Updates**: Automated data collection with configurable refresh intervals

### Fitness Metrics & Analysis
- **Training Load Analysis**: TRIMP (Training Impulse) calculations and acute:chronic workload ratio (ACWR)
- **Recovery Scoring**: Multi-factor recovery assessment based on training load and body composition
- **Fitness Scoring**: Comprehensive fitness level assessment with volume, intensity, and consistency components
- **Sleep-Performance Correlation**: Analysis of how sleep quality impacts athletic performance
- **Body Composition Trends**: Weight, body fat, muscle mass, and hydration monitoring
- **Environmental Impact**: Air quality, humidity, and temperature effects on performance

### Predictive Analytics
- **Performance Predictions**: 7-day ahead performance forecasting with confidence intervals
- **Injury Risk Assessment**: ACWR-based injury risk evaluation and recommendations
- **Training Optimization**: Personalized training recommendations based on current fitness state

### Visualization & Reporting
- **Interactive Dashboards**: Real-time fitness metrics visualization
- **Comprehensive Reports**: Detailed analysis reports with actionable insights
- **Trend Analysis**: Long-term performance and recovery trend identification

## 📊 What You Can Do With This Data

### 1. **Training Load Management**
- Monitor daily/weekly training volume using TRIMP scores
- Track acute:chronic workload ratio to prevent overtraining
- Identify optimal training zones and recovery periods

### 2. **Recovery Optimization**
- Get daily recovery scores based on multiple factors
- Understand how sleep, hydration, and body composition affect recovery
- Plan rest days and active recovery sessions strategically

### 3. **Performance Tracking**
- Track fitness improvements over time
- Identify performance plateaus and breakthrough periods
- Monitor consistency in training habits

### 4. **Health Monitoring**
- Track body composition changes (weight, body fat, muscle mass)
- Monitor hydration levels and their impact on performance
- Correlate environmental factors with workout quality

### 5. **Injury Prevention**
- Early warning system for overtraining using ACWR
- Personalized recommendations for training intensity adjustments
- Long-term trend analysis to identify injury risk patterns

### 6. **Goal Setting & Achievement**
- Set realistic fitness goals based on current capabilities
- Track progress toward specific performance targets
- Adjust training plans based on data-driven insights

## 🛠️ Installation & Setup

### Prerequisites
- Python 3.8+
- VeSync account with smart devices
- Strava API access (already configured in your workspace)

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables
Create a `.env` file in the project root with your VeSync credentials:

```bash
# VeSync API Credentials
VESYNC_USERNAME=your_vesync_email@example.com
VESYNC_PASSWORD=your_vesync_password
VESYNC_TIMEZONE=America/Denver

# Strava API Credentials (if not already configured)
STRAVA_CLIENT_ID=your_strava_client_id
STRAVA_CLIENT_SECRET=your_strava_client_secret
STRAVA_REFRESH_TOKEN=your_strava_refresh_token
```

### 3. Verify Device Compatibility
The system supports various VeSync devices:
- **Smart Scales**: ESWL01 and similar models for body composition
- **Air Purifiers**: Environmental monitoring capabilities
- **Sleep Tracking**: Compatible sleep monitoring devices
- **Humidifiers**: Temperature and humidity sensors

## 🚀 Usage

### 1. Collect VeSync Data
```bash
python vesync_data_collector.py
```
This will:
- Connect to your VeSync account
- Discover connected devices
- Collect current and historical data
- Save raw data to `data/raw/` directory
- Generate summary reports in `data/processed/` directory

### 2. Analyze Fitness Metrics
```bash
python fitness_metrics_analyzer.py
```
This will:
- Load combined Strava and VeSync data
- Calculate comprehensive fitness metrics
- Generate performance insights
- Create visualization plots
- Save detailed reports

### 3. Automated Data Collection
Set up cron jobs or scheduled tasks for regular data collection:
```bash
# Collect VeSync data daily at 6 AM
0 6 * * * cd /path/to/project && python vesync_data_collector.py

# Generate fitness reports weekly
0 8 * * 0 cd /path/to/project && python fitness_metrics_analyzer.py
```

## 📈 Key Metrics Explained

### TRIMP (Training Impulse)
- **Zone 1** (<120 bpm): Recovery/light training
- **Zone 2** (120-140 bpm): Aerobic base building
- **Zone 3** (140-160 bpm): Tempo training
- **Zone 4** (160-180 bpm): Threshold training
- **Zone 5** (>180 bpm): High-intensity intervals

### ACWR (Acute:Chronic Workload Ratio)
- **<0.8**: Detraining risk - increase volume gradually
- **0.8-1.3**: Optimal training zone
- **1.3-1.5**: Moderate injury risk - monitor closely
- **>1.5**: High injury risk - reduce intensity immediately

### Recovery Score Components
- **Training Load Impact**: How recent workouts affect recovery
- **ACWR Impact**: Workload balance considerations
- **Body Composition Impact**: Weight changes and hydration status
- **Sleep Quality**: Rest and recovery correlation

## 🔍 Data Structure

### VeSync Data
```json
{
  "devices": {
    "device_id": {
      "device_name": "Smart Scale",
      "device_type": "ESWL01",
      "connection_status": "online"
    }
  },
  "scale_data": [
    {
      "timestamp": "2025-01-20T08:00:00",
      "weight": 75.5,
      "body_fat": 12.3,
      "muscle_mass": 45.2,
      "water_percentage": 58.1
    }
  ],
  "sleep_data": [
    {
      "timestamp": "2025-01-20T22:00:00",
      "sleep_duration": 480,
      "sleep_quality": 85,
      "deep_sleep": 120,
      "rem_sleep": 90
    }
  ]
}
```

### Fitness Metrics Output
```json
{
  "metrics": {
    "training_load": {
      "weekly_trimp": 450,
      "current_acwr": 1.2,
      "training_volume_hours": 8.5
    },
    "recovery": {
      "average_recovery_score": 75,
      "recovery_trend": "Improving"
    },
    "fitness": {
      "average_fitness_score": 82,
      "fitness_level": "Good"
    }
  }
}
```

## 📊 Sample Insights & Use Cases

### 1. **Overtraining Detection**
- Monitor ACWR trends over time
- Set alerts when ratio exceeds 1.5
- Adjust training plans automatically

### 2. **Recovery Optimization**
- Track sleep quality vs. performance correlation
- Identify optimal sleep duration for your body
- Plan training intensity based on recovery scores

### 3. **Body Composition Goals**
- Set target weight and body fat percentages
- Monitor muscle mass changes with training
- Track hydration levels for optimal performance

### 4. **Seasonal Performance Analysis**
- Compare performance across different seasons
- Analyze environmental impact on workouts
- Plan training cycles based on historical data

## 🔧 Customization

### Adding New Metrics
The modular design allows easy addition of new fitness metrics:
1. Extend the `FitnessMetricsAnalyzer` class
2. Add new calculation methods
3. Integrate with existing reporting system

### Custom Device Support
To add support for new VeSync devices:
1. Identify device type and capabilities
2. Extend data collection methods
3. Add device-specific data processing

### API Integration
The system can be extended to integrate with:
- Garmin Connect
- Apple Health
- Google Fit
- Other fitness tracking platforms

## 📝 Troubleshooting

### Common Issues

**VeSync Connection Failed**
- Verify credentials in `.env` file
- Check internet connection
- Ensure devices are online in VeSync app

**No Data Retrieved**
- Check device compatibility
- Verify device permissions
- Review VeSync app settings

**Missing Metrics**
- Ensure sufficient historical data
- Check data quality and completeness
- Verify calculation parameters

### Debug Mode
Enable detailed logging by modifying log levels in the scripts:
```python
logging.basicConfig(level=logging.DEBUG)
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## 🛠️ Development Approach

This project embraces modern development practices including:
- **AI-Assisted Development**: Leveraging AI tools to accelerate development while maintaining code quality
- **Research-Driven Implementation**: Direct implementation of peer-reviewed research papers
- **Test-Driven Development**: Comprehensive test coverage ensuring reliability
- **Continuous Integration**: Automated testing and deployment pipelines
- **Open Source First**: Transparent development with community collaboration

I believe in using the best tools available to deliver value efficiently. See [CONTRIBUTIONS.md](CONTRIBUTIONS.md) for detailed attribution.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- VeSync for providing smart device APIs
- Strava for comprehensive fitness data
- The open-source community for data analysis libraries
- Sports science researchers whose work informed this project

## 📞 Support

For issues and questions:
1. Check the troubleshooting section
2. Review existing GitHub issues
3. Create a new issue with detailed information

---

**Ready to optimize your fitness performance? Start collecting data and unlock insights today!** 🏃‍♂️💪
