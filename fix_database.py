#!/usr/bin/env python3
"""
Fix database schema by running migration to multi-athlete support
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.core.database_schema import DatabaseSchemaManager

def main():
    """Fix the database schema by running the migration"""
    try:
        print("🔧 Fixing database schema...")
        
        # Initialize database schema manager
        db_manager = DatabaseSchemaManager('data/athlete_performance.db')
        
        # Run the migration to add athlete_id columns
        print("📊 Running migration to multi-athlete support...")
        db_manager.migrate_to_multi_athlete()
        
        print("✅ Database schema fixed successfully!")
        print("📋 The workouts and biometrics tables now have athlete_id columns")
        
    except Exception as e:
        print(f"❌ Failed to fix database schema: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
