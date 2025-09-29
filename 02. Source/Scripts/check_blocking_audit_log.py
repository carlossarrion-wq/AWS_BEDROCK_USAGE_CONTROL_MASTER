#!/usr/bin/env python3

import pymysql
import json
from datetime import datetime

def check_blocking_audit_log():
    """Check the blocking_audit_log table for recent entries"""
    
    # Database connection parameters
    connection_params = {
        'host': 'bedrock-usage-mysql.czuimyk2qu10.eu-west-1.rds.amazonaws.com',
        'user': 'admin',
        'password': 'BedrockUsage2024!',
        'database': 'bedrock_usage',
        'charset': 'utf8mb4',
        'cursorclass': pymysql.cursors.DictCursor
    }
    
    try:
        # Connect to database
        connection = pymysql.connect(**connection_params)
        print("✅ Successfully connected to MySQL database")
        
        with connection.cursor() as cursor:
            # Check if blocking_audit_log table exists
            cursor.execute("SHOW TABLES LIKE 'blocking_audit_log'")
            table_exists = cursor.fetchone()
            
            if not table_exists:
                print("❌ blocking_audit_log table does not exist")
                return
            
            print("✅ blocking_audit_log table exists")
            
            # Get table structure
            cursor.execute("DESCRIBE blocking_audit_log")
            columns = cursor.fetchall()
            print("\n📋 Table structure:")
            for col in columns:
                print(f"  - {col['Field']}: {col['Type']} ({col['Null']}, {col['Key']})")
            
            # Check recent entries
            cursor.execute("""
                SELECT * FROM blocking_audit_log 
                ORDER BY created_at DESC 
                LIMIT 10
            """)
            
            recent_entries = cursor.fetchall()
            print(f"\n📊 Found {len(recent_entries)} recent entries in blocking_audit_log:")
            
            if recent_entries:
                for i, entry in enumerate(recent_entries, 1):
                    print(f"\n{i}. Entry ID: {entry.get('id', 'N/A')}")
                    print(f"   User ID: {entry.get('user_id', 'N/A')}")
                    print(f"   Action: {entry.get('action', 'N/A')}")
                    print(f"   Reason: {entry.get('reason', 'N/A')}")
                    print(f"   Created: {entry.get('created_at', 'N/A')}")
            else:
                print("   No entries found")
            
            # Check user_blocking_status table
            cursor.execute("SHOW TABLES LIKE 'user_blocking_status'")
            blocking_table_exists = cursor.fetchone()
            
            if blocking_table_exists:
                print("\n✅ user_blocking_status table exists")
                
                cursor.execute("""
                    SELECT * FROM user_blocking_status 
                    WHERE user_id = 'sap_003'
                    ORDER BY updated_at DESC 
                    LIMIT 5
                """)
                
                blocking_entries = cursor.fetchall()
                print(f"\n📊 Found {len(blocking_entries)} entries for sap_003 in user_blocking_status:")
                
                for i, entry in enumerate(blocking_entries, 1):
                    print(f"\n{i}. User: {entry.get('user_id', 'N/A')}")
                    print(f"   Blocked: {entry.get('is_blocked', 'N/A')}")
                    print(f"   Reason: {entry.get('blocked_reason', 'N/A')}")
                    print(f"   Blocked At: {entry.get('blocked_at', 'N/A')}")
                    print(f"   Blocked Until: {entry.get('blocked_until', 'N/A')}")
                    print(f"   Updated: {entry.get('updated_at', 'N/A')}")
            else:
                print("❌ user_blocking_status table does not exist")
                
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    finally:
        if 'connection' in locals():
            connection.close()
            print("\n🔒 Database connection closed")

if __name__ == "__main__":
    check_blocking_audit_log()
