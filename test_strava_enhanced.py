#!/usr/bin/env python3
"""
Test Enhanced Strava Connector
Verify that weight, height, and other biometric data can be pulled from Strava
"""

import asyncio
import os
from datetime import date, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_enhanced_strava():
    """Test the enhanced Strava connector with comprehensive data fetching"""
    
    print("🧪 Testing Enhanced Strava Connector")
    print("="*50)
    
    # Check if required environment variables are set
    required_vars = [
        "STRAVA_CLIENT_ID",
        "STRAVA_CLIENT_SECRET", 
        "STRAVA_REFRESH_TOKEN"
    ]
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        print(f"❌ Missing required environment variables: {missing_vars}")
        print("Please set these in your .env file")
        return
    
    print("✅ Environment variables configured")
    
    # Import connector
    try:
        from src.connectors.strava import StravaConnector
        print("✅ Enhanced Strava connector imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import connector: {e}")
        return
    
    # Create connector instance
    config = {
        "client_id": os.getenv("STRAVA_CLIENT_ID"),
        "client_secret": os.getenv("STRAVA_CLIENT_SECRET"),
        "refresh_token": os.getenv("STRAVA_REFRESH_TOKEN")
    }
    
    connector = StravaConnector("strava", config)
    print("✅ Connector instance created")
    
    # Test authentication
    print("\n🔐 Testing authentication...")
    try:
        authenticated = await connector.authenticate()
        if authenticated:
            print("✅ Authentication successful")
        else:
            print("❌ Authentication failed")
            return
    except Exception as e:
        print(f"❌ Authentication test failed: {e}")
        return
    
    # Test workout fetching
    print("\n🏃‍♂️ Testing workout data...")
    try:
        end_date = date.today()
        start_date = end_date - timedelta(days=7)
        
        workouts = await connector.fetch_workouts(start_date, end_date)
        print(f"✅ Fetched {len(workouts)} workouts from Strava")
        
        if workouts:
            # Show sample workout data
            sample_workout = workouts[0]
            print(f"   Sample workout: {sample_workout.sport} - {sample_workout.duration//60} min")
            if sample_workout.calories:
                print(f"   Calories: {sample_workout.calories}")
            if sample_workout.heart_rate_avg:
                print(f"   Avg HR: {sample_workout.heart_rate_avg} bpm")
        
    except Exception as e:
        print(f"❌ Workout fetching failed: {e}")
    
    # Test comprehensive biometric data fetching
    print("\n📊 Testing comprehensive biometric data...")
    try:
        biometrics = await connector.fetch_biometrics(start_date, end_date)
        print(f"✅ Fetched {len(biometrics)} biometric readings from Strava")
        
        if biometrics:
            print("\n📋 Biometric data found:")
            for bio in biometrics:
                print(f"   {bio.metric}: {bio.value} {bio.unit}")
                
                # Special handling for weight and height
                if bio.metric == "weight":
                    print(f"   🎯 WEIGHT FOUND: {bio.value} kg")
                elif bio.metric == "height":
                    print(f"   📏 HEIGHT FOUND: {bio.value} cm")
                elif "calories" in bio.metric:
                    print(f"   🔥 Calories: {bio.value}")
                elif "distance" in bio.metric:
                    print(f"   🏃 Distance: {bio.value/1000:.2f} km")
                elif "zones" in bio.metric:
                    print(f"   ❤️ Heart rate zones: {bio.value} zones")
        else:
            print("⚠️  No biometric data found")
            
    except Exception as e:
        print(f"❌ Biometric fetching failed: {e}")
    
    # Test supported metrics
    print("\n📈 Testing supported metrics...")
    try:
        metrics = connector.get_supported_metrics()
        sports = connector.get_supported_sports()
        print(f"✅ Supported metrics: {len(metrics)} types")
        print(f"✅ Supported sports: {len(sports)} types")
        
        print("\n📊 Available metrics:")
        for metric in metrics:
            print(f"   • {metric}")
            
    except Exception as e:
        print(f"❌ Failed to get supported types: {e}")
    
    # Test data sync
    print("\n🔄 Testing data sync...")
    try:
        sync_result = await connector.sync_data(start_date, end_date)
        if sync_result.get('success'):
            print("✅ Data sync successful")
            print(f"   Workouts: {len(sync_result.get('workouts', []))}")
            print(f"   Biometrics: {len(sync_result.get('biometrics', []))}")
        else:
            print(f"❌ Data sync failed: {sync_result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ Data sync test failed: {e}")
    
    print("\n" + "="*50)
    print("🎯 Enhanced Strava Connector Test Complete!")
    
    if biometrics:
        weight_found = any(bio.metric == "weight" for bio in biometrics)
        height_found = any(bio.metric == "height" for bio in biometrics)
        
        if weight_found:
            print("✅ SUCCESS: Weight data is now being pulled from Strava!")
        else:
            print("⚠️  Weight not found - check your Strava profile settings")
            
        if height_found:
            print("✅ SUCCESS: Height data is now being pulled from Strava!")
        else:
            print("⚠️  Height not found - check your Strava profile settings")
    
    print("\nNext steps:")
    print("1. Check your Strava profile to ensure weight/height are set")
    print("2. Run this test again to verify data is being pulled")
    print("3. Integrate with your main data pipeline")
    print("4. Wait for Garmin approval to add even more data sources!")

if __name__ == "__main__":
    try:
        asyncio.run(test_enhanced_strava())
    except KeyboardInterrupt:
        print("\n❌ Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        print("Check your configuration and try again")
