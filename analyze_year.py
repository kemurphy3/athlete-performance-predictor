#!/usr/bin/env python3
"""
Single-Click Yearly Fitness Analysis Script
Provides comprehensive fitness insights for the past year with AI-powered recommendations
"""

import asyncio
import argparse
import json
import logging
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
import sqlite3
import pandas as pd
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import project modules
try:
    from src.core.multi_athlete_calorie_calculator import MultiAthleteCalorieCalculator
    from src.core.data_ingestion import DataIngestionOrchestrator
    from src.connectors import get_connector, list_available_connectors
    from src.core.models import Workout, BiometricReading, UserProfile
except ImportError as e:
    logger.error(f"Import error: {e}")
    logger.info("Make sure you're running from the project root directory")
    exit(1)

class YearlyFitnessAnalyzer:
    """Comprehensive yearly fitness analysis with AI insights"""
    
    def __init__(self, database_path: str = "data/fitness_data.db"):
        self.db_path = database_path
        self.calculator = MultiAthleteCalorieCalculator(database_path)
        self.orchestrator = DataIngestionOrchestrator(database_path)
        
    async def analyze_year(self, athlete_id: str = "default", days: int = 365) -> Dict[str, Any]:
        """Run complete yearly analysis for specified athlete"""
        
        logger.info(f"🚀 Starting yearly analysis for athlete {athlete_id} (past {days} days)")
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Phase 1: Data Collection
        logger.info("📊 Phase 1: Collecting and syncing data...")
        await self._sync_data_sources(start_date, end_date)
        
        # Phase 2: Core Analysis
        logger.info("🔍 Phase 2: Running core analysis...")
        metrics = await self._analyze_core_metrics(athlete_id, start_date, end_date)
        
        # Phase 3: AI Insights
        logger.info("🤖 Phase 3: Generating AI insights...")
        insights = self._generate_ai_insights(metrics)
        
        # Phase 4: Recommendations
        logger.info("🎯 Phase 4: Creating personalized recommendations...")
        recommendations = self._generate_recommendations(metrics, insights)
        
        # Compile results
        results = {
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
                "days": days
            },
            "athlete": {
                "id": athlete_id,
                "profile": await self._get_athlete_profile(athlete_id)
            },
            "summary_stats": metrics.get("summary_stats", {}),
            "performance_metrics": metrics.get("performance_metrics", {}),
            "health_indicators": metrics.get("health_indicators", {}),
            "training_load": metrics.get("training_load", {}),
            "sport_specific": metrics.get("sport_specific", {}),
            "ai_insights": insights,
            "recommendations": recommendations,
            "raw_data": metrics.get("raw_data", {})
        }
        
        logger.info("✅ Analysis complete!")
        return results
    
    async def _sync_data_sources(self, start_date: datetime, end_date: datetime):
        """Sync all configured data sources"""
        try:
            available_connectors = list_available_connectors()
            logger.info(f"Available connectors: {', '.join(available_connectors)}")
            
            for source in available_connectors:
                try:
                    logger.info(f"Syncing {source}...")
                    
                    # Create configuration for the connector
                    if source == "strava":
                        config = {
                            "client_id": os.getenv("STRAVA_CLIENT_ID"),
                            "client_secret": os.getenv("STRAVA_CLIENT_SECRET"),
                            "refresh_token": os.getenv("STRAVA_REFRESH_TOKEN"),
                            "access_token": os.getenv("STRAVA_ACCESS_TOKEN")
                        }
                    elif source == "vesync":
                        config = {
                            "username": os.getenv("VESYNC_USERNAME"),
                            "password": os.getenv("VESYNC_PASSWORD"),
                            "timezone": os.getenv("VESYNC_TIMEZONE", "America/Denver")
                        }
                    else:
                        config = {}
                    
                    connector = get_connector(source, config)
                    await connector.sync_data(start_date, end_date)
                    logger.info(f"✅ {source} sync complete")
                except Exception as e:
                    logger.warning(f"⚠️ {source} sync failed: {e}")
                    
        except Exception as e:
            logger.warning(f"Data sync failed, using cached data: {e}")
    
    async def _analyze_core_metrics(self, athlete_id: str, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Analyze core fitness metrics"""
        
        # Load workout data
        workouts = await self._load_workouts(athlete_id, start_date, end_date)
        biometrics = await self._load_biometrics(athlete_id, start_date, end_date)
        
        # Calculate summary statistics
        summary_stats = self._calculate_summary_stats(workouts)
        
        # Performance metrics
        performance_metrics = self._analyze_performance(workouts)
        
        # Health indicators
        health_indicators = self._analyze_health(biometrics, workouts)
        
        # Training load analysis
        training_load = self._analyze_training_load(workouts)
        
        # Sport-specific insights
        sport_specific = self._analyze_sport_specific(workouts)
        
        # Raw data for detailed analysis
        raw_data = self._prepare_raw_data(workouts, biometrics)
        
        return {
            "summary_stats": summary_stats,
            "performance_metrics": performance_metrics,
            "health_indicators": health_indicators,
            "training_load": training_load,
            "sport_specific": sport_specific,
            "raw_data": raw_data
        }
    
    async def _load_workouts(self, athlete_id: str, start_date: datetime, end_date: datetime) -> List[Workout]:
        """Load workouts for analysis period"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT * FROM workouts 
                    WHERE athlete_id = ? AND start_time BETWEEN ? AND ?
                    ORDER BY start_time DESC
                """, (athlete_id, start_date.isoformat(), end_date.isoformat()))
                
                rows = cursor.fetchall()
                return [Workout(**dict(zip([col[0] for col in cursor.description], row))) for row in rows]
        except Exception as e:
            logger.error(f"Error loading workouts: {e}")
            return []
    
    async def _load_biometrics(self, athlete_id: str, start_date: datetime, end_date: datetime) -> List[BiometricReading]:
        """Load biometric readings for analysis period"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT * FROM biometrics 
                    WHERE athlete_id = ? AND date BETWEEN ? AND ?
                    ORDER BY date DESC
                """, (athlete_id, start_date.date().isoformat(), end_date.date().isoformat()))
                
                rows = cursor.fetchall()
                return [BiometricReading(**dict(zip([col[0] for col in cursor.description], row))) for row in rows]
        except Exception as e:
            logger.error(f"Error loading biometrics: {e}")
            return []
    
    def _calculate_summary_stats(self, workouts: List[Workout]) -> Dict[str, Any]:
        """Calculate overall summary statistics"""
        if not workouts:
            return {"error": "No workout data available"}
        
        total_workouts = len(workouts)
        total_duration = sum(w.duration for w in workouts if w.duration)
        total_distance = sum(w.distance for w in workouts if w.distance)
        total_calories = sum(w.calories for w in workouts if w.calories)
        
        # Calculate consistency (workouts per week)
        if workouts:
            first_workout = min(w.start_time for w in workouts)
            last_workout = max(w.start_time for w in workouts)
            weeks = max(1, (last_workout - first_workout).days / 7)
            consistency = (total_workouts / weeks) if weeks > 0 else 0
        else:
            consistency = 0
        
        return {
            "total_workouts": total_workouts,
            "total_duration_hours": round(total_duration / 3600, 1) if total_duration else 0,
            "total_distance_km": round(total_distance / 1000, 1) if total_distance else 0,
            "total_calories": total_calories,
            "consistency_percent": round(consistency * 100 / 7, 1),
            "workouts_per_week": round(consistency, 1),
            "avg_workout_duration": round(total_duration / total_workouts / 60, 1) if total_workouts else 0
        }
    
    def _analyze_performance(self, workouts: List[Workout]) -> Dict[str, Any]:
        """Analyze performance trends and improvements"""
        if not workouts:
            return {"error": "No workout data available"}
        
        # Group by sport for sport-specific analysis
        sports = {}
        for workout in workouts:
            if workout.sport not in sports:
                sports[workout.sport] = []
            sports[workout.sport].append(workout)
        
        # Calculate performance trends
        performance_metrics = {}
        for sport, sport_workouts in sports.items():
            if len(sport_workouts) < 3:  # Need multiple workouts for trends
                continue
                
            # Sort by date for trend analysis
            sport_workouts.sort(key=lambda w: w.start_time)
            
            # Calculate pace improvements (if distance and duration available)
            if sport in ['Running', 'Cycling']:
                paces = []
                for w in sport_workouts:
                    if w.distance and w.duration:
                        pace = w.duration / (w.distance / 1000)  # seconds per km
                        paces.append(pace)
                
                if len(paces) >= 2:
                    first_half = np.mean(paces[:len(paces)//2])
                    second_half = np.mean(paces[len(paces)//2:])
                    improvement = ((first_half - second_half) / first_half) * 100
                    performance_metrics[sport] = {
                        "pace_improvement_percent": round(improvement, 1),
                        "first_half_pace": round(first_half, 1),
                        "second_half_pace": round(second_half, 1)
                    }
        
        return performance_metrics
    
    def _analyze_health(self, biometrics: List[BiometricReading], workouts: List[Workout]) -> Dict[str, Any]:
        """Analyze health indicators and trends"""
        health_data = {}
        
        # Analyze weight trends
        weight_readings = [b for b in biometrics if b.metric == 'weight']
        if weight_readings:
            weights = [(b.timestamp, b.value) for b in weight_readings]
            weights.sort(key=lambda x: x[0])
            
            if len(weights) >= 2:
                first_weight = weights[0][1]
                last_weight = weights[-1][1]
                weight_change = last_weight - first_weight
                health_data["weight_trend"] = {
                    "start_weight_kg": round(first_weight, 1),
                    "current_weight_kg": round(last_weight, 1),
                    "change_kg": round(weight_change, 1),
                    "change_percent": round((weight_change / first_weight) * 100, 1)
                }
        
        # Analyze heart rate trends from workouts
        hr_workouts = [w for w in workouts if w.heart_rate_avg]
        if hr_workouts:
            # Group by month for trend analysis
            monthly_hr = {}
            for workout in hr_workouts:
                month_key = workout.start_time.strftime("%Y-%m")
                if month_key not in monthly_hr:
                    monthly_hr[month_key] = []
                monthly_hr[month_key].append(workout.heart_rate_avg)
            
            # Calculate monthly averages
            monthly_averages = {month: np.mean(hrs) for month, hrs in monthly_hr.items()}
            if len(monthly_averages) >= 2:
                months = sorted(monthly_averages.keys())
                first_hr = monthly_averages[months[0]]
                last_hr = monthly_averages[months[-1]]
                hr_change = last_hr - first_hr
                
                health_data["heart_rate_trend"] = {
                    "first_month_avg": round(first_hr, 1),
                    "current_month_avg": round(last_hr, 1),
                    "change_bpm": round(hr_change, 1),
                    "trend": "improving" if hr_change < 0 else "declining"
                }
        
        return health_data
    
    def _analyze_training_load(self, workouts: List[Workout]) -> Dict[str, Any]:
        """Analyze training load and injury risk"""
        if not workouts:
            return {"error": "No workout data available"}
        
        # Calculate acute (7-day) and chronic (28-day) training loads
        now = datetime.now()
        acute_start = now - timedelta(days=7)
        chronic_start = now - timedelta(days=28)
        
        acute_workouts = [w for w in workouts if w.start_time >= acute_start]
        chronic_workouts = [w for w in workouts if w.start_time >= chronic_start]
        
        # Calculate load based on duration and intensity (simplified)
        acute_load = sum(w.duration / 3600 for w in acute_workouts)  # hours
        chronic_load = sum(w.duration / 3600 for w in chronic_workouts) / 4  # weekly average
        
        # Calculate acute:chronic workload ratio
        acwr = acute_load / chronic_load if chronic_load > 0 else 0
        
        # Assess injury risk
        injury_risk = self._assess_injury_risk(acwr, acute_load, chronic_load)
        
        return {
            "acute_load_hours": round(acute_load, 1),
            "chronic_load_hours": round(chronic_load, 1),
            "acwr_ratio": round(acwr, 2),
            "injury_risk": injury_risk,
            "fatigue_level": self._assess_fatigue_level(acute_load, chronic_load)
        }
    
    def _assess_injury_risk(self, acwr: float, acute_load: float, chronic_load: float) -> Dict[str, Any]:
        """Assess injury risk based on training load patterns"""
        risk_score = 0
        risk_level = "LOW"
        
        # ACWR component (40% weight)
        if acwr > 1.5:
            risk_score += 0.4
        elif acwr > 1.3:
            risk_score += 0.3
        elif acwr > 1.1:
            risk_score += 0.2
        
        # Acute load component (30% weight)
        if acute_load > 15:  # More than 15 hours in a week
            risk_score += 0.3
        elif acute_load > 10:
            risk_score += 0.2
        
        # Chronic load component (30% weight)
        if chronic_load > 12:  # More than 12 hours average
            risk_score += 0.3
        elif chronic_load > 8:
            risk_score += 0.2
        
        # Determine risk level
        if risk_score > 0.7:
            risk_level = "HIGH"
        elif risk_score > 0.4:
            risk_level = "MODERATE"
        
        return {
            "score": round(risk_score, 2),
            "level": risk_level,
            "factors": {
                "acwr": acwr,
                "acute_load": acute_load,
                "chronic_load": chronic_load
            }
        }
    
    def _assess_fatigue_level(self, acute_load: float, chronic_load: float) -> str:
        """Assess current fatigue level"""
        if acute_load > chronic_load * 1.3:
            return "HIGH"
        elif acute_load > chronic_load * 1.1:
            return "MODERATE"
        else:
            return "LOW"
    
    def _analyze_sport_specific(self, workouts: List[Workout]) -> Dict[str, Any]:
        """Generate sport-specific insights"""
        sports = {}
        
        for workout in workouts:
            if workout.sport not in sports:
                sports[workout.sport] = {
                    "count": 0,
                    "total_duration": 0,
                    "total_distance": 0,
                    "total_calories": 0,
                    "best_workout": None
                }
            
            sports[workout.sport]["count"] += 1
            sports[workout.sport]["total_duration"] += workout.duration or 0
            sports[workout.sport]["total_distance"] += workout.distance or 0
            sports[workout.sport]["total_calories"] += workout.calories or 0
            
            # Track best workout (by duration or distance)
            if not sports[workout.sport]["best_workout"]:
                sports[workout.sport]["best_workout"] = workout
            elif workout.duration and workout.duration > sports[workout.sport]["best_workout"].duration:
                sports[workout.sport]["best_workout"] = workout
        
        # Add calculated metrics
        for sport, data in sports.items():
            if data["count"] > 0:
                data["avg_duration"] = round(data["total_duration"] / data["count"] / 60, 1)
                data["avg_distance"] = round(data["total_distance"] / data["count"] / 1000, 1) if data["total_distance"] > 0 else 0
                data["avg_calories"] = round(data["total_calories"] / data["count"]) if data["total_calories"] > 0 else 0
        
        return sports
    
    def _prepare_raw_data(self, workouts: List[Workout], biometrics: List[BiometricReading]) -> Dict[str, Any]:
        """Prepare raw data for detailed analysis"""
        return {
            "workout_count": len(workouts),
            "biometric_count": len(biometrics),
            "date_range": {
                "start": min(w.start_time for w in workouts).isoformat() if workouts else None,
                "end": max(w.start_time for w in workouts).isoformat() if workouts else None
            }
        }
    
    def _generate_ai_insights(self, metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate AI-powered insights from metrics"""
        insights = []
        
        # Check if we have any meaningful data
        has_workout_data = (
            "summary_stats" in metrics and 
            metrics["summary_stats"] and 
            "error" not in metrics["summary_stats"]
        )
        
        # If no workout data, provide onboarding insights
        if not has_workout_data:
            insights.extend([
                {
                    "type": "info",
                    "title": "Welcome to Fitness Tracking!",
                    "message": "This is your first fitness analysis. Start by logging your workouts to get personalized insights.",
                    "recommendation": "Begin with 2-3 workouts per week and gradually build consistency"
                },
                {
                    "type": "tip",
                    "title": "Data Sources Available",
                    "message": "Your system is configured to sync with Strava and VeSync. Connect these accounts to automatically import your fitness data.",
                    "recommendation": "Check your API credentials in the .env file and ensure proper authentication"
                }
            ])
            return insights
        
        # Training load insights
        if "training_load" in metrics and metrics["training_load"] and "injury_risk" in metrics["training_load"]:
            injury_risk = metrics["training_load"]["injury_risk"]
            if injury_risk and injury_risk.get("level") == "HIGH":
                acwr = injury_risk.get("factors", {}).get("acwr", 0)
                insights.append({
                    "type": "warning",
                    "title": "High Injury Risk Detected",
                    "message": f"Your training load ratio is {acwr:.2f}, which indicates high injury risk.",
                    "recommendation": "Reduce volume by 30% this week or add 2 rest days"
                })
            elif injury_risk and injury_risk.get("level") == "MODERATE":
                insights.append({
                    "type": "caution",
                    "title": "Moderate Injury Risk",
                    "message": "Your training load is elevated. Monitor for signs of overtraining.",
                    "recommendation": "Consider an easy day or reduce intensity"
                })
        
        # Performance insights
        if "performance_metrics" in metrics:
            for sport, data in metrics["performance_metrics"].items():
                if "pace_improvement_percent" in data and data["pace_improvement_percent"] > 5:
                    insights.append({
                        "type": "achievement",
                        "title": f"Significant {sport} Improvement",
                        "message": f"Your {sport.lower()} pace has improved {data['pace_improvement_percent']}%!",
                        "recommendation": "Maintain current training rhythm"
                    })
        
        # Health insights
        if "health_indicators" in metrics:
            if "weight_trend" in metrics["health_indicators"]:
                weight_change = metrics["health_indicators"]["weight_trend"]["change_percent"]
                if abs(weight_change) > 5:
                    insights.append({
                        "type": "health",
                        "title": "Significant Weight Change",
                        "message": f"Your weight has changed {weight_change:.1f}% over the analysis period.",
                        "recommendation": "Review nutrition and training balance"
                    })
        
        return insights
    
    def _generate_recommendations(self, metrics: Dict[str, Any], insights: List[Dict[str, Any]]) -> List[str]:
        """Generate personalized recommendations"""
        recommendations = []
        
        # Check if we have any meaningful data
        has_workout_data = (
            "summary_stats" in metrics and 
            metrics["summary_stats"] and 
            "error" not in metrics["summary_stats"]
        )
        
        # If no workout data, provide onboarding recommendations
        if not has_workout_data:
            recommendations.extend([
                "Start with 2-3 workouts per week to build consistency",
                "Focus on proper form and gradual progression",
                "Consider mixing cardio and strength training",
                "Track your workouts to monitor progress over time",
                "Set realistic goals and celebrate small achievements"
            ])
            return recommendations
        
        # Training load recommendations
        if "training_load" in metrics and metrics["training_load"]:
            acwr = metrics["training_load"].get("acwr_ratio", 0)
            if acwr > 1.3:
                recommendations.append("Reduce training volume this week to prevent overtraining")
            elif acwr < 0.8:
                recommendations.append("Consider increasing training volume gradually")
        
        # Consistency recommendations
        if "summary_stats" in metrics and metrics["summary_stats"]:
            consistency = metrics["summary_stats"].get("consistency_percent", 0)
            if consistency < 70:
                recommendations.append("Focus on building consistent workout habits")
            elif consistency > 90:
                recommendations.append("Excellent consistency! Consider adding variety to prevent plateaus")
        
        # Sport-specific recommendations
        if "sport_specific" in metrics:
            for sport, data in metrics["sport_specific"].items():
                if data["count"] < 5:
                    recommendations.append(f"Add more {sport.lower()} sessions for better development")
        
        return recommendations
    
    async def _get_athlete_profile(self, athlete_id: str) -> Optional[Dict[str, Any]]:
        """Get athlete profile information"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT name, email, created_at FROM athletes WHERE athlete_id = ?
                """, (athlete_id,))
                row = cursor.fetchone()
                
                if row:
                    return {
                        "name": row[0],
                        "email": row[1],
                        "created_at": row[2]
                    }
                return None
        except Exception as e:
            logger.error(f"Error loading athlete profile: {e}")
            return None

def display_pretty_output(results: Dict[str, Any]):
    """Display results in a pretty console format"""
    
    print("\n" + "="*60)
    print(f"🏃 FITNESS YEAR IN REVIEW - {datetime.now().year}")
    print("="*60)
    
    # Overall Statistics
    if "summary_stats" in results and results["summary_stats"]:
        stats = results["summary_stats"]
        if "error" in stats:
            print(f"\n📊 OVERALL STATISTICS")
            print(f"└─ {stats['error']}")
        else:
            print(f"\n📊 OVERALL STATISTICS")
            print(f"├─ Total Workouts: {stats.get('total_workouts', 0)}")
            print(f"├─ Total Time: {stats.get('total_duration_hours', 0)} hours")
            print(f"├─ Total Distance: {stats.get('total_distance_km', 0)} km")
            print(f"├─ Calories Burned: {stats.get('total_calories', 0):,}")
            print(f"└─ Consistency: {stats.get('consistency_percent', 0)}% ({stats.get('workouts_per_week', 0)} workouts/week)")
    else:
        print(f"\n📊 OVERALL STATISTICS")
        print(f"└─ No data available")
    
    # Training Load
    if "training_load" in results and results["training_load"]:
        load = results["training_load"]
        if "error" in load:
            print(f"\n⚡ TRAINING LOAD ANALYSIS")
            print(f"└─ {load['error']}")
        else:
            print(f"\n⚡ TRAINING LOAD ANALYSIS")
            print(f"├─ Acute Load (7 days): {load.get('acute_load_hours', 0)} hours")
            print(f"├─ Chronic Load (28 days): {load.get('chronic_load_hours', 0)} hours")
            print(f"├─ Load Ratio: {load.get('acwr_ratio', 0):.2f}")
            print(f"├─ Injury Risk: {load.get('injury_risk', {}).get('level', 'UNKNOWN')}")
            print(f"└─ Fatigue Level: {load.get('fatigue_level', 'UNKNOWN')}")
    else:
        print(f"\n⚡ TRAINING LOAD ANALYSIS")
        print(f"└─ No data available")
    
    # AI Insights
    if "ai_insights" in results and results["ai_insights"]:
        print(f"\n🤖 AI INSIGHTS")
        for i, insight in enumerate(results["ai_insights"], 1):
            print(f"{i}. {insight['title']}")
            print(f"   {insight['message']}")
            print(f"   💡 {insight['recommendation']}")
    
    # Recommendations
    if "recommendations" in results and results["recommendations"]:
        print(f"\n🎯 PERSONALIZED RECOMMENDATIONS")
        for i, rec in enumerate(results["recommendations"], 1):
            print(f"{i}. {rec}")
    
    print("\n" + "="*60)

def save_json_report(results: Dict[str, Any], output_file: str = None):
    """Save detailed results to JSON file"""
    if not output_file:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"fitness_analysis_{timestamp}.json"
    
    try:
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        print(f"\n💾 Detailed report saved to: {output_file}")
    except Exception as e:
        print(f"\n❌ Error saving report: {e}")

async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Yearly Fitness Analysis")
    parser.add_argument("--athlete-id", default="default", help="Athlete ID to analyze")
    parser.add_argument("--days", type=int, default=365, help="Number of days to analyze")
    parser.add_argument("--output", help="Output JSON file path")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        # Initialize analyzer
        analyzer = YearlyFitnessAnalyzer()
        
        # Run analysis
        results = await analyzer.analyze_year(args.athlete_id, args.days)
        
        # Display results
        display_pretty_output(results)
        
        # Save detailed report
        save_json_report(results, args.output)
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        print(f"\n❌ Analysis failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
