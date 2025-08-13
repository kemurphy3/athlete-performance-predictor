#!/usr/bin/env python3
"""
Database Schema Fix Script
Adds missing athlete_id columns and tables for multi-athlete support
"""

import sqlite3
import os

def fix_database_schema():
    """Fix the database schema to support multi-athlete functionality"""
    
    db_path = "data/fitness_data.db"
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found at {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔍 Checking current database schema...")
        
        # Check if athlete_id columns exist
        cursor.execute("PRAGMA table_info(workouts)")
        workout_columns = [col[1] for col in cursor.fetchall()]
        
        cursor.execute("PRAGMA table_info(biometrics)")
        biometric_columns = [col[1] for col in cursor.fetchall()]
        
        print(f"Workouts table columns: {workout_columns}")
        print(f"Biometrics table columns: {biometric_columns}")
        
        # Add athlete_id column to workouts if missing
        if 'athlete_id' not in workout_columns:
            print("➕ Adding athlete_id column to workouts table...")
            cursor.execute("ALTER TABLE workouts ADD COLUMN athlete_id TEXT DEFAULT 'default'")
            print("✅ athlete_id column added to workouts")
        else:
            print("✅ athlete_id column already exists in workouts")
        
        # Add athlete_id column to biometrics if missing
        if 'athlete_id' not in biometric_columns:
            print("➕ Adding athlete_id column to biometrics table...")
            cursor.execute("ALTER TABLE biometrics ADD COLUMN athlete_id TEXT DEFAULT 'default'")
            print("✅ athlete_id column added to biometrics")
        else:
            print("✅ athlete_id column already exists in biometrics")
        
        # Create athletes table if it doesn't exist
        print("🔍 Checking for athletes table...")
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='athletes'")
        if not cursor.fetchone():
            print("➕ Creating athletes table...")
            cursor.execute("""
                CREATE TABLE athletes (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            print("✅ athletes table created")
        else:
            print("✅ athletes table already exists")
        
        # Create athlete_profiles table if it doesn't exist
        print("🔍 Checking for athlete_profiles table...")
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='athlete_profiles'")
        if not cursor.fetchone():
            print("➕ Creating athlete_profiles table...")
            cursor.execute("""
                CREATE TABLE athlete_profiles (
                    athlete_id TEXT PRIMARY KEY,
                    age INTEGER,
                    weight REAL,
                    height REAL,
                    activity_level TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (athlete_id) REFERENCES athletes (id)
                )
            """)
            print("✅ athlete_profiles table created")
        else:
            print("✅ athlete_profiles table already exists")
        
        # Create default athlete if none exists
        print("🔍 Checking for default athlete...")
        cursor.execute("SELECT COUNT(*) FROM athletes")
        if cursor.fetchone()[0] == 0:
            print("➕ Creating default athlete...")
            cursor.execute("""
                INSERT INTO athletes (id, name) 
                VALUES ('default', 'Default Athlete')
            """)
            print("✅ default athlete created")
        else:
            print("✅ athletes already exist")
        
        # Commit changes
        conn.commit()
        
        print("\n🎉 Database schema updated successfully!")
        
        # Verify the changes
        print("\n🔍 Verifying updated schema...")
        cursor.execute("PRAGMA table_info(workouts)")
        workout_columns = [col[1] for col in cursor.fetchall()]
        print(f"Updated workouts columns: {workout_columns}")
        
        cursor.execute("PRAGMA table_info(biometrics)")
        biometric_columns = [col[1] for col in cursor.fetchall()]
        print(f"Updated biometrics columns: {biometric_columns}")
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print(f"Available tables: {[table[0] for table in tables]}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error updating database schema: {e}")
        if 'conn' in locals():
            conn.close()
        return False

if __name__ == "__main__":
    print("🔧 Database Schema Fix Script")
    print("=" * 40)
    
    success = fix_database_schema()
    
    if success:
        print("\n✅ Database is now ready for multi-athlete functionality!")
        print("You can now run: python analyze_year.py --verbose")
    else:
        print("\n❌ Failed to fix database schema. Check the error messages above.")
