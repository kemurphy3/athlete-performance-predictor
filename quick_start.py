#!/usr/bin/env python3
"""
Quick Start Script for Athlete Performance Predictor
Provides immediate access to all features with clear guidance
"""

import os
import sys
import subprocess
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
        print("❌ .env file not found. Please copy env_template.txt to .env and add your credentials")
        return False
    print("✅ Environment file found")
    
    # Check data directory
    if not os.path.exists('data'):
        print("❌ Data directory not found. Creating...")
        os.makedirs('data', exist_ok=True)
    
    # Check for activities data
    activities_path = os.path.join('data', 'activities.csv')
    if not os.path.exists(activities_path):
        print("⚠️ No activities.csv found. You'll need to add your Strava data")
    else:
        print("✅ Activities data found")
    
    return True

def show_menu():
    """Display main menu options"""
    print("\n" + "="*60)
    print("🏃‍♂️ ATHLETE PERFORMANCE PREDICTOR - QUICK START")
    print("="*60)
    print("\nChoose an option:")
    print("1. 🚀 Run Complete Analysis (One-Click)")
    print("2. 📊 Launch Interactive Dashboard")
    print("3. 📱 Collect VeSync Data")
    print("4. 🔧 Check System Status")
    print("5. 📚 View Usage Guide")
    print("6. 🧹 Clean Repository")
    print("0. ❌ Exit")
    
    return input("\nEnter your choice (0-6): ")

def run_complete_analysis():
    """Run the one-click fitness analysis"""
    print("\n🚀 Starting complete fitness analysis...")
    print("This will analyze all your data and generate a comprehensive report.")
    
    try:
        # Import and run the main analysis
        from analyze_my_fitness import main as run_analysis
        results = run_analysis()
        
        print("\n✅ Analysis complete!")
        if 'report_file' in results:
            print(f"📄 Report saved to: {results['report_file']}")
        
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Try: pip install -r requirements.txt")
        return False
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        return False

def launch_dashboard():
    """Launch the Streamlit dashboard"""
    print("\n📊 Launching interactive dashboard...")
    print("The dashboard will open in your web browser.")
    print("Press Ctrl+C to stop the dashboard when done.")
    
    try:
        # Check if streamlit is available
        import streamlit
        print("✅ Streamlit available")
        
        # Launch dashboard
        subprocess.run([sys.executable, "-m", "streamlit", "run", "streamlit_app.py"])
        return True
    except ImportError:
        print("❌ Streamlit not installed")
        print("💡 Install with: pip install streamlit")
        return False
    except Exception as e:
        print(f"❌ Dashboard launch failed: {e}")
        return False

def collect_vesync_data():
    """Collect data from VeSync devices"""
    print("\n📱 Collecting VeSync data...")
    
    try:
        # Check if pyvesync is available
        import pyvesync
        print("✅ VeSync library available")
        
        # Run data collection
        from vesync_data_collector import main as collect_data
        collect_data()
        return True
    except ImportError:
        print("❌ VeSync library not installed")
        print("💡 Install with: pip install pyvesync")
        return False
    except Exception as e:
        print(f"❌ Data collection failed: {e}")
        return False

def check_system_status():
    """Check system status and dependencies"""
    print("\n🔧 Checking system status...")
    
    # Check required packages
    required_packages = [
        'pandas', 'numpy', 'matplotlib', 'seaborn',
        'scikit-learn', 'xgboost', 'shap', 'streamlit'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package}")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n⚠️ Missing packages: {', '.join(missing_packages)}")
        print("💡 Install with: pip install -r requirements.txt")
    else:
        print("\n✅ All required packages are installed")
    
    # Check data availability
    print("\n📊 Data Status:")
    data_files = [
        ('data/activities.csv', 'Strava Activities'),
        ('data/strava_activities.json', 'Strava JSON'),
        ('data/raw/vesync_data_*.json', 'VeSync Data')
    ]
    
    for pattern, description in data_files:
        if '*' in pattern:
            # Check for any matching files
            import glob
            matches = glob.glob(pattern)
            if matches:
                print(f"✅ {description}: {len(matches)} files found")
            else:
                print(f"❌ {description}: No files found")
        else:
            if os.path.exists(pattern):
                print(f"✅ {description}: Available")
            else:
                print(f"❌ {description}: Not found")
    
    return True

def view_usage_guide():
    """Display usage guide"""
    print("\n📚 Usage Guide:")
    print("="*50)
    
    guide_file = "USAGE_GUIDE.md"
    if os.path.exists(guide_file):
        try:
            with open(guide_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Display first 500 characters as preview
            preview = content[:500] + "..." if len(content) > 500 else content
            print(preview)
            print(f"\n📖 Full guide available in: {guide_file}")
        except Exception as e:
            print(f"❌ Error reading guide: {e}")
    else:
        print("❌ Usage guide not found")
        print("💡 Run the repository cleanup to create the guide")
    
    return True

def clean_repository():
    """Clean and organize repository"""
    print("\n🧹 Cleaning repository...")
    
    try:
        # Run cleanup script
        from cleanup_repo import cleanup_repository
        cleanup_repository()
        return True
    except ImportError:
        print("❌ Cleanup script not found")
        print("💡 The cleanup script will be created automatically")
        return False
    except Exception as e:
        print(f"❌ Cleanup failed: {e}")
        return False

def main():
    """Main quick start function"""
    print("🏃‍♂️ Welcome to Athlete Performance Predictor!")
    
    # Check environment
    if not check_environment():
        print("\n❌ Environment check failed. Please fix issues above.")
        return
    
    # Main menu loop
    while True:
        choice = show_menu()
        
        if choice == '0':
            print("\n👋 Goodbye! Keep training smart!")
            break
        elif choice == '1':
            run_complete_analysis()
        elif choice == '2':
            launch_dashboard()
        elif choice == '3':
            collect_vesync_data()
        elif choice == '4':
            check_system_status()
        elif choice == '5':
            view_usage_guide()
        elif choice == '6':
            clean_repository()
        else:
            print("❌ Invalid choice. Please enter 0-6.")
        
        input("\nPress Enter to continue...")

if __name__ == "__main__":
    main()
