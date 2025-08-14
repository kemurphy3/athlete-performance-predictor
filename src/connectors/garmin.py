#!/usr/bin/env python3
"""
Garmin Connect Connector for Multi-Source Fitness Data Platform
Implements the BaseConnector interface for Garmin Connect API integration
"""

import asyncio
import logging
from datetime import date, datetime, timedelta
from typing import List, Dict, Any, Optional
import requests
import hashlib
import time

from .base import BaseConnector, ConnectorError, AuthenticationError, RateLimitError, APIError
from ..core.models import Workout, BiometricReading
# Calorie calculation moved to private repository

logger = logging.getLogger(__name__)

class GarminConnectConnector(BaseConnector):
    """Garmin Connect API connector implementation"""
    
    def __init__(self, source_name: str, config: Dict[str, Any]):
        super().__init__(source_name, config)
        self.base_url = "https://connect.garmin.com"
        self.modern_url = "https://connect.garmin.com/modern"
        self.sso_url = "https://sso.garmin.com/sso"
        
        # OAuth2 credentials
        self.client_id = config.get("client_id")
        self.client_secret = config.get("client_secret")
        self.redirect_uri = config.get("redirect_uri")
        
        # Session management
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
        
        # Calorie calculator initialization removed - proprietary logic
        
        # Garmin-specific rate limiting
        self.min_request_interval = 1.0  # Garmin is more restrictive
        
    async def authenticate(self) -> bool:
        """Authenticate with Garmin Connect using OAuth2"""
        try:
            if not all([self.client_id, self.client_secret, self.redirect_uri]):
                self.logger.error("Missing OAuth2 credentials")
                return False
            
            # Check if we have stored tokens
            access_token = self.config.get("access_token")
            refresh_token = self.config.get("refresh_token")
            
            if access_token and refresh_token:
                # Validate existing token
                if await self._validate_token(access_token):
                    self.authenticated = True
                    return True
                else:
                    # Try to refresh token
                    return await self._refresh_token(refresh_token)
            
            # No valid tokens, need to start OAuth flow
            self.logger.info("No valid tokens, OAuth flow required")
            return False
            
        except Exception as e:
            self.logger.error(f"Authentication error: {e}")
            return False
    
    async def _validate_token(self, access_token: str) -> bool:
        """Validate if the access token is still valid"""
        try:
            headers = {"Authorization": f"Bearer {access_token}"}
            response = self.session.get(f"{self.modern_url}/userprofile-service/userprofile/me", headers=headers)
            return response.status_code == 200
        except Exception as e:
            self.logger.error(f"Token validation error: {e}")
            return False
    
    async def _refresh_token(self, refresh_token: str) -> bool:
        """Refresh the access token using refresh token"""
        try:
            data = {
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
                "client_id": self.client_id,
                "client_secret": self.client_secret
            }
            
            response = self.session.post(f"{self.sso_url}/oauth2/token", data=data)
            
            if response.status_code == 200:
                token_data = response.json()
                self.config["access_token"] = token_data["access_token"]
                self.config["refresh_token"] = token_data.get("refresh_token", refresh_token)
                self.authenticated = True
                self.logger.info("Token refreshed successfully")
                return True
            else:
                self.logger.error(f"Token refresh failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"Token refresh error: {e}")
            return False
    
    async def fetch_workouts(self, start_date: date, end_date: date) -> List[Workout]:
        """Fetch workouts from Garmin Connect"""
        if not self.authenticated:
            if not await self.authenticate():
                return []
        
        try:
            workouts = []
            current_date = start_date
            
            while current_date <= end_date:
                # Garmin uses different endpoints for different data types
                # We'll fetch activities and then get detailed data for each
                
                # Get daily activities
                activities = await self._fetch_daily_activities(current_date)
                
                for activity in activities:
                    workout = await self._transform_activity_to_workout(activity, current_date)
                    if workout:
                        workouts.append(workout)
                
                current_date += timedelta(days=1)
                
                # Respect rate limiting
                await asyncio.sleep(self.min_request_interval)
            
            self.logger.info(f"Fetched {len(workouts)} workouts from Garmin Connect")
            return workouts
            
        except Exception as e:
            self.logger.error(f"Error fetching workouts: {e}")
            return []
    
    async def _fetch_daily_activities(self, target_date: date) -> List[Dict[str, Any]]:
        """Fetch activities for a specific date"""
        try:
            # Garmin endpoint for daily activities
            url = f"{self.modern_url}/activitylist-service/activities/dailies"
            params = {
                "startDate": target_date.strftime("%Y-%m-%d"),
                "endDate": target_date.strftime("%Y-%m-%d")
            }
            
            headers = {"Authorization": f"Bearer {self.config['access_token']}"}
            response = self.session.get(url, params=params, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                return data.get("activities", [])
            else:
                self.logger.warning(f"Failed to fetch activities for {target_date}: {response.status_code}")
                return []
                
        except Exception as e:
            self.logger.error(f"Error fetching daily activities: {e}")
            return []
    
    async def _transform_activity_to_workout(self, activity: Dict[str, Any], date: date) -> Optional[Workout]:
        """Transform Garmin activity data to Workout model"""
        try:
            # Map Garmin activity types to our sport types
            sport_mapping = {
                "running": "running",
                "cycling": "cycling",
                "swimming": "swimming",
                "strength_training": "strength",
                "yoga": "yoga",
                "walking": "walking",
                "hiking": "hiking"
            }
            
            activity_type = activity.get("activityType", "").lower()
            sport = sport_mapping.get(activity_type, "other")
            
            # Calculate calories if not provided
            calories = activity.get("calories", 0)
            if not calories and activity.get("duration"):
                # Calorie calculation functionality moved to private repository
                # For demo purposes, use a simple estimate
                duration_minutes = activity.get("duration", 0) / 1000 / 60  # Convert from milliseconds
                calories = int(duration_minutes * 8)  # ~8 cal/min placeholder
            
            workout = Workout(
                id=f"garmin_{activity.get('activityId', 'unknown')}",
                source="garmin_connect",
                date=date,
                sport=sport,
                duration_minutes=activity.get("duration", 0) / 1000 / 60,  # Convert from milliseconds
                distance_meters=activity.get("distance", 0),
                calories=calories,
                heart_rate_avg=activity.get("averageHR", None),
                heart_rate_max=activity.get("maxHR", None),
                elevation_gain_meters=activity.get("elevationGain", 0),
                raw_data=activity
            )
            
            return workout
            
        except Exception as e:
            self.logger.error(f"Error transforming activity to workout: {e}")
            return None
    
    async def fetch_biometrics(self, start_date: date, end_date: date) -> List[BiometricReading]:
        """Fetch biometric readings from Garmin Connect"""
        if not self.authenticated:
            if not await self.authenticate():
                return []
        
        try:
            biometrics = []
            current_date = start_date
            
            while current_date <= end_date:
                # Fetch daily biometrics
                daily_data = await self._fetch_daily_biometrics(current_date)
                if daily_data:
                    biometrics.append(daily_data)
                
                current_date += timedelta(days=1)
                await asyncio.sleep(self.min_request_interval)
            
            self.logger.info(f"Fetched {len(biometrics)} biometric readings from Garmin Connect")
            return biometrics
            
        except Exception as e:
            self.logger.error(f"Error fetching biometrics: {e}")
            return []
    
    async def _fetch_daily_biometrics(self, target_date: date) -> Optional[BiometricReading]:
        """Fetch biometric data for a specific date"""
        try:
            # Garmin endpoint for daily summary
            url = f"{self.modern_url}/usersummary-service/stats/daily"
            params = {"date": target_date.strftime("%Y-%m-%d")}
            
            headers = {"Authorization": f"Bearer {self.config['access_token']}"}
            response = self.session.get(url, params=params, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                
                # Extract relevant biometric data
                biometric = BiometricReading(
                    id=f"garmin_biometric_{target_date.strftime('%Y%m%d')}",
                    source="garmin_connect",
                    date=target_date,
                    steps=data.get("steps", 0),
                    calories_burned=data.get("calories", 0),
                    heart_rate_avg=data.get("averageHR", None),
                    heart_rate_max=data.get("maxHR", None),
                    sleep_hours=data.get("sleepTime", 0) / 3600 if data.get("sleepTime") else None,
                    weight_kg=data.get("weight", None),
                    body_fat_percent=data.get("bodyFat", None),
                    raw_data=data
                )
                
                return biometric
            else:
                self.logger.warning(f"Failed to fetch biometrics for {target_date}: {response.status_code}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error fetching daily biometrics: {e}")
            return None
    
    def get_supported_metrics(self) -> List[str]:
        """Get list of supported biometric metrics"""
        return [
            "steps", "calories_burned", "heart_rate_avg", "heart_rate_max",
            "sleep_hours", "weight_kg", "body_fat_percent", "distance_meters",
            "elevation_gain_meters"
        ]
    
    def get_supported_sports(self) -> List[str]:
        """Get list of supported sport types"""
        return [
            "running", "cycling", "swimming", "strength", "yoga", "walking",
            "hiking", "other"
        ]
    
    async def get_oauth_url(self) -> str:
        """Generate OAuth2 authorization URL for user to visit"""
        if not all([self.client_id, self.redirect_uri]):
            raise ConnectorError("Missing OAuth2 configuration")
        
        params = {
            "client_id": self.client_id,
            "response_type": "code",
            "redirect_uri": self.redirect_uri,
            "scope": "activity",  # Garmin Connect scopes
            "state": hashlib.md5(str(time.time()).encode()).hexdigest()
        }
        
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        return f"{self.sso_url}/oauth2/authorize?{query_string}"
    
    async def exchange_code_for_tokens(self, authorization_code: str) -> bool:
        """Exchange authorization code for access and refresh tokens"""
        try:
            data = {
                "grant_type": "authorization_code",
                "code": authorization_code,
                "redirect_uri": self.redirect_uri,
                "client_id": self.client_id,
                "client_secret": self.client_secret
            }
            
            response = self.session.post(f"{self.sso_url}/oauth2/token", data=data)
            
            if response.status_code == 200:
                token_data = response.json()
                self.config["access_token"] = token_data["access_token"]
                self.config["refresh_token"] = token_data["refresh_token"]
                self.authenticated = True
                self.logger.info("Successfully obtained tokens from authorization code")
                return True
            else:
                self.logger.error(f"Failed to exchange code for tokens: {response.status_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error exchanging code for tokens: {e}")
            return False
