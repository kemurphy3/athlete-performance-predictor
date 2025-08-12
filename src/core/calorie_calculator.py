#!/usr/bin/env python3
"""
Enhanced Calorie Calculator for Fitness Activities
Implements research-based formulas (Keytel et al., 2005) for improved accuracy
"""

import logging
import asyncio
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import math

from .models import Workout, BiometricReading, UserProfile, CalorieCalculationResult

logger = logging.getLogger(__name__)

class EnhancedCalorieCalculator:
    """Enhanced calorie calculator using research-based formulas"""
    
    # Enhanced MET values with intensity variations
    MET_VALUES = {
        # Running (varies by pace)
        'Run': {'easy': 6.0, 'moderate': 8.0, 'hard': 10.0, 'race': 12.0},
        'Trail Run': {'easy': 6.5, 'moderate': 8.5, 'hard': 10.5, 'race': 12.5},
        'Virtual Run': {'easy': 6.0, 'moderate': 8.0, 'hard': 10.0, 'race': 12.0},
        
        # Cycling (varies by intensity)
        'Ride': {'easy': 4.0, 'moderate': 6.0, 'hard': 8.0, 'race': 10.0},
        'Virtual Ride': {'easy': 4.0, 'moderate': 6.0, 'hard': 8.0, 'race': 10.0},
        'Mountain Bike': {'easy': 5.0, 'moderate': 7.0, 'hard': 9.0, 'race': 11.0},
        
        # Swimming (varies by stroke and intensity)
        'Swim': {'easy': 4.0, 'moderate': 6.0, 'hard': 8.0, 'race': 10.0},
        
        # Walking (varies by pace)
        'Walk': {'slow': 2.5, 'moderate': 3.5, 'fast': 4.5, 'race': 6.0},
        'Hike': {'easy': 3.5, 'moderate': 4.5, 'hard': 6.0, 'race': 7.5},
        
        # Team Sports (varies by position and intensity)
        'Soccer': {'defense': 6.0, 'midfield': 7.0, 'forward': 8.0, 'goalkeeper': 4.0},
        'Basketball': {'guard': 7.0, 'forward': 8.0, 'center': 7.5, 'game': 8.0},
        'Tennis': {'singles': 7.0, 'doubles': 6.0, 'practice': 5.0, 'match': 7.5},
        'Volleyball': {'recreational': 3.0, 'competitive': 4.0, 'beach': 5.0},
        
        # Strength Training (varies by rest/work ratio)
        'WeightTraining': {'light': 3.0, 'moderate': 4.0, 'heavy': 5.0, 'circuit': 6.0},
        'StrengthTraining': {'light': 3.0, 'moderate': 4.0, 'heavy': 5.0, 'circuit': 6.0},
        'Crossfit': {'light': 6.0, 'moderate': 8.0, 'hard': 10.0, 'competition': 12.0},
        
        # Other activities
        'Yoga': {'gentle': 2.0, 'moderate': 2.5, 'power': 3.5, 'hot': 4.0},
        'Pilates': {'beginner': 2.0, 'intermediate': 3.0, 'advanced': 4.0},
        'Rowing': {'easy': 4.0, 'moderate': 6.0, 'hard': 8.0, 'race': 10.0},
        'Elliptical': {'easy': 3.0, 'moderate': 5.0, 'hard': 7.0, 'max': 9.0},
        'Stair Stepper': {'easy': 4.0, 'moderate': 6.0, 'hard': 8.0, 'max': 10.0},
        
        # Default for unknown activities
        'default': {'easy': 3.0, 'moderate': 4.0, 'hard': 5.0, 'max': 6.0}
    }
    
    def __init__(self, database_path: str = None):
        """Initialize enhanced calorie calculator"""
        self.logger = logger
        self.database_path = database_path
        # More conservative default profile to prevent overestimation
        self.default_user = UserProfile(
            athlete_id="default",
            age=30,
            gender="male",
            weight_kg=65.0,  # Reduced from 70kg to be more conservative
            height_cm=175.0,
            activity_level="moderate"
        )
    
    def calculate_enhanced(self, workout: Workout, user_profile: Optional[UserProfile] = None, 
                          environmental_data: Optional[Dict[str, Any]] = None) -> CalorieCalculationResult:
        """
        Calculate calories using enhanced methods with research-based formulas
        
        Args:
            workout: Workout data
            user_profile: User profile for personalized calculations
            environmental_data: Weather/environmental conditions
            
        Returns:
            CalorieCalculationResult with calculated calories and confidence
        """
        if user_profile is None:
            user_profile = self.default_user
            self.logger.warning("Using default user profile for calorie calculation")
        
        # Get actual weight from available sources instead of assuming
        actual_weight = self.get_actual_weight_from_sources(workout)
        if actual_weight:
            # Create a copy of user profile with actual weight
            user_profile = user_profile.copy(update={'weight_kg': actual_weight})
            self.logger.info(f"Using actual weight: {actual_weight}kg instead of assumed: {self.default_user.weight_kg}kg")
        
        try:
            # Method 1: Use provided calories if high quality
            if workout.calories and workout.data_quality_score > 0.9:
                return CalorieCalculationResult(
                    calories=workout.calories,
                    method="direct_strava",
                    confidence=workout.data_quality_score,
                    factors={"source": "strava_api", "quality": workout.data_quality_score},
                    quality_score=workout.data_quality_score
                )
            
            # Method 2: Use kilojoules if available
            if workout.raw_data and workout.raw_data.get('kilojoules'):
                kj = workout.raw_data['kilojoules']
                calories = int(kj / 4.184)
                return CalorieCalculationResult(
                    calories=calories,
                    method="kilojoules_conversion",
                    confidence=0.85,
                    factors={"kilojoules": kj, "conversion_factor": 4.184},
                    quality_score=0.85
                )
            
            # Method 3: Research-based heart rate calculation (Keytel et al., 2005)
            if workout.heart_rate_avg and workout.heart_rate_avg > 0:
                calories = self._calculate_from_heart_rate_keytel(workout, user_profile)
                if calories:
                    # Apply environmental adjustments
                    if environmental_data:
                        calories = self._apply_environmental_factors(calories, environmental_data)
                    
                    # Apply validation caps to prevent overestimation
                    calories = self._apply_calorie_validation_caps(calories, workout, user_profile)
                    
                    return CalorieCalculationResult(
                        calories=int(calories),
                        method="heart_rate_keytel",
                        confidence=0.83,
                        factors={
                            "hr_avg": workout.heart_rate_avg,
                            "hr_max": user_profile.calculated_max_hr,
                            "hr_rest": user_profile.resting_hr or 60,
                            "age": user_profile.age,
                            "gender": user_profile.gender,
                            "weight_kg": user_profile.weight_kg,
                            "vo2max": user_profile.vo2max,
                            "environmental": environmental_data
                        },
                        quality_score=0.83
                    )
            
            # Method 4: Enhanced MET calculation with intensity
            if workout.duration and workout.sport:
                calories = self._calculate_met_with_intensity(workout, user_profile)
                if calories:
                    # Apply validation caps to prevent overestimation
                    calories = self._apply_calorie_validation_caps(calories, workout, user_profile)
                    
                    return CalorieCalculationResult(
                        calories=int(calories),
                        method="met_intensity_adjusted",
                        confidence=0.75,
                        factors={
                            "sport": workout.sport,
                            "duration_min": workout.duration / 60,
                            "weight_kg": user_profile.weight_kg,
                            "intensity_factor": self._get_intensity_factor(workout, user_profile)
                        },
                        quality_score=0.75
                    )
            
            # Method 5: Sport-specific calculations
            if workout.sport in ['WeightTraining', 'StrengthTraining']:
                calories = self._calculate_weight_training(workout, user_profile)
                if calories:
                    # Apply validation caps to prevent overestimation
                    calories = self._apply_calorie_validation_caps(calories, workout, user_profile)
                    
                    return CalorieCalculationResult(
                        calories=int(calories),
                        method="weight_training_specialized",
                        confidence=0.70,
                        factors={
                            "sport": workout.sport,
                            "duration_min": workout.duration / 60,
                            "work_ratio": self._estimate_work_ratio(workout),
                            "weight_kg": user_profile.weight_kg
                        },
                        quality_score=0.70
                    )
            
            # Method 6: Basic MET calculation
            calories = self._calculate_basic_met(workout, user_profile)
            if calories:
                # Apply validation caps to prevent overestimation
                calories = self._apply_calorie_validation_caps(calories, workout, user_profile)
                
                return CalorieCalculationResult(
                    calories=int(calories),
                    method="basic_met",
                    confidence=0.60,
                    factors={
                        "sport": workout.sport,
                        "duration_min": workout.duration / 60,
                        "weight_kg": user_profile.weight_kg,
                        "base_met": self._get_base_met(workout.sport)
                    },
                    quality_score=0.60
                )
            
            # Fallback: estimate from distance
            calories = self._calculate_from_distance(workout, user_profile)
            if calories:
                # Apply validation caps to prevent overestimation
                calories = self._apply_calorie_validation_caps(calories, workout, user_profile)
                
                return CalorieCalculationResult(
                    calories=int(calories),
                    method="distance_estimated",
                    confidence=0.50,
                    factors={
                        "sport": workout.sport,
                        "distance_km": workout.distance / 1000 if workout.distance else 0,
                        "weight_kg": user_profile.weight_kg,
                        "estimated_duration": self._estimate_duration_from_distance(workout)
                    },
                    quality_score=0.50
                )
            
            self.logger.warning(f"Could not calculate calories for workout {workout.workout_id}")
            return CalorieCalculationResult(
                calories=0,
                method="failed",
                confidence=0.0,
                factors={"error": "insufficient_data"},
                quality_score=0.0
            )
            
        except Exception as e:
            self.logger.error(f"Error in enhanced calorie calculation: {e}")
            return CalorieCalculationResult(
                calories=0,
                method="error",
                confidence=0.0,
                factors={"error": str(e)},
                quality_score=0.0
            )
    
    def _calculate_from_heart_rate_keytel(self, workout: Workout, user: UserProfile) -> Optional[float]:
        """
        Keytel et al. (2005) formulas - 83% accuracy with personal metrics
        
        Reference: Keytel, L. R., et al. (2005). Prediction of energy expenditure 
        from heart rate monitoring during submaximal exercise. Journal of Sports Sciences, 23(3), 289-297.
        """
        try:
            hr_avg = workout.heart_rate_avg
            duration_min = workout.duration / 60
            
            if user.gender == 'male':
                if user.vo2max:
                    # Most accurate formula with VO2max
                    calories = ((-95.7735 + (0.634 * hr_avg) + (0.404 * user.vo2max) +
                               (0.394 * user.weight_kg) + (0.271 * user.age)) / 4.184) * duration_min
                else:
                    # Without VO2max
                    calories = ((-55.0969 + (0.6309 * hr_avg) + (0.1988 * user.weight_kg) +
                               (0.2017 * user.age)) / 4.184) * duration_min
            else:  # female
                if user.vo2max:
                    calories = ((-59.3954 + (0.45 * hr_avg) + (0.380 * user.vo2max) +
                               (0.103 * user.weight_kg) + (0.274 * user.age)) / 4.184) * duration_min
                else:
                    calories = ((-20.4022 + (0.4472 * hr_avg) + (0.1263 * user.weight_kg) +
                               (0.074 * user.age)) / 4.184) * duration_min
            
            return max(1, calories)
            
        except Exception as e:
            self.logger.error(f"Error in Keytel calculation: {e}")
            return None
    
    def _calculate_met_with_intensity(self, workout: Workout, user: UserProfile) -> Optional[float]:
        """Calculate METs with HR-based intensity adjustments"""
        try:
            base_met = self._get_base_met(workout.sport)
            duration_hours = workout.duration / 3600
            
            if workout.heart_rate_avg and user.resting_hr:
                # Calculate HR zones
                hr_reserve = user.calculated_max_hr - user.resting_hr
                hr_percent = (workout.heart_rate_avg - user.resting_hr) / hr_reserve
                
                # Sport-specific intensity adjustments - REDUCED to prevent overestimation
                intensity_factor = self._get_intensity_factor(workout, user)
                
                # Apply conservative scaling to prevent overestimation
                # Cap the maximum MET adjustment to prevent unrealistic values
                max_intensity_factor = 1.2  # Cap at 20% increase
                intensity_factor = min(intensity_factor, max_intensity_factor)
                
                adjusted_met = base_met * intensity_factor
                
                # Calculate calories
                calories = adjusted_met * user.weight_kg * duration_hours
                return max(1, calories)
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error in MET intensity calculation: {e}")
            return None
    
    def _get_intensity_factor(self, workout: Workout, user: UserProfile) -> float:
        """Get intensity factor based on HR zones and sport type"""
        if not workout.heart_rate_avg or not user.resting_hr:
            return 1.0
        
        # Use actual HR data instead of assuming max HR
        hr_avg = workout.heart_rate_avg
        hr_rest = user.resting_hr or 60
        
        # Calculate HR reserve using actual max HR if available, otherwise use actual HR data
        if user.max_hr:
            hr_max = user.max_hr
        else:
            # Use actual HR data to estimate intensity instead of assuming max HR
            # This prevents overestimation by using real data
            hr_max = hr_avg + (hr_avg - hr_rest) * 0.3  # Conservative estimate
        
        hr_reserve = hr_max - hr_rest
        hr_percent = (hr_avg - hr_rest) / hr_reserve if hr_reserve > 0 else 0.5
        
        # Sport-specific intensity adjustments - REDUCED to prevent overestimation
        if workout.sport in ['Soccer', 'Basketball', 'Tennis']:
            if hr_percent < 0.6:  # Zone 2
                return 0.8  # Reduced from 0.7
            elif hr_percent < 0.7:  # Zone 3
                return 1.0  # No change
            elif hr_percent < 0.8:  # Zone 4
                return 1.1  # Reduced from 1.3
            else:  # Zone 5
                return 1.2  # Reduced from 1.5
        elif workout.sport in ['WeightTraining', 'StrengthTraining']:
            # Weight training typically has lower intensity due to rest periods
            return 0.7  # Reduced from 0.8
        else:
            # Default intensity scaling - REDUCED to prevent overestimation
            return 0.6 + (hr_percent * 0.4)  # 0.6 to 1.0 range (was 0.5 to 1.3)
    
    def _calculate_weight_training(self, workout: Workout, user: UserProfile) -> Optional[float]:
        """Special handling for weight training with work/rest ratios"""
        try:
            # Estimate work/rest ratio
            work_ratio = self._estimate_work_ratio(workout)
            
            # Use MET calculation with work ratio adjustment
            base_met = self._get_base_met(workout.sport)
            duration_hours = workout.duration / 3600
            
            # Apply work ratio to get effective duration
            effective_duration = duration_hours * work_ratio
            
            calories = base_met * user.weight_kg * effective_duration
            return max(1, calories)
            
        except Exception as e:
            self.logger.error(f"Error in weight training calculation: {e}")
            return None
    
    def _estimate_work_ratio(self, workout: Workout) -> float:
        """Estimate work/rest ratio for weight training"""
        # Default 40% work time (60% rest)
        work_ratio = 0.4
        
        if workout.raw_data and 'exercises' in workout.raw_data:
            try:
                # Try to calculate actual work time from sets/reps/rest
                exercises = workout.raw_data.get('exercises', [])
                total_sets = sum(ex.get('sets', 0) for ex in exercises)
                
                if total_sets > 0:
                    # Estimate rest between sets (90 seconds typical)
                    avg_rest_between_sets = 90
                    estimated_rest_time = total_sets * avg_rest_between_sets
                    
                    # Calculate work ratio
                    work_time = max(workout.duration - estimated_rest_time, workout.duration * 0.2)
                    work_ratio = max(0.2, min(0.7, work_time / workout.duration))
                    
            except Exception as e:
                self.logger.warning(f"Could not parse exercise data: {e}")
        
        return work_ratio
    
    def _get_base_met(self, sport: str) -> float:
        """Get base MET value for a sport"""
        if sport in self.MET_VALUES:
            # Return moderate intensity as default
            met_dict = self.MET_VALUES[sport]
            if isinstance(met_dict, dict):
                return met_dict.get('moderate', met_dict.get('easy', 4.0))
            else:
                return met_dict
        
        return self.MET_VALUES['default']['moderate']
    
    def _calculate_basic_met(self, workout: Workout, user: UserProfile) -> Optional[float]:
        """Basic MET calculation without intensity adjustments"""
        try:
            base_met = self._get_base_met(workout.sport)
            duration_hours = workout.duration / 3600
            
            calories = base_met * user.weight_kg * duration_hours
            return max(1, calories)
            
        except Exception as e:
            self.logger.error(f"Error in basic MET calculation: {e}")
            return None
    
    def _calculate_from_distance(self, workout: Workout, user: UserProfile) -> Optional[float]:
        """Estimate calories from distance and sport type"""
        try:
            if not workout.distance:
                return None
            
            # Get MET value
            met_value = self._get_base_met(workout.sport)
            
            # If we have duration, use MET method
            if workout.duration > 0:
                duration_hours = workout.duration / 3600
                calories = met_value * user.weight_kg * duration_hours
                return max(1, calories)
            
            # Otherwise, estimate duration from distance and typical speeds
            estimated_duration = self._estimate_duration_from_distance(workout)
            if estimated_duration:
                duration_hours = estimated_duration / 3600
                calories = met_value * user.weight_kg * duration_hours
                return max(1, calories)
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error in distance calculation: {e}")
            return None
    
    def _estimate_duration_from_distance(self, workout: Workout) -> Optional[float]:
        """Estimate duration from distance using typical speeds"""
        typical_speeds = {
            'Run': 2.8,      # m/s (10 min/mile)
            'Ride': 8.0,     # m/s (22 mph)
            'Walk': 1.4,     # m/s (3 mph)
            'Swim': 1.0,     # m/s (2 mph)
            'Soccer': 2.0,   # m/s (estimated)
            'WeightTraining': 0.5,  # m/s (very slow, mostly stationary)
            'default': 2.0   # m/s
        }
        
        speed = typical_speeds.get(workout.sport, typical_speeds['default'])
        estimated_duration = workout.distance / speed
        
        return estimated_duration
    
    def _apply_environmental_factors(self, calories: float, env_data: Dict[str, Any]) -> float:
        """Apply environmental adjustments to calorie calculations"""
        try:
            # Temperature adjustments (higher temp = more calories due to cooling)
            temp_c = env_data.get('temperature_c')
            if temp_c is not None:
                if temp_c > 25:  # Hot weather
                    calories *= 1.05  # 5% increase
                elif temp_c < 5:   # Cold weather
                    calories *= 1.03  # 3% increase
            
            # Humidity adjustments
            humidity = env_data.get('humidity_percent')
            if humidity is not None and humidity > 70:
                calories *= 1.02  # 2% increase for high humidity
            
            # Elevation adjustments (already handled in workout data)
            # Wind adjustments could be added here
            
            return calories
            
        except Exception as e:
            self.logger.warning(f"Error applying environmental factors: {e}")
            return calories
    
    def _apply_calorie_validation_caps(self, calories: float, workout: Workout, user_profile: UserProfile) -> float:
        """Apply validation caps to prevent unrealistic calorie values"""
        try:
            duration_min = workout.duration / 60
            weight_kg = user_profile.weight_kg
            
            # Sport-specific calorie caps per minute to prevent overestimation
            max_calories_per_minute = {
                'Soccer': 12.0,      # Reduced from unlimited
                'Basketball': 12.0,  # Reduced from unlimited
                'Tennis': 10.0,      # Reduced from unlimited
                'Run': 15.0,         # Reduced from unlimited
                'Ride': 12.0,        # Reduced from unlimited
                'WeightTraining': 8.0,  # Reduced from unlimited
                'Walk': 6.0,         # Reduced from unlimited
                'Swim': 10.0,        # Reduced from unlimited
                'default': 10.0      # Conservative default
            }
            
            sport = workout.sport or 'default'
            max_cpm = max_calories_per_minute.get(sport, max_calories_per_minute['default'])
            
            # Calculate maximum allowed calories
            max_allowed_calories = max_cpm * duration_min
            
            # Apply cap if calories exceed reasonable limit
            if calories > max_allowed_calories:
                self.logger.info(f"Capping calories for {sport}: {calories:.0f} -> {max_allowed_calories:.0f} (max {max_cpm} cal/min)")
                calories = max_allowed_calories
            
            # Additional safety check: calories should not exceed 25 cal/min for any activity
            absolute_max_cpm = 25.0
            absolute_max_calories = absolute_max_cpm * duration_min
            
            if calories > absolute_max_calories:
                self.logger.warning(f"Applying absolute calorie cap: {calories:.0f} -> {absolute_max_calories:.0f} (max {absolute_max_cpm} cal/min)")
                calories = absolute_max_calories
            
            return calories
            
        except Exception as e:
            self.logger.warning(f"Error applying calorie validation caps: {e}")
            return calories
    
    def get_calorie_quality_score(self, workout: Workout, user_profile: Optional[UserProfile] = None) -> float:
        """Get enhanced quality score for calorie calculation"""
        score = 0.0
        
        # Direct calories: highest quality
        if workout.calories and workout.calories > 0:
            score += 0.4
        
        # Kilojoules: high quality
        if workout.raw_data and workout.raw_data.get('kilojoules'):
            score += 0.35
        
        # Heart rate data: good quality
        if workout.heart_rate_avg and workout.heart_rate_avg > 0:
            score += 0.25
            
            # Bonus for personal HR data
            if user_profile and user_profile.resting_hr and user_profile.max_hr:
                score += 0.1
        
        # Duration and sport type: moderate quality
        if workout.duration and workout.sport:
            score += 0.15
        
        # Distance data: lower quality
        if workout.distance:
            score += 0.05
        
        # Environmental data bonus
        if hasattr(workout, 'gps_data') and workout.gps_data:
            score += 0.05
        
        return min(1.0, score)
    
    def estimate_user_weight(self, height_cm: float = 175.0, age: int = 30, 
                           gender: str = 'male', activity_level: str = 'moderate') -> float:
        """Estimate user weight if not provided"""
        # Basic weight estimation (very rough)
        if gender.lower() == 'male':
            base_weight = height_cm - 100
        else:
            base_weight = height_cm - 110
        
        # Adjust for activity level
        activity_multipliers = {
            'sedentary': 0.9,
            'light': 0.95,
            'moderate': 1.0,
            'active': 1.05,
            'very_active': 1.1
        }
        
        multiplier = activity_multipliers.get(activity_level.lower(), 1.0)
        estimated_weight = base_weight * multiplier
        
        return max(45.0, min(150.0, estimated_weight))  # Reasonable bounds

    def get_actual_weight_from_sources(self, workout: Workout) -> Optional[float]:
        """Get actual weight from available data sources, prioritizing most recent"""
        try:
            # Priority 1: Check if workout has weight data
            if hasattr(workout, 'raw_data') and workout.raw_data:
                # Check for weight in Strava data
                if 'athlete' in workout.raw_data and 'weight' in workout.raw_data['athlete']:
                    weight = workout.raw_data['athlete']['weight']
                    if weight and weight > 0:
                        self.logger.info(f"Using weight from Strava workout: {weight}kg")
                        return weight
                
                # Check for weight in VeSync data
                if 'weight' in workout.raw_data:
                    weight = workout.raw_data['weight']
                    if weight and weight > 0:
                        self.logger.info(f"Using weight from VeSync workout: {weight}kg")
                        return weight
            
            # Priority 2: Check database for recent biometric readings
            if self.database_path:
                try:
                    import sqlite3
                    with sqlite3.connect(self.database_path) as conn:
                        cursor = conn.cursor()
                        # Get most recent weight reading from VeSync
                        cursor.execute("""
                            SELECT value FROM biometric_readings 
                            WHERE metric = 'weight' AND data_source = 'vesync'
                            ORDER BY timestamp DESC LIMIT 1
                        """)
                        row = cursor.fetchone()
                        if row and row[0] > 0:
                            weight = float(row[0])
                            self.logger.info(f"Using weight from VeSync biometrics: {weight}kg")
                            return weight
                except Exception as e:
                    self.logger.warning(f"Could not fetch weight from database: {e}")
            
            return None
            
        except Exception as e:
            self.logger.warning(f"Error getting actual weight: {e}")
            return None

