#!/usr/bin/env python3
"""
Calorie Calculator for Fitness Activities
Estimates calories burned when not provided by the data source
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class CalorieCalculator:
    """Calculate calories burned for fitness activities"""
    
    # MET values for different activities (calories per kg per hour)
    MET_VALUES = {
        # Running
        'Run': 8.0,
        'Trail Run': 8.5,
        'Virtual Run': 8.0,
        
        # Cycling
        'Ride': 6.0,
        'Virtual Ride': 6.0,
        'Mountain Bike': 7.0,
        
        # Swimming
        'Swim': 6.0,
        
        # Walking
        'Walk': 3.5,
        'Hike': 4.5,
        
        # Team Sports
        'Soccer': 7.0,
        'Basketball': 8.0,
        'Tennis': 7.0,
        'Volleyball': 4.0,
        
        # Strength Training
        'WeightTraining': 4.0,
        'StrengthTraining': 4.0,
        'Crossfit': 8.0,
        
        # Other
        'Yoga': 2.5,
        'Pilates': 3.0,
        'Rowing': 6.0,
        'Elliptical': 5.0,
        'Stair Stepper': 6.0,
        
        # Default for unknown activities
        'default': 4.0
    }
    
    def __init__(self):
        """Initialize the calorie calculator"""
        self.logger = logger
    
    def calculate_calories(self, workout_data: Dict[str, Any], user_weight_kg: float = 70.0) -> Optional[int]:
        """
        Calculate calories burned for a workout
        
        Args:
            workout_data: Dictionary containing workout information
            user_weight_kg: User's weight in kg (default: 70kg)
            
        Returns:
            Estimated calories burned, or None if calculation not possible
        """
        try:
            # Method 1: Use provided calories if available
            if workout_data.get('calories') and workout_data['calories'] > 0:
                return int(workout_data['calories'])
            
            # Method 2: Use kilojoules if available (1 kcal = 4.184 kJ)
            if workout_data.get('kilojoules') and workout_data['kilojoules'] > 0:
                return int(workout_data['kilojoules'] / 4.184)
            
            # Method 3: Calculate from heart rate if available
            if workout_data.get('average_heartrate') and workout_data.get('elapsed_time'):
                return self._calculate_from_heart_rate(
                    workout_data['average_heartrate'],
                    workout_data['elapsed_time'],
                    user_weight_kg
                )
            
            # Method 4: Calculate from MET values and duration
            if workout_data.get('elapsed_time') and workout_data.get('type'):
                return self._calculate_from_met(
                    workout_data['type'],
                    workout_data['elapsed_time'],
                    user_weight_kg
                )
            
            # Method 5: Estimate from distance and sport type
            if workout_data.get('distance') and workout_data.get('type'):
                return self._calculate_from_distance(
                    workout_data['type'],
                    workout_data['distance'],
                    workout_data.get('elapsed_time', 0),
                    user_weight_kg
                )
            
            self.logger.warning(f"Could not calculate calories for workout {workout_data.get('id', 'unknown')}")
            return None
            
        except Exception as e:
            self.logger.error(f"Error calculating calories: {e}")
            return None
    
    def _calculate_from_heart_rate(self, avg_hr: float, duration_seconds: int, weight_kg: float) -> int:
        """
        Calculate calories from heart rate using the heart rate reserve method
        
        This is more accurate than MET values for activities with heart rate data
        """
        try:
            # Estimate max HR using age (220 - age), assuming average age of 30
            estimated_max_hr = 190  # Conservative estimate
            resting_hr = 60  # Conservative estimate
            
            # Calculate heart rate reserve
            hr_reserve = estimated_max_hr - resting_hr
            
            # Calculate intensity as percentage of HR reserve
            if avg_hr > resting_hr:
                intensity = (avg_hr - resting_hr) / hr_reserve
            else:
                intensity = 0.1  # Very light activity
            
            # Duration in hours
            duration_hours = duration_seconds / 3600
            
            # Calories = weight * duration * intensity * 8.5 (cal/kg/hr for moderate activity)
            calories = weight_kg * duration_hours * intensity * 8.5
            
            return max(1, int(calories))
            
        except Exception as e:
            self.logger.error(f"Error in heart rate calculation: {e}")
            return None
    
    def _calculate_from_met(self, sport_type: str, duration_seconds: int, weight_kg: float) -> int:
        """
        Calculate calories using MET values
        
        Calories = MET * weight (kg) * duration (hours)
        """
        try:
            # Get MET value for sport type
            met_value = self.MET_VALUES.get(sport_type, self.MET_VALUES['default'])
            
            # Convert duration to hours
            duration_hours = duration_seconds / 3600
            
            # Calculate calories
            calories = met_value * weight_kg * duration_hours
            
            return max(1, int(calories))
            
        except Exception as e:
            self.logger.error(f"Error in MET calculation: {e}")
            return None
    
    def _calculate_from_distance(self, sport_type: str, distance_meters: float, 
                               duration_seconds: int, weight_kg: float) -> int:
        """
        Calculate calories from distance and sport type
        
        This is useful for activities where we know the distance but not duration
        """
        try:
            # Get MET value
            met_value = self.MET_VALUES.get(sport_type, self.MET_VALUES['default'])
            
            # If we have duration, use MET method
            if duration_seconds > 0:
                return self._calculate_from_met(sport_type, duration_seconds, weight_kg)
            
            # Otherwise, estimate duration from distance and typical speeds
            typical_speeds = {
                'Run': 2.8,      # m/s (10 min/mile)
                'Ride': 8.0,     # m/s (22 mph)
                'Walk': 1.4,     # m/s (3 mph)
                'Swim': 1.0,     # m/s (2 mph)
                'default': 2.0   # m/s
            }
            
            speed = typical_speeds.get(sport_type, typical_speeds['default'])
            estimated_duration = distance_meters / speed
            
            return self._calculate_from_met(sport_type, estimated_duration, weight_kg)
            
        except Exception as e:
            self.logger.error(f"Error in distance calculation: {e}")
            return None
    
    def get_calorie_quality_score(self, workout_data: Dict[str, Any]) -> float:
        """
        Get a quality score for the calorie calculation (0.0 to 1.0)
        
        Higher scores indicate more reliable calorie estimates
        """
        score = 0.0
        
        # Direct calories: highest quality
        if workout_data.get('calories') and workout_data['calories'] > 0:
            score += 0.4
        
        # Kilojoules: high quality
        if workout_data.get('kilojoules') and workout_data['kilojoules'] > 0:
            score += 0.35
        
        # Heart rate data: good quality
        if workout_data.get('average_heartrate') and workout_data['average_heartrate'] > 0:
            score += 0.25
        
        # Duration and sport type: moderate quality
        if workout_data.get('elapsed_time') and workout_data.get('type'):
            score += 0.15
        
        # Distance data: lower quality
        if workout_data.get('distance'):
            score += 0.05
        
        return min(1.0, score)
    
    def estimate_user_weight(self, height_cm: float = 175.0, age: int = 30, 
                           gender: str = 'male', activity_level: str = 'moderate') -> float:
        """
        Estimate user weight if not provided
        
        This is a rough estimate based on typical body composition
        """
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

