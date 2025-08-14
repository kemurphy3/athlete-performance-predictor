#!/usr/bin/env python3
"""
Demo Calorie Calculator for Public Repository
This is a simplified version for demonstration purposes only.
The proprietary enhanced algorithms are maintained in the private repository.
"""

from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class DemoCalorieCalculator:
    """
    Simplified calorie calculator for demonstration purposes.
    Uses basic MET (Metabolic Equivalent of Task) calculations.
    """
    
    # Basic MET values for common activities
    MET_VALUES = {
        'running': 8.0,
        'cycling': 7.5,
        'walking': 3.5,
        'swimming': 8.0,
        'strength_training': 5.0,
        'yoga': 2.5,
        'default': 4.0
    }
    
    def calculate_calories(self, 
                         activity_type: str,
                         duration_minutes: float,
                         user_weight_kg: float = 70.0) -> float:
        """
        Calculate calories burned using basic MET formula.
        
        Formula: Calories = MET × weight(kg) × time(hours)
        
        Args:
            activity_type: Type of activity
            duration_minutes: Duration in minutes
            user_weight_kg: User weight in kilograms
            
        Returns:
            Estimated calories burned
        """
        met_value = self.MET_VALUES.get(activity_type.lower(), self.MET_VALUES['default'])
        duration_hours = duration_minutes / 60.0
        
        calories = met_value * user_weight_kg * duration_hours
        
        logger.info(f"Demo calculation: {activity_type} for {duration_minutes}min = {calories:.1f} calories")
        
        return round(calories, 1)
    
    def get_supported_activities(self) -> list:
        """Return list of supported activity types"""
        return list(self.MET_VALUES.keys())