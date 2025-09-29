#!/bin/bash

# Fixed deployment method for stored procedure using Python and pymysql
# Uses the pymysql-compatible SQL file without DELIMITER statements

echo "🔧 Deploying stored procedure using Python pymysql (fixed version)..."

# Create a Python script to execute the SQL
cat > deploy_procedure_fixed.py << 'PYTHON_EOF'
import pymysql
import sys

# Database connection details
DB_HOST = "bedrock-usage-mysql.czuimyk2qu10.eu-west-1.rds.amazonaws.com"
DB_USER = "admin"
DB_PASSWORD = "BedrockUsage2024!"
DB_NAME = "bedrock_usage"

def deploy_stored_procedure():
    try:
        # Read the pymysql-compatible SQL file
        with open('13_update_stored_procedures_for_request_limits_pymysql.sql', 'r') as file:
            sql_content = file.read()
        
        # Connect to database
        print("🔌 Connecting to MySQL database...")
        connection = pymysql.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        
        with connection.cursor() as cursor:
            # Split SQL content by semicolons and execute each statement
            statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip() and not stmt.strip().startswith('--')]
            
            for i, statement in enumerate(statements):
                if statement and not statement.startswith('--'):
                    print(f"📝 Executing statement {i+1}/{len(statements)}...")
                    print(f"Statement preview: {statement[:100]}...")
                    cursor.execute(statement)
            
            connection.commit()
            print("✅ Stored procedure deployed successfully!")
            
            # Test the procedure
            print("🧪 Testing the procedure with user 'sap_003'...")
            cursor.execute("CALL CheckUserLimits('sap_003')")
            result = cursor.fetchone()
            print(f"Test result: {result}")
            
    except Exception as e:
        print(f"❌ Error deploying stored procedure: {e}")
        sys.exit(1)
    finally:
        if 'connection' in locals():
            connection.close()

if __name__ == "__main__":
    deploy_stored_procedure()
PYTHON_EOF

# Execute the deployment
echo "🚀 Running stored procedure deployment..."
python3 deploy_procedure_fixed.py

# Clean up
rm deploy_procedure_fixed.py

echo "🎉 Deployment completed!"
