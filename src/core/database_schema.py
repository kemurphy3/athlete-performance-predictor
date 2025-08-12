#!/usr/bin/env python3
"""
Database Schema for Enhanced Calorie Calculation System
Handles user profiles, calibration factors, and weather cache
"""

import sqlite3
import logging
from datetime import datetime
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class DatabaseSchemaManager:
    """Manages database schema for enhanced calorie calculation"""
    
    def __init__(self, database_path: str):
        self.database_path = database_path
        self.logger = logger
    
    def initialize_schema(self):
        """Initialize all required tables for enhanced calorie calculation"""
        try:
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.cursor()
                
                # Create user profiles table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS user_profiles (
                        user_id TEXT PRIMARY KEY,
                        age INTEGER NOT NULL,
                        gender TEXT NOT NULL CHECK (gender IN ('male', 'female')),
                        weight_kg REAL NOT NULL CHECK (weight_kg > 30 AND weight_kg < 300),
                        height_cm REAL CHECK (height_cm > 100 AND height_cm < 250),
                        vo2max REAL CHECK (vo2max > 20 AND vo2max < 80),
                        resting_hr INTEGER CHECK (resting_hr > 40 AND resting_hr < 100),
                        max_hr INTEGER CHECK (max_hr > 120 AND max_hr < 220),
                        activity_level TEXT DEFAULT 'moderate' 
                            CHECK (activity_level IN ('sedentary', 'light', 'moderate', 'active', 'very_active')),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create calorie calibration table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS calorie_calibration (
                        user_id TEXT NOT NULL,
                        sport_category TEXT NOT NULL,
                        calibration_factor REAL DEFAULT 1.0 CHECK (calibration_factor > 0.5 AND calibration_factor < 2.0),
                        sample_count INTEGER DEFAULT 0,
                        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        PRIMARY KEY (user_id, sport_category),
                        FOREIGN KEY (user_id) REFERENCES user_profiles (user_id)
                    )
                """)
                
                # Create weather cache table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS weather_cache (
                        location_hash TEXT PRIMARY KEY,
                        timestamp_bucket INTEGER NOT NULL,
                        temperature_c REAL,
                        humidity_percent REAL CHECK (humidity_percent >= 0 AND humidity_percent <= 100),
                        wind_speed_mps REAL CHECK (wind_speed_mps >= 0),
                        pressure_hpa REAL CHECK (pressure_hpa > 800 AND pressure_hpa < 1200),
                        cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create calorie calculation history table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS calorie_calculation_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        workout_id TEXT NOT NULL,
                        user_id TEXT NOT NULL,
                        original_calories INTEGER,
                        calculated_calories INTEGER NOT NULL,
                        calculation_method TEXT NOT NULL,
                        confidence_score REAL CHECK (confidence_score >= 0 AND confidence_score <= 1),
                        factors TEXT,  -- JSON string of calculation factors
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (workout_id) REFERENCES workouts (workout_id),
                        FOREIGN KEY (user_id) REFERENCES user_profiles (user_id)
                    )
                """)
                
                # Create indexes for performance
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_profiles_gender ON user_profiles(gender)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_calibration_user_sport ON calorie_calibration(user_id, sport_category)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_weather_location_time ON weather_cache(location_hash, timestamp_bucket)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_calorie_history_workout ON calorie_calculation_history(workout_id)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_calorie_history_user ON calorie_calculation_history(user_id)")
                
                conn.commit()
                self.logger.info("Enhanced calorie calculation schema initialized successfully")
                
        except Exception as e:
            self.logger.error(f"Error initializing schema: {e}")
            raise
    
    def create_default_user_profile(self, user_id: str = "default") -> bool:
        """Create a default user profile for testing"""
        try:
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.cursor()
                
                # Check if profile already exists
                cursor.execute("SELECT COUNT(*) FROM user_profiles WHERE user_id = ?", (user_id,))
                if cursor.fetchone()[0] > 0:
                    self.logger.info(f"User profile {user_id} already exists")
                    return True
                
                # Create default profile
                cursor.execute("""
                    INSERT INTO user_profiles (
                        user_id, age, gender, weight_kg, height_cm, 
                        activity_level, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    user_id, 30, 'male', 70.0, 175.0, 
                    'moderate', datetime.now(), datetime.now()
                ))
                
                conn.commit()
                self.logger.info(f"Default user profile created for {user_id}")
                return True
                
        except Exception as e:
            self.logger.error(f"Error creating default user profile: {e}")
            return False
    
    def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user profile by ID"""
        try:
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT user_id, age, gender, weight_kg, height_cm, vo2max, 
                           resting_hr, max_hr, activity_level, created_at, updated_at
                    FROM user_profiles WHERE user_id = ?
                """, (user_id,))
                
                row = cursor.fetchone()
                if row:
                    return {
                        'user_id': row[0],
                        'age': row[1],
                        'gender': row[2],
                        'weight_kg': row[3],
                        'height_cm': row[4],
                        'vo2max': row[5],
                        'resting_hr': row[6],
                        'max_hr': row[7],
                        'activity_level': row[8],
                        'created_at': row[9],
                        'updated_at': row[10]
                    }
                return None
                
        except Exception as e:
            self.logger.error(f"Error getting user profile: {e}")
            return None
    
    def update_user_profile(self, user_id: str, profile_data: Dict[str, Any]) -> bool:
        """Update user profile"""
        try:
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.cursor()
                
                # Build update query dynamically
                fields = []
                values = []
                for key, value in profile_data.items():
                    if key in ['age', 'gender', 'weight_kg', 'height_cm', 'vo2max', 'resting_hr', 'max_hr', 'activity_level']:
                        fields.append(f"{key} = ?")
                        values.append(value)
                
                if not fields:
                    self.logger.warning("No valid fields to update")
                    return False
                
                fields.append("updated_at = ?")
                values.append(datetime.now())
                values.append(user_id)
                
                query = f"UPDATE user_profiles SET {', '.join(fields)} WHERE user_id = ?"
                cursor.execute(query, values)
                
                if cursor.rowcount > 0:
                    conn.commit()
                    self.logger.info(f"User profile {user_id} updated successfully")
                    return True
                else:
                    self.logger.warning(f"No rows updated for user {user_id}")
                    return False
                
        except Exception as e:
            self.logger.error(f"Error updating user profile: {e}")
            return False
    
    def get_calibration_factor(self, user_id: str, sport_category: str) -> float:
        """Get calibration factor for a user and sport category"""
        try:
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT calibration_factor FROM calorie_calibration 
                    WHERE user_id = ? AND sport_category = ?
                """, (user_id, sport_category))
                
                row = cursor.fetchone()
                return row[0] if row else 1.0
                
        except Exception as e:
            self.logger.error(f"Error getting calibration factor: {e}")
            return 1.0
    
    def update_calibration_factor(self, user_id: str, sport_category: str, 
                                new_factor: float, sample_count: int = 1) -> bool:
        """Update calibration factor for a user and sport category"""
        try:
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT OR REPLACE INTO calorie_calibration 
                    (user_id, sport_category, calibration_factor, sample_count, last_updated)
                    VALUES (?, ?, ?, ?, ?)
                """, (user_id, sport_category, new_factor, sample_count, datetime.now()))
                
                conn.commit()
                self.logger.info(f"Calibration factor updated for {user_id} - {sport_category}: {new_factor}")
                return True
                
        except Exception as e:
            self.logger.error(f"Error updating calibration factor: {e}")
            return False
    
    def log_calorie_calculation(self, workout_id: str, user_id: str, 
                               original_calories: Optional[int], calculated_calories: int,
                               method: str, confidence: float, factors: Dict[str, Any]) -> bool:
        """Log a calorie calculation for analysis and calibration"""
        try:
            import json
            
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO calorie_calculation_history 
                    (workout_id, user_id, original_calories, calculated_calories, 
                     calculation_method, confidence_score, factors)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    workout_id, user_id, original_calories, calculated_calories,
                    method, confidence, json.dumps(factors)
                ))
                
                conn.commit()
                return True
                
        except Exception as e:
            self.logger.error(f"Error logging calorie calculation: {e}")
            return False
