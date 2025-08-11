#!/usr/bin/env python3
"""
Quick Start Script for Athlete Performance Predictor

This script helps you test your setup and get started with the system.
It will:
1. Test VeSync connection
2. Test Strava data access
3. Run a sample analysis
4. Provide setup guidance
"""

import os
import sys
from pathlib import Path

def check_environment():
    """Check if environment is properly configured"""
    print("🔍 Checking environment setup...")
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ required. Current version:", sys.version)
        return False
    print("✅ Python version:", sys.version.split()[0])
    
    # Check .env file
    if not os.path.exists('.env'):
        print("❌ .env file not found. Please copy env_template.txt to .env and configure your credentials.")
        return False
    print("✅ .env file found")
    
    # Check required directories
    required_dirs = ['data', 'data/raw', 'data/processed']
    for dir_path in required_dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        print(f"✅ Directory {dir_path} ready")
    
    return True

def test_dependencies():
    """Test if all required packages are installed"""
    print("\n📦 Testing dependencies...")
    
    required_packages = [
        'pyvesync', 'requests', 'pandas', 'numpy', 
        'matplotlib', 'seaborn', 'scikit-learn', 'plotly', 'python-dotenv'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} - not installed")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n❌ Missing packages: {', '.join(missing_packages)}")
        print("Install them with: pip install -r requirements.txt")
        return False
    
    return True

def test_vesync_connection():
    """Test VeSync API connection"""
    print("\n🔌 Testing VeSync connection...")
    
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        username = os.getenv('VESYNC_USERNAME')
        password = os.getenv('VESYNC_PASSWORD')
        
        if not username or not password:
            print("❌ VeSync credentials not found in .env file")
            return False
        
        if username == 'your_vesync_email@example.com':
            print("❌ Please update .env file with your actual VeSync credentials")
            return False
        
        print("✅ VeSync credentials found")
        
        # Test actual connection
        try:
            from pyvesync import VeSync
            vesync = VeSync(username, password, 'America/Denver')
            vesync.login()
            print(f"✅ Successfully connected to VeSync")
            print(f"   Found {len(vesync.devices)} devices")
            
            # List devices
            for device in vesync.devices:
                print(f"   - {device.device_name} ({device.device_type})")
            
            return True
            
        except Exception as e:
            print(f"❌ VeSync connection failed: {e}")
            return False
            
    except ImportError:
        print("❌ python-dotenv not installed")
        return False

def test_strava_data():
    """Test Strava data access"""
    print("\n🏃 Testing Strava data access...")
    
    strava_file = 'data/strava_activities.json'
    if not os.path.exists(strava_file):
        print("❌ Strava data file not found")
        print("   Run: python rag_strava/fetch_strava_data.py")
        return False
    
    try:
        import json
        with open(strava_file, 'r') as f:
            data = json.load(f)
        
        print(f"✅ Strava data found: {len(data)} activities")
        
        # Show sample activity
        if data:
            sample = data[0]
            print(f"   Sample activity: {sample.get('name', 'Unknown')} - {sample.get('type', 'Unknown')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error reading Strava data: {e}")
        return False

def run_sample_analysis():
    """Run a sample fitness analysis"""
    print("\n📊 Running sample fitness analysis...")
    
    try:
        from fitness_metrics_analyzer import FitnessMetricsAnalyzer
        
        # Initialize analyzer
        analyzer = FitnessMetricsAnalyzer()
        
        # Test basic functionality
        training_load = analyzer.calculate_training_load(days=7)
        
        if not training_load.empty:
            print(f"✅ Training load analysis successful")
            print(f"   Recent TRIMP: {training_load['trimp'].sum():.1f}")
            print(f"   Training hours: {training_load['duration_hours'].sum():.1f}")
        else:
            print("⚠️  No recent training data available")
        
        return True
        
    except Exception as e:
        print(f"❌ Fitness analysis failed: {e}")
        return False

def provide_setup_guidance():
    """Provide setup guidance based on test results"""
    print("\n📋 Setup Summary & Next Steps")
    print("=" * 50)
    
    print("\n1. Environment Setup:")
    if os.path.exists('.env'):
        print("   ✅ .env file configured")
    else:
        print("   ❌ Create .env file from env_template.txt")
    
    print("\n2. Dependencies:")
    try:
        import pyvesync
        print("   ✅ pyvesync installed")
    except ImportError:
        print("   ❌ Install: pip install pyvesync")
    
    print("\n3. Data Collection:")
    print("   - Run: python vesync_data_collector.py")
    print("   - Run: python rag_strava/fetch_strava_data.py")
    
    print("\n4. Analysis:")
    print("   - Run: python fitness_metrics_analyzer.py")
    
    print("\n5. Automation (Optional):")
    print("   - Set up cron jobs for daily data collection")
    print("   - Configure weekly report generation")
    
    print("\n6. Monitoring:")
    print("   - Check data/raw/ for VeSync data")
    print("   - Check data/processed/ for reports")
    print("   - Review logs in vesync_data.log")

def main():
    """Main execution function"""
    print("🚀 Athlete Performance Predictor - Quick Start")
    print("=" * 50)
    
    # Run all tests
    tests_passed = 0
    total_tests = 4
    
    if check_environment():
        tests_passed += 1
    
    if test_dependencies():
        tests_passed += 1
    
    if test_vesync_connection():
        tests_passed += 1
    
    if test_strava_data():
        tests_passed += 1
    
    # Try to run sample analysis
    if run_sample_analysis():
        tests_passed += 1
        total_tests += 1
    
    # Summary
    print(f"\n🎯 Setup Status: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed == total_tests:
        print("🎉 All tests passed! Your system is ready to go!")
    else:
        print("⚠️  Some tests failed. Please review the issues above.")
    
    # Provide guidance
    provide_setup_guidance()
    
    print(f"\n💡 For detailed information, see README.md")
    print("🚀 Happy training and analyzing!")

if __name__ == "__main__":
    main()
