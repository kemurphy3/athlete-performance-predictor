#!/usr/bin/env python3
"""
Main Data Ingestion Orchestrator for Multi-Source Fitness Data Platform
Coordinates all connectors, handles deduplication, and manages unified data pipeline
"""

import asyncio
import logging
import sqlite3
from datetime import date, datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import json
import structlog

from .models import Workout, BiometricReading, SyncStatus, DataSource, WorkoutSummary, BiometricSummary
from .deduplication import DeduplicationEngine
from ..connectors import get_connector, list_available_connectors, BaseConnector, ConnectorError

logger = structlog.get_logger()

class DataIngestionOrchestrator:
    """Main orchestrator for multi-source fitness data ingestion"""
    
    def __init__(self, database_path: str = "data/athlete_performance.db"):
        self.database_path = database_path
        self.dedup_engine = DeduplicationEngine()
        self.connectors: Dict[str, BaseConnector] = {}
        self.sync_status: Dict[str, SyncStatus] = {}
        
        # Initialize database
        self._init_database()
        
        # Load existing sync status
        self._load_sync_status()
        
        # Load configured connectors from database
        self._load_configured_connectors()
        
        logger.info("Data ingestion orchestrator initialized", database_path=database_path)
    
    def _init_database(self):
        """Initialize SQLite database with required tables"""
        db_path = Path(self.database_path)
        db_path.parent.mkdir(parents=True, exist_ok=True)
        
        with sqlite3.connect(self.database_path) as conn:
            # Check if we need to migrate existing data
            self._migrate_database_if_needed(conn)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS workouts (
                    workout_id TEXT PRIMARY KEY,
                    start_time TIMESTAMP NOT NULL,
                    end_time TIMESTAMP,
                    sport TEXT NOT NULL,
                    sport_category TEXT,
                    distance REAL,
                    duration INTEGER NOT NULL,
                    calories INTEGER,
                    heart_rate_avg REAL,
                    heart_rate_max INTEGER,
                    elevation_gain REAL,
                    power_avg REAL,
                    cadence_avg REAL,
                    training_load REAL,
                    perceived_exertion INTEGER,
                    has_gps BOOLEAN DEFAULT FALSE,
                    route_hash TEXT,
                    gps_data JSON,
                    source TEXT NOT NULL,
                    external_ids JSON,
                    raw_data JSON,
                    data_quality_score REAL DEFAULT 1.0,
                    ml_features_extracted BOOLEAN DEFAULT FALSE,
                    plugin_data JSON,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS biometrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date DATE NOT NULL,
                    metric_type TEXT NOT NULL,
                    value REAL NOT NULL,
                    unit TEXT NOT NULL,
                    source TEXT NOT NULL,
                    confidence REAL DEFAULT 1.0,
                    external_id TEXT,
                    UNIQUE(date, metric_type, source)
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sync_status (
                    source TEXT PRIMARY KEY,
                    last_sync TIMESTAMP,
                    status TEXT DEFAULT 'pending',
                    error_message TEXT,
                    sync_count INTEGER DEFAULT 0,
                    last_error TIMESTAMP
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS data_sources (
                    name TEXT PRIMARY KEY,
                    enabled BOOLEAN DEFAULT TRUE,
                    priority INTEGER DEFAULT 0,
                    sync_interval_hours INTEGER DEFAULT 24,
                    last_sync TIMESTAMP,
                    auth_token TEXT,
                    refresh_token TEXT,
                    expires_at TIMESTAMP
                )
            """)
            
            # Create indexes for performance
            conn.execute("CREATE INDEX IF NOT EXISTS idx_workouts_start_time ON workouts(start_time)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_workouts_source ON workouts(source)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_biometrics_date ON biometrics(date)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_biometrics_metric ON biometrics(metric_type)")
            
            conn.commit()
        
        logger.info("Database initialized", database_path=self.database_path)
    
    def _migrate_database_if_needed(self, conn):
        """Migrate database schema if needed"""
        try:
            # Check if workouts table exists and get its current schema
            cursor = conn.execute("PRAGMA table_info(workouts)")
            columns = cursor.fetchall()
            
            if not columns:
                # Table doesn't exist, no migration needed
                return
            
            # Check if this is the old schema (9 columns) or new schema (24 columns)
            if len(columns) == 9:  # Old schema
                logger.info("Migrating workouts table from old to new schema")
                
                # Create new table with new schema
                conn.execute("""
                    CREATE TABLE workouts_new (
                        workout_id TEXT PRIMARY KEY,
                        start_time TIMESTAMP NOT NULL,
                        end_time TIMESTAMP,
                        sport TEXT NOT NULL,
                        sport_category TEXT,
                        distance REAL,
                        duration INTEGER NOT NULL,
                        calories INTEGER,
                        heart_rate_avg REAL,
                        heart_rate_max INTEGER,
                        elevation_gain REAL,
                        power_avg REAL,
                        cadence_avg REAL,
                        training_load REAL,
                        perceived_exertion INTEGER,
                        has_gps BOOLEAN DEFAULT FALSE,
                        route_hash TEXT,
                        gps_data JSON,
                        source TEXT NOT NULL,
                        external_ids JSON,
                        raw_data JSON,
                        data_quality_score REAL DEFAULT 1.0,
                        ml_features_extracted BOOLEAN DEFAULT FALSE,
                        plugin_data JSON,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Copy data from old table to new table
                conn.execute("""
                    INSERT INTO workouts_new 
                    (workout_id, start_time, sport, sport_category, distance, duration, source, external_ids, raw_data, created_at)
                    SELECT workout_id, start_time, sport, sport_category, distance, duration, source, external_ids, raw_data, created_at
                    FROM workouts
                """)
                
                # Drop old table and rename new table
                conn.execute("DROP TABLE workouts")
                conn.execute("ALTER TABLE workouts_new RENAME TO workouts")
                
                # Recreate indexes
                conn.execute("CREATE INDEX IF NOT EXISTS idx_workouts_start_time ON workouts(start_time)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_workouts_source ON workouts(source)")
                
                logger.info("Workouts table migration completed")
                
        except Exception as e:
            logger.warning("Database migration failed", error=str(e))
    
    def _force_migrate_database(self):
        """Force migration by recreating the database schema"""
        try:
            logger.info("Force migrating database schema")
            
            with sqlite3.connect(self.database_path) as conn:
                # Drop existing tables
                conn.execute("DROP TABLE IF EXISTS workouts")
                conn.execute("DROP TABLE IF EXISTS biometrics")
                conn.execute("DROP TABLE IF EXISTS sync_status")
                conn.execute("DROP TABLE IF EXISTS data_sources")
                
                # Recreate with new schema
                conn.execute("""
                    CREATE TABLE workouts (
                        workout_id TEXT PRIMARY KEY,
                        start_time TIMESTAMP NOT NULL,
                        end_time TIMESTAMP,
                        sport TEXT NOT NULL,
                        sport_category TEXT,
                        distance REAL,
                        duration INTEGER NOT NULL,
                        calories INTEGER,
                        heart_rate_avg REAL,
                        heart_rate_max INTEGER,
                        elevation_gain REAL,
                        power_avg REAL,
                        cadence_avg REAL,
                        training_load REAL,
                        perceived_exertion INTEGER,
                        has_gps BOOLEAN DEFAULT FALSE,
                        route_hash TEXT,
                        gps_data JSON,
                        source TEXT NOT NULL,
                        external_ids JSON,
                        raw_data JSON,
                        data_quality_score REAL DEFAULT 1.0,
                        ml_features_extracted BOOLEAN DEFAULT FALSE,
                        plugin_data JSON,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                conn.execute("""
                    CREATE TABLE biometrics (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        date DATE NOT NULL,
                        metric_type TEXT NOT NULL,
                        value REAL NOT NULL,
                        unit TEXT NOT NULL,
                        source TEXT NOT NULL,
                        confidence REAL DEFAULT 1.0,
                        external_id TEXT,
                        UNIQUE(date, metric_type, source)
                    )
                """)
                
                conn.execute("""
                    CREATE TABLE sync_status (
                        source TEXT PRIMARY KEY,
                        last_sync TIMESTAMP,
                        status TEXT DEFAULT 'pending',
                        error_message TEXT,
                        sync_count INTEGER DEFAULT 0,
                        last_error TIMESTAMP
                    )
                """)
                
                conn.execute("""
                    CREATE TABLE data_sources (
                        name TEXT PRIMARY KEY,
                        enabled BOOLEAN DEFAULT TRUE,
                        priority INTEGER DEFAULT 0,
                        sync_interval_hours INTEGER DEFAULT 24,
                        last_sync TIMESTAMP,
                        auth_token TEXT,
                        refresh_token TEXT,
                        expires_at TIMESTAMP
                    )
                """)
                
                # Create indexes
                conn.execute("CREATE INDEX IF NOT EXISTS idx_workouts_start_time ON workouts(start_time)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_workouts_source ON workouts(source)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_biometrics_date ON biometrics(date)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_biometrics_metric ON biometrics(metric_type)")
                
                conn.commit()
                
            logger.info("Database schema migration completed")
            
        except Exception as e:
            logger.error("Force migration failed", error=str(e))
    
    def _load_sync_status(self):
        """Load existing sync status from database"""
        try:
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.execute("SELECT * FROM sync_status")
                for row in cursor.fetchall():
                    source, last_sync, status, error_message, sync_count, last_error = row
                    self.sync_status[source] = SyncStatus(
                        data_source=source,
                        last_sync=datetime.fromisoformat(last_sync) if last_sync else None,
                        status=status,
                        error_message=error_message,
                        sync_count=sync_count,
                        last_error=datetime.fromisoformat(last_error) if last_error else None
                    )
        except Exception as e:
            logger.warning("Could not load sync status", error=str(e))
    
    def register_connector(self, name: str, config: Dict[str, Any]) -> bool:
        """Register and initialize a connector"""
        try:
            connector = get_connector(name, config)
            self.connectors[name] = connector
            
            # Save connector configuration to database
            self._save_connector_config(name, config)
            
            # Initialize sync status if not exists
            if name not in self.sync_status:
                self.sync_status[name] = SyncStatus(data_source=name)
            
            logger.info("Connector registered", connector=name)
            return True
            
        except Exception as e:
            logger.error("Failed to register connector", connector=name, error=str(e))
            return False
    
    def _save_connector_config(self, name: str, config: Dict[str, Any]):
        """Save connector configuration to database"""
        try:
            with sqlite3.connect(self.database_path) as conn:
                # Store essential config (without sensitive tokens)
                safe_config = {
                    'name': name,
                    'enabled': True,
                    'priority': 0,
                    'sync_interval_hours': 24,
                    'last_sync': None
                }
                
                # Add non-sensitive config values
                for key, value in config.items():
                    if key not in ['access_token', 'refresh_token', 'client_secret']:
                        safe_config[key] = str(value)
                
                conn.execute("""
                    INSERT OR REPLACE INTO data_sources 
                    (name, enabled, priority, sync_interval_hours, last_sync)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    safe_config['name'],
                    safe_config['enabled'],
                    safe_config['priority'],
                    safe_config['sync_interval_hours'],
                    safe_config['last_sync']
                ))
                
                conn.commit()
                
        except Exception as e:
            logger.warning("Could not save connector config", connector=name, error=str(e))
    
    def _load_configured_connectors(self):
        """Load configured connectors from database"""
        try:
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.execute("SELECT name FROM data_sources WHERE enabled = TRUE")
                configured_sources = [row[0] for row in cursor.fetchall()]
                
                for source_name in configured_sources:
                    try:
                        # Get config from environment variables
                        config = self._get_connector_config_from_env(source_name)
                        if config:
                            # Re-register the connector
                            self.register_connector(source_name, config)
                    except Exception as e:
                        logger.warning("Could not load connector", connector=source_name, error=str(e))
                        
        except Exception as e:
            logger.warning("Could not load configured connectors", error=str(e))
    
    def _get_connector_config_from_env(self, source_name: str) -> Optional[Dict[str, Any]]:
        """Get connector configuration from environment variables"""
        import os
        
        if source_name == "strava":
            config = {
                "access_token": os.getenv("STRAVA_ACCESS_TOKEN"),
                "refresh_token": os.getenv("STRAVA_REFRESH_TOKEN"),
                "client_id": os.getenv("STRAVA_CLIENT_ID"),
                "client_secret": os.getenv("STRAVA_CLIENT_SECRET")
            }
            # Only return config if we have the essential credentials
            if config.get("client_id") and config.get("client_secret"):
                return config
        return None
    
    async def sync_all_sources(self, days: int = 30, sources: Optional[List[str]] = None) -> Dict[str, Any]:
        """Synchronize data from all configured sources"""
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        
        logger.info("Starting sync of all sources", start_date=start_date.isoformat(), end_date=end_date.isoformat())
        
        # Filter sources if specified
        sources_to_sync = sources if sources else list(self.connectors.keys())
        
        # Sync each source concurrently
        sync_tasks = []
        for source_name in sources_to_sync:
            if source_name in self.connectors:
                task = self._sync_source(source_name, start_date, end_date)
                sync_tasks.append(task)
        
        if not sync_tasks:
            logger.warning("No sources to sync")
            return {'error': 'No sources configured'}
        
        # Execute all syncs concurrently
        results = await asyncio.gather(*sync_tasks, return_exceptions=True)
        
        # Process results
        sync_summary = {
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'sources_synced': len(sources_to_sync),
            'successful_syncs': 0,
            'failed_syncs': 0,
            'total_workouts': 0,
            'total_biometrics': 0,
            'source_results': {}
        }
        
        all_workouts = []
        all_biometrics = []
        
        for i, result in enumerate(results):
            source_name = sources_to_sync[i]
            
            if isinstance(result, Exception):
                logger.error("Sync failed", source=source_name, error=str(result))
                sync_summary['failed_syncs'] += 1
                sync_summary['source_results'][source_name] = {
                    'success': False,
                    'error': str(result)
                }
                
                # Update sync status
                if source_name in self.sync_status:
                    self.sync_status[source_name].status = 'error'
                    self.sync_status[source_name].error_message = str(result)
                    self.sync_status[source_name].last_error = datetime.utcnow()
            else:
                sync_summary['successful_syncs'] += 1
                sync_summary['source_results'][source_name] = result
                
                if result['success']:
                    all_workouts.extend(result['workouts'])
                    all_biometrics.extend(result['biometrics'])
                    sync_summary['total_workouts'] += len(result['workouts'])
                    sync_summary['total_biometrics'] += len(result['biometrics'])
                
                # Update sync status
                if source_name in self.sync_status:
                    self.sync_status[source_name].status = 'active'
                    self.sync_status[source_name].error_message = None
        
        # Deduplicate data
        if all_workouts or all_biometrics:
            logger.info("Starting deduplication", 
                       workouts_count=len(all_workouts), 
                       biometrics_count=len(all_biometrics))
            
            # Deduplicate workouts
            if all_workouts:
                original_workout_count = len(all_workouts)
                deduped_workouts = self.dedup_engine.deduplicate_workouts(all_workouts)
                workout_stats = self.dedup_engine.get_deduplication_stats(original_workout_count, len(deduped_workouts))
                sync_summary['workout_deduplication'] = workout_stats
                all_workouts = deduped_workouts
            
            # Deduplicate biometrics
            if all_biometrics:
                original_biometric_count = len(all_biometrics)
                deduped_biometrics = self.dedup_engine.deduplicate_biometrics(all_biometrics)
                biometric_stats = self.dedup_engine.get_deduplication_stats(original_biometric_count, len(deduped_biometrics))
                sync_summary['biometric_deduplication'] = biometric_stats
                all_biometrics = deduped_biometrics
            
            # Store deduplicated data
            self._store_workouts(all_workouts)
            self._store_biometrics(all_biometrics)
        
        # Update sync status in database
        self._update_sync_status_db()
        
        logger.info("Sync completed", summary=sync_summary)
        return sync_summary
    
    async def _sync_source(self, source_name: str, start_date: date, end_date: date) -> Dict[str, Any]:
        """Synchronize data from a single source"""
        try:
            connector = self.connectors[source_name]
            result = await connector.sync_data(start_date, end_date)
            return result
            
        except Exception as e:
            logger.error("Source sync failed", source=source_name, error=str(e))
            return {
                'source': source_name,
                'workouts': [],
                'biometrics': [],
                                        'sync_time': datetime.now().isoformat(),
                'success': False,
                'error': str(e)
            }
    
    def _store_workouts(self, workouts: List[Workout]):
        """Store workouts in database"""
        if not workouts:
            return
        
        try:
            with sqlite3.connect(self.database_path) as conn:
                for workout in workouts:
                    conn.execute("""
                        INSERT OR REPLACE INTO workouts 
                        (workout_id, start_time, end_time, sport, sport_category, distance, duration, calories, 
                         heart_rate_avg, heart_rate_max, elevation_gain, power_avg, cadence_avg, training_load, 
                         perceived_exertion, has_gps, route_hash, gps_data, source, external_ids, raw_data, 
                         data_quality_score, ml_features_extracted, plugin_data)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        workout.workout_id,
                        workout.start_time.isoformat(),
                        workout.end_time.isoformat(),
                        workout.sport,
                        workout.sport_category,
                        workout.distance,
                        workout.duration,
                        workout.calories,
                        workout.heart_rate_avg,
                        workout.heart_rate_max,
                        workout.elevation_gain,
                        workout.power_avg,
                        workout.cadence_avg,
                        workout.training_load,
                        workout.perceived_exertion,
                        workout.has_gps,
                        workout.route_hash,
                        json.dumps(workout.gps_data) if workout.gps_data else None,
                        workout.data_source,
                        json.dumps(workout.external_ids),
                        json.dumps(workout.raw_data) if workout.raw_data else None,
                        workout.data_quality_score,
                        workout.ml_features_extracted,
                        json.dumps(workout.plugin_data)
                    ))
                conn.commit()
            
            logger.info("Workouts stored", count=len(workouts))
            
        except Exception as e:
            logger.error("Failed to store workouts", error=str(e))
    
    def _store_biometrics(self, biometrics: List[BiometricReading]):
        """Store biometric readings in database"""
        if not biometrics:
            return
        
        try:
            with sqlite3.connect(self.database_path) as conn:
                for reading in biometrics:
                    conn.execute("""
                        INSERT OR REPLACE INTO biometrics 
                        (date, metric_type, value, unit, source, confidence, external_id)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        reading.date_value.isoformat(),
                        reading.metric_type,
                        reading.value,
                        reading.unit,
                        reading.data_source,
                        reading.confidence,
                        reading.external_id
                    ))
                conn.commit()
            
            logger.info("Biometrics stored", count=len(biometrics))
            
        except Exception as e:
            logger.error("Failed to store biometrics", error=str(e))
    
    def _update_sync_status_db(self):
        """Update sync status in database"""
        try:
            with sqlite3.connect(self.database_path) as conn:
                for source, status in self.sync_status.items():
                    conn.execute("""
                        INSERT OR REPLACE INTO sync_status 
                        (source, last_sync, status, error_message, sync_count, last_error)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        source,
                        status.last_sync.isoformat() if status.last_sync else None,
                        status.status,
                        status.error_message,
                        status.sync_count,
                        status.last_error.isoformat() if status.last_error else None
                    ))
                conn.commit()
        except Exception as e:
            logger.error("Failed to update sync status", error=str(e))
    
    def get_workouts(self, start_date: Optional[date] = None, end_date: Optional[date] = None, 
                     source: Optional[str] = None, sport_category: Optional[str] = None) -> List[Workout]:
        """Retrieve workouts from database with optional filtering"""
        try:
            query = "SELECT * FROM workouts WHERE 1=1"
            params = []
            
            if start_date:
                query += " AND start_time >= ?"
                params.append(start_date.isoformat())
            
            if end_date:
                query += " AND start_time <= ?"
                params.append(end_date.isoformat())
            
            if source:
                query += " AND source = ?"
                params.append(source)
            
            if sport_category:
                query += " AND sport_category = ?"
                params.append(sport_category)
            
            query += " ORDER BY start_time DESC"
            
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.execute(query, params)
                workouts = []
                
                for row in cursor.fetchall():
                    # Handle both old and new schemas gracefully
                    try:
                        if len(row) == 9:  # Old schema
                            workout = Workout(
                                workout_id=row[0],
                                start_time=datetime.fromisoformat(row[1]),
                                end_time=None,  # Not available in old schema
                                sport=row[2],
                                sport_category=row[3],
                                distance=row[4],
                                duration=row[5],
                                calories=None,
                                heart_rate_avg=None,
                                heart_rate_max=None,
                                elevation_gain=None,
                                power_avg=None,
                                cadence_avg=None,
                                training_load=None,
                                perceived_exertion=None,
                                has_gps=False,
                                route_hash=None,
                                gps_data=None,
                                data_source=row[6],
                                external_ids=json.loads(row[7]) if row[7] else {},
                                raw_data=json.loads(row[8]) if row[8] else None,
                                data_quality_score=1.0,
                                ml_features_extracted=False,
                                plugin_data={}
                            )
                        else:  # New schema
                            workout = Workout(
                                workout_id=row[0],
                                start_time=datetime.fromisoformat(row[1]),
                                end_time=datetime.fromisoformat(row[2]) if row[2] else None,
                                sport=row[3],
                                sport_category=row[4],
                                distance=row[5],
                                duration=row[6],
                                calories=row[7],
                                heart_rate_avg=row[8],
                                heart_rate_max=row[9],
                                elevation_gain=row[10],
                                power_avg=row[11],
                                cadence_avg=row[12],
                                training_load=row[13],
                                perceived_exertion=row[14],
                                has_gps=bool(row[15]) if row[15] is not None else False,
                                route_hash=row[16],
                                gps_data=json.loads(row[17]) if row[17] else None,
                                data_source=row[18],
                                external_ids=json.loads(row[19]) if row[19] else {},
                                raw_data=json.loads(row[20]) if row[20] else None,
                                data_quality_score=row[21] if row[21] is not None else 1.0,
                                ml_features_extracted=bool(row[22]) if row[22] is not None else False,
                                plugin_data=json.loads(row[23]) if row[23] else {}
                            )
                    except Exception as e:
                        logger.warning("Failed to create workout from row", row=row, error=str(e))
                        continue
                    workouts.append(workout)
                
                return workouts
                
        except Exception as e:
            logger.error("Failed to retrieve workouts", error=str(e))
            return []
    
    def get_biometrics(self, start_date: Optional[date] = None, end_date: Optional[date] = None,
                       metric_type: Optional[str] = None, source: Optional[str] = None) -> List[BiometricReading]:
        """Retrieve biometric readings from database with optional filtering"""
        try:
            query = "SELECT * FROM biometrics WHERE 1=1"
            params = []
            
            if start_date:
                query += " AND date >= ?"
                params.append(start_date.isoformat())
            
            if end_date:
                query += " AND date <= ?"
                params.append(end_date.isoformat())
            
            if metric_type:
                query += " AND metric_type = ?"
                params.append(metric_type)
            
            if source:
                query += " AND source = ?"
                params.append(source)
            
            query += " ORDER BY date DESC"
            
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.execute(query, params)
                biometrics = []
                
                for row in cursor.fetchall():
                    reading = BiometricReading(
                        date_value=date.fromisoformat(row[1]),
                        metric_type=row[2],
                        value=row[3],
                        unit=row[4],
                        data_source=row[5],
                        confidence=row[6],
                        external_id=row[7]
                    )
                    biometrics.append(reading)
                
                return biometrics
                
        except Exception as e:
            logger.error("Failed to retrieve biometrics", error=str(e))
            return []
    
    def get_sync_status(self) -> Dict[str, Any]:
        """Get current sync status for all sources"""
        return {
            source: status.dict() for source, status in self.sync_status.items()
        }
    
    def get_workout_summary(self, start_date: Optional[date] = None, end_date: Optional[date] = None) -> WorkoutSummary:
        """Get summary statistics for workouts"""
        workouts = self.get_workouts(start_date, end_date)
        
        summary = WorkoutSummary()
        summary.total_workouts = len(workouts)
        
        if workouts:
            summary.total_duration = sum(w.duration for w in workouts)
            summary.total_distance = sum(w.distance or 0 for w in workouts)
            summary.total_calories = sum(w.calories or 0 for w in workouts)
            
            # Sport breakdown
            for workout in workouts:
                summary.sport_breakdown[workout.sport] = summary.sport_breakdown.get(workout.sport, 0) + 1
                summary.category_breakdown[workout.sport_category] = summary.category_breakdown.get(workout.sport_category, 0) + 1
                summary.source_breakdown[workout.data_source] = summary.source_breakdown.get(workout.data_source, 0) + 1
        
        return summary
    
    def get_biometric_summary(self, start_date: Optional[date] = None, end_date: Optional[date] = None) -> BiometricSummary:
        """Get summary statistics for biometric readings"""
        biometrics = self.get_biometrics(start_date, end_date)
        
        summary = BiometricSummary()
        summary.total_readings = len(biometrics)
        
        if biometrics:
            # Metrics by type
            for reading in biometrics:
                summary.metrics_by_type[reading.metric_type] = summary.metrics_by_type.get(reading.metric_type, 0) + 1
                
                if reading.metric_type not in summary.sources_by_type:
                    summary.sources_by_type[reading.metric_type] = {}
                summary.sources_by_type[reading.metric_type][reading.data_source] = summary.sources_by_type[reading.metric_type].get(reading.data_source, 0) + 1
        
        return summary
    
    def export_data(self, format: str = "parquet", output_path: Optional[str] = None) -> str:
        """Export data in specified format"""
        try:
            if format.lower() == "parquet":
                return self._export_parquet(output_path)
            elif format.lower() == "csv":
                return self._export_csv(output_path)
            else:
                raise ValueError(f"Unsupported export format: {format}")
                
        except Exception as e:
            logger.error("Export failed", format=format, error=str(e))
            raise
    
    def _export_parquet(self, output_path: Optional[str] = None) -> str:
        """Export data as Parquet files"""
        try:
            import pandas as pd
            
            if not output_path:
                output_path = f"data/export_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Export workouts
            workouts = self.get_workouts()
            if workouts:
                workout_data = []
                for w in workouts:
                    workout_data.append({
                        'workout_id': w.workout_id,
                        'start_time': w.start_time,
                        'sport': w.sport,
                        'sport_category': w.sport_category,
                        'distance': w.distance,
                        'duration': w.duration,
                        'source': w.data_source
                    })
                
                df_workouts = pd.DataFrame(workout_data)
                df_workouts.to_parquet(f"{output_path}_workouts.parquet", index=False)
            
            # Export biometrics
            biometrics = self.get_biometrics()
            if biometrics:
                biometric_data = []
                for b in biometrics:
                    biometric_data.append({
                        'date': b.date_value,
                        'metric_type': b.metric_type,
                        'value': b.value,
                        'unit': b.unit,
                        'source': b.data_source,
                        'confidence': b.confidence
                    })
                
                df_biometrics = pd.DataFrame(biometric_data)
                df_biometrics.to_parquet(f"{output_path}_biometrics.parquet", index=False)
            
            logger.info("Data exported to Parquet", output_path=output_path)
            return output_path
            
        except ImportError:
            raise ImportError("pandas is required for Parquet export")
    
    def _export_csv(self, output_path: Optional[str] = None) -> str:
        """Export data as CSV files"""
        try:
            import pandas as pd
            
            if not output_path:
                output_path = f"data/export_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Export workouts
            workouts = self.get_workouts()
            if workouts:
                workout_data = []
                for w in workouts:
                    workout_data.append({
                        'workout_id': w.workout_id,
                        'start_time': w.start_time,
                        'sport': w.sport,
                        'sport_category': w.sport_category,
                        'distance': w.distance,
                        'duration': w.duration,
                        'source': w.data_source
                    })
                
                df_workouts = pd.DataFrame(workout_data)
                df_workouts.to_csv(f"{output_path}_workouts.csv", index=False)
            
            # Export biometrics
            biometrics = self.get_biometrics()
            if biometrics:
                biometric_data = []
                for b in biometrics:
                    biometric_data.append({
                        'date': b.date_value,
                        'metric_type': b.metric_type,
                        'value': b.value,
                        'unit': b.unit,
                        'source': b.data_source,
                        'confidence': b.confidence
                    })
                
                df_biometrics = pd.DataFrame(biometric_data)
                df_biometrics.to_csv(f"{output_path}_biometrics.csv", index=False)
            
            logger.info("Data exported to CSV", output_path=output_path)
            return output_path
            
        except ImportError:
            raise ImportError("pandas is required for CSV export")
    
    def get_configured_sources(self) -> List[str]:
        """Get list of configured data sources"""
        return list(self.connectors.keys())
    
    def get_available_connectors(self) -> List[str]:
        """Get list of available connector types"""
        return list_available_connectors()
    
    def cleanup(self):
        """Clean up resources"""
        for connector in self.connectors.values():
            try:
                connector.cleanup()
            except Exception as e:
                logger.warning("Connector cleanup failed", connector=connector.source_name, error=str(e))
        
        logger.info("Data ingestion orchestrator cleaned up")
