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
# Calorie calculation moved to private repository

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
        
        # Calorie calculator initialization removed - proprietary logic
        
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
        
        # Use calories from Strava if provided
        raw_calories = activity.get("calories")
        if raw_calories and raw_calories > 0:
            calculated_calories = raw_calories
        else:
            # Calorie calculation functionality moved to private repository
            # For demo purposes, use a simple estimate based on duration
            calculated_calories = int(activity["elapsed_time"] / 60 * 8)  # ~8 cal/min placeholder
        
        return Workout(
            workout_id=str(activity["id"]),
            athlete_id="default",  # Use default athlete for now
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
            training_load=None,
            perceived_exertion=None,
            has_gps=bool(activity.get("start_latlng")),
            route_hash=None,
            gps_data={"start_latlng": activity.get("start_latlng")} if activity.get("start_latlng") else {},
            data_source="strava",
            external_ids={"strava": str(activity["id"])},
            raw_data=activity,
            data_quality_score=0.8,
            ml_features_extracted=False,
            plugin_data={}
        )
    
    async def fetch_biometrics(self, start_date: date, end_date: date) -> List[BiometricReading]:
        """Fetch comprehensive biometric data from Strava"""
        if not self.authenticated:
            if not await self.authenticate():
                return []
        
        try:
            biometrics = []
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            # 1. Get athlete profile (weight, height, etc.)
            profile_response = requests.get(f"{self.base_url}/athlete", headers=headers)
            if profile_response.status_code == 200:
                profile = profile_response.json()
                
                # Add weight if available (this is what you were looking for!)
                if profile.get("weight"):
                    biometrics.append(BiometricReading(
                        reading_id=f"strava_weight_{date.today().strftime('%Y%m%d')}",
                        athlete_id="default",  # Use default athlete for now
                        timestamp=datetime.now(),
                        metric="weight",
                        value=float(profile["weight"]),
                        unit="kg",
                        data_source="strava",
                        raw_data={"profile": profile}
                    ))
                    self.logger.info(f"Found Strava weight: {profile['weight']} kg")
                
                # Add height if available
                if profile.get("height"):
                    biometrics.append(BiometricReading(
                        reading_id=f"strava_height_{date.today().strftime('%Y%m%d')}",
                        athlete_id="default",
                        timestamp=datetime.now(),
                        metric="height",
                        value=float(profile["height"]),
                        unit="cm",
                        data_source="strava",
                        raw_data={"profile": profile}
                    ))
                    self.logger.info(f"Found Strava height: {profile['height']} cm")
                
                # Add other profile metrics
                if profile.get("follower_count"):
                    biometrics.append(BiometricReading(
                        reading_id=f"strava_followers_{date.today().strftime('%Y%m%d')}",
                        athlete_id="default",
                        timestamp=datetime.now(),
                        metric="followers",
                        value=float(profile["follower_count"]),
                        unit="count",
                        data_source="strava",
                        raw_data={"profile": profile}
                    ))
            
            # 2. Get athlete stats (recent totals, all-time totals)
            stats_response = requests.get(f"{self.base_url}/athlete/stats", headers=headers)
            if stats_response.status_code == 200:
                stats = stats_response.json()
                
                # Add recent run totals
                if "recent_run_totals" in stats:
                    recent = stats["recent_run_totals"]
                    if recent.get("count") > 0:
                        biometrics.append(BiometricReading(
                            reading_id=f"strava_recent_runs_{date.today().strftime('%Y%m%d')}",
                            athlete_id="default",
                            timestamp=datetime.now(),
                            metric="recent_run_distance",
                            value=float(recent.get("distance", 0)),
                            unit="meters",
                            data_source="strava",
                            raw_data={"recent_runs": recent}
                        ))
                        
                        # Add recent run calories
                        if recent.get("calories"):
                            biometrics.append(BiometricReading(
                                reading_id=f"strava_recent_runs_calories_{date.today().strftime('%Y%m%d')}",
                                athlete_id="default",
                                timestamp=datetime.now(),
                                metric="recent_run_calories",
                                value=float(recent.get("calories", 0)),
                                unit="calories",
                                data_source="strava",
                                raw_data={"recent_runs": recent}
                            ))
                
                # Add recent ride totals
                if "recent_ride_totals" in stats:
                    recent_rides = stats["recent_ride_totals"]
                    if recent_rides.get("count") > 0:
                        biometrics.append(BiometricReading(
                            reading_id=f"strava_recent_rides_{date.today().strftime('%Y%m%d')}",
                            athlete_id="default",
                            timestamp=datetime.now(),
                            metric="recent_ride_distance",
                            value=float(recent_rides.get("distance", 0)),
                            unit="meters",
                            data_source="strava",
                            raw_data={"recent_rides": recent_rides}
                        ))
                        
                        # Add recent ride calories
                        if recent_rides.get("calories"):
                            biometrics.append(BiometricReading(
                                reading_id=f"strava_recent_rides_calories_{date.today().strftime('%Y%m%d')}",
                                athlete_id="default",
                                timestamp=datetime.now(),
                                metric="recent_ride_calories",
                                value=float(recent_rides.get("calories", 0)),
                                unit="calories",
                                data_source="strava",
                                raw_data={"recent_rides": recent_rides}
                            ))
                
                # Add all-time totals
                if "all_run_totals" in stats:
                    all_runs = stats["all_run_totals"]
                    biometrics.append(BiometricReading(
                        reading_id=f"strava_alltime_runs_{date.today().strftime('%Y%m%d')}",
                        athlete_id="default",
                        timestamp=datetime.now(),
                        metric="alltime_run_distance",
                        value=float(all_runs.get("distance", 0)),
                        unit="meters",
                        data_source="strava",
                        raw_data={"all_time_runs": all_runs}
                    ))
                    
                    if all_runs.get("calories"):
                        biometrics.append(BiometricReading(
                            reading_id=f"strava_alltime_runs_calories_{date.today().strftime('%Y%m%d')}",
                            athlete_id="default",
                            timestamp=datetime.now(),
                            metric="alltime_run_calories",
                            value=float(all_runs.get("calories", 0)),
                            unit="calories",
                            data_source="strava",
                            raw_data={"all_time_runs": all_runs}
                        ))
                
                if "all_ride_totals" in stats:
                    all_rides = stats["all_ride_totals"]
                    biometrics.append(BiometricReading(
                        reading_id=f"strava_alltime_rides_{date.today().strftime('%Y%m%d')}",
                        athlete_id="default",
                        timestamp=datetime.now(),
                        metric="alltime_ride_distance",
                        value=float(all_rides.get("distance", 0)),
                        unit="meters",
                        data_source="strava",
                        raw_data={"all_time_rides": all_rides}
                    ))
                    
                    if all_rides.get("calories"):
                        biometrics.append(BiometricReading(
                            reading_id=f"strava_alltime_rides_calories_{date.today().strftime('%Y%m%d')}",
                            athlete_id="default",
                            timestamp=datetime.now(),
                            metric="alltime_ride_calories",
                            value=float(all_rides.get("calories", 0)),
                            unit="calories",
                            data_source="strava",
                            raw_data={"all_time_rides": all_rides}
                        ))
            
            # 3. Get athlete zones (heart rate zones)
            zones_response = requests.get(f"{self.base_url}/athlete/zones", headers=headers)
            if zones_response.status_code == 200:
                zones = zones_response.json()
                if zones:
                    # Add heart rate zones as biometric data
                    for zone_type, zone_data in zones.items():
                        if zone_data and len(zone_data) > 0:
                            # Store zones as a special metric type
                            biometrics.append(BiometricReading(
                                reading_id=f"strava_zones_{zone_type}_{date.today().strftime('%Y%m%d')}",
                                athlete_id="default",
                                timestamp=datetime.now(),
                                metric=f"heart_rate_zones_{zone_type}",
                                value=float(len(zone_data)),  # Number of zones
                                unit="zones",
                                data_source="strava",
                                raw_data={"zones": {zone_type: zone_data}}
                            ))
            
            self.logger.info(f"Fetched {len(biometrics)} comprehensive biometric readings from Strava")
            return biometrics
            
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
        return [
            "weight", "height", "followers",
            "recent_run_distance", "recent_run_calories",
            "recent_ride_distance", "recent_ride_calories",
            "alltime_run_distance", "alltime_run_calories",
            "alltime_ride_distance", "alltime_ride_calories",
            "heart_rate_zones"
        ]
    
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
