#!/usr/bin/env python3
"""
Test Enhanced Blocking Functionality
Comprehensive test suite for the enhanced AWS Bedrock blocking system
"""

import pymysql
import json
import boto3
from datetime import datetime, timedelta
import sys
import time

# Database connection parameters
RDS_HOST = "bedrock-usage-mysql.czuimyk2qu10.eu-west-1.rds.amazonaws.com"
RDS_USER = "admin"
RDS_PASSWORD = "BedrockUsage2024!"
RDS_DB = "bedrock_usage"

# AWS clients
lambda_client = boto3.client('lambda', region_name='eu-west-1')
iam_client = boto3.client('iam')

def get_db_connection():
    """Get database connection"""
    return pymysql.connect(
        host=RDS_HOST,
        user=RDS_USER,
        password=RDS_PASSWORD,
        database=RDS_DB,
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True
    )

def print_test_header(test_name):
    """Print formatted test header"""
    print(f"\n{'='*60}")
    print(f"🧪 TEST: {test_name}")
    print(f"{'='*60}")

def print_success(message):
    """Print success message"""
    print(f"✅ {message}")

def print_error(message):
    """Print error message"""
    print(f"❌ {message}")

def print_info(message):
    """Print info message"""
    print(f"ℹ️  {message}")

def setup_test_user(connection, user_id, daily_limit=5, administrative_safe='N'):
    """Setup test user with specific limits"""
    with connection.cursor() as cursor:
        # Delete existing user data
        cursor.execute("DELETE FROM user_blocking_status WHERE user_id = %s", [user_id])
        cursor.execute("DELETE FROM blocking_audit_log WHERE user_id = %s", [user_id])
        cursor.execute("DELETE FROM bedrock_requests WHERE user_id = %s", [user_id])
        cursor.execute("DELETE FROM user_limits WHERE user_id = %s", [user_id])
        
        # Create test user with specific limits
        cursor.execute("""
            INSERT INTO user_limits 
            (user_id, team, person, daily_request_limit, monthly_request_limit, administrative_safe, created_at)
            VALUES (%s, 'test_team', 'Test Person', %s, 1000, %s, NOW())
        """, [user_id, daily_limit, administrative_safe])
        
        print_info(f"Test user {user_id} created with daily_limit={daily_limit}, admin_safe={administrative_safe}")

def simulate_bedrock_requests(user_id, count):
    """Simulate multiple Bedrock requests for a user"""
    print_info(f"Simulating {count} Bedrock requests for user {user_id}")
    
    for i in range(count):
        payload = {
            "detail": {
                "eventName": "InvokeModel",
                "userIdentity": {
                    "arn": f"arn:aws:iam::701055077130:user/{user_id}"
                },
                "requestParameters": {
                    "modelId": "anthropic.claude-3-5-sonnet-20240620-v1:0"
                },
                "sourceIPAddress": "127.0.0.1",
                "userAgent": "test-agent",
                "requestID": f"test-request-{user_id}-{i+1}",
                "eventTime": datetime.utcnow().isoformat() + "Z",
                "awsRegion": "eu-west-1"
            }
        }
        
        try:
            response = lambda_client.invoke(
                FunctionName='bedrock-realtime-logger-fixed',
                Payload=json.dumps(payload)
            )
            
            response_payload = json.loads(response['Payload'].read())
            if response['StatusCode'] == 200:
                print_info(f"  Request {i+1}/{count}: SUCCESS")
            else:
                print_error(f"  Request {i+1}/{count}: FAILED - {response_payload}")
                
        except Exception as e:
            print_error(f"  Request {i+1}/{count}: ERROR - {str(e)}")
        
        # Small delay between requests
        time.sleep(0.5)

def check_user_blocking_status(connection, user_id):
    """Check user's blocking status in database"""
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT is_blocked, blocked_reason, blocked_at, blocked_until, requests_at_blocking
            FROM user_blocking_status 
            WHERE user_id = %s
        """, [user_id])
        
        result = cursor.fetchone()
        if result:
            print_info(f"Blocking Status for {user_id}:")
            print_info(f"  - Is Blocked: {result['is_blocked']}")
            print_info(f"  - Reason: {result['blocked_reason']}")
            print_info(f"  - Blocked At: {result['blocked_at']}")
            print_info(f"  - Blocked Until: {result['blocked_until']}")
            print_info(f"  - Requests at Blocking: {result['requests_at_blocking']}")
            return result['is_blocked'] == 'Y'
        else:
            print_info(f"No blocking status found for {user_id}")
            return False

def check_audit_log(connection, user_id):
    """Check audit log entries for user"""
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT operation_type, operation_reason, performed_by, performed_at
            FROM blocking_audit_log 
            WHERE user_id = %s
            ORDER BY performed_at DESC
            LIMIT 5
        """, [user_id])
        
        results = cursor.fetchall()
        if results:
            print_info(f"Recent audit log entries for {user_id}:")
            for entry in results:
                print_info(f"  - {entry['operation_type']}: {entry['operation_reason']} by {entry['performed_by']} at {entry['performed_at']}")
        else:
            print_info(f"No audit log entries found for {user_id}")

def check_iam_policy(user_id):
    """Check IAM policy for user"""
    try:
        policy_name = f"{user_id}_BedrockPolicy"
        response = iam_client.get_user_policy(UserName=user_id, PolicyName=policy_name)
        
        policy_doc = response['PolicyDocument']
        has_deny = any(stmt.get('Effect') == 'Deny' for stmt in policy_doc['Statement'])
        
        print_info(f"IAM Policy for {user_id}:")
        print_info(f"  - Policy exists: YES")
        print_info(f"  - Has DENY statement: {has_deny}")
        
        return has_deny
        
    except iam_client.exceptions.NoSuchEntityException:
        print_info(f"IAM Policy for {user_id}: NOT FOUND")
        return False
    except Exception as e:
        print_error(f"Error checking IAM policy for {user_id}: {str(e)}")
        return False

def test_normal_blocking():
    """Test 1: Normal user blocking when limits are exceeded"""
    print_test_header("Normal User Blocking")
    
    connection = get_db_connection()
    test_user = "test_blocking_user"
    
    try:
        # Setup test user with low limit
        setup_test_user(connection, test_user, daily_limit=3, administrative_safe='N')
        
        # Simulate requests up to limit
        print_info("Phase 1: Simulate requests within limit")
        simulate_bedrock_requests(test_user, 2)
        
        # Check status - should not be blocked
        is_blocked = check_user_blocking_status(connection, test_user)
        if not is_blocked:
            print_success("User is NOT blocked within limits - CORRECT")
        else:
            print_error("User is blocked within limits - INCORRECT")
            return False
        
        # Simulate request that exceeds limit
        print_info("Phase 2: Simulate request that exceeds limit")
        simulate_bedrock_requests(test_user, 2)  # This should trigger blocking
        
        # Check status - should be blocked
        is_blocked = check_user_blocking_status(connection, test_user)
        if is_blocked:
            print_success("User is BLOCKED after exceeding limits - CORRECT")
        else:
            print_error("User is NOT blocked after exceeding limits - INCORRECT")
            return False
        
        # Check audit log
        check_audit_log(connection, test_user)
        
        # Check IAM policy
        has_deny = check_iam_policy(test_user)
        if has_deny:
            print_success("IAM DENY policy created - CORRECT")
        else:
            print_error("IAM DENY policy NOT created - INCORRECT")
            return False
        
        print_success("Normal blocking test PASSED")
        return True
        
    except Exception as e:
        print_error(f"Normal blocking test FAILED: {str(e)}")
        return False
    finally:
        connection.close()

def test_administrative_protection():
    """Test 2: Administrative protection prevents blocking"""
    print_test_header("Administrative Protection")
    
    connection = get_db_connection()
    test_user = "test_admin_protected_user"
    
    try:
        # Setup test user with administrative protection
        setup_test_user(connection, test_user, daily_limit=2, administrative_safe='Y')
        
        # Simulate requests that would normally trigger blocking
        print_info("Simulating requests that exceed limit for admin-protected user")
        simulate_bedrock_requests(test_user, 5)  # Way over limit
        
        # Check status - should NOT be blocked due to admin protection
        is_blocked = check_user_blocking_status(connection, test_user)
        if not is_blocked:
            print_success("Admin-protected user is NOT blocked - CORRECT")
        else:
            print_error("Admin-protected user is blocked - INCORRECT")
            return False
        
        # Check that no audit log entries were created
        check_audit_log(connection, test_user)
        
        # Check that no IAM deny policy was created
        has_deny = check_iam_policy(test_user)
        if not has_deny:
            print_success("No IAM DENY policy created for admin-protected user - CORRECT")
        else:
            print_error("IAM DENY policy created for admin-protected user - INCORRECT")
            return False
        
        print_success("Administrative protection test PASSED")
        return True
        
    except Exception as e:
        print_error(f"Administrative protection test FAILED: {str(e)}")
        return False
    finally:
        connection.close()

def test_automatic_unblocking():
    """Test 3: Automatic unblocking when block expires"""
    print_test_header("Automatic Unblocking")
    
    connection = get_db_connection()
    test_user = "test_unblock_user"
    
    try:
        # Setup test user
        setup_test_user(connection, test_user, daily_limit=2, administrative_safe='N')
        
        # First, trigger blocking
        print_info("Phase 1: Trigger blocking")
        simulate_bedrock_requests(test_user, 3)
        
        # Verify user is blocked
        is_blocked = check_user_blocking_status(connection, test_user)
        if not is_blocked:
            print_error("User should be blocked but isn't")
            return False
        
        # Manually set block expiration to past (simulate expired block)
        print_info("Phase 2: Simulate expired block")
        with connection.cursor() as cursor:
            past_time = datetime.now() - timedelta(hours=1)
            cursor.execute("""
                UPDATE user_blocking_status 
                SET blocked_until = %s 
                WHERE user_id = %s
            """, [past_time, test_user])
        
        # Simulate a new request - this should trigger automatic unblocking
        print_info("Phase 3: Simulate request after block expiration")
        simulate_bedrock_requests(test_user, 1)
        
        # Check if user was automatically unblocked
        is_blocked = check_user_blocking_status(connection, test_user)
        if not is_blocked:
            print_success("User was automatically unblocked - CORRECT")
        else:
            print_error("User was NOT automatically unblocked - INCORRECT")
            return False
        
        # Check audit log for unblock entry
        check_audit_log(connection, test_user)
        
        # Check that IAM deny policy was removed
        has_deny = check_iam_policy(test_user)
        if not has_deny:
            print_success("IAM DENY policy removed after unblocking - CORRECT")
        else:
            print_error("IAM DENY policy still exists after unblocking - INCORRECT")
            return False
        
        print_success("Automatic unblocking test PASSED")
        return True
        
    except Exception as e:
        print_error(f"Automatic unblocking test FAILED: {str(e)}")
        return False
    finally:
        connection.close()

def test_database_integration():
    """Test 4: Database tables integration"""
    print_test_header("Database Tables Integration")
    
    connection = get_db_connection()
    
    try:
        # Check that all required tables exist
        with connection.cursor() as cursor:
            # Check user_limits table has administrative_safe field
            cursor.execute("""
                SELECT COLUMN_NAME 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = 'bedrock_usage' 
                AND TABLE_NAME = 'user_limits' 
                AND COLUMN_NAME = 'administrative_safe'
            """)
            
            if cursor.fetchone():
                print_success("user_limits.administrative_safe field exists")
            else:
                print_error("user_limits.administrative_safe field missing")
                return False
            
            # Check user_blocking_status table exists
            cursor.execute("""
                SELECT COUNT(*) as table_count
                FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_SCHEMA = 'bedrock_usage' 
                AND TABLE_NAME = 'user_blocking_status'
            """)
            
            if cursor.fetchone()['table_count'] > 0:
                print_success("user_blocking_status table exists")
            else:
                print_error("user_blocking_status table missing")
                return False
            
            # Check blocking_audit_log table exists
            cursor.execute("""
                SELECT COUNT(*) as table_count
                FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_SCHEMA = 'bedrock_usage' 
                AND TABLE_NAME = 'blocking_audit_log'
            """)
            
            if cursor.fetchone()['table_count'] > 0:
                print_success("blocking_audit_log table exists")
            else:
                print_error("blocking_audit_log table missing")
                return False
        
        print_success("Database integration test PASSED")
        return True
        
    except Exception as e:
        print_error(f"Database integration test FAILED: {str(e)}")
        return False
    finally:
        connection.close()

def cleanup_test_data():
    """Clean up test data"""
    print_test_header("Cleanup Test Data")
    
    connection = get_db_connection()
    test_users = ["test_blocking_user", "test_admin_protected_user", "test_unblock_user"]
    
    try:
        with connection.cursor() as cursor:
            for user_id in test_users:
                cursor.execute("DELETE FROM user_blocking_status WHERE user_id = %s", [user_id])
                cursor.execute("DELETE FROM blocking_audit_log WHERE user_id = %s", [user_id])
                cursor.execute("DELETE FROM bedrock_requests WHERE user_id = %s", [user_id])
                cursor.execute("DELETE FROM user_limits WHERE user_id = %s", [user_id])
                
                # Try to remove IAM policy
                try:
                    policy_name = f"{user_id}_BedrockPolicy"
                    iam_client.delete_user_policy(UserName=user_id, PolicyName=policy_name)
                    print_info(f"Removed IAM policy for {user_id}")
                except:
                    pass  # Policy might not exist
        
        print_success("Test data cleanup completed")
        
    except Exception as e:
        print_error(f"Cleanup failed: {str(e)}")
    finally:
        connection.close()

def main():
    """Run all tests"""
    print("🚀 Enhanced Blocking System Test Suite")
    print("=" * 60)
    
    tests = [
        ("Database Integration", test_database_integration),
        ("Normal Blocking", test_normal_blocking),
        ("Administrative Protection", test_administrative_protection),
        ("Automatic Unblocking", test_automatic_unblocking),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                print_error(f"{test_name} test FAILED")
        except Exception as e:
            print_error(f"{test_name} test ERROR: {str(e)}")
    
    # Cleanup
    cleanup_test_data()
    
    # Summary
    print_test_header("Test Results Summary")
    print(f"Tests Passed: {passed}/{total}")
    
    if passed == total:
        print_success("🎉 ALL TESTS PASSED! Enhanced blocking system is working correctly.")
        return 0
    else:
        print_error(f"❌ {total - passed} tests failed. Please check the implementation.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
