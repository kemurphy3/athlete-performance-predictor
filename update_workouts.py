#!/usr/bin/env python3
import sqlite3

def update_workouts():
    conn = sqlite3.connect('data/athlete_performance.db')
    cursor = conn.cursor()
    
    # Update workouts without athlete_id to use 'default'
    cursor.execute("UPDATE workouts SET athlete_id = 'default' WHERE athlete_id IS NULL")
    updated_count = cursor.rowcount
    
    conn.commit()
    print(f"Updated {updated_count} workouts with default athlete_id")
    
    # Verify the update
    cursor.execute("SELECT COUNT(*) FROM workouts WHERE athlete_id = 'default'")
    default_count = cursor.fetchone()[0]
    print(f"Total workouts with default athlete_id: {default_count}")
    
    conn.close()

if __name__ == "__main__":
    update_workouts()
