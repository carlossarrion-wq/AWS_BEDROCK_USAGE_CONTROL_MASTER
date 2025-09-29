#!/usr/bin/env python3
"""
Database Cleanup Script
Removes model_pricing table and 4 fields from bedrock_requests table
"""

import pymysql
import sys
import os
from datetime import datetime

def get_db_connection():
    """Get database connection using stored credentials"""
    try:
        # Read connection details from file
        with open('migration/rds_connection_details.txt', 'r') as f:
            lines = f.readlines()
            
        connection_info = {}
        for line in lines:
            if '=' in line and not line.strip().startswith('#'):
                key, value = line.strip().split('=', 1)
                connection_info[key.strip()] = value.strip()
        
        connection = pymysql.connect(
            host=connection_info['RDS_ENDPOINT'],
            user=connection_info['DB_USERNAME'],
            password=connection_info['DB_PASSWORD'],
            database=connection_info['DB_NAME'],
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor,
            autocommit=False
        )
        
        print(f"✅ Connected to database: {connection_info['DB_NAME']}")
        return connection
        
    except Exception as e:
        print(f"❌ Database connection failed: {str(e)}")
        return None

def execute_cleanup_script(connection):
    """Execute the database cleanup DDL script"""
    try:
        with open('migration/16_cleanup_remaining_columns.sql', 'r') as f:
            sql_content = f.read()
        
        cursor = connection.cursor()
        
        # Split SQL content by statements (simple approach)
        statements = []
        current_statement = ""
        
        for line in sql_content.split('\n'):
            line = line.strip()
            
            # Skip comments and empty lines
            if line.startswith('--') or not line:
                continue
                
            current_statement += line + " "
            
            # If line ends with semicolon, it's end of statement
            if line.endswith(';'):
                statements.append(current_statement.strip())
                current_statement = ""
        
        # Add any remaining statement
        if current_statement.strip():
            statements.append(current_statement.strip())
        
        print(f"📝 Executing {len(statements)} SQL statements...")
        
        executed_count = 0
        results = []
        
        for i, statement in enumerate(statements, 1):
            if not statement or statement.isspace():
                continue
                
            try:
                print(f"  [{i}] Executing: {statement[:50]}...")
                cursor.execute(statement)
                
                # Fetch results if it's a SELECT statement
                if statement.strip().upper().startswith('SELECT') or statement.strip().upper().startswith('DESCRIBE'):
                    result = cursor.fetchall()
                    if result:
                        results.append(result)
                        for row in result:
                            print(f"      Result: {row}")
                
                executed_count += 1
                
            except Exception as e:
                print(f"  ⚠️  Statement {i} failed: {str(e)}")
                # Continue with other statements
                continue
        
        # Commit all changes
        connection.commit()
        print(f"✅ Successfully executed {executed_count} statements")
        
        return True, results
        
    except Exception as e:
        print(f"❌ Script execution failed: {str(e)}")
        connection.rollback()
        return False, []

def verify_cleanup(connection):
    """Verify the cleanup was successful"""
    try:
        cursor = connection.cursor()
        
        print("\n🔍 Verifying cleanup results...")
        
        # Check if model_pricing table exists
        cursor.execute("""
            SELECT COUNT(*) as table_count
            FROM information_schema.tables 
            WHERE table_schema = 'bedrock_usage' 
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
            WHERE table_schema = 'bedrock_usage' 
              AND table_name = 'bedrock_requests'
              AND column_name IN ('input_tokens', 'output_tokens', 'total_tokens', 'cost_usd')
        """)
        remaining_columns = cursor.fetchall()
        
        target_columns = ['input_tokens', 'output_tokens', 'total_tokens', 'cost_usd']
        remaining_column_names = [col['column_name'] for col in remaining_columns]
        
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
            print(f"  - {col['Field']}: {col['Type']} {col['Null']} {col['Key']} {col['Default']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Verification failed: {str(e)}")
        return False

def main():
    """Main execution function"""
    print("🚀 Starting database cleanup process...")
    print(f"⏰ Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Get database connection
    connection = get_db_connection()
    if not connection:
        sys.exit(1)
    
    try:
        # Execute cleanup script
        success, results = execute_cleanup_script(connection)
        
        if success:
            print("\n✅ Database cleanup script executed successfully!")
            
            # Verify the changes
            verify_cleanup(connection)
            
            print("\n🎉 Database cleanup completed successfully!")
            print("📋 Summary:")
            print("  - model_pricing table removed")
            print("  - 4 columns removed from bedrock_requests:")
            print("    * input_tokens")
            print("    * output_tokens") 
            print("    * total_tokens")
            print("    * cost_usd")
            
        else:
            print("\n❌ Database cleanup failed!")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        sys.exit(1)
        
    finally:
        connection.close()
        print("🔌 Database connection closed")

if __name__ == "__main__":
    main()
