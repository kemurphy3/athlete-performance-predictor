#!/usr/bin/env python3
"""
Database Schema for Enhanced Multi-Athlete Calorie Calculation System
Handles user profiles, calibration factors, weather cache, and multi-athlete support
"""

import sqlite3
import logging
from datetime import datetime
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class DatabaseSchemaManager:
    """Manages database schema for enhanced multi-athlete calorie calculation"""
    
    def __init__(self, database_path: str):
        self.database_path = database_path
        self.logger = logger
    
    def initialize_schema(self):
        """Initialize all required tables for enhanced multi-athlete calorie calculation"""
        try:
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.cursor()
                
                # Create athletes table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS athletes (
                        athlete_id TEXT PRIMARY KEY,
                        name TEXT NOT NULL,
                        email TEXT UNIQUE,
                        active BOOLEAN DEFAULT TRUE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create athlete profiles table (renamed from user_profiles)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS athlete_profiles (
                        athlete_id TEXT PRIMARY KEY,
                        age INTEGER NOT NULL,
                        gender TEXT NOT NULL CHECK (gender IN ('male', 'female')),
                        weight_kg REAL NOT NULL,
                        height_cm REAL,
                        vo2max REAL,
                        resting_hr INTEGER,
                        max_hr INTEGER,
                        activity_level TEXT DEFAULT 'moderate' 
                            CHECK (activity_level IN ('sedentary', 'light', 'moderate', 'active', 'very_active')),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (athlete_id) REFERENCES athletes(athlete_id)
                    )
                """)
                
                # Create multi-athlete data sources table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS athlete_data_sources (
                        athlete_id TEXT NOT NULL,
                        source_name TEXT NOT NULL,
                        auth_token TEXT,
                        refresh_token TEXT,
                        expires_at TIMESTAMP,
                        last_sync TIMESTAMP,
                        active BOOLEAN DEFAULT TRUE,
                        PRIMARY KEY (athlete_id, source_name),
                        FOREIGN KEY (athlete_id) REFERENCES athletes(athlete_id)
                    )
                """)
                
                # Create per-athlete calorie calibration table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS athlete_calorie_calibration (
                        athlete_id TEXT NOT NULL,
                        sport_category TEXT NOT NULL,
                        calibration_factor REAL DEFAULT 1.0,
                        sample_count INTEGER DEFAULT 0,
                        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        PRIMARY KEY (athlete_id, sport_category),
                        FOREIGN KEY (athlete_id) REFERENCES athletes(athlete_id)
                    )
                """)
                
                # Handle existing weather_cache table - add expires_at column if missing
                cursor.execute("PRAGMA table_info(weather_cache)")
                weather_columns = [col[1] for col in cursor.fetchall()]
                
                if 'weather_cache' in weather_columns and 'expires_at' not in weather_columns:
                    try:
                        cursor.execute("ALTER TABLE weather_cache ADD COLUMN expires_at TIMESTAMP")
                        self.logger.info("Added expires_at column to existing weather_cache table")
                    except sqlite3.OperationalError:
                        # Column might already exist
                        pass
                
                # Create weather cache table if it doesn't exist
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS weather_cache (
                        location_hash TEXT PRIMARY KEY,
                        temperature_c REAL,
                        humidity_percent REAL,
                        wind_speed_mps REAL,
                        pressure_hpa REAL,
                        cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        expires_at TIMESTAMP
                    )
                """)
                
                # Create elevation cache table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS elevation_cache (
                        coordinates_hash TEXT PRIMARY KEY,
                        elevation_m REAL,
                        cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        expires_at TIMESTAMP
                    )
                """)
                
                # Create indexes for performance
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_athlete_profiles_activity 
                    ON athlete_profiles(activity_level, age, gender)
                """)
                
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_athlete_data_sources_active 
                    ON athlete_data_sources(athlete_id, active)
                """)
                
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_calibration_sport 
                    ON athlete_calorie_calibration(sport_category, calibration_factor)
                """)
                
                # Only create weather index if expires_at column exists
                cursor.execute("PRAGMA table_info(weather_cache)")
                weather_columns = [col[1] for col in cursor.fetchall()]
                if 'expires_at' in weather_columns:
                    cursor.execute("""
                        CREATE INDEX IF NOT EXISTS idx_weather_cache_expires 
                        ON weather_cache(expires_at)
                    """)
                
                conn.commit()
                self.logger.info("Multi-athlete database schema initialized successfully")
                
        except Exception as e:
            self.logger.error(f"Failed to initialize database schema: {e}")
            raise
    
    def migrate_to_multi_athlete(self):
        """Migrate existing single-user database to multi-athlete support"""
        try:
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.cursor()
                
                # Check if migration is needed
                cursor.execute("PRAGMA table_info(workouts)")
                columns = [col[1] for col in cursor.fetchall()]
                
                if 'athlete_id' not in columns:
                    self.logger.info("Starting migration to multi-athlete support...")
                    
                    # Add athlete_id column to workouts table
                    cursor.execute("ALTER TABLE workouts ADD COLUMN athlete_id TEXT DEFAULT 'default'")
                    
                    # Add athlete_id column to biometrics table (note: table name is 'biometrics', not 'biometric_readings')
                    cursor.execute("ALTER TABLE biometrics ADD COLUMN athlete_id TEXT DEFAULT 'default'")
                    
                    # Create default athlete
                    cursor.execute("""
                        INSERT OR IGNORE INTO athletes (athlete_id, name, active)
                        VALUES ('default', 'Default Athlete', TRUE)
                    """)
                    
                    # Create default athlete profile
                    cursor.execute("""
                        INSERT OR IGNORE INTO athlete_profiles 
                        (athlete_id, age, gender, weight_kg, activity_level)
                        VALUES ('default', 35, 'male', 70.0, 'moderate')
                    """)
                    
                    # Create indexes for multi-athlete support
                    cursor.execute("""
                        CREATE INDEX IF NOT EXISTS idx_workouts_athlete 
                        ON workouts(athlete_id, start_time DESC)
                    """)
                    
                    cursor.execute("""
                        CREATE INDEX IF NOT EXISTS idx_biometrics_athlete 
                        ON biometrics(athlete_id, timestamp DESC)
                    """)
                    
                    conn.commit()
                    self.logger.info("Successfully migrated to multi-athlete support")
                else:
                    self.logger.info("Database already supports multi-athlete")
                    
        except Exception as e:
            self.logger.error(f"Failed to migrate to multi-athlete: {e}")
            raise
    
    def create_default_user_profile(self, athlete_id: str = 'default'):
        """Create a default user profile for the specified athlete"""
        try:
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.cursor()
                
                # Check if profile already exists
                cursor.execute("SELECT COUNT(*) FROM athlete_profiles WHERE athlete_id = ?", (athlete_id,))
                if cursor.fetchone()[0] > 0:
                    self.logger.info(f"Profile already exists for athlete {athlete_id}")
                    return
                
                # Create default profile
                cursor.execute("""
                    INSERT INTO athlete_profiles 
                    (athlete_id, age, gender, weight_kg, height_cm, activity_level)
                    VALUES (?, 35, 'male', 70.0, 175.0, 'moderate')
                """, (athlete_id,))
                
                conn.commit()
                self.logger.info(f"Created default profile for athlete {athlete_id}")
                
        except Exception as e:
            self.logger.error(f"Failed to create default profile: {e}")
            raise
    
    def get_athlete_profile(self, athlete_id: str) -> Optional[Dict[str, Any]]:
        """Get athlete profile from database"""
        try:
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.execute("""
                    SELECT age, gender, weight_kg, height_cm, vo2max, resting_hr, max_hr, activity_level
                    FROM athlete_profiles 
                    WHERE athlete_id = ?
                """, (athlete_id,))
                
                row = cursor.fetchone()
                if row:
                    return {
                        'athlete_id': athlete_id,
                        'age': row[0],
                        'gender': row[1],
                        'weight_kg': row[2],
                        'height_cm': row[3],
                        'vo2max': row[4],
                        'resting_hr': row[5],
                        'max_hr': row[6],
                        'activity_level': row[7]
                    }
        except Exception as e:
            self.logger.warning(f"Could not get athlete profile: {e}")
        
        return None
    
    def update_athlete_profile(self, athlete_id: str, profile_data: Dict[str, Any]):
        """Update athlete profile in database"""
        try:
            with sqlite3.connect(self.database_path) as conn:
                # Build dynamic UPDATE query
                fields = []
                values = []
                
                for field, value in profile_data.items():
                    if field != 'athlete_id' and value is not None:
                        fields.append(f"{field} = ?")
                        values.append(value)
                
                if fields:
                    values.append(athlete_id)  # For WHERE clause
                    query = f"""
                        UPDATE athlete_profiles 
                        SET {', '.join(fields)}, updated_at = CURRENT_TIMESTAMP
                        WHERE athlete_id = ?
                    """
                    
                    conn.execute(query, values)
                    conn.commit()
                    self.logger.info(f"Updated profile for athlete {athlete_id}")
                    
        except Exception as e:
            self.logger.error(f"Failed to update athlete profile: {e}")
            raise
    
    def get_calibration_factor(self, athlete_id: str, sport: str) -> float:
        """Get calibration factor for athlete and sport"""
        try:
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.execute("""
                    SELECT calibration_factor FROM athlete_calorie_calibration
                    WHERE athlete_id = ? AND sport_category = ?
                """, (athlete_id, sport))
                
                row = cursor.fetchone()
                if row:
                    return row[0]
                    
        except Exception as e:
            self.logger.warning(f"Could not get calibration factor: {e}")
        
        return 1.0  # Default no calibration
    
    def update_calibration_factor(self, athlete_id: str, sport: str, factor: float, sample_count: int = 1):
        """Update calibration factor for athlete and sport"""
        try:
            with sqlite3.connect(self.database_path) as conn:
                conn.execute("""
                    INSERT INTO athlete_calorie_calibration 
                    (athlete_id, sport_category, calibration_factor, sample_count, last_updated)
                    VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                    ON CONFLICT(athlete_id, sport_category) DO UPDATE SET
                        calibration_factor = ?,
                        sample_count = ?,
                        last_updated = CURRENT_TIMESTAMP
                """, (athlete_id, sport, factor, sample_count, factor, sample_count))
                
                conn.commit()
                self.logger.info(f"Updated calibration for {athlete_id}:{sport} = {factor}")
                
        except Exception as e:
            self.logger.error(f"Failed to update calibration factor: {e}")
            raise
    
    def get_weather_data(self, location_hash: str) -> Optional[Dict[str, Any]]:
        """Get cached weather data for location"""
        try:
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.execute("""
                    SELECT temperature_c, humidity_percent, wind_speed_mps, pressure_hpa, cached_at, expires_at
                    FROM weather_cache
                    WHERE location_hash = ? AND expires_at > CURRENT_TIMESTAMP
                """, (location_hash,))
                
                row = cursor.fetchone()
                if row:
                    return {
                        'temperature_c': row[0],
                        'humidity_percent': row[1],
                        'wind_speed_mps': row[2],
                        'pressure_hpa': row[3],
                        'cached_at': row[4],
                        'expires_at': row[5]
                    }
                    
        except Exception as e:
            self.logger.warning(f"Could not get weather data: {e}")
        
        return None
    
    def cache_weather_data(self, location_hash: str, weather_data: Dict[str, Any], ttl_minutes: int = 15):
        """Cache weather data with TTL"""
        try:
            with sqlite3.connect(self.database_path) as conn:
                expires_at = datetime.now().timestamp() + (ttl_minutes * 60)
                
                conn.execute("""
                    INSERT OR REPLACE INTO weather_cache 
                    (location_hash, temperature_c, humidity_percent, wind_speed_mps, pressure_hpa, expires_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    location_hash,
                    weather_data.get('temperature_c'),
                    weather_data.get('humidity_percent'),
                    weather_data.get('wind_speed_mps'),
                    weather_data.get('pressure_hpa'),
                    expires_at
                ))
                
                conn.commit()
                self.logger.info(f"Cached weather data for {location_hash}")
                
        except Exception as e:
            self.logger.error(f"Failed to cache weather data: {e}")
            raise
