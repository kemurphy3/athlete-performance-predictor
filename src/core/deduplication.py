#!/usr/bin/env python3
"""
Intelligent Deduplication Engine for Multi-Source Fitness Data
Handles overlapping workout and biometric records with source precedence
"""

import hashlib
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass
import logging
from .models import Workout, BiometricReading

logger = logging.getLogger(__name__)

@dataclass
class DeduplicationMatch:
    """Result of deduplication matching"""
    primary_workout: Workout
    duplicate_workouts: List[Workout]
    confidence: float
    match_reason: str
    merged_data: Dict[str, Any]

class DeduplicationEngine:
    """Three-tier deduplication engine with source precedence"""
    
    # Source precedence (lower index = higher priority)
    PRECEDENCE = ["garmin", "strava", "fitbit", "oura", "whoop", "withings", "healthkit", "health_connect"]
    
    # Matching thresholds
    TEMPORAL_THRESHOLD_MINUTES = 5  # Start time within 5 minutes
    DURATION_THRESHOLD_PERCENT = 10  # Duration within 10%
    GPS_SIMILARITY_THRESHOLD = 0.8   # GPS route similarity threshold
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.info("Initialized deduplication engine")
    
    def deduplicate_workouts(self, workouts: List[Workout]) -> List[Workout]:
        """Deduplicate workouts using three-tier matching"""
        if not workouts:
            return []
        
        self.logger.info(f"Starting deduplication of {len(workouts)} workouts")
        
        # Step 1: Group by external ID matches
        id_groups = self._group_by_external_ids(workouts)
        
        # Step 2: Find temporal matches
        temporal_groups = self._group_by_temporal_similarity(workouts)
        
        # Step 3: Find GPS route matches
        gps_groups = self._group_by_gps_similarity(workouts)
        
        # Step 4: Merge all groups
        merged_workouts = self._merge_workout_groups(workouts, id_groups, temporal_groups, gps_groups)
        
        self.logger.info(f"Deduplication complete: {len(workouts)} -> {len(merged_workouts)} workouts")
        return merged_workouts
    
    def _group_by_external_ids(self, workouts: List[Workout]) -> Dict[str, List[Workout]]:
        """Group workouts by matching external IDs"""
        groups = {}
        
        for workout in workouts:
            for source, ext_id in workout.external_ids.items():
                if ext_id:
                    key = f"{source}_{ext_id}"
                    if key not in groups:
                        groups[key] = []
                    groups[key].append(workout)
        
        # Filter groups with multiple workouts
        return {k: v for k, v in groups.items() if len(v) > 1}
    
    def _group_by_temporal_similarity(self, workouts: List[Workout]) -> List[List[Workout]]:
        """Group workouts by temporal similarity"""
        groups = []
        processed = set()
        
        for i, workout1 in enumerate(workouts):
            if i in processed:
                continue
            
            group = [workout1]
            processed.add(i)
            
            for j, workout2 in enumerate(workouts[i+1:], i+1):
                if j in processed:
                    continue
                
                if self._are_temporally_similar(workout1, workout2):
                    group.append(workout2)
                    processed.add(j)
            
            if len(group) > 1:
                groups.append(group)
        
        return groups
    
    def _are_temporally_similar(self, workout1: Workout, workout2: Workout) -> bool:
        """Check if two workouts are temporally similar"""
        # Start time within threshold
        start_diff = abs((workout1.start_time - workout2.start_time).total_seconds() / 60)
        if start_diff > self.TEMPORAL_THRESHOLD_MINUTES:
            return False
        
        # Duration within threshold
        duration_diff = abs(workout1.duration - workout2.duration) / max(workout1.duration, workout2.duration) * 100
        if duration_diff > self.DURATION_THRESHOLD_PERCENT:
            return False
        
        # Same sport category
        if workout1.sport_category != workout2.sport_category:
            return False
        
        return True
    
    def _group_by_gps_similarity(self, workouts: List[Workout]) -> List[List[Workout]]:
        """Group workouts by GPS route similarity"""
        groups = []
        processed = set()
        
        gps_workouts = [w for w in workouts if w.has_gps and w.route_hash]
        
        for i, workout1 in enumerate(gps_workouts):
            if i in processed:
                continue
            
            group = [workout1]
            processed.add(i)
            
            for j, workout2 in enumerate(gps_workouts[i+1:], i+1):
                if j in processed:
                    continue
                
                if self._are_gps_similar(workout1, workout2):
                    group.append(workout2)
                    processed.add(j)
            
            if len(group) > 1:
                groups.append(group)
        
        return groups
    
    def _are_gps_similar(self, workout1: Workout, workout2: Workout) -> bool:
        """Check if two workouts have similar GPS routes"""
        if not (workout1.has_gps and workout2.has_gps):
            return False
        
        # If both have route hashes, compare them
        if workout1.route_hash and workout2.route_hash:
            return workout1.route_hash == workout2.route_hash
        
        # If GPS data available, calculate similarity
        if workout1.gps_data and workout2.gps_data:
            similarity = self._calculate_gps_similarity(workout1.gps_data, workout2.gps_data)
            return similarity >= self.GPS_SIMILARITY_THRESHOLD
        
        return False
    
    def _calculate_gps_similarity(self, gps1: Dict[str, Any], gps2: Dict[str, Any]) -> float:
        """Calculate GPS route similarity (simplified implementation)"""
        try:
            # Extract coordinate arrays
            coords1 = gps1.get('coordinates', [])
            coords2 = gps2.get('coordinates', [])
            
            if not coords1 or not coords2:
                return 0.0
            
            # Simple coordinate matching (in practice, use more sophisticated algorithms)
            matches = 0
            total = min(len(coords1), len(coords2))
            
            for i in range(total):
                if i < len(coords1) and i < len(coords2):
                    coord1 = coords1[i]
                    coord2 = coords2[i]
                    
                    # Check if coordinates are within 10 meters
                    if self._coordinates_within_distance(coord1, coord2, 10):
                        matches += 1
            
            return matches / total if total > 0 else 0.0
            
        except Exception as e:
            self.logger.warning(f"Error calculating GPS similarity: {e}")
            return 0.0
    
    def _coordinates_within_distance(self, coord1: List[float], coord2: List[float], max_distance_meters: float) -> bool:
        """Check if two coordinates are within specified distance"""
        try:
            from math import radians, cos, sin, asin, sqrt
            
            # Haversine formula for distance calculation
            lat1, lon1 = coord1[1], coord1[0]  # Assuming [lon, lat] format
            lat2, lon2 = coord2[1], coord2[0]
            
            # Convert to radians
            lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
            
            # Haversine formula
            dlat = lat2 - lat1
            dlon = lon2 - lon1
            a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
            c = 2 * asin(sqrt(a))
            r = 6371000  # Earth's radius in meters
            
            distance = c * r
            return distance <= max_distance_meters
            
        except Exception as e:
            self.logger.warning(f"Error calculating coordinate distance: {e}")
            return False
    
    def _merge_workout_groups(self, all_workouts: List[Workout], 
                             id_groups: Dict[str, List[Workout]],
                             temporal_groups: List[List[Workout]],
                             gps_groups: List[List[Workout]]) -> List[Workout]:
        """Merge all workout groups into final deduplicated list"""
        # Start with all workouts
        merged_workouts = all_workouts.copy()
        
        # Process ID groups first (highest confidence)
        for group in id_groups.values():
            merged_workout = self._merge_workout_group(group)
            if merged_workout:
                # Remove duplicates, add merged version
                for workout in group:
                    if workout in merged_workouts:
                        merged_workouts.remove(workout)
                merged_workouts.append(merged_workout)
        
        # Process temporal groups
        for group in temporal_groups:
            if not any(w in merged_workouts for w in group):
                continue  # Already processed in ID groups
            
            merged_workout = self._merge_workout_group(group)
            if merged_workout:
                # Remove duplicates, add merged version
                for workout in group:
                    if workout in merged_workouts:
                        merged_workouts.remove(workout)
                merged_workouts.append(merged_workout)
        
        # Process GPS groups
        for group in gps_groups:
            if not any(w in merged_workouts for w in group):
                continue  # Already processed
            
            merged_workout = self._merge_workout_group(group)
            if merged_workout:
                # Remove duplicates, add merged version
                for workout in group:
                    if workout in merged_workouts:
                        merged_workouts.remove(workout)
                merged_workouts.append(merged_workout)
        
        return merged_workouts
    
    def _merge_workout_group(self, workouts: List[Workout]) -> Optional[Workout]:
        """Merge a group of duplicate workouts"""
        if not workouts:
            return None
        
        if len(workouts) == 1:
            return workouts[0]
        
        # Sort by precedence
        sorted_workouts = sorted(workouts, key=lambda w: self._get_source_precedence(w.source))
        primary = sorted_workouts[0]
        
        # Merge data from all workouts
        merged_data = self._merge_workout_data(sorted_workouts)
        
        # Create merged workout
        merged_workout = Workout(
            workout_id=primary.workout_id,
            start_time=primary.start_time,
            end_time=primary.end_time,
            duration=primary.duration,
            sport=primary.sport,
            sport_category=primary.sport_category,
            distance=merged_data.get('distance'),
            calories=merged_data.get('calories'),
            heart_rate_avg=merged_data.get('heart_rate_avg'),
            heart_rate_max=merged_data.get('heart_rate_max'),
            elevation_gain=merged_data.get('elevation_gain'),
            power_avg=merged_data.get('power_avg'),
            cadence_avg=merged_data.get('cadence_avg'),
            training_load=merged_data.get('training_load'),
            perceived_exertion=merged_data.get('perceived_exertion'),
            has_gps=merged_data.get('has_gps', False),
            route_hash=merged_data.get('route_hash'),
            gps_data=merged_data.get('gps_data'),
            source=primary.source,
            external_ids=merged_data.get('external_ids', {}),
            raw_data=merged_data.get('raw_data'),
            data_quality_score=merged_data.get('data_quality_score', 1.0),
            ml_features_extracted=False,  # Reset for re-processing
            plugin_data=merged_data.get('plugin_data', {})
        )
        
        self.logger.info(f"Merged {len(workouts)} workouts into {merged_workout.workout_id}")
        return merged_workout
    
    def _merge_workout_data(self, workouts: List[Workout]) -> Dict[str, Any]:
        """Merge data from multiple workouts"""
        merged = {
            'external_ids': {},
            'raw_data': {},
            'plugin_data': {},
            'has_gps': False,
            'route_hash': None,
            'gps_data': None
        }
        
        # Collect all external IDs
        for workout in workouts:
            merged['external_ids'].update(workout.external_ids)
            if workout.raw_data:
                merged['raw_data'].update(workout.raw_data)
            if workout.plugin_data:
                merged['plugin_data'].update(workout.plugin_data)
        
        # Merge numeric fields (take best available)
        numeric_fields = ['distance', 'calories', 'heart_rate_avg', 'heart_rate_max', 
                         'elevation_gain', 'power_avg', 'cadence_avg', 'training_load', 'perceived_exertion']
        
        for field in numeric_fields:
            values = [getattr(w, field) for w in workouts if getattr(w, field) is not None]
            if values:
                # For most fields, take the highest value (most complete)
                if field in ['distance', 'calories', 'elevation_gain', 'power_avg', 'cadence_avg', 'training_load']:
                    merged[field] = max(values)
                # For heart rate, take the highest max and average
                elif field in ['heart_rate_max']:
                    merged[field] = max(values)
                elif field in ['heart_rate_avg']:
                    merged[field] = sum(values) / len(values)  # Average
                else:
                    merged[field] = values[0]  # Take first available
        
        # GPS data - take from highest precedence source
        for workout in workouts:
            if workout.has_gps:
                merged['has_gps'] = True
                merged['route_hash'] = workout.route_hash
                merged['gps_data'] = workout.gps_data
                break
        
        # Calculate overall data quality score
        quality_scores = [w.data_quality_score for w in workouts]
        merged['data_quality_score'] = max(quality_scores) if quality_scores else 1.0
        
        return merged
    
    def _get_source_precedence(self, source: str) -> int:
        """Get precedence index for a source (lower = higher priority)"""
        try:
            return self.PRECEDENCE.index(source)
        except ValueError:
            return len(self.PRECEDENCE)  # Unknown sources get lowest priority
    
    def deduplicate_biometrics(self, readings: List[BiometricReading]) -> List[BiometricReading]:
        """Deduplicate biometric readings"""
        if not readings:
            return []
        
        self.logger.info(f"Starting biometric deduplication of {len(readings)} readings")
        
        # Group by date, metric type, and source
        grouped = {}
        for reading in readings:
            key = (reading.date, reading.metric_type, reading.source)
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(reading)
        
        # Merge duplicates within each group
        deduplicated = []
        for key, group in grouped.items():
            if len(group) == 1:
                deduplicated.append(group[0])
            else:
                # Merge multiple readings for same metric on same day from same source
                merged = self._merge_biometric_group(group)
                deduplicated.append(merged)
        
        self.logger.info(f"Biometric deduplication complete: {len(readings)} -> {len(deduplicated)} readings")
        return deduplicated
    
    def _merge_biometric_group(self, readings: List[BiometricReading]) -> BiometricReading:
        """Merge a group of duplicate biometric readings"""
        if len(readings) == 1:
            return readings[0]
        
        # Sort by confidence (highest first)
        sorted_readings = sorted(readings, key=lambda r: r.confidence, reverse=True)
        primary = sorted_readings[0]
        
        # Calculate weighted average of values
        total_weight = sum(r.confidence for r in readings)
        weighted_value = sum(r.value * r.confidence for r in readings) / total_weight
        
        # Create merged reading
        merged = BiometricReading(
            date=primary.date,
            metric_type=primary.metric_type,
            value=weighted_value,
            unit=primary.unit,
            source=primary.source,
            confidence=min(1.0, total_weight / len(readings)),  # Average confidence
            external_id=primary.external_id
        )
        
        return merged
    
    def get_deduplication_stats(self, original_count: int, final_count: int) -> Dict[str, Any]:
        """Get statistics about the deduplication process"""
        duplicates_removed = original_count - final_count
        reduction_percent = (duplicates_removed / original_count * 100) if original_count > 0 else 0
        
        return {
            'original_count': original_count,
            'final_count': final_count,
            'duplicates_removed': duplicates_removed,
            'reduction_percent': reduction_percent,
            'efficiency': final_count / original_count if original_count > 0 else 1.0
        }
