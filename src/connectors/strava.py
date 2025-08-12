#!/usr/bin/env python3
"""
Strava Connector for Multi-Source Fitness Data Platform
Implements the BaseConnector interface for Strava API integration
"""

import asyncio
import logging
from datetime import date, datetime, timedelta
from typing import List, Dict, Any, Optional
import requests

from .base import BaseConnector, ConnectorError, AuthenticationError, RateLimitError, APIError
from ..core.models import Workout, BiometricReading
from ..core.calorie_calculator import CalorieCalculator

logger = logging.getLogger(__name__)

class StravaConnector(BaseConnector):
    """Strava API connector implementation"""
    
    def __init__(self, source_name: str, config: Dict[str, Any]):
        super().__init__(source_name, config)
        self.base_url = "https://www.strava.com/api/v3"
        self.access_token = config.get("access_token")
        self.refresh_token = config.get("refresh_token")
        self.client_id = config.get("client_id")
        self.client_secret = config.get("client_secret")
        
        # Initialize calorie calculator
        self.calorie_calculator = CalorieCalculator()
        
    async def authenticate(self) -> bool:
        """Authenticate with Strava using stored tokens"""
        try:
            # If we have a refresh token but no access token, try to refresh first
            if not self.access_token and self.refresh_token and self.client_id and self.client_secret:
                self.logger.info("No access token, attempting to refresh from refresh token")
                return await self._refresh_token()
            
            # If we have an access token, test it
            if self.access_token:
                headers = {"Authorization": f"Bearer {self.access_token}"}
                response = requests.get(f"{self.base_url}/athlete", headers=headers)
                
                if response.status_code == 200:
                    self.authenticated = True
                    self.logger.info("Strava authentication successful")
                    return True
                elif response.status_code == 401:
                    # Token expired, try to refresh
                    if self.refresh_token and self.client_id and self.client_secret:
                        return await self._refresh_token()
                    else:
                        self.logger.error("Token expired and no refresh credentials")
                        return False
                else:
                    self.logger.error(f"Authentication failed: {response.status_code}")
                    return False
            else:
                self.logger.warning("No access token or refresh token configured")
                return False
                
        except Exception as e:
            self.logger.error(f"Authentication error: {e}")
            return False
    
    async def _refresh_token(self) -> bool:
        """Refresh the access token"""
        try:
            data = {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "grant_type": "refresh_token",
                "refresh_token": self.refresh_token
            }
            
            response = requests.post("https://www.strava.com/oauth/token", data=data)
            
            if response.status_code == 200:
                token_data = response.json()
                self.logger.info(f"Token refresh response: {token_data}")
                self.access_token = token_data["access_token"]
                self.refresh_token = token_data.get("refresh_token", self.refresh_token)
                self.authenticated = True
                self.logger.info(f"Token refreshed successfully. New token: {self.access_token[:10]}...")
                return True
            else:
                self.logger.error(f"Token refresh failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"Token refresh error: {e}")
            return False
    
    async def fetch_workouts(self, start_date: date, end_date: date) -> List[Workout]:
        """Fetch workouts from Strava"""
        if not self.authenticated:
            if not await self.authenticate():
                return []
        
        try:
            # Convert dates to Unix timestamps
            start_timestamp = int(datetime.combine(start_date, datetime.min.time()).timestamp())
            end_timestamp = int(datetime.combine(end_date, datetime.max.time()).timestamp())
            
            self.logger.info(f"Using access token: {self.access_token[:10]}... for activities request")
            headers = {"Authorization": f"Bearer {self.access_token}"}
            params = {
                "after": start_timestamp,
                "before": end_timestamp,
                "per_page": 200
            }
            
            self.logger.info(f"Making request to {self.base_url}/athlete/activities with params: {params}")
            response = requests.get(f"{self.base_url}/athlete/activities", headers=headers, params=params)
            
            self.logger.info(f"Activities response status: {response.status_code}")
            if response.status_code != 200:
                self.logger.error(f"Activities response headers: {dict(response.headers)}")
                self.logger.error(f"Activities response body: {response.text[:200]}")
            
            if response.status_code == 200:
                activities = response.json()
                workouts = []
                
                for activity in activities:
                    try:
                        workout = self._convert_activity_to_workout(activity)
                        workouts.append(workout)
                    except Exception as e:
                        self.logger.warning(f"Failed to convert activity {activity.get('id')}: {e}")
                        continue
                
                self.logger.info(f"Fetched {len(workouts)} workouts from Strava")
                return workouts
            else:
                self.logger.error(f"Failed to fetch activities: {response.status_code}")
                return []
                
        except Exception as e:
            self.logger.error(f"Error fetching workouts: {e}")
            return []
    
    def _convert_activity_to_workout(self, activity: Dict[str, Any]) -> Workout:
        """Convert Strava activity to Workout model"""
        start_time = datetime.fromisoformat(activity["start_date"].replace("Z", "+00:00"))
        end_time = start_time + timedelta(seconds=activity["elapsed_time"])
        
        # Determine sport category
        sport_type = activity.get("type", "").lower()
        if sport_type in ["run", "walk", "hike"]:
            sport_category = "endurance"
        elif sport_type in ["weighttraining", "strengthtraining"]:
            sport_category = "strength"
        elif sport_type in ["soccer", "basketball", "tennis"]:
            sport_category = "ball_sport"
        else:
            sport_category = "other"
        
        # Calculate calories if not provided by Strava
        raw_calories = activity.get("calories")
        if raw_calories and raw_calories > 0:
            calculated_calories = raw_calories
        else:
            # Use calorie calculator to estimate calories
            calculated_calories = self.calorie_calculator.calculate_calories(activity)
        
        return Workout(
            workout_id=str(activity["id"]),
            start_time=start_time,
            end_time=end_time,
            duration=activity["elapsed_time"],
            sport=activity.get("type", "Unknown"),
            sport_category=sport_category,
            distance=activity.get("distance"),
            calories=calculated_calories,
            heart_rate_avg=activity.get("average_heartrate"),
            heart_rate_max=activity.get("max_heartrate"),
            elevation_gain=activity.get("total_elevation_gain"),
            power_avg=activity.get("average_watts"),
            cadence_avg=activity.get("average_cadence"),
            training_load=activity.get("training_load"),
            perceived_exertion=activity.get("perceived_exertion"),
            has_gps=bool(activity.get("map")),
            route_hash=activity.get("map", {}).get("id"),
            gps_data=activity.get("map"),
            data_source="strava",
            external_ids={"strava": str(activity["id"])},
            raw_data=activity,
            data_quality_score=0.8  # Strava data is generally high quality
        )
    
    async def fetch_biometrics(self, start_date: date, end_date: date) -> List[BiometricReading]:
        """Fetch biometric data from Strava (limited availability)"""
        # Strava doesn't provide many biometrics, but we can get some basic stats
        if not self.authenticated:
            if not await self.authenticate():
                return []
        
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            response = requests.get(f"{self.base_url}/athlete/stats", headers=headers)
            
            if response.status_code == 200:
                stats = response.json()
                biometrics = []
                
                # Add basic stats as biometric readings
                if "recent_run_totals" in stats:
                    recent = stats["recent_run_totals"]
                    if recent.get("count") > 0:
                        biometrics.append(BiometricReading(
                            date_value=date.today(),
                            metric_type="steps",
                            value=float(recent.get("distance", 0)),
                            unit="meters",
                            data_source="strava",
                            confidence=0.7
                        ))
                
                self.logger.info(f"Fetched {len(biometrics)} biometric readings from Strava")
                return biometrics
            else:
                self.logger.error(f"Failed to fetch stats: {response.status_code}")
                return []
                
        except Exception as e:
            self.logger.error(f"Error fetching biometrics: {e}")
            return []
    
    async def sync_data(self, start_date: date, end_date: date) -> Dict[str, Any]:
        """Sync data from Strava for the specified date range"""
        try:
            self.logger.info(f"Starting sync for strava from {start_date} to {end_date}")
            
            # Fetch workouts and biometrics
            workouts = await self.fetch_workouts(start_date, end_date)
            biometrics = await self.fetch_biometrics(start_date, end_date)
            
            # Return in the format expected by the orchestrator
            return {
                'source': 'strava',
                'workouts': workouts,
                'biometrics': biometrics,
                'sync_time': datetime.now().isoformat(),
                'success': True
            }
            
        except Exception as e:
            self.logger.error(f"Sync failed for strava: {e}")
            return {
                'source': 'strava',
                'workouts': [],
                'biometrics': [],
                'sync_time': datetime.now().isoformat(),
                'success': False,
                'error': str(e)
            }
    
    def get_supported_metrics(self) -> List[str]:
        """Get list of supported biometric metrics"""
        return ["steps", "distance"]
    
    def get_supported_sports(self) -> List[str]:
        """Get list of supported sport types"""
        return [
            "Run", "Walk", "Hike", "Ride", "Swim", "WeightTraining", 
            "Yoga", "CrossFit", "Soccer", "Basketball", "Tennis"
        ]
    
    def get_required_config_fields(self) -> List[str]:
        """Get list of required configuration fields"""
        return ["client_id", "client_secret"]
    
    def get_connector_description(self) -> str:
        """Get human-readable description of this connector"""
        return "Strava API connector for fitness activities and athlete data"
