#!/usr/bin/env python3
"""
Launcher script for the AI Fitness Dashboard
Run this to start the interactive dashboard
"""

import subprocess
import sys
import os

def main():
    """Launch the AI Fitness Dashboard"""
    print("🚀 Launching AI Fitness Coach Dashboard...")
    print("The dashboard will open in your web browser.")
    print("Press Ctrl+C to stop the dashboard when done.")
    
    # Check if streamlit is available
    try:
        import streamlit
        print("✅ Streamlit available")
    except ImportError:
        print("❌ Streamlit not installed")
        print("💡 Install with: pip install streamlit")
        return 1
    
    # Launch dashboard
    dashboard_path = "src/visualization/ai_dashboard.py"
    
    if not os.path.exists(dashboard_path):
        print(f"❌ Dashboard not found at: {dashboard_path}")
        return 1
    
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", dashboard_path,
            "--server.port", "8501",
            "--server.headless", "false"
        ])
    except KeyboardInterrupt:
        print("\n🛑 Dashboard stopped by user")
    except Exception as e:
        print(f"❌ Error launching dashboard: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
