#!/usr/bin/env python3
"""
Data Source Adapter
Normalizes workout data from different sources to provide consistent data for multi-athlete support
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class DataSourceAdapter:
    """Adapt various data sources to provide consistent data"""
    
    @staticmethod
    def normalize_workout_data(workout: Dict[str, Any], source: str) -> Dict[str, Any]:
        """Normalize workout data from different sources"""
        
        normalized = {}
        
        # Map source-specific fields to standard fields
        field_mappings = {
            'strava': {
                'id': 'external_id',
                'start_date': 'start_time',
                'elapsed_time': 'duration',
                'type': 'sport',
                'average_heartrate': 'heart_rate_avg',
                'max_heartrate': 'heart_rate_max',
                'total_elevation_gain': 'elevation_gain',
                'kilojoules': 'kilojoules',
                'athlete': 'athlete_data'
            },
            'garmin': {
                'activityId': 'external_id',
                'startTimeLocal': 'start_time',
                'duration': 'duration',
                'activityType': 'sport',
                'averageHR': 'heart_rate_avg',
                'maxHR': 'heart_rate_max',
                'elevationGain': 'elevation_gain',
                'calories': 'calories'
            },
            'apple_health': {
                'identifier': 'external_id',
                'startDate': 'start_time',
                'duration': 'duration',
                'workoutActivityType': 'sport',
                'averageHeartRate': 'heart_rate_avg',
                'activeEnergyBurned': 'calories'
            },
            'vesync': {
                'device_id': 'external_id',
                'timestamp': 'start_time',
                'duration': 'duration',
                'activity_type': 'sport',
                'heart_rate': 'heart_rate_avg',
                'calories': 'calories'
            }
        }
        
        mapping = field_mappings.get(source, {})
        
        for source_field, standard_field in mapping.items():
            if source_field in workout:
                normalized[standard_field] = workout[source_field]
        
        # Handle missing duration by calculating from start/end times
        if 'duration' not in normalized and 'start_time' in normalized and 'end_time' in workout:
            try:
                start = datetime.fromisoformat(normalized['start_time'])
                end = datetime.fromisoformat(workout['end_time'])
                normalized['duration'] = int((end - start).total_seconds())
            except (ValueError, TypeError):
                logger.warning(f"Could not parse start/end times for duration calculation")
        
        # Estimate missing heart rate from perceived exertion
        if 'heart_rate_avg' not in normalized and 'perceived_exertion' in workout:
            # Rough estimate: RPE 6-20 scale maps to 60-200 HR
            rpe = workout['perceived_exertion']
            if isinstance(rpe, (int, float)) and 6 <= rpe <= 20:
                normalized['heart_rate_avg'] = 60 + (rpe * 10)
        
        # Handle missing calories with basic estimation
        if 'calories' not in normalized and 'duration' in normalized:
            # Basic MET estimation for common activities
            sport = normalized.get('sport', 'Unknown')
            duration_hours = normalized['duration'] / 3600
            
            # Conservative MET values for unknown activities
            met_values = {
                'Run': 8.0, 'Walk': 3.5, 'Ride': 6.0, 'Swim': 6.0,
                'Soccer': 7.0, 'Basketball': 8.0, 'Tennis': 7.0,
                'WeightTraining': 4.0, 'Yoga': 2.5, 'default': 4.0
            }
            
            met = met_values.get(sport, met_values['default'])
            # Assume 70kg weight for estimation
            estimated_calories = int(met * 70 * duration_hours)
            normalized['estimated_calories'] = estimated_calories
        
        # Normalize sport names to standard categories
        if 'sport' in normalized:
            normalized['sport'] = DataSourceAdapter._normalize_sport_name(normalized['sport'])
        
        # Add source metadata
        normalized['data_source'] = source
        normalized['original_data'] = workout
        
        return normalized
    
    @staticmethod
    def _normalize_sport_name(sport: str) -> str:
        """Normalize sport names to standard categories"""
        
        sport_lower = sport.lower()
        
        # Running variations
        if any(word in sport_lower for word in ['run', 'jog', 'sprint']):
            return 'Run'
        
        # Cycling variations
        if any(word in sport_lower for word in ['ride', 'bike', 'cycle', 'spin']):
            return 'Ride'
        
        # Swimming variations
        if any(word in sport_lower for word in ['swim', 'pool', 'open water']):
            return 'Swim'
        
        # Walking variations
        if any(word in sport_lower for word in ['walk', 'hike', 'trek']):
            return 'Walk'
        
        # Team sports
        if any(word in sport_lower for word in ['soccer', 'football', 'futbol']):
            return 'Soccer'
        if any(word in sport_lower for word in ['basketball', 'hoops', 'bball']):
            return 'Basketball'
        if any(word in sport_lower for word in ['tennis', 'racket']):
            return 'Tennis'
        
        # Strength training
        if any(word in sport_lower for word in ['weight', 'strength', 'lift', 'gym']):
            return 'WeightTraining'
        
        # Yoga and flexibility
        if any(word in sport_lower for word in ['yoga', 'pilates', 'stretch']):
            return 'Yoga'
        
        # Return original if no match found
        return sport
    
    @staticmethod
    def extract_athlete_info(workout: Dict[str, Any], source: str) -> Dict[str, Any]:
        """Extract athlete information from workout data"""
        
        athlete_info = {}
        
        if source == 'strava' and 'athlete' in workout:
            athlete_data = workout['athlete']
            if isinstance(athlete_data, dict):
                athlete_info.update({
                    'external_id': athlete_data.get('id'),
                    'name': athlete_data.get('firstname', '') + ' ' + athlete_data.get('lastname', ''),
                    'weight': athlete_data.get('weight'),
                    'height': athlete_data.get('height')
                })
        
        elif source == 'garmin' and 'user' in workout:
            user_data = workout['user']
            if isinstance(user_data, dict):
                athlete_info.update({
                    'external_id': user_data.get('userId'),
                    'name': user_data.get('displayName'),
                    'weight': user_data.get('weight'),
                    'height': user_data.get('height')
                })
        
        elif source == 'apple_health':
            # Apple Health typically doesn't include user profile in workout data
            # User profile is managed separately in Health app
            pass
        
        elif source == 'vesync':
            # VeSync data is typically device-based, not user-based
            pass
        
        return athlete_info
    
    @staticmethod
    def validate_workout_data(workout: Dict[str, Any], source: str) -> Dict[str, Any]:
        """Validate and clean workout data"""
        
        validation_errors = []
        cleaned_workout = workout.copy()
        
        # Required fields
        required_fields = ['start_time', 'duration', 'sport']
        for field in required_fields:
            if field not in cleaned_workout:
                validation_errors.append(f"Missing required field: {field}")
        
        # Validate duration
        if 'duration' in cleaned_workout:
            duration = cleaned_workout['duration']
            if not isinstance(duration, (int, float)) or duration <= 0:
                validation_errors.append(f"Invalid duration: {duration}")
                cleaned_workout['duration'] = 0
        
        # Validate heart rate
        if 'heart_rate_avg' in cleaned_workout:
            hr = cleaned_workout['heart_rate_avg']
            if not isinstance(hr, (int, float)) or hr < 40 or hr > 220:
                validation_errors.append(f"Invalid heart rate: {hr}")
                del cleaned_workout['heart_rate_avg']
        
        # Validate calories
        if 'calories' in cleaned_workout:
            cal = cleaned_workout['calories']
            if not isinstance(cal, (int, float)) or cal < 0 or cal > 5000:
                validation_errors.append(f"Invalid calories: {cal}")
                del cleaned_workout['calories']
        
        # Add validation metadata
        cleaned_workout['validation_errors'] = validation_errors
        cleaned_workout['is_valid'] = len(validation_errors) == 0
        
        if validation_errors:
            logger.warning(f"Workout validation errors for {source}: {validation_errors}")
        
        return cleaned_workout
    
    @staticmethod
    def estimate_missing_data(workout: Dict[str, Any], source: str) -> Dict[str, Any]:
        """Estimate missing data based on available information"""
        
        estimated_workout = workout.copy()
        
        # Estimate missing end_time
        if 'start_time' in workout and 'duration' in workout and 'end_time' not in workout:
            try:
                start = datetime.fromisoformat(workout['start_time'])
                end = start + timedelta(seconds=workout['duration'])
                estimated_workout['end_time'] = end.isoformat()
            except (ValueError, TypeError):
                pass
        
        # Estimate missing distance for running/cycling
        if 'distance' not in workout and 'duration' in workout and 'sport' in workout:
            sport = workout['sport'].lower()
            duration_hours = workout['duration'] / 3600
            
            # Typical speeds (m/s)
            typical_speeds = {
                'run': 2.8,      # ~10 min/mile
                'ride': 8.0,     # ~22 mph
                'walk': 1.4,     # ~3 mph
                'swim': 1.0,     # ~2 mph
                'soccer': 2.0,   # estimated
                'basketball': 1.5,  # estimated
                'tennis': 2.5,   # estimated
            }
            
            speed = typical_speeds.get(sport, 2.0)
            estimated_distance = speed * duration_hours * 3600  # Convert to meters
            estimated_workout['estimated_distance'] = estimated_distance
        
        # Estimate missing heart rate from activity type
        if 'heart_rate_avg' not in workout and 'sport' in workout:
            sport = workout['sport'].lower()
            
            # Typical HR ranges for activities
            hr_ranges = {
                'run': (140, 180),
                'ride': (120, 160),
                'swim': (130, 170),
                'walk': (80, 120),
                'soccer': (140, 180),
                'basketball': (140, 180),
                'tennis': (130, 170),
                'weighttraining': (100, 140),
                'yoga': (60, 100)
            }
            
            if sport in hr_ranges:
                min_hr, max_hr = hr_ranges[sport]
                estimated_hr = (min_hr + max_hr) // 2
                estimated_workout['estimated_heart_rate_avg'] = estimated_hr
        
        return estimated_workout
