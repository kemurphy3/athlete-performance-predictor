#!/usr/bin/env python3
"""
Connectors package for Multi-Source Fitness Data Platform
"""

from .base import BaseConnector, ConnectorError, AuthenticationError, RateLimitError, APIError
from .strava import StravaConnector
# VeSync connector moved to private repository

# Registry of available connectors
AVAILABLE_CONNECTORS = {
    "strava": StravaConnector,
    # Additional proprietary connectors available in private repository
}

def get_connector(source_name: str, config: dict) -> BaseConnector:
    """Get a connector instance for the specified source"""
    if source_name not in AVAILABLE_CONNECTORS:
        raise ValueError(f"Unknown connector: {source_name}")
    
    connector_class = AVAILABLE_CONNECTORS[source_name]
    return connector_class(source_name, config)

def list_available_connectors() -> list:
    """List all available connector names"""
    return list(AVAILABLE_CONNECTORS.keys())
