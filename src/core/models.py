#!/usr/bin/env python3
"""
Minimal Data Models for Multi-Source Fitness Data Platform
"""

from datetime import datetime, date
from typing import Dict, List, Optional, Any, Literal
from pydantic import BaseModel, Field

class Workout(BaseModel):
    """Unified workout model for multi-source fitness data"""
    
    workout_id: str = Field(..., description="Deterministic hash for deduplication")
    start_time: datetime = Field(..., description="Workout start time in UTC")
    end_time: datetime = Field(..., description="Workout end time in UTC")
    duration: int = Field(..., description="Duration in seconds")
    sport: str = Field(..., description="Raw sport name from source")
    sport_category: str = Field(..., description="Categorized sport type")
    distance: Optional[float] = Field(None, description="Distance in meters")
    calories: Optional[int] = Field(None, description="Calories burned")
    heart_rate_avg: Optional[float] = Field(None, description="Average heart rate")
    heart_rate_max: Optional[int] = Field(None, description="Maximum heart rate")
    elevation_gain: Optional[float] = Field(None, description="Elevation gain in meters")
    power_avg: Optional[float] = Field(None, description="Average power in watts")
    cadence_avg: Optional[float] = Field(None, description="Average cadence")
    training_load: Optional[float] = Field(None, description="Training load score")
    perceived_exertion: Optional[int] = Field(None, description="RPE 1-10 scale")
    has_gps: bool = Field(False, description="Whether workout has GPS data")
    route_hash: Optional[str] = Field(None, description="Hash of simplified GPS route")
    gps_data: Optional[Dict[str, Any]] = Field(None, description="Raw GPS data for plugins")
    data_source: str = Field(..., description="Data source")
    external_ids: Dict[str, str] = Field(default_factory=dict, description="External IDs from sources")
    raw_data: Optional[Dict[str, Any]] = Field(None, description="Source-specific raw data")
    data_quality_score: float = Field(1.0, description="Data completeness score 0-1")
    ml_features_extracted: bool = Field(False, description="Whether ML features have been extracted")
    plugin_data: Dict[str, Any] = Field(default_factory=dict, description="Plugin analysis results")

class BiometricReading(BaseModel):
    """Unified biometric reading model"""
    
    date_value: date = Field(..., description="Date of the reading")
    metric_type: str = Field(..., description="Type of biometric measurement")
    value: float = Field(..., description="Numeric value of the measurement")
    unit: str = Field(..., description="Unit of measurement")
    data_source: str = Field(..., description="Data source")
    confidence: float = Field(1.0, description="Confidence in the measurement 0-1")
    external_id: Optional[str] = Field(None, description="External ID from source")

class SyncStatus(BaseModel):
    """Status of data synchronization for each source"""
    
    data_source: str = Field(..., description="Data source name")
    last_sync: Optional[datetime] = Field(None, description="Last successful sync time")
    status: str = Field("pending", description="Current sync status")
    error_message: Optional[str] = Field(None, description="Last error message if any")
    sync_count: int = Field(0, description="Number of successful syncs")
    last_error: Optional[datetime] = Field(None, description="Last error occurrence")

class DataSource(BaseModel):
    """Configuration for a data source"""
    
    name: str = Field(..., description="Source name")
    enabled: bool = Field(True, description="Whether source is enabled")
    priority: int = Field(0, description="Priority for deduplication (lower = higher priority)")
    sync_interval_hours: int = Field(24, description="Sync interval in hours")
    last_sync: Optional[datetime] = Field(None, description="Last sync time")
    auth_token: Optional[str] = Field(None, description="Encrypted authentication token")
    refresh_token: Optional[str] = Field(None, description="Encrypted refresh token")
    expires_at: Optional[datetime] = Field(None, description="Token expiration time")

class WorkoutSummary(BaseModel):
    """Summary statistics for workouts"""
    
    total_workouts: int = Field(0, description="Total number of workouts")
    total_duration: int = Field(0, description="Total duration in seconds")
    total_distance: float = Field(0.0, description="Total distance in meters")
    total_calories: int = Field(0, description="Total calories burned")
    sport_breakdown: Dict[str, int] = Field(default_factory=dict, description="Workouts by sport")
    category_breakdown: Dict[str, int] = Field(default_factory=dict, description="Workouts by category")
    source_breakdown: Dict[str, int] = Field(default_factory=dict, description="Workouts by source")
    weekly_workouts: Dict[str, int] = Field(default_factory=dict, description="Workouts by week")
    monthly_workouts: Dict[str, int] = Field(default_factory=dict, description="Workouts by month")

class BiometricSummary(BaseModel):
    """Summary statistics for biometric readings"""
    
    total_readings: int = Field(0, description="Total number of readings")
    metrics_by_type: Dict[str, int] = Field(default_factory=dict, description="Readings by metric type")
    sources_by_type: Dict[str, Dict[str, int]] = Field(default_factory=dict, description="Sources by metric type")
    daily_averages: Dict[str, Dict[str, float]] = Field(default_factory=dict, description="Daily averages by metric")
    weekly_trends: Dict[str, Dict[str, float]] = Field(default_factory=dict, description="Weekly trends by metric")
