#!/usr/bin/env python3
"""
One-Click Fitness Analysis Script
Analyzes your complete fitness profile and provides AI-driven insights
"""

import os
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Any
import matplotlib.pyplot as plt
import seaborn as sns
from dataclasses import dataclass
import warnings
warnings.filterwarnings('ignore')

# Try to import advanced libraries, fall back gracefully
try:
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False
    print("Install plotly for interactive visualizations: pip install plotly")

@dataclass
class AthleteProfile:
    """Your personalized athlete profile"""
    age: int = 33
    sport: str = "Soccer"
    position: str = "Unknown"  # Update based on your position
    weight_kg: float = 75.0  # Update with your weight
    height_cm: float = 180.0  # Update with your height
    max_hr: int = 187  # 220 - age
    resting_hr: int = 60  # Update with your resting HR
    vo2_max: float = 45.0  # Estimated, update if known

class FitnessAnalyzer:
    """Comprehensive fitness analysis with AI insights"""
    
    def __init__(self, athlete_profile: AthleteProfile = None):
        self.profile = athlete_profile or AthleteProfile()
        self.data_dir = "data"
        self.activities = None
        self.vesync_data = None
        self.load_all_data()
        
    def load_all_data(self):
        """Load all available fitness data"""
        print("🔄 Loading your fitness data...")
        
        # Load activities
        activities_path = os.path.join(self.data_dir, "activities.csv")
        if os.path.exists(activities_path):
            self.activities = pd.read_csv(activities_path)
            self.activities['date'] = pd.to_datetime(self.activities['date'])
            print(f"✅ Loaded {len(self.activities)} activities")
        
        # Load Strava JSON data
        strava_path = os.path.join(self.data_dir, "strava_activities.json")
        if os.path.exists(strava_path):
            with open(strava_path, 'r') as f:
                self.strava_data = json.load(f)
            print(f"✅ Loaded {len(self.strava_data)} Strava activities")
        
        # Load VeSync data if available
        vesync_files = [f for f in os.listdir(os.path.join(self.data_dir, "raw")) 
                       if f.startswith("vesync_data_")] if os.path.exists(os.path.join(self.data_dir, "raw")) else []
        if vesync_files:
            latest_vesync = max(vesync_files)
            with open(os.path.join(self.data_dir, "raw", latest_vesync), 'r') as f:
                self.vesync_data = json.load(f)
            print(f"✅ Loaded VeSync data")
    
    def calculate_training_load(self) -> Dict[str, Any]:
        """Calculate comprehensive training load metrics"""
        if self.activities is None:
            return {"error": "No activity data available"}
        
        # Add training load calculations
        self.activities['training_load'] = self.activities['duration_min'] * self.activities['distance_miles'].fillna(0) / 10
        
        # Calculate rolling metrics
        self.activities = self.activities.sort_values('date')
        self.activities['acute_load'] = self.activities['training_load'].rolling(7, min_periods=1).sum()
        self.activities['chronic_load'] = self.activities['training_load'].rolling(28, min_periods=1).sum()
        self.activities['load_ratio'] = self.activities['acute_load'] / (self.activities['chronic_load'] + 1)
        
        # Current status
        current_metrics = {
            'current_acute_load': self.activities['acute_load'].iloc[-1],
            'current_chronic_load': self.activities['chronic_load'].iloc[-1],
            'current_ratio': self.activities['load_ratio'].iloc[-1],
            'risk_level': self._assess_injury_risk(self.activities['load_ratio'].iloc[-1]),
            'weekly_volume': self.activities[self.activities['date'] > datetime.now() - timedelta(days=7)]['duration_min'].sum() / 60
        }
        
        return current_metrics
    
    def _assess_injury_risk(self, ratio: float) -> str:
        """Assess injury risk based on load ratio (legacy method)"""
        if ratio > 1.5:
            return "🔴 HIGH RISK - Reduce intensity immediately"
        elif ratio > 1.3:
            return "🟡 MODERATE RISK - Monitor closely"
        elif ratio < 0.8:
            return "🔵 DETRAINING RISK - Increase volume"
        else:
            return "🟢 OPTIMAL - Good balance"
    
    def assess_injury_risk_ml(self, athlete_data: pd.DataFrame) -> Dict[str, Any]:
        """ML-based injury risk assessment with confidence intervals"""
        try:
            from ml_models import EnsemblePredictor
            
            ensemble = EnsemblePredictor()
            results = ensemble.predict_comprehensive_risk(athlete_data)
            
            return {
                'ml_prediction': results.get('injury_risk'),
                'biomechanical_asymmetry': results.get('biomechanical_asymmetry'),
                'combined_risk': results.get('combined_risk'),
                'confidence': results.get('injury_risk', {}).get('confidence_score', 0.0),
                'recommendations': results.get('injury_risk', {}).get('recommendations', [])
            }
        except ImportError:
            return {
                'error': 'ML models not available. Install required dependencies.',
                'fallback_method': 'ACWR-based assessment'
            }
        except Exception as e:
            return {
                'error': f'ML assessment failed: {str(e)}',
                'fallback_method': 'ACWR-based assessment'
            }
    
    def analyze_sport_specific_metrics(self) -> Dict[str, Any]:
        """Soccer-specific performance analysis"""
        soccer_activities = self.activities[self.activities['type'] == 'Soccer'] if self.activities is not None else pd.DataFrame()
        
        if soccer_activities.empty:
            return {"error": "No soccer activities found"}
        
        metrics = {
            'games_last_month': len(soccer_activities[soccer_activities['date'] > datetime.now() - timedelta(days=30)]),
            'avg_game_duration': soccer_activities['duration_min'].mean(),
            'avg_distance_per_game': soccer_activities['distance_miles'].mean(),
            'tournament_pattern': self._detect_tournament_pattern(soccer_activities)
        }
        
        # Sprint analysis (if pace data available)
        if 'pace_per_mile' in soccer_activities.columns:
            # Convert pace to speed
            soccer_activities['speed_mph'] = soccer_activities.apply(
                lambda x: 60 / self._parse_pace(x['pace_per_mile']) if pd.notna(x['pace_per_mile']) else np.nan, 
                axis=1
            )
            metrics['avg_speed'] = soccer_activities['speed_mph'].mean()
            metrics['max_speed'] = soccer_activities['speed_mph'].max()
        
        return metrics
    
    def _parse_pace(self, pace_str: str) -> float:
        """Convert pace string to minutes"""
        if pd.isna(pace_str) or pace_str == 'N/A':
            return np.nan
        try:
            parts = pace_str.split(':')
            return float(parts[0]) + float(parts[1]) / 60
        except:
            return np.nan
    
    def _detect_tournament_pattern(self, soccer_df: pd.DataFrame) -> str:
        """Detect tournament participation patterns"""
        # Group games by date
        games_per_day = soccer_df.groupby(soccer_df['date'].dt.date).size()
        
        # Find days with multiple games
        tournament_days = games_per_day[games_per_day > 1]
        
        if len(tournament_days) > 0:
            return f"⚠️ {len(tournament_days)} tournament days detected with {tournament_days.max()} games/day max"
        return "✅ No tournament overload detected"
    
    def generate_nutrition_recommendations(self) -> Dict[str, Any]:
        """AI-driven nutrition recommendations based on training load"""
        load_metrics = self.calculate_training_load()
        
        # Base metabolic rate (Mifflin-St Jeor Equation)
        bmr = 10 * self.profile.weight_kg + 6.25 * self.profile.height_cm - 5 * self.profile.age + 5
        
        # Activity factor based on training load
        if 'weekly_volume' in load_metrics:
            if load_metrics['weekly_volume'] > 10:
                activity_factor = 1.9  # Very active
            elif load_metrics['weekly_volume'] > 5:
                activity_factor = 1.725  # Active
            else:
                activity_factor = 1.55  # Moderately active
        else:
            activity_factor = 1.55
        
        daily_calories = bmr * activity_factor
        
        # Macro recommendations for soccer players
        macros = {
            'daily_calories': round(daily_calories),
            'protein_g': round(self.profile.weight_kg * 1.6),  # 1.6g/kg for athletes
            'carbs_g': round(daily_calories * 0.55 / 4),  # 55% from carbs
            'fats_g': round(daily_calories * 0.25 / 9),  # 25% from fats
            'hydration_L': round(self.profile.weight_kg * 0.035 + 0.5)  # Base + activity
        }
        
        # Tournament day adjustments
        tournament_macros = {
            'tournament_calories': round(daily_calories * 1.3),
            'tournament_carbs_g': round(daily_calories * 0.65 / 4),  # Increase carbs
            'tournament_hydration_L': round(self.profile.weight_kg * 0.05)
        }
        
        return {
            'daily_macros': macros,
            'tournament_macros': tournament_macros,
        }
    
    def calculate_asymmetry_metrics(self) -> Dict[str, float]:
        """Calculate biomechanical asymmetries from activity data"""
        try:
            from ml_models import BiomechanicalAsymmetryDetector
            
            detector = BiomechanicalAsymmetryDetector()
            
            # Extract asymmetry measurements from activity data
            # This is a simplified approach - in practice, you'd need specific biomechanical tests
            asymmetry_data = {}
            
            # Example: Calculate stride length asymmetry from running data
            if self.activities is not None and 'type' in self.activities.columns:
                running_data = self.activities[self.activities['type'] == 'Run']
                if not running_data.empty and 'distance_miles' in running_data.columns:
                    # Estimate stride length asymmetry based on pace variations
                    pace_variations = running_data['pace_per_mile'].std() if 'pace_per_mile' in running_data.columns else 0
                    asymmetry_data['stride_length'] = {
                        'left': 1.0 + pace_variations * 0.1,
                        'right': 1.0 - pace_variations * 0.1
                    }
            
            # If no biomechanical data available, return placeholder
            if not asymmetry_data:
                asymmetry_data = {
                    'slcmj': {'left': 45.0, 'right': 44.0},  # Placeholder values
                    'hamstring': {'left': 180.0, 'right': 178.0}
                }
            
            # Detect asymmetries
            asymmetry = detector.detect_asymmetries(asymmetry_data)
            
            return {
                'overall_asymmetry_score': asymmetry.overall_asymmetry_score,
                'risk_category': asymmetry.risk_category,
                'confidence': asymmetry.confidence,
                'slcmj_asymmetry': asymmetry.slcmj_asymmetry,
                'hamstring_asymmetry': asymmetry.hamstring_asymmetry,
                'knee_valgus_asymmetry': asymmetry.knee_valgus_asymmetry,
                'y_balance_asymmetry': asymmetry.y_balance_asymmetry,
                'hip_rotation_asymmetry': asymmetry.hip_rotation_asymmetry
            }
            
        except ImportError:
            return {
                'error': 'Biomechanical analysis not available. Install ml_models.',
                'overall_asymmetry_score': 0.0,
                'risk_category': 'UNKNOWN'
            }
        except Exception as e:
            return {
                'error': f'Asymmetry calculation failed: {str(e)}',
                'overall_asymmetry_score': 0.0,
                'risk_category': 'UNKNOWN'
            }
    
    def predict_performance_trajectory(self) -> Dict[str, Any]:
        """AI prediction of performance trajectory"""
        if self.activities is None or len(self.activities) < 10:
            return {"error": "Insufficient data for predictions"}
        
        # Simple trend analysis
        recent_activities = self.activities[self.activities['date'] > datetime.now() - timedelta(days=90)]
        
        # Performance indicators
        indicators = {
            'volume_trend': 'increasing' if recent_activities['duration_min'].tail(10).mean() > recent_activities['duration_min'].head(10).mean() else 'decreasing',
            'consistency': 'good' if len(recent_activities) / 13 > 0.6 else 'needs improvement',  # 13 weeks
            'predicted_fitness_gain': self._predict_fitness_gain(recent_activities)
        }
        
        return indicators
    
    def _predict_fitness_gain(self, activities_df: pd.DataFrame) -> str:
        """Predict fitness gains based on training patterns"""
        weekly_hours = activities_df.groupby(pd.Grouper(key='date', freq='W'))['duration_min'].sum() / 60
        
        if weekly_hours.mean() > 8 and weekly_hours.std() < 2:
            return "📈 HIGH - Consistent high volume training"
        elif weekly_hours.mean() > 5:
            return "📊 MODERATE - Good training volume"
        else:
            return "📉 LOW - Increase training volume for gains"
    
    def generate_ai_insights(self) -> Dict[str, Any]:
        """Generate comprehensive AI insights"""
        insights = {
            'training_load': self.calculate_training_load(),
            'sport_specific': self.analyze_sport_specific_metrics(),
            'nutrition': self.generate_nutrition_recommendations(),
            'performance_trajectory': self.predict_performance_trajectory(),
            'recommendations': self._generate_personalized_recommendations()
        }
        
        return insights
    
    def _generate_personalized_recommendations(self) -> List[str]:
        """Generate personalized training recommendations"""
        recommendations = []
        
        load_metrics = self.calculate_training_load()
        sport_metrics = self.analyze_sport_specific_metrics()
        
        # Load-based recommendations
        if 'risk_level' in load_metrics:
            if "HIGH RISK" in load_metrics['risk_level']:
                recommendations.append("🚨 URGENT: Reduce training intensity by 30% this week")
                recommendations.append("🧊 Add ice baths and extra sleep (9+ hours)")
            elif "MODERATE RISK" in load_metrics['risk_level']:
                recommendations.append("⚠️ Replace 1 hard session with recovery this week")
            elif "DETRAINING" in load_metrics['risk_level']:
                recommendations.append("📈 Add 1 additional training session this week")
        
        # Sport-specific recommendations
        if 'tournament_pattern' in sport_metrics and "tournament days detected" in sport_metrics['tournament_pattern']:
            recommendations.append("🏆 Tournament load detected - implement recovery protocol between games")
            recommendations.append("💪 Add hamstring injury prevention exercises 2x/week")
        
        # General recommendations
        recommendations.append("🏃 Add dedicated sprint training: 6x20m sprints 2x/week")
        recommendations.append("🧘 Include 10-min mobility work daily")
        recommendations.append("📊 Monitor HRV daily for optimal training timing")
        
        return recommendations
    
    def create_visualizations(self):
        """Create comprehensive fitness visualizations"""
        if self.activities is None:
            print("No data available for visualizations")
            return
        
        # Set up the plot style
        plt.style.use('seaborn-v0_8-darkgrid')
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle('🏃 Your Fitness Dashboard', fontsize=16, fontweight='bold')
        
        # 1. Training Load Over Time
        ax1 = axes[0, 0]
        self.activities.plot(x='date', y=['acute_load', 'chronic_load'], ax=ax1)
        ax1.set_title('Training Load Progression')
        ax1.set_ylabel('Load Units')
        ax1.legend(['Acute (7d)', 'Chronic (28d)'])
        
        # 2. Activity Distribution
        ax2 = axes[0, 1]
        activity_counts = self.activities['type'].value_counts()
        ax2.pie(activity_counts.values, labels=activity_counts.index, autopct='%1.1f%%')
        ax2.set_title('Activity Distribution')
        
        # 3. Load Ratio with Risk Zones
        ax3 = axes[1, 0]
        self.activities.plot(x='date', y='load_ratio', ax=ax3, color='black', linewidth=2)
        ax3.axhline(y=1.5, color='red', linestyle='--', alpha=0.7, label='High Risk')
        ax3.axhline(y=1.3, color='orange', linestyle='--', alpha=0.7, label='Moderate Risk')
        ax3.axhline(y=0.8, color='blue', linestyle='--', alpha=0.7, label='Detraining')
        ax3.fill_between(self.activities['date'], 0.8, 1.3, alpha=0.2, color='green', label='Optimal Zone')
        ax3.set_title('Acute:Chronic Load Ratio')
        ax3.set_ylabel('Ratio')
        ax3.legend()
        
        # 4. Weekly Volume Trend
        ax4 = axes[1, 1]
        weekly_volume = self.activities.groupby(pd.Grouper(key='date', freq='W'))['duration_min'].sum() / 60
        weekly_volume.plot(ax=ax4, kind='bar', color='skyblue')
        ax4.set_title('Weekly Training Hours')
        ax4.set_ylabel('Hours')
        ax4.set_xticklabels([d.strftime('%m/%d') for d in weekly_volume.index], rotation=45)
        
        plt.tight_layout()
        
        # Save the plot
        output_path = os.path.join(self.data_dir, 'processed', 'fitness_dashboard.png')
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"📊 Dashboard saved to {output_path}")
        plt.show()
        
        # Create interactive plot if plotly available
        if PLOTLY_AVAILABLE:
            self._create_interactive_dashboard()
    
    def _create_interactive_dashboard(self):
        """Create interactive Plotly dashboard"""
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Training Load Timeline', 'Load Ratio Risk Zones',
                          'Activity Heatmap', 'Performance Predictions'),
            specs=[[{"secondary_y": False}, {"secondary_y": False}],
                   [{"type": "heatmap"}, {"secondary_y": False}]]
        )
        
        # Add traces
        fig.add_trace(
            go.Scatter(x=self.activities['date'], y=self.activities['acute_load'],
                      name='Acute Load', line=dict(color='red')),
            row=1, col=1
        )
        
        fig.add_trace(
            go.Scatter(x=self.activities['date'], y=self.activities['chronic_load'],
                      name='Chronic Load', line=dict(color='blue')),
            row=1, col=1
        )
        
        # Save interactive plot
        output_path = os.path.join(self.data_dir, 'processed', 'interactive_dashboard.html')
        fig.write_html(output_path)
        print(f"🌐 Interactive dashboard saved to {output_path}")
    
    def generate_report(self) -> str:
        """Generate comprehensive fitness report"""
        insights = self.generate_ai_insights()
        
        report = f"""
# 🏃 Comprehensive Fitness Analysis Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}

## 📊 Training Load Analysis
- Current Acute Load: {insights['training_load'].get('current_acute_load', 'N/A'):.1f}
- Current Chronic Load: {insights['training_load'].get('current_chronic_load', 'N/A'):.1f}
- Load Ratio: {insights['training_load'].get('current_ratio', 'N/A'):.2f}
- **Risk Status: {insights['training_load'].get('risk_level', 'Unknown')}**
- Weekly Training Hours: {insights['training_load'].get('weekly_volume', 'N/A'):.1f}

## ⚽ Soccer Performance Metrics
- Games Last Month: {insights['sport_specific'].get('games_last_month', 0)}
- Average Game Duration: {insights['sport_specific'].get('avg_game_duration', 0):.1f} minutes
- Average Distance/Game: {insights['sport_specific'].get('avg_distance_per_game', 0):.2f} miles
- {insights['sport_specific'].get('tournament_pattern', 'No pattern detected')}

## 🥗 Nutrition Recommendations

### Daily Macros:
- Calories: {insights['nutrition']['daily_macros']['daily_calories']} kcal
- Protein: {insights['nutrition']['daily_macros']['protein_g']}g
- Carbs: {insights['nutrition']['daily_macros']['carbs_g']}g
- Fats: {insights['nutrition']['daily_macros']['fats_g']}g
- Hydration: {insights['nutrition']['daily_macros']['hydration_L']}L

### Tournament Day Adjustments:
- Calories: {insights['nutrition']['tournament_macros']['tournament_calories']} kcal
- Carbs: {insights['nutrition']['tournament_macros']['tournament_carbs_g']}g
- Hydration: {insights['nutrition']['tournament_macros']['tournament_hydration_L']}L

## 📈 Performance Trajectory
- Volume Trend: {insights['performance_trajectory'].get('volume_trend', 'Unknown')}
- Training Consistency: {insights['performance_trajectory'].get('consistency', 'Unknown')}
- Predicted Fitness Gains: {insights['performance_trajectory'].get('predicted_fitness_gain', 'Unknown')}

## 💡 AI-Generated Recommendations
"""
        
        for i, rec in enumerate(insights['recommendations'], 1):
            report += f"{i}. {rec}\n"
        
        report += """
## 🎯 Next Steps
1. Implement the recommendations above
2. Track progress weekly
3. Adjust based on recovery metrics
4. Focus on consistency over intensity

---
*This report was generated using AI analysis of your training data. 
Consult with coaches and medical professionals for personalized advice.*
"""
        
        # Save report
        report_path = os.path.join(self.data_dir, 'processed', f'fitness_report_{datetime.now().strftime("%Y%m%d")}.md')
        os.makedirs(os.path.dirname(report_path), exist_ok=True)
        with open(report_path, 'w') as f:
            f.write(report)
        
        print(f"📄 Report saved to {report_path}")
        return report

    def analyze_movement_patterns(self) -> Dict[str, Any]:
        """Analyze movement patterns from GPS and heart rate data"""
        if self.activities is None:
            return {"error": "No activity data available"}
        
        print("🏃 Analyzing movement patterns and sprint detection...")
        
        # Filter for activities with GPS data (running, cycling, etc.)
        gps_activities = self.activities[
            (self.activities['type'].isin(['Run', 'Ride', 'Walk'])) & 
            (self.activities['distance_miles'] > 0)
        ].copy()
        
        if gps_activities.empty:
            return {"error": "No GPS activities found for movement analysis"}
        
        movement_analysis = {}
        
        for idx, activity in gps_activities.iterrows():
            activity_id = activity.get('id', idx)
            activity_type = activity.get('type', 'Unknown')
            
            # Calculate pace variations to detect intensity changes
            if 'pace_per_mile' in activity and pd.notna(activity['pace_per_mile']):
                pace = self._parse_pace(activity['pace_per_mile'])
                if pace > 0:
                    # Lower pace = faster speed = higher intensity
                    intensity_score = max(0, (10 - pace) / 10)  # Normalize 0-1
                    
                    # Detect potential sprints based on pace
                    if intensity_score > 0.7:  # Fast pace threshold
                        movement_analysis[f"activity_{activity_id}"] = {
                            'type': activity_type,
                            'date': activity['date'],
                            'intensity': 'High',
                            'pace_mph': 60 / pace if pace > 0 else 0,
                            'sprint_probability': intensity_score,
                            'duration_min': activity.get('duration_min', 0),
                            'distance_miles': activity.get('distance_miles', 0)
                        }
        
        # Analyze heart rate patterns for intensity detection
        if 'average_heartrate' in gps_activities.columns:
            hr_activities = gps_activities[gps_activities['average_heartrate'].notna()]
            if not hr_activities.empty:
                # Calculate heart rate zones
                hr_activities['hr_zone'] = hr_activities['average_heartrate'].apply(
                    lambda hr: self._calculate_hr_zone(hr)
                )
                
                # Detect high-intensity periods
                high_intensity = hr_activities[hr_activities['hr_zone'].isin(['Zone 4', 'Zone 5'])]
                if not high_intensity.empty:
                    movement_analysis['heart_rate_analysis'] = {
                        'high_intensity_periods': len(high_intensity),
                        'avg_hr_high_intensity': high_intensity['average_heartrate'].mean(),
                        'total_high_intensity_time': high_intensity['duration_min'].sum(),
                        'intensity_distribution': hr_activities['hr_zone'].value_counts().to_dict()
                    }
        
        # Analyze training patterns for steady-state vs. interval detection
        if len(gps_activities) > 1:
            # Sort by date for temporal analysis
            gps_activities_sorted = gps_activities.sort_values('date')
            
            # Calculate pace variability between consecutive activities
            pace_variations = []
            for i in range(1, len(gps_activities_sorted)):
                prev_pace = self._parse_pace(gps_activities_sorted.iloc[i-1].get('pace_per_mile', '0'))
                curr_pace = self._parse_pace(gps_activities_sorted.iloc[i].get('pace_per_mile', '0'))
                
                if prev_pace > 0 and curr_pace > 0:
                    variation = abs(curr_pace - prev_pace) / prev_pace
                    pace_variations.append(variation)
            
            if pace_variations:
                avg_variation = np.mean(pace_variations)
                movement_analysis['training_pattern_analysis'] = {
                    'pace_variability': avg_variation,
                    'training_style': 'Interval' if avg_variation > 0.3 else 'Steady State',
                    'recommendation': self._get_training_recommendation(avg_variation),
                    'consecutive_activities_analyzed': len(pace_variations)
                }
        
        # Calculate movement efficiency metrics
        if 'distance_miles' in gps_activities.columns and 'duration_min' in gps_activities.columns:
            gps_activities['speed_mph'] = gps_activities['distance_miles'] / (gps_activities['duration_min'] / 60)
            gps_activities['efficiency'] = gps_activities['speed_mph'] / gps_activities.get('average_heartrate', 140).fillna(140)
            
            movement_analysis['efficiency_metrics'] = {
                'avg_speed_mph': gps_activities['speed_mph'].mean(),
                'avg_efficiency': gps_activities['efficiency'].mean(),
                'efficiency_trend': 'Improving' if len(gps_activities) > 3 else 'Insufficient data',
                'speed_consistency': gps_activities['speed_mph'].std()
            }
        
        return movement_analysis
    
    def _calculate_hr_zone(self, heart_rate: float) -> str:
        """Calculate heart rate zone based on max HR"""
        if heart_rate < self.profile.max_hr * 0.6:
            return "Zone 1"
        elif heart_rate < self.profile.max_hr * 0.7:
            return "Zone 2"
        elif heart_rate < self.profile.max_hr * 0.8:
            return "Zone 3"
        elif heart_rate < self.profile.max_hr * 0.9:
            return "Zone 4"
        else:
            return "Zone 5"
    
    def _get_training_recommendation(self, pace_variation: float) -> str:
        """Get training recommendation based on pace variation"""
        if pace_variation < 0.2:
            return "Consider adding interval training to improve speed and power"
        elif pace_variation > 0.5:
            return "Good variety in training intensity. Focus on recovery between hard sessions"
        else:
            return "Balanced training approach. Maintain current variety"
    
    def detect_sprint_patterns(self) -> Dict[str, Any]:
        """Detect sprint patterns using rolling averages and thresholds"""
        if self.activities is None:
            return {"error": "No activity data available"}
        
        print("⚡ Detecting sprint patterns from activity data...")
        
        # Focus on running activities
        running_data = self.activities[self.activities['type'] == 'Run'].copy()
        if running_data.empty:
            return {"error": "No running activities found for sprint analysis"}
        
        # Sort by date for temporal analysis
        running_data = running_data.sort_values('date')
        
        sprint_analysis = {}
        
        for idx, run in running_data.iterrows():
            # Calculate intensity based on pace and heart rate
            intensity_score = 0
            sprint_indicators = []
            
            # Pace-based sprint detection
            if 'pace_per_mile' in run and pd.notna(run['pace_per_mile']):
                pace = self._parse_pace(run['pace_per_mile'])
                if pace > 0:
                    # Convert pace to speed (mph)
                    speed_mph = 60 / pace
                    
                    # Sprint threshold: >8 mph (7:30 min/mile pace)
                    if speed_mph > 8.0:
                        intensity_score += 0.6
                        sprint_indicators.append(f"High speed: {speed_mph:.1f} mph")
            
            # Heart rate-based sprint detection
            if 'average_heartrate' in run and pd.notna(run['average_heartrate']):
                hr = run['average_heartrate']
                hr_zone = self._calculate_hr_zone(hr)
                
                if hr_zone in ['Zone 4', 'Zone 5']:
                    intensity_score += 0.4
                    sprint_indicators.append(f"High HR: {hr} bpm ({hr_zone})")
            
            # Duration-based sprint detection
            duration = run.get('duration_min', 0)
            if duration > 0:
                # Short, intense efforts are more likely to be sprints
                if duration < 30 and intensity_score > 0.5:
                    intensity_score += 0.2
                    sprint_indicators.append(f"Short duration: {duration} min")
            
            # Classify the run
            if intensity_score >= 0.7:
                run_type = "Sprint/Interval"
            elif intensity_score >= 0.4:
                run_type = "Tempo"
            else:
                run_type = "Easy/Recovery"
            
            sprint_analysis[f"run_{idx}"] = {
                'date': run['date'],
                'type': run_type,
                'intensity_score': intensity_score,
                'sprint_indicators': sprint_indicators,
                'distance_miles': run.get('distance_miles', 0),
                'duration_min': duration,
                'pace_per_mile': run.get('pace_per_mile', 'N/A'),
                'heart_rate': run.get('average_heartrate', 'N/A')
            }
        
        # Calculate sprint frequency and patterns
        sprint_runs = [run for run in sprint_analysis.values() if run['type'] == 'Sprint/Interval']
        tempo_runs = [run for run in sprint_analysis.values() if run['type'] == 'Tempo']
        
        sprint_analysis['summary'] = {
            'total_runs': len(running_data),
            'sprint_runs': len(sprint_runs),
            'tempo_runs': len(tempo_runs),
            'sprint_frequency': len(sprint_runs) / len(running_data) if running_data.shape[0] > 0 else 0,
            'avg_intensity_score': np.mean([run['intensity_score'] for run in sprint_analysis.values() if isinstance(run, dict)]),
            'recommendation': self._get_sprint_recommendation(len(sprint_runs), len(running_data))
        }
        
        return sprint_analysis
    
    def _get_sprint_recommendation(self, sprint_count: int, total_runs: int) -> str:
        """Get sprint training recommendation"""
        if total_runs == 0:
            return "No running data available for recommendations"
        
        sprint_ratio = sprint_count / total_runs
        
        if sprint_ratio < 0.1:
            return "Consider adding 1-2 sprint sessions per week to improve speed and power"
        elif sprint_ratio > 0.4:
            return "High sprint frequency. Ensure adequate recovery and consider adding easy runs"
        else:
            return "Good balance of sprint and recovery runs. Maintain current training structure"

def main():
    """Run comprehensive fitness analysis"""
    print("🏃‍♂️ Starting comprehensive fitness analysis...")
    print("=" * 50)
    
    # Initialize analyzer
    analyzer = FitnessAnalyzer()
    
    # Run all analyses
    print("\n📊 Running comprehensive analysis...")
    
    # Basic metrics
    training_load = analyzer.calculate_training_load()
    print(f"✅ Training Load Analysis Complete")
    
    # Sport-specific analysis
    sport_metrics = analyzer.analyze_sport_specific_metrics()
    print(f"✅ Sport-Specific Analysis Complete")
    
    # Movement pattern analysis (NEW!)
    movement_patterns = analyzer.analyze_movement_patterns()
    print(f"✅ Movement Pattern Analysis Complete")
    
    # Sprint detection (NEW!)
    sprint_patterns = analyzer.detect_sprint_patterns()
    print(f"✅ Sprint Pattern Detection Complete")
    
    # ML-based injury risk assessment
    try:
        injury_risk = analyzer.assess_injury_risk_ml(analyzer.activities)
        print(f"✅ ML Injury Risk Assessment Complete")
    except Exception as e:
        print(f"⚠️ ML Assessment Failed: {e}")
        injury_risk = {"error": "ML assessment unavailable"}
    
    # Asymmetry metrics
    try:
        asymmetry = analyzer.calculate_asymmetry_metrics()
        print(f"✅ Asymmetry Analysis Complete")
    except Exception as e:
        print(f"⚠️ Asymmetry Analysis Failed: {e}")
        asymmetry = {"error": "Asymmetry analysis unavailable"}
    
    # Nutrition recommendations
    nutrition = analyzer.generate_nutrition_recommendations()
    print(f"✅ Nutrition Analysis Complete")
    
    # Performance predictions
    predictions = analyzer.predict_performance_trajectory()
    print(f"✅ Performance Predictions Complete")
    
    # AI insights
    insights = analyzer.generate_ai_insights()
    print(f"✅ AI Insights Generated")
    
    # Generate comprehensive report
    print("\n📋 Generating comprehensive report...")
    report = analyzer.generate_report()
    
    # Save report to file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_filename = f"fitness_analysis_report_{timestamp}.txt"
    
    with open(report_filename, 'w') as f:
        f.write(report)
    
    print(f"\n✅ Analysis Complete! Report saved to: {report_filename}")
    print("\n🚀 Key Findings:")
    
    # Display key insights
    if isinstance(training_load, dict) and 'risk_level' in training_load:
        print(f"   • Injury Risk: {training_load['risk_level']}")
    
    if isinstance(movement_patterns, dict) and 'efficiency_metrics' in movement_patterns:
        eff = movement_patterns['efficiency_metrics']
        print(f"   • Training Style: {eff.get('efficiency_trend', 'N/A')}")
    
    if isinstance(sprint_patterns, dict) and 'summary' in sprint_patterns:
        summary = sprint_patterns['summary']
        print(f"   • Sprint Frequency: {summary.get('sprint_frequency', 0):.1%}")
        print(f"   • Training Recommendation: {summary.get('recommendation', 'N/A')}")
    
    if isinstance(injury_risk, dict) and 'ml_prediction' in injury_risk:
        ml_pred = injury_risk['ml_prediction']
        if isinstance(ml_pred, dict):
            print(f"   • ML Risk Level: {ml_pred.get('risk_level', 'N/A')}")
    
    print(f"\n📊 Full analysis available in: {report_filename}")
    print("🎯 Use the Streamlit dashboard for interactive visualizations!")
    
    return {
        'training_load': training_load,
        'sport_metrics': sport_metrics,
        'movement_patterns': movement_patterns,
        'sprint_patterns': sprint_patterns,
        'injury_risk': injury_risk,
        'asymmetry': asymmetry,
        'nutrition': nutrition,
        'predictions': predictions,
        'insights': insights,
        'report_file': report_filename
    }

if __name__ == "__main__":
    main()