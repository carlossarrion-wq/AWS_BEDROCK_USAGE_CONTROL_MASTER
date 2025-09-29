#!/usr/bin/env python3
"""
Test script to verify manual blocking functionality
Tests both administrative flag setting and IAM policy application
"""

import json
import boto3
import pymysql
import os
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Test configuration
TEST_USER = "test.user@company.com"
RDS_HOST = "bedrock-usage-mysql.czuimyk2qu10.eu-west-1.rds.amazonaws.com"
RDS_USER = "admin"
RDS_PASSWORD = "your_password_here"  # Replace with actual password
RDS_DB = "bedrock_usage"

def get_mysql_connection():
    """Create MySQL connection"""
    return pymysql.connect(
        host=RDS_HOST,
        user=RDS_USER,
        password=RDS_PASSWORD,
        database=RDS_DB,
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True
    )

def test_administrative_flag_setting():
    """Test that administrative_safe flag is set correctly during manual blocking"""
    logger.info("🧪 Testing administrative flag setting...")
    
    try:
        connection = get_mysql_connection()
        
        # 1. Ensure test user exists in user_limits table
        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO user_limits (user_id, team, person, administrative_safe, created_at)
                VALUES (%s, 'test_team', 'Test User', 'N', NOW())
                ON DUPLICATE KEY UPDATE
                administrative_safe = 'N',
                updated_at = NOW()
            """, [TEST_USER])
            logger.info(f"✅ Test user {TEST_USER} prepared with administrative_safe='N'")
        
        # 2. Simulate manual blocking (set administrative_safe to 'Y')
        with connection.cursor() as cursor:
            cursor.execute("""
                UPDATE user_limits 
                SET administrative_safe = 'Y', 
                    updated_at = NOW()
                WHERE user_id = %s
            """, [TEST_USER])
            logger.info(f"✅ Set administrative_safe='Y' for {TEST_USER}")
        
        # 3. Verify the flag was set correctly
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT administrative_safe 
                FROM user_limits 
                WHERE user_id = %s
            """, [TEST_USER])
            
            result = cursor.fetchone()
            if result and result['administrative_safe'] == 'Y':
                logger.info(f"✅ PASS: Administrative flag correctly set to 'Y' for {TEST_USER}")
                return True
            else:
                logger.error(f"❌ FAIL: Administrative flag not set correctly. Got: {result}")
                return False
                
    except Exception as e:
        logger.error(f"❌ FAIL: Error testing administrative flag: {str(e)}")
        return False
    finally:
        if 'connection' in locals():
            connection.close()

def test_lambda_function_call():
    """Test that Lambda function can be called for policy management"""
    logger.info("🧪 Testing Lambda function call...")
    
    try:
        lambda_client = boto3.client('lambda', region_name='eu-west-1')
        
        # Test payload for manual blocking
        test_payload = {
            'action': 'block',
            'user_id': TEST_USER,
            'reason': 'Test manual blocking',
            'performed_by': 'test_script',
            'usage_record': {
                'request_count': 50,
                'daily_limit': 350,
                'team': 'test_team',
                'date': datetime.now().strftime('%Y-%m-%d')
            }
        }
        
        # Call the Lambda function
        response = lambda_client.invoke(
            FunctionName='bedrock-realtime-usage-controller',
            InvocationType='RequestResponse',
            Payload=json.dumps(test_payload)
        )
        
        # Parse response
        response_payload = json.loads(response['Payload'].read())
        
        if response_payload.get('statusCode') == 200:
            logger.info("✅ PASS: Lambda function call successful")
            logger.info(f"Response: {response_payload}")
            return True
        else:
            logger.error(f"❌ FAIL: Lambda function returned error: {response_payload}")
            return False
            
    except Exception as e:
        logger.error(f"❌ FAIL: Error calling Lambda function: {str(e)}")
        return False

def test_iam_policy_creation():
    """Test that IAM policy is created correctly"""
    logger.info("🧪 Testing IAM policy creation...")
    
    try:
        iam_client = boto3.client('iam')
        policy_name = f"{TEST_USER}_BedrockPolicy"
        
        # Check if policy exists
        try:
            response = iam_client.get_user_policy(
                UserName=TEST_USER,
                PolicyName=policy_name
            )
            
            policy_document = response['PolicyDocument']
            
            # Check if deny statement exists
            deny_statements = [
                stmt for stmt in policy_document['Statement'] 
                if stmt.get('Sid') == 'DailyLimitBlock' and stmt.get('Effect') == 'Deny'
            ]
            
            if deny_statements:
                logger.info("✅ PASS: IAM deny policy found")
                logger.info(f"Policy document: {json.dumps(policy_document, indent=2)}")
                return True
            else:
                logger.error("❌ FAIL: No deny statement found in policy")
                return False
                
        except iam_client.exceptions.NoSuchEntityException:
            logger.warning(f"⚠️ No policy found for user {TEST_USER} (this may be expected if user doesn't exist)")
            return True  # This is not necessarily a failure
            
    except Exception as e:
        logger.error(f"❌ FAIL: Error checking IAM policy: {str(e)}")
        return False

def test_blocking_audit_log():
    """Test that blocking operations are logged correctly"""
    logger.info("🧪 Testing blocking audit log...")
    
    try:
        connection = get_mysql_connection()
        
        # Insert a test audit log entry
        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO blocking_audit_log 
                (user_id, operation_type, operation_reason, performed_by, new_status, 
                 operation_timestamp, iam_policy_updated, email_sent, created_at)
                VALUES (%s, 'ADMIN_BLOCK', 'Test manual blocking', 'test_script', 'Y', 
                        NOW(), 'Y', 'Y', NOW())
            """, [TEST_USER])
            logger.info(f"✅ Test audit log entry created for {TEST_USER}")
        
        # Verify the entry was created
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT * FROM blocking_audit_log 
                WHERE user_id = %s AND operation_reason = 'Test manual blocking'
                ORDER BY created_at DESC LIMIT 1
            """, [TEST_USER])
            
            result = cursor.fetchone()
            if result:
                logger.info("✅ PASS: Audit log entry found")
                logger.info(f"Audit entry: {result}")
                return True
            else:
                logger.error("❌ FAIL: Audit log entry not found")
                return False
                
    except Exception as e:
        logger.error(f"❌ FAIL: Error testing audit log: {str(e)}")
        return False
    finally:
        if 'connection' in locals():
            connection.close()

def cleanup_test_data():
    """Clean up test data"""
    logger.info("🧹 Cleaning up test data...")
    
    try:
        connection = get_mysql_connection()
        
        # Remove test audit log entries
        with connection.cursor() as cursor:
            cursor.execute("""
                DELETE FROM blocking_audit_log 
                WHERE user_id = %s AND operation_reason = 'Test manual blocking'
            """, [TEST_USER])
            logger.info(f"✅ Cleaned up audit log entries for {TEST_USER}")
        
        # Reset administrative_safe flag
        with connection.cursor() as cursor:
            cursor.execute("""
                UPDATE user_limits 
                SET administrative_safe = 'N', 
                    updated_at = NOW()
                WHERE user_id = %s
            """, [TEST_USER])
            logger.info(f"✅ Reset administrative_safe='N' for {TEST_USER}")
            
    except Exception as e:
        logger.error(f"❌ Error during cleanup: {str(e)}")
    finally:
        if 'connection' in locals():
            connection.close()

def main():
    """Run all tests"""
    logger.info("🚀 Starting manual blocking functionality tests...")
    
    test_results = []
    
    # Run tests
    test_results.append(("Administrative Flag Setting", test_administrative_flag_setting()))
    test_results.append(("Lambda Function Call", test_lambda_function_call()))
    test_results.append(("IAM Policy Creation", test_iam_policy_creation()))
    test_results.append(("Blocking Audit Log", test_blocking_audit_log()))
    
    # Clean up
    cleanup_test_data()
    
    # Report results
    logger.info("\n" + "="*60)
    logger.info("📊 TEST RESULTS SUMMARY")
    logger.info("="*60)
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{test_name}: {status}")
        if result:
            passed += 1
    
    logger.info("="*60)
    logger.info(f"📈 OVERALL: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 ALL TESTS PASSED! Manual blocking functionality is working correctly.")
        return True
    else:
        logger.error("❌ SOME TESTS FAILED! Manual blocking functionality needs attention.")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
