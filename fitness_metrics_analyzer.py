#!/usr/bin/env python3
"""
Fitness Metrics Analyzer for Athlete Performance Predictor

This script analyzes combined data from VeSync devices and Strava activities
to calculate comprehensive fitness metrics and insights.

Metrics calculated include:
- Training Load & Recovery
- Body Composition Trends
- Sleep Performance Correlation
- Environmental Impact on Performance
- Fitness Score Calculations
- Performance Predictions
"""

import os
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import warnings
warnings.filterwarnings('ignore')

# Set plotting style
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")

class FitnessMetricsAnalyzer:
    """Analyzes fitness data from multiple sources"""
    
    def __init__(self, data_dir: str = "data"):
        """Initialize analyzer with data directory"""
        self.data_dir = data_dir
        self.strava_data = None
        self.vesync_data = None
        self.combined_data = None
        
        # Load data
        self.load_data()
        
    def load_data(self):
        """Load Strava and VeSync data"""
        # Load Strava data
        strava_path = os.path.join(self.data_dir, "strava_activities.json")
        if os.path.exists(strava_path):
            with open(strava_path, 'r') as f:
                self.strava_data = json.load(f)
            print(f"Loaded {len(self.strava_data)} Strava activities")
        
        # Load VeSync data (most recent)
        vesync_files = [f for f in os.listdir(os.path.join(self.data_dir, "raw")) 
                       if f.startswith("vesync_data_")]
        if vesync_files:
            latest_vesync = max(vesync_files)
            vesync_path = os.path.join(self.data_dir, "raw", latest_vesync)
            with open(vesync_path, 'r') as f:
                self.vesync_data = json.load(f)
            print(f"Loaded VeSync data from {latest_vesync}")
        
        # Load processed activities CSV
        activities_path = os.path.join(self.data_dir, "activities.csv")
        if os.path.exists(activities_path):
            self.activities_df = pd.read_csv(activities_path)
            print(f"Loaded {len(self.activities_df)} processed activities")
    
    def calculate_training_load(self, days: int = 30) -> pd.DataFrame:
        """Calculate training load metrics using TRIMP (Training Impulse) method"""
        if self.strava_data is None:
            print("No Strava data available")
            return pd.DataFrame()
        
        # Convert to DataFrame
        activities_df = pd.DataFrame(self.strava_data)
        
        # Filter for recent activities
        cutoff_date = datetime.now() - timedelta(days=days)
        activities_df['start_date'] = pd.to_datetime(activities_df['start_date'])
        recent_activities = activities_df[activities_df['start_date'] >= cutoff_date].copy()
        
        # Calculate TRIMP for each activity
        def calculate_trimp(row):
            """Calculate TRIMP score based on heart rate zones"""
            if pd.isna(row.get('average_heartrate')) or pd.isna(row.get('moving_time')):
                return 0
            
            # Heart rate zones (simplified)
            hr = row['average_heartrate']
            time_minutes = row['moving_time'] / 60
            
            # TRIMP calculation based on heart rate zones
            if hr < 120:  # Zone 1
                return time_minutes * 1
            elif hr < 140:  # Zone 2
                return time_minutes * 2
            elif hr < 160:  # Zone 3
                return time_minutes * 3
            elif hr < 180:  # Zone 4
                return time_minutes * 4
            else:  # Zone 5
                return time_minutes * 5
        
        recent_activities['trimp'] = recent_activities.apply(calculate_trimp, axis=1)
        recent_activities['duration_hours'] = recent_activities['moving_time'] / 3600
        
        # Daily aggregation
        daily_load = recent_activities.groupby(
            recent_activities['start_date'].dt.date
        ).agg({
            'trimp': 'sum',
            'duration_hours': 'sum',
            'distance': 'sum',
            'total_elevation_gain': 'sum'
        }).reset_index()
        
        daily_load['date'] = pd.to_datetime(daily_load['date'])
        daily_load['rolling_trimp_7d'] = daily_load['trimp'].rolling(7).sum()
        daily_load['rolling_trimp_28d'] = daily_load['trimp'].rolling(28).sum()
        
        # Calculate acute:chronic workload ratio (ACWR)
        daily_load['acwr'] = daily_load['rolling_trimp_7d'] / daily_load['rolling_trimp_28d']
        
        return daily_load
    
    def analyze_body_composition(self, days: int = 30) -> pd.DataFrame:
        """Analyze body composition trends from VeSync scale data"""
        if not self.vesync_data or 'scale_data' not in self.vesync_data:
            print("No VeSync scale data available")
            return pd.DataFrame()
        
        scale_data = self.vesync_data['scale_data']
        if not scale_data:
            return pd.DataFrame()
        
        # Convert to DataFrame
        scale_df = pd.DataFrame(scale_data)
        scale_df['timestamp'] = pd.to_datetime(scale_df['timestamp'])
        
        # Filter for recent data
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_scale = scale_df[scale_df['timestamp'] >= cutoff_date].copy()
        
        if recent_scale.empty:
            return pd.DataFrame()
        
        # Calculate trends
        recent_scale = recent_scale.sort_values('timestamp')
        
        # Calculate rolling averages
        for col in ['weight', 'body_fat', 'muscle_mass', 'water_percentage']:
            if col in recent_scale.columns and recent_scale[col].notna().any():
                recent_scale[f'{col}_7d_avg'] = recent_scale[col].rolling(7).mean()
                recent_scale[f'{col}_trend'] = recent_scale[col].diff()
        
        return recent_scale
    
    def calculate_recovery_score(self, training_load: pd.DataFrame, 
                                body_comp: pd.DataFrame) -> pd.DataFrame:
        """Calculate recovery score based on training load and body composition"""
        if training_load.empty:
            return pd.DataFrame()
        
        recovery_data = []
        
        for _, row in training_load.iterrows():
            date = row['date']
            
            # Find corresponding body composition data
            body_data = None
            if not body_comp.empty:
                body_data = body_comp[body_comp['timestamp'].dt.date == date.date()]
            
            # Calculate recovery score components
            recovery_score = 100  # Start with perfect score
            
            # Training load impact
            if row['trimp'] > 100:  # High training load
                recovery_score -= 20
            elif row['trimp'] > 50:  # Moderate training load
                recovery_score -= 10
            
            # ACWR impact (acute:chronic workload ratio)
            if not pd.isna(row['acwr']):
                if row['acwr'] > 1.5:  # High injury risk
                    recovery_score -= 30
                elif row['acwr'] > 1.3:  # Moderate injury risk
                    recovery_score -= 20
                elif row['acwr'] < 0.8:  # Detraining risk
                    recovery_score -= 10
            
            # Body composition impact (if available)
            if body_data is not None and not body_data.empty:
                body_row = body_data.iloc[0]
                
                # Weight change impact
                if 'weight_trend' in body_row and not pd.isna(body_row['weight_trend']):
                    weight_change = body_row['weight_trend']
                    if abs(weight_change) > 2:  # Significant weight change
                        recovery_score -= 15
                
                # Hydration impact
                if 'water_percentage' in body_row and not pd.isna(body_row['water_percentage']):
                    water = body_row['water_percentage']
                    if water < 50:  # Low hydration
                        recovery_score -= 10
            
            # Ensure score is within bounds
            recovery_score = max(0, min(100, recovery_score))
            
            recovery_data.append({
                'date': date,
                'recovery_score': recovery_score,
                'trimp': row['trimp'],
                'acwr': row['acwr'],
                'training_duration': row['duration_hours']
            })
        
        return pd.DataFrame(recovery_data)
    
    def calculate_fitness_score(self, training_load: pd.DataFrame, 
                               body_comp: pd.DataFrame) -> pd.DataFrame:
        """Calculate overall fitness score"""
        if training_load.empty:
            return pd.DataFrame()
        
        fitness_data = []
        
        for _, row in training_load.iterrows():
            date = row['date']
            
            # Base fitness score starts at 50
            fitness_score = 50
            
            # Training volume contribution (up to +30 points)
            if row['duration_hours'] > 0:
                volume_score = min(30, row['duration_hours'] * 10)
                fitness_score += volume_score
            
            # Training intensity contribution (up to +20 points)
            if row['trimp'] > 0:
                intensity_score = min(20, row['trimp'] / 10)
                fitness_score += intensity_score
            
            # Consistency bonus (up to +10 points)
            if not pd.isna(row['rolling_trimp_7d']) and row['rolling_trimp_7d'] > 0:
                consistency_score = min(10, row['rolling_trimp_7d'] / 50)
                fitness_score += consistency_score
            
            # Ensure score is within bounds
            fitness_score = max(0, min(100, fitness_score))
            
            fitness_data.append({
                'date': date,
                'fitness_score': fitness_score,
                'volume_score': min(30, row['duration_hours'] * 10),
                'intensity_score': min(20, row['trimp'] / 10) if row['trimp'] > 0 else 0,
                'consistency_score': min(10, row['rolling_trimp_7d'] / 50) if not pd.isna(row['rolling_trimp_7d']) and row['rolling_trimp_7d'] > 0 else 0
            })
        
        return pd.DataFrame(fitness_data)
    
    def analyze_sleep_performance_correlation(self) -> Dict[str, Any]:
        """Analyze correlation between sleep and performance"""
        if not self.vesync_data or 'sleep_data' not in self.vesync_data:
            return {"error": "No sleep data available"}
        
        sleep_data = self.vesync_data['sleep_data']
        if not sleep_data:
            return {"error": "Empty sleep data"}
        
        # Convert to DataFrame
        sleep_df = pd.DataFrame(sleep_data)
        sleep_df['timestamp'] = pd.to_datetime(sleep_df['timestamp'])
        
        # Get training load data
        training_load = self.calculate_training_load(days=60)
        
        if training_load.empty:
            return {"error": "No training data available for correlation"}
        
        # Merge sleep and training data by date
        sleep_df['date'] = sleep_df['timestamp'].dt.date
        training_load['date'] = training_load['date'].dt.date
        
        merged_data = pd.merge(sleep_df, training_load, on='date', how='inner')
        
        if merged_data.empty:
            return {"error": "No overlapping sleep and training data"}
        
        # Calculate correlations
        correlations = {}
        
        # Sleep duration vs performance
        if 'sleep_duration' in merged_data.columns and 'trimp' in merged_data.columns:
            sleep_duration_corr = merged_data['sleep_duration'].corr(merged_data['trimp'])
            correlations['sleep_duration_vs_trimp'] = sleep_duration_corr
        
        # Sleep quality vs performance
        if 'sleep_quality' in merged_data.columns and 'trimp' in merged_data.columns:
            sleep_quality_corr = merged_data['sleep_quality'].corr(merged_data['trimp'])
            correlations['sleep_quality_vs_trimp'] = sleep_quality_corr
        
        # Deep sleep vs recovery
        if 'deep_sleep' in merged_data.columns and 'recovery_score' in merged_data.columns:
            deep_sleep_corr = merged_data['deep_sleep'].corr(merged_data['recovery_score'])
            correlations['deep_sleep_vs_recovery'] = deep_sleep_corr
        
        return {
            "correlations": correlations,
            "data_points": len(merged_data),
            "date_range": {
                "start": merged_data['date'].min().isoformat(),
                "end": merged_data['date'].max().isoformat()
            }
        }
    
    def generate_performance_predictions(self, days_ahead: int = 7) -> pd.DataFrame:
        """Generate performance predictions based on current trends"""
        training_load = self.calculate_training_load(days=60)
        
        if training_load.empty:
            return pd.DataFrame()
        
        # Simple trend-based prediction
        predictions = []
        
        # Get recent trends
        recent_trimp = training_load['trimp'].tail(14)  # Last 2 weeks
        recent_acwr = training_load['acwr'].tail(14)
        
        if len(recent_trimp) < 7:
            return pd.DataFrame()
        
        # Calculate trends
        trimp_trend = recent_trimp.tail(7).mean() - recent_trimp.head(7).mean()
        acwr_trend = recent_acwr.tail(7).mean() - recent_acwr.head(7).mean()
        
        # Generate predictions
        current_date = datetime.now()
        for i in range(1, days_ahead + 1):
            future_date = current_date + timedelta(days=i)
            
            # Predict TRIMP (with trend continuation and some regression to mean)
            predicted_trimp = max(0, recent_trimp.mean() + (trimp_trend * 0.5 * i))
            
            # Predict ACWR (with regression to mean)
            predicted_acwr = 1.0 + (acwr_trend * 0.8 ** i)
            
            # Predict performance category
            if predicted_acwr > 1.5:
                performance_category = "High Injury Risk"
            elif predicted_acwr > 1.3:
                performance_category = "Moderate Injury Risk"
            elif predicted_acwr < 0.8:
                performance_category = "Detraining Risk"
            else:
                performance_category = "Optimal Training Zone"
            
            predictions.append({
                'date': future_date,
                'predicted_trimp': predicted_trimp,
                'predicted_acwr': predicted_acwr,
                'performance_category': performance_category,
                'confidence': max(0.1, 1.0 - (i * 0.1))  # Confidence decreases with time
            })
        
        return pd.DataFrame(predictions)
    
    def create_comprehensive_report(self) -> Dict[str, Any]:
        """Generate comprehensive fitness analysis report"""
        print("Generating comprehensive fitness analysis report...")
        
        report = {
            "generated_at": datetime.now().isoformat(),
            "data_summary": {},
            "metrics": {},
            "insights": {},
            "recommendations": []
        }
        
        # Calculate all metrics
        training_load = self.calculate_training_load(days=30)
        body_comp = self.analyze_body_composition(days=30)
        recovery_score = self.calculate_recovery_score(training_load, body_comp)
        fitness_score = self.calculate_fitness_score(training_load, body_comp)
        sleep_correlation = self.analyze_sleep_performance_correlation()
        predictions = self.generate_performance_predictions(days_ahead=7)
        
        # Data summary
        report["data_summary"] = {
            "strava_activities": len(self.strava_data) if self.strava_data else 0,
            "vesync_devices": len(self.vesync_data.get('devices', {})) if self.vesync_data else 0,
            "scale_measurements": len(self.vesync_data.get('scale_data', [])) if self.vesync_data else 0,
            "sleep_sessions": len(self.vesync_data.get('sleep_data', [])) if self.vesync_data else 0,
            "analysis_period_days": 30
        }
        
        # Key metrics
        if not training_load.empty:
            recent_trimp = training_load['trimp'].tail(7).sum()
            recent_acwr = training_load['acwr'].tail(7).mean()
            
            report["metrics"]["training_load"] = {
                "weekly_trimp": recent_trimp,
                "current_acwr": recent_acwr,
                "training_volume_hours": training_load['duration_hours'].tail(7).sum()
            }
        
        if not recovery_score.empty:
            avg_recovery = recovery_score['recovery_score'].mean()
            report["metrics"]["recovery"] = {
                "average_recovery_score": avg_recovery,
                "recovery_trend": "Improving" if avg_recovery > 70 else "Needs attention"
            }
        
        if not fitness_score.empty:
            avg_fitness = fitness_score['fitness_score'].mean()
            report["metrics"]["fitness"] = {
                "average_fitness_score": avg_fitness,
                "fitness_level": self._categorize_fitness_level(avg_fitness)
            }
        
        # Sleep correlation insights
        if "correlations" in sleep_correlation:
            report["insights"]["sleep_performance"] = sleep_correlation["correlations"]
        
        # Generate recommendations
        recommendations = []
        
        if not training_load.empty and not training_load['acwr'].empty:
            current_acwr = training_load['acwr'].iloc[-1]
            if current_acwr > 1.5:
                recommendations.append("Reduce training intensity - ACWR indicates high injury risk")
            elif current_acwr < 0.8:
                recommendations.append("Increase training volume - ACWR indicates detraining risk")
        
        if not recovery_score.empty:
            avg_recovery = recovery_score['recovery_score'].mean()
            if avg_recovery < 60:
                recommendations.append("Focus on recovery - consider rest days or active recovery")
        
        if not body_comp.empty and 'weight_trend' in body_comp.columns:
            weight_trend = body_comp['weight_trend'].mean()
            if abs(weight_trend) > 1:
                recommendations.append("Monitor body composition changes - significant weight fluctuations detected")
        
        report["recommendations"] = recommendations
        
        # Save report
        report_path = os.path.join(self.data_dir, "processed", f"fitness_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        os.makedirs(os.path.dirname(report_path), exist_ok=True)
        
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"Comprehensive report saved to {report_path}")
        return report
    
    def _categorize_fitness_level(self, score: float) -> str:
        """Categorize fitness score into levels"""
        if score >= 90:
            return "Elite"
        elif score >= 80:
            return "Excellent"
        elif score >= 70:
            return "Good"
        elif score >= 60:
            return "Fair"
        elif score >= 50:
            return "Below Average"
        else:
            return "Poor"
    
    def plot_metrics(self, save_plots: bool = True):
        """Create visualization plots of key metrics"""
        training_load = self.calculate_training_load(days=30)
        
        if training_load.empty:
            print("No training data available for plotting")
            return
        
        # Create subplots
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle('Fitness Metrics Dashboard', fontsize=16, fontweight='bold')
        
        # Plot 1: Training Load Over Time
        axes[0, 0].plot(training_load['date'], training_load['trimp'], marker='o', linewidth=2)
        axes[0, 0].set_title('Daily Training Load (TRIMP)')
        axes[0, 0].set_ylabel('TRIMP Score')
        axes[0, 0].tick_params(axis='x', rotation=45)
        axes[0, 0].grid(True, alpha=0.3)
        
        # Plot 2: ACWR Trend
        axes[0, 1].plot(training_load['date'], training_load['acwr'], marker='s', color='orange', linewidth=2)
        axes[0, 1].axhline(y=1.5, color='red', linestyle='--', alpha=0.7, label='High Risk Threshold')
        axes[0, 1].axhline(y=0.8, color='blue', linestyle='--', alpha=0.7, label='Detraining Threshold')
        axes[0, 1].set_title('Acute:Chronic Workload Ratio (ACWR)')
        axes[0, 1].set_ylabel('ACWR')
        axes[0, 1].legend()
        axes[0, 1].tick_params(axis='x', rotation=45)
        axes[0, 1].grid(True, alpha=0.3)
        
        # Plot 3: Training Duration
        axes[1, 0].bar(training_load['date'], training_load['duration_hours'], alpha=0.7, color='green')
        axes[1, 0].set_title('Daily Training Duration')
        axes[1, 0].set_ylabel('Hours')
        axes[1, 0].tick_params(axis='x', rotation=45)
        axes[1, 0].grid(True, alpha=0.3)
        
        # Plot 4: Rolling TRIMP
        axes[1, 1].plot(training_load['date'], training_load['rolling_trimp_7d'], 
                        label='7-day Rolling', linewidth=2, color='purple')
        axes[1, 1].plot(training_load['date'], training_load['rolling_trimp_28d'], 
                        label='28-day Rolling', linewidth=2, color='brown')
        axes[1, 1].set_title('Rolling Training Load')
        axes[1, 1].set_ylabel('TRIMP Score')
        axes[1, 1].legend()
        axes[1, 1].tick_params(axis='x', rotation=45)
        axes[1, 1].grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if save_plots:
            plot_path = os.path.join(self.data_dir, "processed", f"fitness_metrics_plots_{datetime.now().strftime('%Y%m%d')}.png")
            os.makedirs(os.path.dirname(plot_path), exist_ok=True)
            plt.savefig(plot_path, dpi=300, bbox_inches='tight')
            print(f"Plots saved to {plot_path}")
        
        plt.show()

def main():
    """Main execution function"""
    try:
        # Initialize analyzer
        analyzer = FitnessMetricsAnalyzer()
        
        # Generate comprehensive report
        report = analyzer.create_comprehensive_report()
        
        # Print key insights
        print("\n=== FITNESS ANALYSIS SUMMARY ===")
        print(f"Training Load: {report['metrics'].get('training_load', {}).get('weekly_trimp', 'N/A')} TRIMP (weekly)")
        print(f"Recovery Score: {report['metrics'].get('recovery', {}).get('average_recovery_score', 'N/A')}")
        print(f"Fitness Level: {report['metrics'].get('fitness', {}).get('fitness_level', 'N/A')}")
        
        if report['recommendations']:
            print("\n=== RECOMMENDATIONS ===")
            for i, rec in enumerate(report['recommendations'], 1):
                print(f"{i}. {rec}")
        
        # Create visualizations
        analyzer.plot_metrics(save_plots=True)
        
    except Exception as e:
        print(f"Error in analysis: {e}")
        raise

if __name__ == "__main__":
    main()
