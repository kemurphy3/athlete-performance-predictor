#!/usr/bin/env python3
"""
VeSync Connector for Multi-Source Fitness Data Platform
Provides integration with VeSync smart devices for body composition and environmental data
"""

import asyncio
import logging
import os
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Any, Tuple
import json

from .base import BaseConnector, ConnectorError, AuthenticationError, RateLimitError, APIError
from ..core.models import Workout, BiometricReading

logger = logging.getLogger(__name__)

class VeSyncConnector(BaseConnector):
    """VeSync smart device connector for body composition and environmental data"""
    
    def __init__(self, source_name: str, config: Dict[str, Any]):
        """Initialize VeSync connector"""
        super().__init__(source_name, config)
        
        # VeSync credentials
        self.username = config.get('username') or os.getenv('VESYNC_USERNAME')
        self.password = config.get('password') or os.getenv('VESYNC_PASSWORD')
        self.timezone = config.get('timezone') or os.getenv('VESYNC_TIMEZONE', 'America/Denver')
        
        # Initialize VeSync client
        self.vesync = None
        self.devices = {}
        
    async def authenticate(self) -> bool:
        """Authenticate with VeSync API"""
        try:
            # Import pyvesync
            try:
                from pyvesync import VeSync
            except ImportError:
                raise ConnectorError("pyvesync library not installed. Install with: pip install pyvesync")
            
            # Create VeSync instance and login
            self.vesync = VeSync(self.username, self.password, self.timezone)
            self.vesync.login()
            
            # Test connection by getting devices
            self.devices = await self._get_devices()
            
            self.authenticated = True
            logger.info(f"Successfully authenticated with VeSync. Found {len(self.devices)} devices")
            return True
            
        except Exception as e:
            logger.error(f"VeSync authentication failed: {e}")
            raise AuthenticationError(f"VeSync authentication failed: {e}")
    
    async def _get_devices(self) -> Dict[str, Any]:
        """Get all connected VeSync devices"""
        try:
            if not self.vesync:
                logger.warning("VeSync client not initialized")
                return {}
            
            devices = {}
            # Check if devices attribute exists and is iterable
            if hasattr(self.vesync, 'devices') and self.vesync.devices is not None:
                for device in self.vesync.devices:
                    try:
                        device_info = {
                            'device_id': getattr(device, 'device_id', 'unknown'),
                            'device_name': getattr(device, 'device_name', 'Unknown Device'),
                            'device_type': getattr(device, 'device_type', 'unknown'),
                            'model': getattr(device, 'model', 'unknown'),
                            'connection_status': getattr(device, 'connection_status', 'unknown'),
                            'is_on': getattr(device, 'is_on', None) if hasattr(device, 'is_on') else None
                        }
                        devices[device_info['device_id']] = device_info
                        logger.info(f"Found VeSync device: {device_info['device_name']} ({device_info['device_type']})")
                    except Exception as e:
                        logger.warning(f"Error processing device: {e}")
                        continue
            else:
                logger.warning("No devices found or devices attribute is None")
            
            return devices
            
        except Exception as e:
            logger.error(f"Error getting VeSync devices: {e}")
            return {}
    
    async def fetch_workouts(self, start_date: date, end_date: date) -> List[Workout]:
        """Fetch workout data from VeSync (if any)"""
        # VeSync doesn't provide workout data, but we return empty list for consistency
        return []
    
    async def fetch_biometrics(self, start_date: date, end_date: date) -> List[BiometricReading]:
        """Fetch biometric data from VeSync devices"""
        try:
            if not self.vesync:
                raise ConnectorError("Not authenticated with VeSync")
            
            biometrics = []
            
            # Check if we have any devices
            if not self.devices:
                logger.info("No VeSync devices found, returning empty biometric list")
                return []
            
            # Get data from smart scales
            scales = [d for d in self.devices.values() if 'scale' in d.get('device_type', '').lower()]
            
            for scale in scales:
                logger.info(f"Collecting data from scale: {scale.get('device_name', 'Unknown Scale')}")
                
                try:
                    # For now, create sample data structure
                    # In production, you'd get real data from the scale
                    sample_biometric = BiometricReading(
                        date_value=datetime.now().date(),
                        metric_type='body_composition',
                        value=0.0,  # Would be populated with real data
                        unit='kg',
                        data_source=self.source_name,
                        confidence=1.0,
                        external_id=scale.get('device_id', 'unknown')
                    )
                    biometrics.append(sample_biometric)
                    
                except Exception as e:
                    logger.warning(f"Failed to get data from scale {scale.get('device_name', 'Unknown')}: {e}")
            
            # Get environmental data from air purifiers/humidifiers
            env_devices = [d for d in self.devices.values() if 'air' in d.get('device_type', '').lower() or 'humidifier' in d.get('device_type', '').lower()]
            
            for device in env_devices:
                try:
                    env_data = BiometricReading(
                        date_value=datetime.now().date(),
                        metric_type='environmental',
                        value=0.0,  # Would be populated with real data
                        unit='ppm',
                        data_source=self.source_name,
                        confidence=1.0,
                        external_id=device.get('device_id', 'unknown')
                    )
                    biometrics.append(env_data)
                    
                except Exception as e:
                    logger.warning(f"Failed to get environmental data from {device.get('device_name', 'Unknown')}: {e}")
            
            logger.info(f"Collected {len(biometrics)} biometric readings from VeSync")
            return biometrics
            
        except Exception as e:
            logger.error(f"Error collecting VeSync biometrics: {e}")
            raise ConnectorError(f"Failed to collect VeSync biometrics: {e}")
    
    def _process_scale_data(self, scale_data: Any, device_name: str) -> Optional[BiometricReading]:
        """Process raw scale data into standardized format"""
        try:
            # This would process the actual scale data
            # For now, return None as we're using sample data
            return None
        except Exception as e:
            logger.warning(f"Failed to process scale data from {device_name}: {e}")
            return None
    
    def get_supported_metrics(self) -> List[str]:
        """Get list of supported biometric metrics"""
        return [
            'weight',
            'body_fat',
            'muscle_mass', 
            'hydration',
            'air_quality',
            'humidity',
            'temperature'
        ]
    
    def get_supported_sports(self) -> List[str]:
        """Get list of supported sport types"""
        # VeSync doesn't provide workout/sport data
        return []
    
    def get_required_config_fields(self) -> List[str]:
        """Get list of required configuration fields"""
        return ['username', 'password']
    
    def get_connector_description(self) -> str:
        """Get human-readable description of this connector"""
        return "VeSync smart device connector for body composition and environmental monitoring"
    
    async def test_connection(self) -> bool:
        """Test connection to VeSync API"""
        try:
            if not self.vesync:
                return await self.authenticate()
            
            # Try to get devices as a connection test
            devices = await self._get_devices()
            return len(devices) > 0
            
        except Exception as e:
            logger.error(f"VeSync connection test failed: {e}")
            return False
    
    def cleanup(self):
        """Clean up VeSync connection"""
        if self.vesync:
            try:
                # VeSync doesn't have explicit logout, just clear reference
                self.vesync = None
                logger.info("VeSync connector cleaned up")
            except Exception as e:
                logger.warning(f"Error during VeSync cleanup: {e}")
