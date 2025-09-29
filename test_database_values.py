#!/usr/bin/env python3
"""
Test script to check what values are actually stored in the database
for the blocking functionality.
"""

import pymysql
import os
from datetime import datetime

# Database configuration
DB_CONFIG = {
    'host': 'bedrock-usage-mysql.czuimyk2qu10.eu-west-1.rds.amazonaws.com',
    'port': 3306,
    'database': 'bedrock_usage',
    'user': 'admin',
    'password': os.environ.get('DB_PASSWORD', ''),  # You'll need to set this
    'charset': 'utf8mb4'
}

def test_database_values():
    """Check what values are actually stored in the database"""
    try:
        # Connect to database
        connection = pymysql.connect(**DB_CONFIG)
        
        with connection.cursor() as cursor:
            # Check current timezone settings
            cursor.execute("SELECT @@session.time_zone, @@global.time_zone, NOW() as current_time")
            timezone_info = cursor.fetchone()
            print(f"Database timezone info: {timezone_info}")
            
            # Check the most recent blocking record for delta_001
            cursor.execute("""
                SELECT user_id, blocked_at, blocked_until, created_at, updated_at
                FROM bedrock_usage.user_blocking_status 
                WHERE user_id = 'delta_001'
                ORDER BY updated_at DESC 
                LIMIT 1
            """)
            
            result = cursor.fetchone()
            if result:
                print(f"\nMost recent blocking record for delta_001:")
                print(f"User ID: {result[0]}")
                print(f"Blocked At: {result[1]}")
                print(f"Blocked Until: {result[2]}")
                print(f"Created At: {result[3]}")
                print(f"Updated At: {result[4]}")
                
                # Calculate the difference between blocked_at and blocked_until
                if result[1] and result[2]:
                    blocked_at = result[1]
                    blocked_until = result[2]
                    duration = blocked_until - blocked_at
                    print(f"Duration: {duration} ({duration.days} days)")
            else:
                print("No blocking record found for delta_001")
            
            # Check recent audit log entries
            cursor.execute("""
                SELECT user_id, operation_timestamp, blocked_until, operation_reason
                FROM bedrock_usage.blocking_audit_log 
                WHERE user_id = 'delta_001' 
                ORDER BY operation_timestamp DESC 
                LIMIT 3
            """)
            
            audit_results = cursor.fetchall()
            print(f"\nRecent audit log entries for delta_001:")
            for i, audit in enumerate(audit_results):
                print(f"  {i+1}. Timestamp: {audit[1]}, Blocked Until: {audit[2]}, Reason: {audit[3]}")
        
        connection.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    print("Testing database values...")
    test_database_values()
