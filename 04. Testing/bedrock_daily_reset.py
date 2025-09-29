#!/usr/bin/env python3
"""
AWS Bedrock Usage Control System - Daily Reset Lambda (Simplified Version)
=========================================================================

This Lambda function performs daily reset operations including:
1. Unblocking all currently blocked users
2. Setting administrative_safe field in user_limits
3. Updating IAM policies to restore Bedrock access
4. Sending email notifications to reset users

Triggered by CloudWatch Events cron schedule at 00:00 CET daily.

Author: AWS Bedrock Usage Control System
Version: 3.0.0 (Simplified RDS MySQL)
"""

import json
import boto3
import pymysql
import os
from datetime import datetime, timezone, timedelta
import logging
from typing import Dict, Any, List, Optional
import pytz

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# AWS clients
lambda_client = boto3.client('lambda')
sns = boto3.client('sns')
iam = boto3.client('iam')

# RDS connection parameters
RDS_HOST = os.environ['RDS_ENDPOINT']
RDS_USER = os.environ['RDS_USERNAME']
RDS_PASSWORD = os.environ['RDS_PASSWORD']
RDS_DB = os.environ['RDS_DATABASE']

# Configuration
REGION = os.environ.get('AWS_REGION', 'eu-west-1')
ACCOUNT_ID = os.environ.get('ACCOUNT_ID', '701055077130')
SNS_TOPIC_ARN = os.environ.get('SNS_TOPIC_ARN', f'arn:aws:sns:{REGION}:{ACCOUNT_ID}:bedrock-usage-alerts')
EMAIL_SERVICE_FUNCTION = os.environ.get('EMAIL_SERVICE_FUNCTION', 'bedrock-email-service')

# CET timezone
CET = pytz.timezone('Europe/Madrid')

# Connection pool
connection_pool = None

def get_current_cet_time() -> datetime:
    """Get current time in CET timezone"""
    return datetime.now(CET)

def get_cet_timestamp_string() -> str:
    """Get current CET timestamp as string for database"""
    return get_current_cet_time().strftime('%Y-%m-%d %H:%M:%S')

def get_mysql_connection():
    """Create MySQL connection with connection pooling"""
    global connection_pool
    
    if connection_pool is None:
        connection_pool = pymysql.connect(
            host=RDS_HOST,
            user=RDS_USER,
            password=RDS_PASSWORD,
            database=RDS_DB,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor,
            autocommit=True,
            connect_timeout=5,
            read_timeout=5,
            write_timeout=5
        )
    
    try:
        connection_pool.ping(reconnect=True)
        return connection_pool
    except Exception as e:
        logger.error(f"Connection failed, creating new one: {str(e)}")
        connection_pool = pymysql.connect(
            host=RDS_HOST,
            user=RDS_USER,
            password=RDS_PASSWORD,
            database=RDS_DB,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor,
            autocommit=True,
            connect_timeout=5,
            read_timeout=5,
            write_timeout=5
        )
        return connection_pool

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main Lambda handler for daily reset operations
    
    Args:
        event: CloudWatch Events cron event or manual trigger
        context: Lambda context object
        
    Returns:
        Dict with status code and reset results
    """
    try:
        current_cet_time = get_current_cet_time()
        logger.info(f"Starting daily reset at {current_cet_time.isoformat()} CET")
        logger.info(f"Event: {json.dumps(event, default=str)}")
        
        connection = get_mysql_connection()
        logger.info("✅ Successfully connected to MySQL database")
        
        reset_results = {
            'reset_timestamp': get_cet_timestamp_string(),
            'users_unblocked': 0,
            'users_notified': 0,
            'admin_safe_removed': 0,
            'errors': []
        }
        
        # Execute daily reset: unblock users and send notifications
        unblock_results = unblock_all_blocked_users_and_notify(connection)
        reset_results['users_unblocked'] = unblock_results['unblocked_count']
        reset_results['users_notified'] = unblock_results['notified_count']
        reset_results['admin_safe_removed'] = unblock_results['admin_safe_removed_count']
        reset_results['errors'].extend(unblock_results['errors'])
        
        logger.info(f"Daily reset completed successfully: {reset_results}")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Daily reset completed successfully',
                'results': reset_results
            })
        }
        
    except Exception as e:
        logger.error(f"Error during daily reset: {str(e)}", exc_info=True)
        
        # Send error notification
        send_error_notification(str(e))
        
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': f'Daily reset failed: {str(e)}',
                'timestamp': get_cet_timestamp_string()
            })
        }

def unblock_all_blocked_users_and_notify(connection) -> Dict[str, Any]:
    """
    Unblock users whose blocking expiration date has passed and manage administrative_safe flags
    
    Args:
        connection: MySQL database connection
        
    Returns:
        Dict with unblock and notification results
    """
    try:
        results = {
            'unblocked_count': 0,
            'notified_count': 0,
            'admin_safe_removed_count': 0,
            'errors': [],
            'unblocked_users': [],
            'admin_safe_removed_users': []
        }
        
        current_cet_timestamp = get_cet_timestamp_string()
        current_cet_datetime = get_current_cet_time()
        
        # Step 1: Get blocked users whose expiration date has passed
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    ubs.user_id, 
                    ubs.blocked_reason,
                    ubs.blocked_until,
                    ul.team,
                    ul.person,
                    ul.daily_request_limit,
                    ul.administrative_safe
                FROM user_blocking_status ubs
                JOIN user_limits ul ON ubs.user_id = ul.user_id
                WHERE ubs.is_blocked = 'Y' 
                AND (ubs.blocked_until IS NULL OR ubs.blocked_until <= %s)
            """, [current_cet_datetime])
            
            expired_blocked_users = cursor.fetchall()
        
        # Step 2: Get active users with administrative_safe = 'Y' to remove the flag
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    ul.user_id,
                    ul.team,
                    ul.person,
                    ul.daily_request_limit
                FROM user_limits ul
                LEFT JOIN user_blocking_status ubs ON ul.user_id = ubs.user_id
                WHERE ul.administrative_safe = 'Y' 
                AND (ubs.is_blocked IS NULL OR ubs.is_blocked = 'N')
            """)
            
            active_admin_safe_users = cursor.fetchall()
            
        logger.info(f"Found {len(expired_blocked_users)} blocked users with expired blocks to unblock")
        logger.info(f"Found {len(active_admin_safe_users)} active users with administrative_safe flag to remove")
        
        # Process expired blocked users
        for user in expired_blocked_users:
            user_id = user['user_id']
            
            try:
                # Execute user unblocking workflow
                success = execute_user_unblocking(connection, user_id)
                
                if success:
                    results['unblocked_count'] += 1
                    results['unblocked_users'].append(user_id)
                    logger.info(f"Successfully unblocked user {user_id} (expiration passed)")
                    
                    # Send email notification to user
                    email_sent = send_reset_email_notification(user)
                    if email_sent:
                        results['notified_count'] += 1
                        logger.info(f"Email notification sent to user {user_id}")
                    else:
                        results['errors'].append(f"Failed to send email to user {user_id}")
                        
                else:
                    error_msg = f"Failed to unblock user {user_id}"
                    results['errors'].append(error_msg)
                    logger.error(error_msg)
                
            except Exception as e:
                error_msg = f"Error processing blocked user {user_id}: {str(e)}"
                results['errors'].append(error_msg)
                logger.error(error_msg)
        
        # Process active users with administrative_safe flag
        for user in active_admin_safe_users:
            user_id = user['user_id']
            
            try:
                success = remove_administrative_safe_flag(connection, user_id)
                
                if success:
                    results['admin_safe_removed_count'] += 1
                    results['admin_safe_removed_users'].append(user_id)
                    logger.info(f"Successfully removed administrative_safe flag from active user {user_id}")
                else:
                    error_msg = f"Failed to remove administrative_safe flag from user {user_id}"
                    results['errors'].append(error_msg)
                    logger.error(error_msg)
                    
            except Exception as e:
                error_msg = f"Error removing administrative_safe flag for user {user_id}: {str(e)}"
                results['errors'].append(error_msg)
                logger.error(error_msg)
        
        logger.info(f"Daily reset completed: {results['unblocked_count']} users unblocked, {results['notified_count']} users notified, {results['admin_safe_removed_count']} admin_safe flags removed")
        return results
        
    except Exception as e:
        logger.error(f"Error in unblock_all_blocked_users_and_notify: {str(e)}")
        return {
            'unblocked_count': 0,
            'notified_count': 0,
            'admin_safe_removed_count': 0,
            'errors': [str(e)],
            'unblocked_users': [],
            'admin_safe_removed_users': []
        }

def execute_user_unblocking(connection, user_id: str) -> bool:
    """
    Execute complete user unblocking workflow
    
    Args:
        connection: MySQL database connection
        user_id: User ID to unblock
        
    Returns:
        True if successful, False otherwise
    """
    try:
        current_cet_timestamp = get_cet_timestamp_string()
        
        # 1. Update USER_BLOCKING_STATUS table
        with connection.cursor() as cursor:
            cursor.execute("""
                UPDATE user_blocking_status 
                SET is_blocked = 'N',
                    blocked_reason = 'Daily reset unblock',
                    blocked_until = NULL,
                    last_reset_at = %s,
                    updated_at = %s
                WHERE user_id = %s
            """, [current_cet_timestamp, current_cet_timestamp, user_id])
        
        # 2. Remove administrative_safe field if it was set (users being unblocked should have flag removed)
        with connection.cursor() as cursor:
            cursor.execute("""
                UPDATE user_limits 
                SET administrative_safe = 'N',
                    updated_at = %s
                WHERE user_id = %s AND administrative_safe = 'Y'
            """, [current_cet_timestamp, user_id])
        
        # 3. Log to BLOCKING_AUDIT_LOG
        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO blocking_audit_log 
                (user_id, operation_type, operation_reason, performed_by, operation_timestamp, created_at)
                VALUES (%s, 'UNBLOCK', 'Daily reset', 'daily_reset', %s, %s)
            """, [user_id, current_cet_timestamp, current_cet_timestamp])
        
        # 4. Remove IAM deny policy (if exists)
        try:
            implement_iam_unblocking(user_id)
        except Exception as e:
            logger.warning(f"IAM policy removal failed for {user_id}: {str(e)}")
            # Continue with unblocking even if IAM fails
        
        logger.info(f"✅ Successfully executed complete unblocking for user {user_id}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to execute user unblocking for {user_id}: {str(e)}")
        return False

def implement_iam_unblocking(user_id: str) -> bool:
    """
    Remove IAM deny policy for user unblocking
    
    Args:
        user_id: User ID to unblock
        
    Returns:
        True if successful, False otherwise
    """
    try:
        policy_name = f"{user_id}_BedrockPolicy"
        
        try:
            response = iam.get_user_policy(UserName=user_id, PolicyName=policy_name)
            current_policy = response['PolicyDocument']
            
            # Remove deny statements
            current_policy['Statement'] = [
                stmt for stmt in current_policy['Statement'] 
                if stmt.get('Sid') != 'DailyLimitBlock'
            ]
            
            # Ensure there's at least an allow statement
            has_allow = any(stmt.get('Effect') == 'Allow' for stmt in current_policy['Statement'])
            if not has_allow:
                current_policy['Statement'].append({
                    "Sid": "BedrockAccess",
                    "Effect": "Allow",
                    "Action": [
                        "bedrock:InvokeModel",
                        "bedrock:InvokeModelWithResponseStream"
                    ],
                    "Resource": "*"
                })
            
            iam.put_user_policy(
                UserName=user_id,
                PolicyName=policy_name,
                PolicyDocument=json.dumps(current_policy, separators=(',', ':'))
            )
            
            logger.info(f"✅ Successfully removed IAM deny policy for user {user_id}")
            return True
            
        except iam.exceptions.NoSuchEntityException:
            logger.info(f"No existing policy found for user {user_id}, no action needed")
            return True
        
    except Exception as e:
        logger.error(f"❌ Failed to remove IAM deny policy for user {user_id}: {str(e)}")
        return False

def send_reset_email_notification(user_data: Dict[str, Any]) -> bool:
    """
    Send email notification to user about daily reset
    
    Args:
        user_data: Dictionary containing user information
        
    Returns:
        True if email sent successfully, False otherwise
    """
    try:
        user_id = user_data['user_id']
        team = user_data.get('team', 'Unknown')
        person = user_data.get('person', user_id)
        daily_limit = user_data.get('daily_request_limit', 350)
        
        # Prepare email payload
        email_payload = {
            'email_type': 'daily_reset',
            'user_id': user_id,
            'user_data': {
                'person': person,
                'team': team,
                'daily_limit': daily_limit,
                'reset_timestamp': get_cet_timestamp_string()
            }
        }
        
        # Invoke email service Lambda function
        response = lambda_client.invoke(
            FunctionName=EMAIL_SERVICE_FUNCTION,
            InvocationType='Event',  # Asynchronous invocation
            Payload=json.dumps(email_payload)
        )
        
        logger.info(f"Email notification triggered for user {user_id}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send email notification for user {user_data.get('user_id', 'unknown')}: {str(e)}")
        return False

def remove_administrative_safe_flag(connection, user_id: str) -> bool:
    """
    Remove administrative_safe flag from active user
    
    Args:
        connection: MySQL database connection
        user_id: User ID to remove flag from
        
    Returns:
        True if successful, False otherwise
    """
    try:
        current_cet_timestamp = get_cet_timestamp_string()
        
        with connection.cursor() as cursor:
            cursor.execute("""
                UPDATE user_limits 
                SET administrative_safe = 'N',
                    updated_at = %s
                WHERE user_id = %s AND administrative_safe = 'Y'
            """, [current_cet_timestamp, user_id])
            
            # Check if any rows were affected
            if cursor.rowcount > 0:
                logger.info(f"✅ Successfully removed administrative_safe flag for user {user_id}")
                
                # Log the operation
                cursor.execute("""
                    INSERT INTO blocking_audit_log 
                    (user_id, operation_type, operation_reason, performed_by, operation_timestamp, created_at)
                    VALUES (%s, 'ADMIN_SAFE_REMOVED', 'Daily reset - remove admin safe flag', 'daily_reset', %s, %s)
                """, [user_id, current_cet_timestamp, current_cet_timestamp])
                
                return True
            else:
                logger.info(f"No administrative_safe flag to remove for user {user_id}")
                return True
        
    except Exception as e:
        logger.error(f"❌ Failed to remove administrative_safe flag for user {user_id}: {str(e)}")
        return False

def send_error_notification(error_message: str) -> None:
    """
    Send error notification when daily reset fails
    
    Args:
        error_message: Error message to send
    """
    try:
        current_cet_timestamp = get_cet_timestamp_string()
        
        sns.publish(
            TopicArn=SNS_TOPIC_ARN,
            Subject="🚨 Bedrock Daily Reset FAILED",
            Message=f"""
CRITICAL: Bedrock Daily Reset Failed

Timestamp: {current_cet_timestamp} CET
Error: {error_message}

This requires immediate attention as users may remain blocked and the system may not reset properly.

Please check CloudWatch logs for detailed error information.
"""
        )
        
        logger.info("Sent error notification")
        
    except Exception as e:
        logger.error(f"Error sending error notification: {str(e)}")

# For testing purposes
if __name__ == "__main__":
    # Test event (CloudWatch Events cron trigger)
    test_event = {
        "version": "0",
        "id": "test-event-id",
        "detail-type": "Scheduled Event",
        "source": "aws.events",
        "account": "701055077130",
        "time": "2025-01-16T00:00:00Z",
        "region": "eu-west-1",
        "resources": [
            "arn:aws:events:eu-west-1:701055077130:rule/bedrock-daily-reset"
        ],
        "detail": {}
    }
    
    # Manual test event
    manual_test_event = {
        "source": "manual",
        "action": "daily_reset",
        "timestamp": get_cet_timestamp_string()
    }
    
    # Mock context
    class MockContext:
        def __init__(self):
            self.function_name = "bedrock-daily-reset"
            self.memory_limit_in_mb = 512
            self.invoked_function_arn = "arn:aws:lambda:eu-west-1:701055077130:function:bedrock-daily-reset"
    
    # Test the handler
    print("Testing simplified daily reset operation:")
    result = lambda_handler(test_event, MockContext())
    print(json.dumps(result, indent=2))
