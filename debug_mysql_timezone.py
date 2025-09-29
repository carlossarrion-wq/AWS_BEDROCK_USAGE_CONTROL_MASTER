#!/usr/bin/env python3
"""
Debug script to test MySQL timezone handling and datetime insertion
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
    'password': os.environ.get('DB_PASSWORD', ''),
    'charset': 'utf8mb4'
}

def debug_mysql_timezone():
    """Debug MySQL timezone handling"""
    try:
        # Connect to database
        connection = pymysql.connect(**DB_CONFIG)
        
        with connection.cursor() as cursor:
            print("=== MySQL Timezone Debug ===")
            
            # Check timezone settings
            cursor.execute("SELECT @@session.time_zone, @@global.time_zone, NOW() as current_time")
            timezone_info = cursor.fetchone()
            print(f"Session timezone: {timezone_info[0]}")
            print(f"Global timezone: {timezone_info[1]}")
            print(f"Current MySQL time: {timezone_info[2]}")
            
            # Test datetime insertion with the exact values from our JavaScript
            test_user = "test_debug_user"
            blocked_at = "2025-09-29 22:38:05"
            blocked_until = "2025-12-28 21:38:05"  # This should be 90 days later
            
            print(f"\n=== Testing Datetime Insertion ===")
            print(f"Inserting blocked_at: {blocked_at}")
            print(f"Inserting blocked_until: {blocked_until}")
            
            # Delete any existing test record
            cursor.execute("DELETE FROM bedrock_usage.user_blocking_status WHERE user_id = %s", (test_user,))
            
            # Insert test record with exact same query as JavaScript
            insert_query = """
                INSERT INTO bedrock_usage.user_blocking_status 
                (user_id, is_blocked, blocked_reason, blocked_at, blocked_until, created_at)
                VALUES (%s, 'Y', %s, %s, %s, %s)
            """
            
            cursor.execute(insert_query, [test_user, "TEST DEBUG", blocked_at, blocked_until, blocked_at])
            
            # Immediately query what was stored
            cursor.execute("""
                SELECT user_id, blocked_at, blocked_until, created_at
                FROM bedrock_usage.user_blocking_status 
                WHERE user_id = %s
            """, (test_user,))
            
            result = cursor.fetchone()
            if result:
                print(f"\n=== What was actually stored ===")
                print(f"User ID: {result[0]}")
                print(f"Blocked At: {result[1]}")
                print(f"Blocked Until: {result[2]}")
                print(f"Created At: {result[3]}")
                
                # Calculate duration
                if result[1] and result[2]:
                    duration = result[2] - result[1]
                    print(f"Stored Duration: {duration} ({duration.days} days)")
                    
                    # Compare with expected
                    expected_blocked_at = datetime.strptime(blocked_at, "%Y-%m-%d %H:%M:%S")
                    expected_blocked_until = datetime.strptime(blocked_until, "%Y-%m-%d %H:%M:%S")
                    expected_duration = expected_blocked_until - expected_blocked_at
                    print(f"Expected Duration: {expected_duration} ({expected_duration.days} days)")
                    
                    if duration.days != expected_duration.days:
                        print(f"❌ MISMATCH! Expected {expected_duration.days} days, got {duration.days} days")
                    else:
                        print(f"✅ Duration matches expected value")
            
            # Clean up test record
            cursor.execute("DELETE FROM bedrock_usage.user_blocking_status WHERE user_id = %s", (test_user,))
            
        connection.commit()
        connection.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    print("Debugging MySQL timezone handling...")
    debug_mysql_timezone()
