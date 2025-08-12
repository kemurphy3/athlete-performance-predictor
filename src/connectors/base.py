#!/usr/bin/env python3
"""
Abstract Base Connector for Multi-Source Fitness Data
Defines the interface that all data source connectors must implement
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from datetime import date, datetime, timedelta
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass
import time
import random

from ..core.models import Workout, BiometricReading

logger = logging.getLogger(__name__)

@dataclass
class RateLimitInfo:
    """Rate limiting information"""
    retry_after: int
    remaining_requests: int
    reset_time: Optional[datetime] = None

class ConnectorError(Exception):
    """Base exception for connector errors"""
    pass

class AuthenticationError(ConnectorError):
    """Authentication failed"""
    pass

class RateLimitError(ConnectorError):
    """Rate limit exceeded"""
    def __init__(self, message: str, retry_after: int):
        super().__init__(message)
        self.retry_after = retry_after

class APIError(ConnectorError):
    """API request failed"""
    pass

class BaseConnector(ABC):
    """Abstract base class for all data source connectors"""
    
    def __init__(self, source_name: str, config: Dict[str, Any]):
        self.source_name = source_name
        self.config = config
        self.logger = logging.getLogger(f"connector.{source_name}")
        self.authenticated = False
        self.last_sync = None
        self.sync_count = 0
        
        # Rate limiting
        self.rate_limit_info = None
        self.last_request_time = 0
        self.min_request_interval = 0.1  # Minimum seconds between requests
        
        self.logger.info(f"Initialized {source_name} connector")
    
    @abstractmethod
    async def authenticate(self) -> bool:
        """Handle OAuth2 or API key authentication"""
        pass
    
    @abstractmethod
    async def fetch_workouts(self, start_date: date, end_date: date) -> List[Workout]:
        """Fetch and transform workouts to canonical model"""
        pass
    
    @abstractmethod
    async def fetch_biometrics(self, start_date: date, end_date: date) -> List[BiometricReading]:
        """Fetch daily biometric readings"""
        pass
    
    @abstractmethod
    def get_supported_metrics(self) -> List[str]:
        """Get list of supported biometric metrics"""
        pass
    
    @abstractmethod
    def get_supported_sports(self) -> List[str]:
        """Get list of supported sport types"""
        pass
    
    async def handle_rate_limit(self, retry_after: int):
        """Handle rate limiting with exponential backoff and jitter"""
        self.logger.warning(f"Rate limit hit, waiting {retry_after} seconds")
        
        # Add jitter to prevent thundering herd
        jitter = random.uniform(0.1, 0.3) * retry_after
        wait_time = retry_after + jitter
        
        self.logger.info(f"Waiting {wait_time:.1f} seconds with jitter")
        await asyncio.sleep(wait_time)
    
    async def make_request(self, request_func, *args, **kwargs):
        """Make a rate-limited request with retry logic"""
        max_retries = 3
        base_delay = 1
        
        for attempt in range(max_retries):
            try:
                # Respect minimum request interval
                time_since_last = time.time() - self.last_request_time
                if time_since_last < self.min_request_interval:
                    await asyncio.sleep(self.min_request_interval - time_since_last)
                
                # Make the request
                result = await request_func(*args, **kwargs)
                self.last_request_time = time.time()
                
                # Update rate limit info if available
                if hasattr(result, 'headers'):
                    self._update_rate_limit_info(result.headers)
                
                return result
                
            except RateLimitError as e:
                if attempt < max_retries - 1:
                    self.logger.warning(f"Rate limit hit on attempt {attempt + 1}, retrying...")
                    await self.handle_rate_limit(e.retry_after)
                    continue
                else:
                    raise
                    
            except (APIError, AuthenticationError) as e:
                # Don't retry on auth or API errors
                raise
                
            except Exception as e:
                if attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
                    self.logger.warning(f"Request failed on attempt {attempt + 1}, retrying in {delay:.1f}s: {e}")
                    await asyncio.sleep(delay)
                    continue
                else:
                    self.logger.error(f"Request failed after {max_retries} attempts: {e}")
                    raise APIError(f"Request failed after {max_retries} attempts: {e}")
    
    def _update_rate_limit_info(self, headers: Dict[str, str]):
        """Update rate limit information from response headers"""
        try:
            retry_after = headers.get('Retry-After')
            if retry_after:
                self.rate_limit_info = RateLimitInfo(
                    retry_after=int(retry_after),
                    remaining_requests=int(headers.get('X-RateLimit-Remaining', 0)),
                    reset_time=datetime.fromtimestamp(int(headers.get('X-RateLimit-Reset', 0)))
                )
        except (ValueError, TypeError) as e:
            self.logger.debug(f"Could not parse rate limit headers: {e}")
    
    async def test_connection(self) -> bool:
        """Test if the connector can successfully connect and authenticate"""
        try:
            self.logger.info(f"Testing connection to {self.source_name}")
            
            # Try to authenticate
            if not await self.authenticate():
                self.logger.error(f"Authentication failed for {self.source_name}")
                return False
            
            # Try to fetch a small amount of data
            test_end_date = date.today()
            test_start_date = test_end_date - timedelta(days=1)
            
            try:
                workouts = await self.fetch_workouts(test_start_date, test_end_date)
                self.logger.info(f"Successfully fetched {len(workouts)} test workouts")
            except Exception as e:
                self.logger.warning(f"Could not fetch test workouts: {e}")
            
            try:
                biometrics = await self.fetch_biometrics(test_start_date, test_end_date)
                self.logger.info(f"Successfully fetched {len(biometrics)} test biometric readings")
            except Exception as e:
                self.logger.warning(f"Could not fetch test biometrics: {e}")
            
            self.logger.info(f"Connection test successful for {self.source_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Connection test failed for {self.source_name}: {e}")
            return False
    
    def get_sync_status(self) -> Dict[str, Any]:
        """Get current sync status for this connector"""
        return {
            'source': self.source_name,
            'authenticated': self.authenticated,
            'last_sync': self.last_sync.isoformat() if self.last_sync else None,
            'sync_count': self.sync_count,
            'rate_limit_info': {
                'retry_after': self.rate_limit_info.retry_after if self.rate_limit_info else None,
                'remaining_requests': self.rate_limit_info.remaining_requests if self.rate_limit_info else None,
                'reset_time': self.rate_limit_info.reset_time.isoformat() if self.rate_limit_info and self.rate_limit_info.reset_time else None
            } if self.rate_limit_info else None
        }
    
    def update_sync_status(self, success: bool, error_message: str = None):
        """Update sync status after a sync operation"""
        if success:
            self.last_sync = datetime.utcnow()
            self.sync_count += 1
            self.logger.info(f"Sync completed successfully for {self.source_name}")
        else:
            self.logger.error(f"Sync failed for {self.source_name}: {error_message}")
    
    async def sync_data(self, start_date: date, end_date: date) -> Dict[str, Any]:
        """Synchronize data for the specified date range"""
        self.logger.info(f"Starting sync for {self.source_name} from {start_date} to {end_date}")
        
        try:
            # Ensure authentication
            if not self.authenticated:
                if not await self.authenticate():
                    raise AuthenticationError(f"Failed to authenticate with {self.source_name}")
            
            # Fetch workouts
            workouts = await self.fetch_workouts(start_date, end_date)
            self.logger.info(f"Fetched {len(workouts)} workouts from {self.source_name}")
            
            # Fetch biometrics
            biometrics = await self.fetch_biometrics(start_date, end_date)
            self.logger.info(f"Fetched {len(biometrics)} biometric readings from {self.source_name}")
            
            # Update sync status
            self.update_sync_status(True)
            
            return {
                'source': self.source_name,
                'workouts': workouts,
                'biometrics': biometrics,
                'sync_time': datetime.utcnow().isoformat(),
                'success': True
            }
            
        except Exception as e:
            error_msg = str(e)
            self.update_sync_status(False, error_msg)
            self.logger.error(f"Sync failed for {self.source_name}: {error_msg}")
            
            return {
                'source': self.source_name,
                'workouts': [],
                'biometrics': [],
                'sync_time': datetime.utcnow().isoformat(),
                'success': False,
                'error': error_msg
            }
    
    def validate_config(self) -> bool:
        """Validate connector configuration"""
        required_fields = self.get_required_config_fields()
        
        for field in required_fields:
            if field not in self.config or not self.config[field]:
                self.logger.error(f"Missing required config field: {field}")
                return False
        
        return True
    
    @abstractmethod
    def get_required_config_fields(self) -> List[str]:
        """Get list of required configuration fields"""
        pass
    
    def get_optional_config_fields(self) -> List[str]:
        """Get list of optional configuration fields"""
        return []
    
    def get_config_schema(self) -> Dict[str, Any]:
        """Get configuration schema for this connector"""
        return {
            'required': self.get_required_config_fields(),
            'optional': self.get_optional_config_fields(),
            'description': self.get_connector_description()
        }
    
    @abstractmethod
    def get_connector_description(self) -> str:
        """Get human-readable description of this connector"""
        pass
    
    def cleanup(self):
        """Clean up resources when connector is no longer needed"""
        self.logger.info(f"Cleaning up {self.source_name} connector")
        # Override in subclasses if needed

class ConnectorRegistry:
    """Registry for managing all available connectors"""
    
    def __init__(self):
        self.connectors: Dict[str, type] = {}
        self.logger = logging.getLogger("connector_registry")
    
    def register(self, name: str, connector_class: type):
        """Register a connector class"""
        if not issubclass(connector_class, BaseConnector):
            raise ValueError(f"Connector class must inherit from BaseConnector")
        
        self.connectors[name] = connector_class
        self.logger.info(f"Registered connector: {name}")
    
    def get_connector(self, name: str) -> Optional[type]:
        """Get a connector class by name"""
        return self.connectors.get(name)
    
    def list_connectors(self) -> List[str]:
        """List all registered connector names"""
        return list(self.connectors.keys())
    
    def create_connector(self, name: str, config: Dict[str, Any]) -> Optional[BaseConnector]:
        """Create a connector instance"""
        connector_class = self.get_connector(name)
        if connector_class:
            try:
                return connector_class(name, config)
            except Exception as e:
                self.logger.error(f"Failed to create connector {name}: {e}")
                return None
        return None
    
    def get_connector_info(self, name: str) -> Optional[Dict[str, Any]]:
        """Get information about a connector"""
        connector_class = self.get_connector(name)
        if connector_class:
            # Create a temporary instance to get schema info
            try:
                temp_config = {field: "test" for field in connector_class.get_required_config_fields()}
                temp_instance = connector_class(name, temp_config)
                return {
                    'name': name,
                    'description': temp_instance.get_connector_description(),
                    'supported_metrics': temp_instance.get_supported_metrics(),
                    'supported_sports': temp_instance.get_supported_sports(),
                    'config_schema': temp_instance.get_config_schema()
                }
            except Exception as e:
                self.logger.warning(f"Could not get info for connector {name}: {e}")
                return None
        return None

# Global connector registry
connector_registry = ConnectorRegistry()
