#!/usr/bin/env python3
"""
Multi-Athlete Calorie Calculator
Extends EnhancedCalorieCalculator with multi-athlete support and robust missing data handling
"""

import logging
import sqlite3
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import uuid

from .calorie_calculator import EnhancedCalorieCalculator
from .models import (
    Workout, BiometricReading, UserProfile, CalorieCalculationResult,
    Athlete, AthleteDataSource, AthleteCalorieCalibration
)

logger = logging.getLogger(__name__)

class MultiAthleteCalorieCalculator(EnhancedCalorieCalculator):
    """Enhanced calculator with multi-athlete support and robust defaults"""
    
    def __init__(self, database_path: str):
        super().__init__(database_path)
        self.athlete_profiles_cache = {}
        self.calibration_cache = {}
        self.logger = logger
        
    def calculate_for_athlete(self, workout: Workout, athlete_id: Optional[str] = None) -> CalorieCalculationResult:
        """
        Calculate calories for specific athlete with graceful degradation
        
        Handles missing data by falling back through calculation methods:
        1. Direct calories from device (95% accuracy)
        2. Power/kilojoules (90% accuracy)
        3. HR + personal profile (83% accuracy)
        4. HR + default profile (75% accuracy)
        5. MET + personal profile (70% accuracy)
        6. MET + default profile (60% accuracy)
        7. Distance estimate (50% accuracy)
        """
        # Use athlete_id from workout if not provided
        if not athlete_id:
            athlete_id = getattr(workout, 'athlete_id', 'default')
        
        # Try to load athlete profile, fall back to defaults
        athlete_profile = self._get_or_create_athlete_profile(athlete_id)
        
        # Get athlete-specific calibration
        calibration_factor = self._get_calibration_factor(athlete_id, workout.sport)
        
        # Calculate using parent class enhanced method
        result = super().calculate_enhanced(workout, athlete_profile)
        
        # Apply athlete-specific calibration
        if calibration_factor != 1.0:
            result.calories = int(result.calories * calibration_factor)
            result.factors['calibration_factor'] = calibration_factor
            result.factors['athlete_id'] = athlete_id
        
        # Store result for future calibration if device provided calories
        if workout.calories and result.method != "direct_strava":
            self._update_calibration(athlete_id, workout.sport, workout.calories, result.calories)
        
        return result
    
    def _get_or_create_athlete_profile(self, athlete_id: str) -> UserProfile:
        """Get athlete profile with intelligent defaults for missing data"""
        
        # Check cache first
        if athlete_id in self.athlete_profiles_cache:
            return self.athlete_profiles_cache[athlete_id]
        
        # Try to load from database
        profile = self._load_athlete_profile(athlete_id)
        
        if not profile:
            # Create minimal profile with smart defaults
            profile = self._create_minimal_profile(athlete_id)
        
        # Fill in missing data with estimates
        profile = self._enhance_profile_with_estimates(profile, athlete_id)
        
        # Cache for performance
        self.athlete_profiles_cache[athlete_id] = profile
        
        return profile
    
    def _load_athlete_profile(self, athlete_id: str) -> Optional[UserProfile]:
        """Load athlete profile from database"""
        try:
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.execute("""
                    SELECT age, gender, weight_kg, height_cm, vo2max, resting_hr, max_hr, activity_level
                    FROM athlete_profiles 
                    WHERE athlete_id = ?
                """, (athlete_id,))
                
                row = cursor.fetchone()
                if row:
                    return UserProfile(
                        athlete_id=athlete_id,
                        age=row[0],
                        gender=row[1],
                        weight_kg=row[2],
                        height_cm=row[3],
                        vo2max=row[4],
                        resting_hr=row[5],
                        max_hr=row[6],
                        activity_level=row[7]
                    )
        except Exception as e:
            self.logger.warning(f"Could not load athlete profile for {athlete_id}: {e}")
        
        return None
    
    def _create_minimal_profile(self, athlete_id: str) -> UserProfile:
        """Create minimal profile when no data exists"""
        
        # Try to estimate from recent workouts
        estimates = self._estimate_from_workout_history(athlete_id)
        
        return UserProfile(
            athlete_id=athlete_id,
            age=estimates.get('age', 35),  # Conservative default
            gender=estimates.get('gender', 'male'),
            weight_kg=estimates.get('weight', 70.0),
            activity_level=estimates.get('activity_level', 'moderate')
        )
    
    def _estimate_from_workout_history(self, athlete_id: str) -> Dict[str, Any]:
        """Estimate athlete characteristics from their workout patterns"""
        
        estimates = {}
        
        try:
            with sqlite3.connect(self.database_path) as conn:
                # Estimate activity level from workout frequency
                cursor = conn.execute("""
                    SELECT COUNT(*) as workout_count,
                           AVG(duration) as avg_duration,
                           AVG(heart_rate_avg) as avg_hr
                    FROM workouts
                    WHERE athlete_id = ? AND start_time > date('now', '-30 days')
                """, (athlete_id,))
                
                row = cursor.fetchone()
                if row:
                    workout_count = row[0]
                    if workout_count > 20:
                        estimates['activity_level'] = 'very_active'
                    elif workout_count > 12:
                        estimates['activity_level'] = 'active'
                    elif workout_count > 6:
                        estimates['activity_level'] = 'moderate'
                    else:
                        estimates['activity_level'] = 'light'
                
                # Try to get weight from recent biometric readings
                cursor = conn.execute("""
                    SELECT value FROM biometrics
                    WHERE athlete_id = ? AND metric_type = 'weight'
                    ORDER BY date_value DESC LIMIT 1
                """, (athlete_id,))
                
                row = cursor.fetchone()
                if row:
                    estimates['weight'] = row[0]
                    
        except Exception as e:
            self.logger.warning(f"Could not estimate athlete data: {e}")
        
        return estimates
    
    def _enhance_profile_with_estimates(self, profile: UserProfile, athlete_id: str) -> UserProfile:
        """Fill in missing profile data with intelligent estimates"""
        
        # Estimate VO2max from workout performance if missing
        if not profile.vo2max:
            vo2max_estimate = self._estimate_vo2max_from_workouts(athlete_id, profile)
            if vo2max_estimate:
                profile.vo2max = vo2max_estimate
        
        # Estimate resting HR from morning readings if missing
        if not profile.resting_hr:
            resting_hr = self._estimate_resting_hr(athlete_id)
            if resting_hr:
                profile.resting_hr = resting_hr
        
        return profile
    
    def _estimate_vo2max_from_workouts(self, athlete_id: str, profile: UserProfile) -> Optional[float]:
        """Estimate VO2max from workout performance"""
        try:
            with sqlite3.connect(self.database_path) as conn:
                # Get recent running workouts with HR data
                cursor = conn.execute("""
                    SELECT duration, heart_rate_avg, distance
                    FROM workouts
                    WHERE athlete_id = ? AND sport = 'Run' AND heart_rate_avg > 0
                    ORDER BY start_time DESC LIMIT 10
                """, (athlete_id,))
                
                workouts = cursor.fetchall()
                if len(workouts) >= 3:
                    # Simple VO2max estimation based on HR and pace
                    # This is a rough estimate - real VO2max testing is more accurate
                    avg_hr = sum(w[1] for w in workouts) / len(workouts)
                    avg_pace = sum(w[2] / w[0] for w in workouts if w[2] and w[0]) / len(workouts)
                    
                    # Rough VO2max estimation (ml/kg/min)
                    if avg_pace > 0:
                        # Faster pace + lower HR = higher VO2max
                        estimated_vo2max = 50 + (avg_pace * 100) - (avg_hr * 0.2)
                        return max(30, min(80, estimated_vo2max))  # Reasonable bounds
                        
        except Exception as e:
            self.logger.warning(f"Could not estimate VO2max: {e}")
        
        return None
    
    def _estimate_resting_hr(self, athlete_id: str) -> Optional[int]:
        """Estimate resting HR from morning biometric readings"""
        try:
            with sqlite3.connect(self.database_path) as conn:
                # Get morning HR readings (before 9 AM)
                cursor = conn.execute("""
                    SELECT value FROM biometrics
                    WHERE athlete_id = ? AND metric_type = 'heart_rate'
                    AND strftime('%H', timestamp) < '09'
                    ORDER BY timestamp DESC LIMIT 5
                """, (athlete_id,))
                
                readings = cursor.fetchall()
                if readings:
                    # Use lowest reading as resting HR estimate
                    resting_hr = min(r[0] for r in readings)
                    return int(resting_hr)
                    
        except Exception as e:
            self.logger.warning(f"Could not estimate resting HR: {e}")
        
        return None
    
    def _get_calibration_factor(self, athlete_id: str, sport: str) -> float:
        """Get athlete-specific calibration factor for a sport"""
        
        cache_key = f"{athlete_id}:{sport}"
        if cache_key in self.calibration_cache:
            return self.calibration_cache[cache_key]
        
        try:
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.execute("""
                    SELECT calibration_factor FROM athlete_calorie_calibration
                    WHERE athlete_id = ? AND sport_category = ?
                """, (athlete_id, sport))
                
                row = cursor.fetchone()
                if row:
                    factor = row[0]
                    self.calibration_cache[cache_key] = factor
                    return factor
                    
        except Exception as e:
            self.logger.warning(f"Could not get calibration factor: {e}")
        
        # Default to no calibration
        return 1.0
    
    def _update_calibration(self, athlete_id: str, sport: str, actual_calories: int, 
                           predicted_calories: int):
        """Update athlete-specific calibration factor"""
        
        if predicted_calories <= 0:
            return
        
        ratio = actual_calories / predicted_calories
        
        # Sanity check - ignore outliers
        if ratio < 0.5 or ratio > 2.0:
            self.logger.warning(f"Ignoring outlier calibration ratio: {ratio}")
            return
        
        try:
            with sqlite3.connect(self.database_path) as conn:
                conn.execute("""
                    INSERT INTO athlete_calorie_calibration 
                    (athlete_id, sport_category, calibration_factor, sample_count, last_updated)
                    VALUES (?, ?, ?, 1, CURRENT_TIMESTAMP)
                    ON CONFLICT(athlete_id, sport_category) DO UPDATE SET
                        calibration_factor = (calibration_factor * sample_count + ?) / (sample_count + 1),
                        sample_count = sample_count + 1,
                        last_updated = CURRENT_TIMESTAMP
                """, (athlete_id, sport, ratio, ratio))
                
            # Update cache
            cache_key = f"{athlete_id}:{sport}"
            self.calibration_cache[cache_key] = ratio
            
        except Exception as e:
            self.logger.error(f"Failed to update calibration: {e}")
    
    def create_athlete(self, name: str, email: Optional[str] = None) -> str:
        """Create a new athlete in the system"""
        athlete_id = str(uuid.uuid4())
        
        try:
            with sqlite3.connect(self.database_path) as conn:
                # Create athlete record
                conn.execute("""
                    INSERT INTO athletes (athlete_id, name, email, created_at, active)
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP, TRUE)
                """, (athlete_id, name, email))
                
                # Create default profile
                default_profile = UserProfile(
                    athlete_id=athlete_id,
                    age=35,
                    gender='male',
                    weight_kg=70.0,
                    activity_level='moderate'
                )
                
                # Save profile
                conn.execute("""
                    INSERT INTO athlete_profiles 
                    (athlete_id, age, gender, weight_kg, height_cm, vo2max, resting_hr, max_hr, activity_level)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    default_profile.athlete_id,
                    default_profile.age,
                    default_profile.gender,
                    default_profile.weight_kg,
                    default_profile.height_cm,
                    default_profile.vo2max,
                    default_profile.resting_hr,
                    default_profile.max_hr,
                    default_profile.activity_level
                ))
                
                conn.commit()
                self.logger.info(f"Created athlete: {name} (ID: {athlete_id})")
                return athlete_id
                
        except Exception as e:
            self.logger.error(f"Failed to create athlete: {e}")
            raise
    
    def get_athlete_workouts(self, athlete_id: str, start_date: str, end_date: str) -> List[Workout]:
        """Get workouts for a specific athlete in date range"""
        workouts = []
        
        try:
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.execute("""
                    SELECT workout_id, athlete_id, start_time, end_time, duration, sport, sport_category,
                           distance, calories, heart_rate_avg, heart_rate_max, elevation_gain,
                           power_avg, cadence_avg, training_load, perceived_exertion, has_gps,
                           route_hash, gps_data, source, external_ids, raw_data,
                           data_quality_score, ml_features_extracted, plugin_data
                    FROM workouts
                    WHERE athlete_id = ? AND start_time BETWEEN ? AND ?
                    ORDER BY start_time DESC
                """, (athlete_id, start_date, end_date))
                
                for row in cursor.fetchall():
                    workout = Workout(
                        workout_id=row[0],
                        athlete_id=row[1],
                        start_time=datetime.fromisoformat(row[2]),
                        end_time=datetime.fromisoformat(row[3]) if row[3] else None,
                        duration=row[4],
                        sport=row[5],
                        sport_category=row[6],
                        distance=row[7],
                        calories=row[8],
                        heart_rate_avg=row[9],
                        heart_rate_max=row[10],
                        elevation_gain=row[11],
                        power_avg=row[12],
                        cadence_avg=row[13],
                        training_load=row[14],
                        perceived_exertion=row[15],
                        has_gps=bool(row[16]),
                        route_hash=row[17],
                        gps_data=row[18],
                        data_source=row[19],
                        external_ids=row[20],
                        raw_data=row[21],
                        data_quality_score=row[22],
                        ml_features_extracted=bool(row[23]),
                        plugin_data=row[24]
                    )
                    workouts.append(workout)
                    
        except Exception as e:
            self.logger.error(f"Failed to get athlete workouts: {e}")
        
        return workouts
