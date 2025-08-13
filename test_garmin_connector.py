#!/usr/bin/env python3
"""
Test script for Garmin Connect Connector
Use this to verify your Garmin Connect API configuration
"""

import asyncio
import os
from datetime import date, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_garmin_connector():
    """Test the Garmin Connect connector"""
    
    # Check if required environment variables are set
    required_vars = [
        "GARMIN_CLIENT_ID",
        "GARMIN_CLIENT_SECRET", 
        "GARMIN_REDIRECT_URI"
    ]
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        print(f"❌ Missing required environment variables: {missing_vars}")
        print("Please set these in your .env file")
        return
    
    print("✅ Environment variables configured")
    
    # Import connector
    try:
        from src.connectors.garmin import GarminConnectConnector
        print("✅ Garmin Connect connector imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import connector: {e}")
        return
    
    # Create connector instance
    config = {
        "client_id": os.getenv("GARMIN_CLIENT_ID"),
        "client_secret": os.getenv("GARMIN_CLIENT_SECRET"),
        "redirect_uri": os.getenv("GARMIN_REDIRECT_URI")
    }
    
    connector = GarminConnectConnector("garmin_connect", config)
    print("✅ Connector instance created")
    
    # Test OAuth URL generation
    try:
        auth_url = await connector.get_oauth_url()
        print(f"✅ OAuth URL generated: {auth_url[:80]}...")
    except Exception as e:
        print(f"❌ Failed to generate OAuth URL: {e}")
        return
    
    # Test authentication (will fail without tokens, but should handle gracefully)
    print("\n🔐 Testing authentication...")
    try:
        authenticated = await connector.authenticate()
        if authenticated:
            print("✅ Authentication successful (using stored tokens)")
        else:
            print("ℹ️  Authentication failed (expected without tokens)")
            print("   This is normal for first-time setup")
    except Exception as e:
        print(f"❌ Authentication test failed: {e}")
    
    # Test supported metrics and sports
    print("\n📊 Testing supported data types...")
    try:
        metrics = connector.get_supported_metrics()
        sports = connector.get_supported_sports()
        print(f"✅ Supported metrics: {len(metrics)} types")
        print(f"✅ Supported sports: {len(sports)} types")
    except Exception as e:
        print(f"❌ Failed to get supported types: {e}")
    
    print("\n" + "="*50)
    print("🎯 Garmin Connect Connector Test Complete!")
    print("\nNext steps:")
    print("1. Visit the OAuth URL above to authorize your application")
    print("2. Handle the callback to get authorization code")
    print("3. Use exchange_code_for_tokens() to get access tokens")
    print("4. Test data fetching with fetch_workouts() and fetch_biometrics()")
    print("\nSee docs/technical/GARMIN_CONNECT_SETUP.md for detailed instructions")

if __name__ == "__main__":
    print("🧪 Testing Garmin Connect Connector")
    print("="*50)
    
    try:
        asyncio.run(test_garmin_connector())
    except KeyboardInterrupt:
        print("\n❌ Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        print("Check your configuration and try again")
