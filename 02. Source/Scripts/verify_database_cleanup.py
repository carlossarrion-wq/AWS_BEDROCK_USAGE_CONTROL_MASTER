#!/usr/bin/env python3
"""
Verify Database Cleanup
Check that model_pricing table and 4 fields from bedrock_requests were removed
"""

import pymysql
import sys

def get_db_connection():
    """Get database connection using stored credentials"""
    try:
        with open('migration/rds_connection_details.txt', 'r') as f:
            lines = f.readlines()
            
        connection_info = {}
        for line in lines:
            if ':' in line:
                key, value = line.strip().split(':', 1)
                connection_info[key.strip()] = value.strip()
        
        connection = pymysql.connect(
            host=connection_info['Host'],
            user=connection_info['Username'],
            password=connection_info['Password'],
            database=connection_info['Database'],
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        
        print(f"✅ Connected to database: {connection_info['Database']}")
        return connection
        
    except Exception as e:
        print(f"❌ Database connection failed: {str(e)}")
        return None

def verify_cleanup(connection):
    """Verify the cleanup was successful"""
    try:
        cursor = connection.cursor()
        
        print("\n🔍 Verifying database cleanup results...")
        
        # Check if model_pricing table exists
        cursor.execute("""
            SELECT COUNT(*) as table_count
            FROM information_schema.tables 
            WHERE table_schema = 'bedrock_usage_control' 
              AND table_name = 'model_pricing'
        """)
        model_pricing_result = cursor.fetchone()
        
        if model_pricing_result['table_count'] == 0:
            print("✅ model_pricing table: REMOVED")
        else:
            print("❌ model_pricing table: STILL EXISTS")
        
        # Check bedrock_requests columns
        cursor.execute("""
            SELECT column_name
            FROM information_schema.columns 
            WHERE table_schema = 'bedrock_usage_control' 
              AND table_name = 'bedrock_requests'
              AND column_name IN ('input_tokens', 'output_tokens', 'total_tokens', 'cost_usd')
        """)
        remaining_columns = cursor.fetchall()
        
        target_columns = ['input_tokens', 'output_tokens', 'total_tokens', 'cost_usd']
        remaining_column_names = [col['column_name'] for col in remaining_columns]
        
        print("\n📋 Column removal status:")
        for col in target_columns:
            if col in remaining_column_names:
                print(f"❌ {col}: STILL EXISTS")
            else:
                print(f"✅ {col}: REMOVED")
        
        # Show current bedrock_requests structure
        print("\n📋 Current bedrock_requests table structure:")
        cursor.execute("DESCRIBE bedrock_requests")
        columns = cursor.fetchall()
        
        for col in columns:
            print(f"  - {col['Field']}: {col['Type']}")
        
        # Summary
        cleanup_success = (model_pricing_result['table_count'] == 0 and 
                          len(remaining_column_names) == 0)
        
        if cleanup_success:
            print("\n🎉 DATABASE CLEANUP COMPLETED SUCCESSFULLY!")
            print("📋 Summary:")
            print("  ✅ model_pricing table removed")
            print("  ✅ All 4 columns removed from bedrock_requests:")
            print("    • input_tokens")
            print("    • output_tokens") 
            print("    • total_tokens")
            print("    • cost_usd")
        else:
            print("\n⚠️  DATABASE CLEANUP INCOMPLETE")
            if model_pricing_result['table_count'] > 0:
                print("  ❌ model_pricing table still exists")
            if remaining_column_names:
                print(f"  ❌ {len(remaining_column_names)} columns still exist: {remaining_column_names}")
        
        return cleanup_success
        
    except Exception as e:
        print(f"❌ Verification failed: {str(e)}")
        return False

def main():
    """Main execution function"""
    print("🔍 Verifying database cleanup...")
    
    connection = get_db_connection()
    if not connection:
        sys.exit(1)
    
    try:
        success = verify_cleanup(connection)
        if success:
            print("\n✅ Verification completed - cleanup successful!")
        else:
            print("\n❌ Verification failed - cleanup incomplete!")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        sys.exit(1)
        
    finally:
        connection.close()

if __name__ == "__main__":
    main()
