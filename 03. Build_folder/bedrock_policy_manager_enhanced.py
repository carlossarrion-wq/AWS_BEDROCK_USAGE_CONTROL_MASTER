#!/usr/bin/env python3
"""
AWS Bedrock Individual Blocking System - Enhanced Policy Manager Lambda
=======================================================================

This Lambda function manages IAM policies for user blocking/unblocking by:
1. Adding/removing Deny statements to user policies dynamically
2. Blocking users when daily limits are exceeded
3. Unblocking users during daily reset or manual intervention
4. Maintaining audit trail of all policy modifications
5. Sending enhanced email notifications for admin scenarios

Enhanced with comprehensive email delivery functionality for:
- Admin blocking emails (manual admin block)
- Admin unblocking emails (manual admin unblock)

Author: AWS Bedrock Usage Control System
Version: 2.0.0
"""

import json
import boto3
import logging
from datetime import datetime, date
from typing import Dict, Any, Optional
import os

# Import the enhanced email service
from bedrock_email_service import create_email_service

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# AWS clients
iam = boto3.client('iam')
dynamodb = boto3.resource('dynamodb')
sns = boto3.client('sns')
lambda_client = boto3.client('lambda')

# Configuration
REGION = os.environ.get('AWS_REGION', 'eu-west-1')
ACCOUNT_ID = os.environ.get('ACCOUNT_ID', '701055077130')
TABLE_NAME = os.environ.get('DYNAMODB_TABLE', 'bedrock_user_daily_usage')
SNS_TOPIC_ARN = os.environ.get('SNS_TOPIC_ARN', f'arn:aws:sns:{REGION}:{ACCOUNT_ID}:bedrock-usage-alerts')

# Email configuration
EMAIL_NOTIFICATIONS_ENABLED = os.environ.get('EMAIL_NOTIFICATIONS_ENABLED', 'true').lower() == 'true'

# Policy configuration
BEDROCK_POLICY_SUFFIX = "_BedrockPolicy"
DENY_STATEMENT_SID = "DailyLimitBlock"

# Initialize enhanced email service if enabled
email_service = None
if EMAIL_NOTIFICATIONS_ENABLED:
    try:
        email_service = create_email_service()
        logger.info("Enhanced email service initialized in policy manager")
    except Exception as e:
        logger.error(f"Failed to initialize email service in policy manager: {str(e)}")
        email_service = None

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main Lambda handler for managing IAM policies
    
    Args:
        event: Event containing action, user_id, and other parameters
        context: Lambda context object
        
    Returns:
        Dict with status code and operation results
    """
    try:
        logger.info(f"Processing policy management event: {json.dumps(event, default=str)}")
        
        # Validate required parameters
        if 'action' not in event or 'user_id' not in event:
            logger.error("Missing required parameters: action and user_id")
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Missing required parameters: action and user_id'})
            }
        
        action = event['action']
        user_id = event['user_id']
        reason = event.get('reason', 'unspecified')
        
        logger.info(f"Processing {action} action for user {user_id}, reason: {reason}")
        
        # Route to appropriate handler
        if action == 'block':
            result = block_user_access(user_id, reason, event.get('usage_record', {}), event)
        elif action == 'unblock':
            result = unblock_user_access(user_id, reason, event)
        elif action == 'check_status':
            result = check_user_block_status(user_id)
        else:
            logger.error(f"Invalid action: {action}")
            return {
                'statusCode': 400,
                'body': json.dumps({'error': f'Invalid action: {action}'})
            }
        
        return result
        
    except Exception as e:
        logger.error(f"Error processing policy management event: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

def block_user_access(user_id: str, reason: str, usage_record: Dict[str, Any], event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Block user access by adding Deny statement to their IAM policy
    
    Args:
        user_id: The user ID to block
        reason: Reason for blocking
        usage_record: Current usage record from DynamoDB
        event: Full event data
        
    Returns:
        Dict with operation result
    """
    try:
        logger.info(f"Blocking user {user_id} - Reason: {reason}")
        
        # Check for warning threshold (80%) before blocking
        current_usage = int(usage_record.get('request_count', 0))
        daily_limit = int(usage_record.get('daily_limit', 250))
        warning_threshold = int(daily_limit * 0.8)  # 80% threshold
        
        # Send warning email if at 80% threshold and not already blocked
        if current_usage >= warning_threshold and current_usage < daily_limit:
            send_warning_notification(user_id, usage_record)
        
        # Get user's Bedrock policy name
        policy_name = f"{user_id}{BEDROCK_POLICY_SUFFIX}"
        
        # Get current policy or create base policy if it doesn't exist
        current_policy = get_or_create_user_policy(user_id, policy_name)
        
        # Check if user is already blocked
        if is_user_blocked(current_policy):
            logger.info(f"User {user_id} is already blocked")
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'message': f'User {user_id} is already blocked',
                    'action': 'block',
                    'user_id': user_id,
                    'already_blocked': True
                })
            }
        
        # Create deny statement
        deny_statement = create_deny_statement(user_id)
        
        # Remove any existing deny statement and add new one
        updated_policy = add_deny_statement(current_policy, deny_statement)
        
        # Update the policy
        iam.put_user_policy(
            UserName=user_id,
            PolicyName=policy_name,
            PolicyDocument=json.dumps(updated_policy, separators=(',', ':'))
        )
        
        # Calculate expiration date based on block type
        from datetime import datetime, timedelta, timezone
        
        performed_by = event.get('performed_by', 'system')
        
        if performed_by != 'system':
            # Administrative block: today + 24 hours
            expires_at = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat().replace('+00:00', 'Z')
        else:
            # Automatic block: tomorrow at 00:00 CET
            # CET is UTC+1, CEST is UTC+2 (during daylight saving time)
            cet_offset = timezone(timedelta(hours=1))  # CET (winter time)
            cest_offset = timezone(timedelta(hours=2))  # CEST (summer time)
            
            # Get current UTC time
            now_utc = datetime.now(timezone.utc)
            
            # Convert to CET/CEST (approximate - for exact DST rules we'd need more complex logic)
            # For simplicity, assume CEST from March to October
            current_month = now_utc.month
            is_dst = 3 <= current_month <= 10  # Rough DST period
            madrid_tz = cest_offset if is_dst else cet_offset
            
            # Get current time in Madrid timezone
            now_madrid = now_utc.astimezone(madrid_tz)
            
            # Calculate tomorrow at 00:00 in Madrid timezone
            tomorrow_madrid = now_madrid.date() + timedelta(days=1)
            tomorrow_midnight_madrid = datetime.combine(tomorrow_madrid, datetime.min.time()).replace(tzinfo=madrid_tz)
            
            # Convert to UTC for storage
            expires_at = tomorrow_midnight_madrid.astimezone(timezone.utc).isoformat().replace('+00:00', 'Z')
        
        # Update DynamoDB record
        update_user_block_status(user_id, 'BLOCKED', reason, expires_at)
        
        # NEW: Set admin_protection_by field to track who performed the block
        performed_by = event.get('performed_by', 'system')
        set_block_performed_by(user_id, performed_by)
        
        # Add expires_at to usage_record for email notification
        usage_record_with_expiration = usage_record.copy()
        usage_record_with_expiration['expires_at'] = expires_at
        
        # Send notification (including enhanced email for all block types)
        send_block_notification(user_id, reason, usage_record_with_expiration, performed_by)
        
        # Log operation to history
        log_operation_to_history(user_id, 'BLOCK', reason, performed_by, 'SUCCESS')
        
        logger.info(f"Successfully blocked user {user_id}")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': f'User {user_id} blocked successfully',
                'action': 'block',
                'user_id': user_id,
                'reason': reason,
                'blocked_at': datetime.utcnow().isoformat()
            })
        }
        
    except Exception as e:
        logger.error(f"Error blocking user {user_id}: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': f'Error blocking user {user_id}: {str(e)}',
                'action': 'block',
                'user_id': user_id
            })
        }

def unblock_user_access(user_id: str, reason: str, event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Unblock user access by removing Deny statement from their IAM policy
    
    Args:
        user_id: The user ID to unblock
        reason: Reason for unblocking
        event: Full event data
        
    Returns:
        Dict with operation result
    """
    try:
        logger.info(f"Unblocking user {user_id} - Reason: {reason}")
        
        # Get user's Bedrock policy name
        policy_name = f"{user_id}{BEDROCK_POLICY_SUFFIX}"
        
        try:
            # Get current policy
            response = iam.get_user_policy(UserName=user_id, PolicyName=policy_name)
            policy_document = response['PolicyDocument']
            
            # AWS returns PolicyDocument as a URL-decoded JSON string, need to parse it
            if isinstance(policy_document, str):
                current_policy = json.loads(policy_document)
            else:
                current_policy = policy_document
        except iam.exceptions.NoSuchEntityException:
            logger.warning(f"Policy {policy_name} not found for user {user_id}")
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'message': f'User {user_id} policy not found - already unblocked',
                    'action': 'unblock',
                    'user_id': user_id,
                    'already_unblocked': True
                })
            }
        
        # Check if user is currently blocked
        if not is_user_blocked(current_policy):
            logger.info(f"User {user_id} is not currently blocked")
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'message': f'User {user_id} is not currently blocked',
                    'action': 'unblock',
                    'user_id': user_id,
                    'already_unblocked': True
                })
            }
        
        # Remove deny statement
        updated_policy = remove_deny_statement(current_policy)
        
        # Update the policy
        iam.put_user_policy(
            UserName=user_id,
            PolicyName=policy_name,
            PolicyDocument=json.dumps(updated_policy, separators=(',', ':'))
        )
        
        # Update DynamoDB record
        update_user_block_status(user_id, 'ACTIVE', reason)
        
        # NEW: Handle administrative protection based on who performed the unblock
        performed_by = event.get('performed_by', 'system')
        reason = event.get('reason', 'unspecified')
        
        if performed_by != 'system' and performed_by != 'daily_reset':
            # Manual admin unblock - set administrative protection
            set_administrative_protection(user_id, performed_by)
        elif reason == 'automatic_expiration':
            # Automatic expiration unblock - clear administrative protection
            clear_administrative_protection(user_id)
        
        # Send notification (including enhanced email for admin unblocks)
        send_unblock_notification(user_id, reason, performed_by)
        
        # Log operation to history
        log_operation_to_history(user_id, 'UNBLOCK', reason, performed_by, 'SUCCESS')
        
        logger.info(f"Successfully unblocked user {user_id}")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': f'User {user_id} unblocked successfully',
                'action': 'unblock',
                'user_id': user_id,
                'reason': reason,
                'unblocked_at': datetime.utcnow().isoformat()
            })
        }
        
    except Exception as e:
        logger.error(f"Error unblocking user {user_id}: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': f'Error unblocking user {user_id}: {str(e)}',
                'action': 'unblock',
                'user_id': user_id
            })
        }

def check_user_block_status(user_id: str) -> Dict[str, Any]:
    """
    Check if user is currently blocked
    
    Args:
        user_id: The user ID to check
        
    Returns:
        Dict with user block status
    """
    try:
        logger.info(f"Checking block status for user {user_id}")
        
        # Get user's Bedrock policy name
        policy_name = f"{user_id}{BEDROCK_POLICY_SUFFIX}"
        
        try:
            # Get current policy
            response = iam.get_user_policy(UserName=user_id, PolicyName=policy_name)
            policy_document = response['PolicyDocument']
            
            # AWS returns PolicyDocument as a URL-decoded JSON string, need to parse it
            if isinstance(policy_document, str):
                current_policy = json.loads(policy_document)
            else:
                current_policy = policy_document
            
            is_blocked = is_user_blocked(current_policy)
            
        except iam.exceptions.NoSuchEntityException:
            logger.info(f"Policy {policy_name} not found for user {user_id} - user is not blocked")
            is_blocked = False
        
        # Get additional information from DynamoDB
        block_type = 'None'
        blocked_since = None
        expires_at = None
        
        if is_blocked:
            try:
                table = dynamodb.Table(TABLE_NAME)
                today = date.today().isoformat()
                
                response = table.get_item(
                    Key={'user_id': user_id, 'date': today}
                )
                
                if 'Item' in response:
                    item = response['Item']
                    blocked_since = item.get('blocked_at')
                    block_type = 'Manual' if item.get('status') == 'BLOCKED' else 'None'
                    expires_at = item.get('expires_at', 'Indefinite')
                    
            except Exception as dynamo_error:
                logger.error(f"Error getting DynamoDB info for {user_id}: {str(dynamo_error)}")
                # Continue with basic info
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'user_id': user_id,
                'is_blocked': is_blocked,
                'block_type': block_type,
                'blocked_since': blocked_since,
                'expires_at': expires_at,
                'checked_at': datetime.utcnow().isoformat()
            })
        }
        
    except Exception as e:
        logger.error(f"Error checking block status for user {user_id}: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': f'Error checking block status for user {user_id}: {str(e)}',
                'user_id': user_id
            })
        }

def get_or_create_user_policy(user_id: str, policy_name: str) -> Dict[str, Any]:
    """
    Get existing user policy or create a base policy if it doesn't exist
    
    Args:
        user_id: The user ID
        policy_name: The policy name
        
    Returns:
        Dict with policy document
    """
    try:
        # Try to get existing policy
        response = iam.get_user_policy(UserName=user_id, PolicyName=policy_name)
        policy_document = response['PolicyDocument']
        
        # AWS returns PolicyDocument as a URL-decoded JSON string, need to parse it
        if isinstance(policy_document, str):
            return json.loads(policy_document)
        else:
            return policy_document
        
    except iam.exceptions.NoSuchEntityException:
        # Policy doesn't exist, create base policy
        logger.info(f"Creating base Bedrock policy for user {user_id}")
        
        base_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "BedrockAccess",
                    "Effect": "Allow",
                    "Action": [
                        "bedrock:InvokeModel",
                        "bedrock:InvokeModelWithResponseStream"
                    ],
                    "Resource": "*"
                }
            ]
        }
        
        # Create the policy
        iam.put_user_policy(
            UserName=user_id,
            PolicyName=policy_name,
            PolicyDocument=json.dumps(base_policy, separators=(',', ':'))
        )
        
        return base_policy

def create_deny_statement(user_id: str) -> Dict[str, Any]:
    """
    Create deny statement for blocking user access
    
    Args:
        user_id: The user ID to create deny statement for
        
    Returns:
        Dict with deny statement
    """
    return {
        "Sid": DENY_STATEMENT_SID,
        "Effect": "Deny",
        "Action": [
            "bedrock:InvokeModel",
            "bedrock:InvokeModelWithResponseStream"
        ],
        "Resource": "*"
    }

def add_deny_statement(policy: Dict[str, Any], deny_statement: Dict[str, Any]) -> Dict[str, Any]:
    """
    Add deny statement to policy (removing any existing deny statement first)
    
    Args:
        policy: Current policy document
        deny_statement: Deny statement to add
        
    Returns:
        Updated policy document
    """
    # Remove any existing deny statement
    policy['Statement'] = [
        stmt for stmt in policy['Statement'] 
        if stmt.get('Sid') != DENY_STATEMENT_SID
    ]
    
    # Add new deny statement at the beginning (deny statements should be evaluated first)
    policy['Statement'].insert(0, deny_statement)
    
    return policy

def remove_deny_statement(policy: Dict[str, Any]) -> Dict[str, Any]:
    """
    Remove deny statement from policy
    
    Args:
        policy: Current policy document
        
    Returns:
        Updated policy document
    """
    policy['Statement'] = [
        stmt for stmt in policy['Statement'] 
        if stmt.get('Sid') != DENY_STATEMENT_SID
    ]
    
    return policy

def is_user_blocked(policy: Dict[str, Any]) -> bool:
    """
    Check if user is currently blocked based on policy
    
    Args:
        policy: Policy document to check
        
    Returns:
        True if user is blocked, False otherwise
    """
    for statement in policy.get('Statement', []):
        if (statement.get('Sid') == DENY_STATEMENT_SID and 
            statement.get('Effect') == 'Deny'):
            return True
    return False

def update_user_block_status(user_id: str, status: str, reason: str, expires_at: str = None) -> None:
    """
    Update user block status in DynamoDB
    
    Args:
        user_id: The user ID
        status: New status (ACTIVE, BLOCKED)
        reason: Reason for status change
        expires_at: When the block expires (optional)
    """
    try:
        table = dynamodb.Table(TABLE_NAME)
        today = date.today().isoformat()
        
        # First try to get the item to see if it exists
        try:
            response = table.get_item(Key={'user_id': user_id, 'date': today})
            item_exists = 'Item' in response
        except Exception:
            item_exists = False
        
        if not item_exists:
            # Create new item if it doesn't exist
            item = {
                'user_id': user_id,
                'date': today,
                'status': status,
                'last_status_change': datetime.utcnow().isoformat(),
                'last_status_reason': reason,
                'request_count': 0,
                'daily_limit': 250  # Default limit
            }
            
            # Add specific timestamps based on status
            if status == 'BLOCKED':
                item['blocked_at'] = datetime.utcnow().isoformat() + 'Z'
                item['expires_at'] = expires_at if expires_at else 'Indefinite'
            elif status == 'ACTIVE':
                item['unblocked_at'] = datetime.utcnow().isoformat() + 'Z'
                item['expires_at'] = None
            
            table.put_item(Item=item)
            logger.info(f"Created new DynamoDB record for {user_id} with status {status}")
        else:
            # Update existing item
            update_expression = 'SET #status = :status, last_status_change = :now, last_status_reason = :reason'
            expression_values = {
                ':status': status,
                ':now': datetime.utcnow().isoformat(),
                ':reason': reason
            }
            
            # Add specific timestamps based on status
            if status == 'BLOCKED':
                update_expression += ', blocked_at = :blocked_at'
                expression_values[':blocked_at'] = datetime.utcnow().isoformat() + 'Z'
                
                # Add expiration date if provided
                if expires_at:
                    update_expression += ', expires_at = :expires_at'
                    expression_values[':expires_at'] = expires_at
                else:
                    update_expression += ', expires_at = :expires_at'
                    expression_values[':expires_at'] = 'Indefinite'
                    
            elif status == 'ACTIVE':
                update_expression += ', unblocked_at = :unblocked_at'
                expression_values[':unblocked_at'] = datetime.utcnow().isoformat() + 'Z'
                # Clear expiration when unblocking
                update_expression += ', expires_at = :expires_at'
                expression_values[':expires_at'] = None
            
            table.update_item(
                Key={'user_id': user_id, 'date': today},
                UpdateExpression=update_expression,
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues=expression_values
            )
            logger.info(f"Updated DynamoDB status for {user_id} to {status} (expires: {expires_at})")
        
    except Exception as e:
        logger.error(f"Error updating DynamoDB status for {user_id}: {str(e)}")
        # Don't raise exception as this is not critical for the blocking operation

def send_block_notification(user_id: str, reason: str, usage_record: Dict[str, Any], performed_by: str) -> None:
    """
    Send notification when user is blocked (including enhanced email for all block types)
    
    Args:
        user_id: The user ID that was blocked
        reason: Reason for blocking
        usage_record: Current usage record (with expires_at information)
        performed_by: Who performed the block
    """
    try:
        # Send SNS notification
        message = {
            'event_type': 'user_blocked',
            'user_id': user_id,
            'reason': reason,
            'blocked_at': datetime.utcnow().isoformat(),
            'current_usage': usage_record.get('request_count', 0),
            'daily_limit': usage_record.get('daily_limit', 0),
            'team': usage_record.get('team', 'unknown'),
            'date': usage_record.get('date', date.today().isoformat()),
            'performed_by': performed_by,
            'expires_at': usage_record.get('expires_at')
        }
        
        sns.publish(
            TopicArn=SNS_TOPIC_ARN,
            Subject=f"Bedrock User Blocked: {user_id}",
            Message=json.dumps(message, indent=2)
        )
        
        # Send enhanced email notification for all block types
        if email_service:
            try:
                if performed_by != 'system':
                    # Admin blocking email
                    email_sent = email_service.send_admin_blocking_email(user_id, performed_by, reason, usage_record)
                    if email_sent:
                        logger.info(f"Sent admin blocking email for {user_id}")
                    else:
                        logger.warning(f"Failed to send admin blocking email for {user_id}")
                else:
                    # Automatic blocking email
                    email_sent = email_service.send_blocking_email(user_id, usage_record, reason)
                    if email_sent:
                        logger.info(f"Sent automatic blocking email for {user_id}")
                    else:
                        logger.warning(f"Failed to send automatic blocking email for {user_id}")
            except Exception as e:
                logger.error(f"Error sending blocking email for {user_id}: {str(e)}")
        
        logger.info(f"Sent block notification for {user_id}")
        
    except Exception as e:
        logger.error(f"Error sending block notification for {user_id}: {str(e)}")

def send_unblock_notification(user_id: str, reason: str, performed_by: str) -> None:
    """
    Send notification when user is unblocked (including enhanced email for all unblock types)
    
    Args:
        user_id: The user ID that was unblocked
        reason: Reason for unblocking
        performed_by: Who performed the unblock
    """
    try:
        # Send SNS notification
        message = {
            'event_type': 'user_unblocked',
            'user_id': user_id,
            'reason': reason,
            'unblocked_at': datetime.utcnow().isoformat(),
            'performed_by': performed_by
        }
        
        sns.publish(
            TopicArn=SNS_TOPIC_ARN,
            Subject=f"Bedrock User Unblocked: {user_id}",
            Message=json.dumps(message, indent=2)
        )
        
        # Send enhanced email notification for all unblock types
        if email_service:
            try:
                if performed_by != 'system' and performed_by != 'daily_reset':
                    # Admin unblocking email
                    email_sent = email_service.send_admin_unblocking_email(user_id, performed_by, reason)
                    if email_sent:
                        logger.info(f"Sent admin unblocking email for {user_id}")
                    else:
                        logger.warning(f"Failed to send admin unblocking email for {user_id}")
                else:
                    # Automatic unblocking email
                    email_sent = email_service.send_unblocking_email(user_id, reason)
                    if email_sent:
                        logger.info(f"Sent automatic unblocking email for {user_id}")
                    else:
                        logger.warning(f"Failed to send automatic unblocking email for {user_id}")
            except Exception as e:
                logger.error(f"Error sending unblocking email for {user_id}: {str(e)}")
        
        logger.info(f"Sent unblock notification for {user_id}")
        
    except Exception as e:
        logger.error(f"Error sending unblock notification for {user_id}: {str(e)}")

def set_block_performed_by(user_id: str, performed_by: str) -> None:
    """
    Set who performed the block operation in DynamoDB
    
    Args:
        user_id: The user ID that was blocked
        performed_by: Who performed the block (admin user or 'system')
    """
    try:
        table = dynamodb.Table(TABLE_NAME)
        today = date.today().isoformat()
        
        # Set admin_protection_by field to track who performed the block
        # Use upsert to handle missing records
        table.update_item(
            Key={'user_id': user_id, 'date': today},
            UpdateExpression='SET admin_protection_by = :by',
            ExpressionAttributeValues={
                ':by': performed_by
            },
            ReturnValues='NONE'
        )
        
        logger.info(f"Set block performed by {performed_by} for user {user_id}")
        
    except Exception as e:
        logger.warning(f"Could not set block performed by for {user_id}: {str(e)}")
        # Don't raise exception as this is not critical for the main operation

def set_administrative_protection(user_id: str, performed_by: str) -> None:
    """
    Set administrative protection flag for user to prevent automatic blocking today
    
    Args:
        user_id: The user ID to protect
        performed_by: Who performed the manual unblock
    """
    try:
        table = dynamodb.Table(TABLE_NAME)
        today = date.today().isoformat()
        
        # Set admin_protection flag in DynamoDB
        table.update_item(
            Key={'user_id': user_id, 'date': today},
            UpdateExpression='SET admin_protection = :protection, admin_protection_by = :by, admin_protection_at = :at',
            ExpressionAttributeValues={
                ':protection': True,
                ':by': performed_by,
                ':at': datetime.utcnow().isoformat()
            }
        )
        
        logger.info(f"Set administrative protection for {user_id} by {performed_by}")
        
    except Exception as e:
        logger.error(f"Error setting administrative protection for {user_id}: {str(e)}")
        # Don't raise exception as this is not critical for the main operation

def clear_administrative_protection(user_id: str) -> None:
    """
    Clear administrative protection flag for user when unblocked by automatic expiration
    This ensures the user returns to normal ACTIVE state instead of ACTIVE ADMIN
    
    Args:
        user_id: The user ID to clear protection from
    """
    try:
        table = dynamodb.Table(TABLE_NAME)
        today = date.today().isoformat()
        
        # Clear admin_protection flag in DynamoDB
        table.update_item(
            Key={'user_id': user_id, 'date': today},
            UpdateExpression='SET admin_protection = :protection, admin_protection_cleared_at = :at',
            ExpressionAttributeValues={
                ':protection': False,
                ':at': datetime.utcnow().isoformat()
            }
        )
        
        logger.info(f"Cleared administrative protection for {user_id} due to automatic expiration")
        
    except Exception as e:
        logger.error(f"Error clearing administrative protection for {user_id}: {str(e)}")
        # Don't raise exception as this is not critical for the main operation

def send_warning_notification(user_id: str, usage_record: Dict[str, Any]) -> None:
    """
    Send warning notification when user reaches 80% of daily limit
    
    Args:
        user_id: The user ID that reached warning threshold
        usage_record: Current usage record from DynamoDB
    """
    try:
        current_usage = int(usage_record.get('request_count', 0))
        daily_limit = int(usage_record.get('daily_limit', 250))
        percentage = int((current_usage / daily_limit) * 100) if daily_limit > 0 else 0
        
        # Send SNS notification
        message = {
            'event_type': 'user_warning',
            'user_id': user_id,
            'warning_at': datetime.utcnow().isoformat(),
            'current_usage': current_usage,
            'daily_limit': daily_limit,
            'percentage': percentage,
            'team': usage_record.get('team', 'unknown'),
            'date': usage_record.get('date', date.today().isoformat()),
            'threshold': '80%'
        }
        
        sns.publish(
            TopicArn=SNS_TOPIC_ARN,
            Subject=f"Bedrock Usage Warning: {user_id} ({percentage}%)",
            Message=json.dumps(message, indent=2)
        )
        
        # Send warning email
        if email_service:
            try:
                email_sent = email_service.send_warning_email(user_id, usage_record)
                if email_sent:
                    logger.info(f"Sent warning email for {user_id} at {percentage}% usage")
                else:
                    logger.warning(f"Failed to send warning email for {user_id}")
            except Exception as e:
                logger.error(f"Error sending warning email for {user_id}: {str(e)}")
        
        logger.info(f"Sent warning notification for {user_id} at {percentage}% usage ({current_usage}/{daily_limit})")
        
    except Exception as e:
        logger.error(f"Error sending warning notification for {user_id}: {str(e)}")

def log_operation_to_history(user_id: str, operation: str, reason: str, performed_by: str, status: str) -> None:
    """
    Log blocking/unblocking operation to history
    
    Args:
        user_id: The user ID
        operation: BLOCK or UNBLOCK
        reason: Reason for the operation
        performed_by: Who performed the operation
        status: SUCCESS or FAILED
    """
    try:
        operation_data = {
            'action': 'log_operation',
            'operation': {
                'user_id': user_id,
                'operation': operation,
                'reason': reason,
                'performed_by': performed_by,
                'status': status,
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            }
        }
        
        # Invoke bedrock-blocking-history Lambda function
        lambda_client.invoke(
            FunctionName='bedrock-blocking-history',
            InvocationType='Event',  # Asynchronous invocation
            Payload=json.dumps(operation_data)
        )
        
        logger.info(f"Logged {operation} operation for {user_id} to history")
        
    except Exception as e:
        logger.error(f"Error logging operation to history for {user_id}: {str(e)}")
        # Don't raise exception as this is not critical for the main operation


# For testing purposes
if __name__ == "__main__":
    # Test events
    test_block_event = {
        "action": "block",
        "user_id": "test_user_001",
        "reason": "manual_admin_block",
        "performed_by": "admin_user",
        "usage_record": {
            "request_count": 55,
            "daily_limit": 50,
            "team": "test_team",
            "date": "2025-01-15"
        }
    }
    
    test_unblock_event = {
        "action": "unblock",
        "user_id": "test_user_001",
        "reason": "manual_admin_unblock",
        "performed_by": "admin_user"
    }
    
    test_check_event = {
        "action": "check_status",
        "user_id": "test_user_001"
    }
    
    # Mock context
    class MockContext:
        def __init__(self):
            self.function_name = "bedrock-policy-manager-enhanced"
            self.memory_limit_in_mb = 256
            self.invoked_function_arn = "arn:aws:lambda:eu-west-1:701055077130:function:bedrock-policy-manager-enhanced"
    
    # Test the handlers
    print("Testing admin block operation:")
    result = lambda_handler(test_block_event, MockContext())
    print(json.dumps(result, indent=2))
    
    print("\nTesting check status operation:")
    result = lambda_handler(test_check_event, MockContext())
    print(json.dumps(result, indent=2))
    
    print("\nTesting admin unblock operation:")
    result = lambda_handler(test_unblock_event, MockContext())
    print(json.dumps(result, indent=2))
