import json
import pymysql
import os
import logging
from datetime import datetime, date
from decimal import Decimal
from typing import Dict, List, Any, Optional

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Database configuration from environment variables
DB_CONFIG = {
    'host': os.environ.get('DB_HOST', 'bedrock-usage-mysql.czuimyk2qu10.eu-west-1.rds.amazonaws.com'),
    'port': 3306,
    'database': os.environ.get('DB_NAME', 'bedrock_usage'),
    'user': os.environ.get('DB_USER', 'admin'),
    'password': os.environ.get('DB_PASSWORD'),
    'charset': 'utf8mb4',
    'connect_timeout': 10,
    'read_timeout': 30,
    'write_timeout': 30
}

def get_db_connection():
    """Create and return a database connection"""
    try:
        connection = pymysql.connect(
            host=DB_CONFIG['host'],
            port=DB_CONFIG['port'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            database=DB_CONFIG['database'],
            charset=DB_CONFIG['charset'],
            connect_timeout=DB_CONFIG['connect_timeout'],
            read_timeout=DB_CONFIG['read_timeout'],
            write_timeout=DB_CONFIG['write_timeout'],
            cursorclass=pymysql.cursors.DictCursor,
            autocommit=True
        )
        logger.info("✅ Successfully connected to MySQL database")
        return connection
    except Exception as e:
        logger.error(f"❌ Failed to connect to MySQL database: {str(e)}")
        raise

def json_serializer(obj):
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    elif isinstance(obj, Decimal):
        return float(obj)
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

def execute_query(connection, query: str, params: List[Any] = None) -> List[Dict[str, Any]]:
    """Execute a SQL query and return results"""
    try:
        with connection.cursor() as cursor:
            logger.info(f"🔍 Executing query: {query[:100]}...")
            
            # Convert ? placeholders to %s for PyMySQL compatibility
            if params and '?' in query:
                query = query.replace('?', '%s')
                logger.info(f"🔄 Converted query placeholders from ? to %s")
            
            if params:
                cursor.execute(query, params)
                logger.info(f"📝 Query parameters: {params}")
            else:
                cursor.execute(query)
            
            # For SELECT queries, fetch results
            if query.strip().upper().startswith('SELECT'):
                results = cursor.fetchall()
                logger.info(f"📊 Query returned {len(results)} rows")
                return results
            else:
                # For INSERT/UPDATE/DELETE queries, return affected rows
                affected_rows = cursor.rowcount
                logger.info(f"📝 Query affected {affected_rows} rows")
                return [{'affected_rows': affected_rows}]
                
    except Exception as e:
        logger.error(f"❌ Error executing query: {str(e)}")
        raise

def lambda_handler(event, context):
    """
    Lambda function handler for MySQL query execution
    
    Expected event structure:
    {
        "action": "query",
        "query": "SELECT * FROM table WHERE column = ?",
        "params": ["value1", "value2"]
    }
    """
    
    logger.info(f"🚀 MySQL Query Executor Lambda started")
    logger.info(f"📥 Received event: {json.dumps(event, default=str)}")
    
    connection = None
    
    try:
        # Validate input
        if not isinstance(event, dict):
            raise ValueError("Event must be a dictionary")
        
        action = event.get('action')
        if action != 'query':
            raise ValueError(f"Unsupported action: {action}")
        
        query = event.get('query')
        if not query:
            raise ValueError("Query is required")
        
        params = event.get('params', [])
        if not isinstance(params, list):
            raise ValueError("Params must be a list")
        
        # Connect to database
        connection = get_db_connection()
        
        # Execute query
        results = execute_query(connection, query, params)
        
        # Convert results to JSON-serializable format
        serialized_results = json.loads(json.dumps(results, default=json_serializer))
        
        # Return success response
        response = {
            'statusCode': 200,
            'data': serialized_results,
            'message': f'Query executed successfully, returned {len(results)} rows'
        }
        
        logger.info(f"✅ Query execution completed successfully")
        return response
        
    except Exception as e:
        error_message = f"Error executing MySQL query: {str(e)}"
        logger.error(f"❌ {error_message}")
        
        return {
            'statusCode': 500,
            'errorMessage': error_message,
            'data': []
        }
        
    finally:
        # Clean up database connection
        if connection:
            try:
                connection.close()
                logger.info("🔌 Database connection closed")
            except Exception as e:
                logger.error(f"Error closing database connection: {str(e)}")

def test_connection():
    """Test function to verify database connectivity"""
    try:
        connection = get_db_connection()
        
        # Test with a simple query
        test_query = "SELECT 1 as test_value, NOW() as current_time"
        results = execute_query(connection, test_query)
        
        logger.info(f"🧪 Connection test successful: {results}")
        
        connection.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ Connection test failed: {str(e)}")
        return False

# For local testing
if __name__ == "__main__":
    # Test the connection
    print("Testing MySQL connection...")
    if test_connection():
        print("✅ Connection test passed")
    else:
        print("❌ Connection test failed")
    
    # Test query execution
    test_event = {
        "action": "query",
        "query": "SELECT COUNT(*) as total_requests FROM bedrock_requests WHERE request_timestamp >= DATE_SUB(NOW(), INTERVAL 24 HOUR)",
        "params": []
    }
    
    print("\nTesting query execution...")
    result = lambda_handler(test_event, None)
    print(f"Result: {json.dumps(result, indent=2, default=str)}")
