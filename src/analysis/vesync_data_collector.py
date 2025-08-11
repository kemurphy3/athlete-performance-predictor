#!/usr/bin/env python3
"""
VeSync Data Collector for Athlete Performance Predictor

This script collects data from VeSync smart devices (smart scales, air purifiers, etc.)
and integrates it with existing Strava fitness data for comprehensive health analysis.

Requirements:
- VeSync account credentials
- pyvesync library
- .env file with credentials
"""

import os
import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import pandas as pd
import numpy as np
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('vesync_data.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class VeSyncDataCollector:
    """Collects data from VeSync smart devices"""
    
    def __init__(self):
        """Initialize VeSync connection"""
        self.username = os.getenv('VESYNC_USERNAME')
        self.password = os.getenv('VESYNC_PASSWORD')
        self.timezone = os.getenv('VESYNC_TIMEZONE', 'America/Denver')
        
        if not self.username or not self.password:
            raise ValueError("VeSync credentials not found in environment variables")
        
        try:
            from pyvesync import VeSync
            self.vesync = VeSync(self.username, self.password, self.timezone)
            self.vesync.login()
            logger.info("Successfully connected to VeSync")
        except ImportError:
            logger.error("pyvesync library not found. Install with: pip install pyvesync")
            raise
        except Exception as e:
            logger.error(f"Failed to connect to VeSync: {e}")
            raise
    
    def get_devices(self) -> Dict[str, Any]:
        """Get all connected VeSync devices"""
        try:
            devices = {}
            for device in self.vesync.devices:
                device_info = {
                    'device_id': device.device_id,
                    'device_name': device.device_name,
                    'device_type': device.device_type,
                    'model': device.model,
                    'connection_status': device.connection_status,
                    'is_on': device.is_on if hasattr(device, 'is_on') else None
                }
                devices[device.device_id] = device_info
                logger.info(f"Found device: {device.device_name} ({device.device_type})")
            
            return devices
        except Exception as e:
            logger.error(f"Error getting devices: {e}")
            return {}
    
    def get_scale_data(self, days_back: int = 30) -> List[Dict[str, Any]]:
        """Get weight and body composition data from smart scales"""
        try:
            scale_data = []
            
            # Get all scale devices
            scales = [d for d in self.vesync.devices if d.device_type == 'ESWL01' or 'scale' in d.device_type.lower()]
            
            if not scales:
                logger.warning("No smart scale devices found")
                return []
            
            for scale in scales:
                logger.info(f"Collecting data from scale: {scale.device_name}")
                
                # Get historical data
                try:
                    # Note: pyvesync may have limited historical data access
                    # This is a placeholder for the actual implementation
                    if hasattr(scale, 'get_scale_data'):
                        data = scale.get_scale_data()
                        scale_data.extend(data)
                    else:
                        logger.warning(f"Scale {scale.device_name} doesn't support data retrieval")
                except Exception as e:
                    logger.error(f"Error getting data from scale {scale.device_name}: {e}")
            
            return scale_data
            
        except Exception as e:
            logger.error(f"Error getting scale data: {e}")
            return []
    
    def get_sleep_data(self, days_back: int = 30) -> List[Dict[str, Any]]:
        """Get sleep data from compatible devices"""
        try:
            sleep_data = []
            
            # Look for sleep tracking devices
            sleep_devices = [d for d in self.vesync.devices if 'sleep' in d.device_type.lower() or 'bed' in d.device_type.lower()]
            
            if not sleep_devices:
                logger.warning("No sleep tracking devices found")
                return []
            
            for device in sleep_devices:
                logger.info(f"Collecting sleep data from: {device.device_name}")
                
                # Placeholder for sleep data collection
                # Implementation depends on specific device capabilities
                try:
                    if hasattr(device, 'get_sleep_data'):
                        data = device.get_sleep_data()
                        sleep_data.extend(data)
                except Exception as e:
                    logger.error(f"Error getting sleep data from {device.device_name}: {e}")
            
            return sleep_data
            
        except Exception as e:
            logger.error(f"Error getting sleep data: {e}")
            return []
    
    def get_environmental_data(self, days_back: int = 30) -> List[Dict[str, Any]]:
        """Get environmental data from air purifiers, humidifiers, etc."""
        try:
            env_data = []
            
            # Look for environmental monitoring devices
            env_devices = [d for d in self.vesync.devices if any(
                device_type in d.device_type.lower() for device_type in 
                ['air', 'humidifier', 'purifier', 'monitor']
            )]
            
            if not env_devices:
                logger.warning("No environmental monitoring devices found")
                return []
            
            for device in env_devices:
                logger.info(f"Collecting environmental data from: {device.device_name}")
                
                try:
                    # Get current environmental readings
                    if hasattr(device, 'get_environmental_data'):
                        data = device.get_environmental_data()
                        env_data.append({
                            'device_id': device.device_id,
                            'device_name': device.device_name,
                            'timestamp': datetime.now().isoformat(),
                            'data': data
                        })
                    elif hasattr(device, 'air_quality'):
                        # Some devices expose air quality directly
                        env_data.append({
                            'device_id': device.device_id,
                            'device_name': device.device_name,
                            'timestamp': datetime.now().isoformat(),
                            'air_quality': getattr(device, 'air_quality', None),
                            'humidity': getattr(device, 'humidity', None),
                            'temperature': getattr(device, 'temperature', None)
                        })
                except Exception as e:
                    logger.error(f"Error getting environmental data from {device.device_name}: {e}")
            
            return env_data
            
        except Exception as e:
            logger.error(f"Error getting environmental data: {e}")
            return []
    
    def collect_all_data(self, days_back: int = 30) -> Dict[str, Any]:
        """Collect all available data from VeSync devices"""
        logger.info(f"Starting data collection for the past {days_back} days")
        
        all_data = {
            'collection_timestamp': datetime.now().isoformat(),
            'devices': self.get_devices(),
            'scale_data': self.get_scale_data(days_back),
            'sleep_data': self.get_sleep_data(days_back),
            'environmental_data': self.get_environmental_data(days_back)
        }
        
        # Save raw data
        output_path = f"data/raw/vesync_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(all_data, f, indent=2)
        
        logger.info(f"Data saved to {output_path}")
        return all_data
    
    def create_summary_report(self, data: Dict[str, Any]) -> pd.DataFrame:
        """Create a summary report of collected data"""
        summary_data = []
        
        # Device summary
        if data.get('devices'):
            for device_id, device_info in data['devices'].items():
                summary_data.append({
                    'data_type': 'device_info',
                    'device_id': device_id,
                    'device_name': device_info['device_name'],
                    'device_type': device_info['device_type'],
                    'connection_status': device_info['connection_status'],
                    'timestamp': data['collection_timestamp']
                })
        
        # Scale data summary
        if data.get('scale_data'):
            for entry in data['scale_data']:
                summary_data.append({
                    'data_type': 'scale_measurement',
                    'device_id': entry.get('device_id'),
                    'timestamp': entry.get('timestamp'),
                    'weight': entry.get('weight'),
                    'body_fat': entry.get('body_fat'),
                    'muscle_mass': entry.get('muscle_mass'),
                    'water_percentage': entry.get('water_percentage')
                })
        
        # Sleep data summary
        if data.get('sleep_data'):
            for entry in data['sleep_data']:
                summary_data.append({
                    'data_type': 'sleep_session',
                    'device_id': entry.get('device_id'),
                    'timestamp': entry.get('timestamp'),
                    'sleep_duration': entry.get('sleep_duration'),
                    'sleep_quality': entry.get('sleep_quality'),
                    'deep_sleep': entry.get('deep_sleep'),
                    'light_sleep': entry.get('light_sleep'),
                    'rem_sleep': entry.get('rem_sleep')
                })
        
        # Environmental data summary
        if data.get('environmental_data'):
            for entry in data['environmental_data']:
                summary_data.append({
                    'data_type': 'environmental_reading',
                    'device_id': entry.get('device_id'),
                    'timestamp': entry.get('timestamp'),
                    'air_quality': entry.get('air_quality'),
                    'humidity': entry.get('humidity'),
                    'temperature': entry.get('temperature')
                })
        
        df = pd.DataFrame(summary_data)
        
        # Save summary
        summary_path = f"data/processed/vesync_summary_{datetime.now().strftime('%Y%m%d')}.csv"
        os.makedirs(os.path.dirname(summary_path), exist_ok=True)
        df.to_csv(summary_path, index=False)
        
        logger.info(f"Summary report saved to {summary_path}")
        return df

def main():
    """Main execution function"""
    try:
        # Create data collector
        collector = VeSyncDataCollector()
        
        # Collect all data
        data = collector.collect_all_data(days_back=30)
        
        # Create summary report
        summary_df = collector.create_summary_report(data)
        
        # Print summary
        print("\n=== VeSync Data Collection Summary ===")
        print(f"Devices found: {len(data.get('devices', {}))}")
        print(f"Scale measurements: {len(data.get('scale_data', []))}")
        print(f"Sleep sessions: {len(data.get('sleep_data', []))}")
        print(f"Environmental readings: {len(data.get('environmental_data', []))}")
        
        if not summary_df.empty:
            print(f"\nData types collected:")
            print(summary_df['data_type'].value_counts())
        
        print(f"\nData saved to data/raw/ and data/processed/ directories")
        
    except Exception as e:
        logger.error(f"Error in main execution: {e}")
        raise

if __name__ == "__main__":
    main()
