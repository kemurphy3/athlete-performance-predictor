#!/usr/bin/env python3
import sqlite3

def check_database():
    conn = sqlite3.connect('data/athlete_performance.db')
    cursor = conn.cursor()
    
    # List all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    
    print("Database tables:")
    for table in tables:
        table_name = table[0]
        print(f"\n{table_name}:")
        
        # Count rows
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"  Rows: {count}")
            
            # Show sample data if table has data
            if count > 0:
                cursor.execute(f"SELECT * FROM {table_name} LIMIT 1")
                sample = cursor.fetchone()
                if sample:
                    print(f"  Sample row: {sample}")
        except Exception as e:
            print(f"  Error: {e}")
    
    conn.close()

if __name__ == "__main__":
    check_database()
