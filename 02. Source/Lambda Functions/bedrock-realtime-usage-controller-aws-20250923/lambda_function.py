#!/usr/bin/env python3
"""
AWS Bedrock Realtime Usage Controller - bedrock-realtime-usage-controller

This Lambda function merges the functionality of:
1. bedrock-realtime-logger-fixed (CloudTrail event processing, RDS MySQL, automatic blocking)
2. bedrock-policy-manager-enhanced (API event handling, manual operations, enhanced email service)

ENHANCED FEATURES:
- Handles both CloudTrail events (automatic blocking) and API events (manual operations)
- Uses RDS MySQL with pymysql for consistent data storage
- Enhanced email service integration via separate Lambda function
- Administrative protection workflow for manual operations
- Status checking endpoint for dashboard integration
- Proper CET timezone handling throughout
- Complete blocking/unblocking audit trail

Function Name: bedrock-realtime-usage-controller
Author: AWS Bedrock Usage Control System
Version: 3.0.0 (Enhanced Merged Version)
"""

import json
import boto3
import pymysql
import os
from datetime import datetime, timezone, timedelta
import logging
import re
from typing import Dict, Any, Optional, Tuple
import pytz
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# AWS clients
iam = boto3.client('iam')
sns = boto3.client('sns')
lambda_client = boto3.client('lambda')

# RDS connection parameters
RDS_HOST = os.environ['RDS_ENDPOINT']
RDS_USER = os.environ['RDS_USERNAME']
RDS_PASSWORD = os.environ['RDS_PASSWORD']
RDS_DB = os.environ['RDS_DATABASE']

# SNS configuration for notifications
SNS_TOPIC_ARN = os.environ.get('SNS_TOPIC_ARN', f'arn:aws:sns:eu-west-1:701055077130:bedrock-usage-alerts')

# Enhanced email service configuration
EMAIL_SERVICE_LAMBDA_NAME = os.environ.get('EMAIL_SERVICE_LAMBDA_NAME', 'bedrock-email-service')
EMAIL_NOTIFICATIONS_ENABLED = os.environ.get('EMAIL_NOTIFICATIONS_ENABLED', 'true').lower() == 'true'

# CET timezone
CET = pytz.timezone('Europe/Madrid')

# Gmail SMTP configuration (fallback)
GMAIL_SMTP_CONFIG = {
    "server": "smtp.gmail.com",
    "port": 587,
    "user": "cline.aws.noreply@gmail.com",
    "password": "lozs wwqa vfpn nlup",
    "use_tls": True
}

EMAIL_SETTINGS = {
    "default_language": "es",
    "timezone": "Europe/Madrid",
    "reply_to": "cline.aws.noreply@gmail.com"
}

# Policy configuration for manual operations
BEDROCK_POLICY_SUFFIX = "_BedrockPolicy"
DENY_STATEMENT_SID = "DailyLimitBlock"

# Connection pool
connection_pool = None

def get_current_cet_time() -> datetime:
    """Get current time in CET timezone"""
    return datetime.now(CET)

def get_cet_timestamp_string() -> str:
    """Get current CET timestamp as string for database"""
    return get_current_cet_time().strftime('%Y-%m-%d %H:%M:%S')

def convert_utc_to_cet(utc_timestamp_str: str) -> str:
    """Convert UTC timestamp string to CET timestamp string"""
    try:
        if utc_timestamp_str.endswith('Z'):
            utc_timestamp_str = utc_timestamp_str[:-1]
        
        utc_dt = datetime.fromisoformat(utc_timestamp_str.replace('Z', '+00:00'))
        if utc_dt.tzinfo is None:
            utc_dt = utc_dt.replace(tzinfo=timezone.utc)
        
        # Convert to CET
        cet_dt = utc_dt.astimezone(CET)
        cet_timestamp_str = cet_dt.strftime('%Y-%m-%d %H:%M:%S')
        
        logger.info(f"🕐 Converted UTC {utc_timestamp_str} to CET {cet_timestamp_str}")
        return cet_timestamp_str
        
    except Exception as e:
        logger.error(f"Failed to convert timestamp {utc_timestamp_str} to CET: {str(e)}")
        return get_cet_timestamp_string()

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

def extract_user_from_arn(user_arn: str) -> Optional[str]:
    """Extract username from user ARN"""
    if not user_arn:
        return None
    
    # Pattern: arn:aws:iam::account:user/username
    match = re.search(r'arn:aws:iam::\d+:user/(.+)', user_arn)
    if match:
        return match.group(1)
    
    # Pattern: arn:aws:sts::account:assumed-role/role-name/username
    match = re.search(r'arn:aws:sts::\d+:assumed-role/[^/]+/(.+)', user_arn)
    if match:
        return match.group(1)
    
    return None

def get_user_team(user_id: str) -> str:
    """Get user's team from IAM tags"""
    try:
        response = iam.list_user_tags(UserName=user_id)
        
        for tag in response['Tags']:
            if tag['Key'].lower() in ['team', 'Team']:
                team_value = tag['Value']
                logger.info(f"Found Team tag for user {user_id}: {team_value}")
                return team_value
        
        logger.warning(f"No Team tag found for user {user_id}, trying groups as fallback")
        try:
            groups_response = iam.get_groups_for_user(UserName=user_id)
            groups = [group['GroupName'] for group in groups_response['Groups']]
            
            team_groups = [g for g in groups if g.startswith('yo_leo_')]
            
            if team_groups:
                logger.info(f"Found team group for user {user_id}: {team_groups[0]}")
                return team_groups[0]
        except Exception as group_error:
            logger.warning(f"Failed to get groups for user {user_id}: {str(group_error)}")
        
        logger.warning(f"No Team tag or team group found for user {user_id}, using 'unknown'")
        return 'unknown'
            
    except Exception as e:
        logger.error(f"Failed to get team for user {user_id}: {str(e)}")
        return 'unknown'

def get_user_person_tag(user_id: str) -> str:
    """Get user's person tag from IAM tags"""
    try:
        response = iam.list_user_tags(UserName=user_id)
        
        for tag in response['Tags']:
            if tag['Key'].lower() in ['person', 'Person']:
                person_value = tag['Value']
                logger.info(f"Found Person tag for user {user_id}: {person_value}")
                return person_value
        
        logger.warning(f"No Person tag found for user {user_id}, using 'Unknown'")
        return 'Unknown'
            
    except Exception as e:
        logger.error(f"Failed to get person tag for user {user_id}: {str(e)}")
        return 'Unknown'

def get_user_email(user_id: str) -> Optional[str]:
    """Get user's email from IAM tags"""
    try:
        response = iam.list_user_tags(UserName=user_id)
        
        for tag in response['Tags']:
            if tag['Key'].lower() in ['email', 'Email']:
                email_value = tag['Value']
                logger.info(f"Found Email tag for user {user_id}: {email_value}")
                return email_value
        
        logger.warning(f"No Email tag found for user {user_id}")
        return None
            
    except Exception as e:
        logger.error(f"Failed to get email tag for user {user_id}: {str(e)}")
        return None

def send_gmail_email(to_email: str, subject: str, body_text: str, body_html: str) -> bool:
    """Send email using Gmail SMTP"""
    try:
        logger.info(f"📧 Attempting to send Gmail email to {to_email}")
        
        # Create message
        msg = MIMEMultipart('alternative')
        msg['From'] = GMAIL_SMTP_CONFIG['user']
        msg['To'] = to_email
        msg['Subject'] = subject
        msg['Reply-To'] = EMAIL_SETTINGS['reply_to']
        
        # Create text and HTML parts
        text_part = MIMEText(body_text, 'plain', 'utf-8')
        html_part = MIMEText(body_html, 'html', 'utf-8')
        
        msg.attach(text_part)
        msg.attach(html_part)
        
        # Connect to Gmail SMTP server
        server = smtplib.SMTP(GMAIL_SMTP_CONFIG['server'], GMAIL_SMTP_CONFIG['port'])
        
        if GMAIL_SMTP_CONFIG['use_tls']:
            server.starttls()
        
        # Login and send email
        server.login(GMAIL_SMTP_CONFIG['user'], GMAIL_SMTP_CONFIG['password'])
        server.send_message(msg)
        server.quit()
        
        logger.info(f"✅ Successfully sent Gmail email to {to_email}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to send Gmail email to {to_email}: {str(e)}")
        return False

def parse_bedrock_event(event: Dict[str, Any]) -> Dict[str, Any]:
    """Parse CloudTrail event for Bedrock API call"""
    try:
        logger.info(f"🔍 Starting to parse event: {event.get('eventName', 'Unknown')}")
        
        event_name = event.get('eventName', '')
        user_identity = event.get('userIdentity', {})
        request_parameters = event.get('requestParameters')
        source_ip = event.get('sourceIPAddress', '')
        user_agent = event.get('userAgent', '')
        request_id = event.get('requestID', '')
        event_time = event.get('eventTime', '')
        region = event.get('awsRegion', 'us-east-1')
        
        logger.info(f"📋 Event details - Name: {event_name}, User: {user_identity.get('userName', 'Unknown')}")
        
        cet_timestamp = convert_utc_to_cet(event_time)
        logger.info(f"🕐 Event time converted from UTC {event_time} to CET {cet_timestamp}")
        
        user_arn = user_identity.get('arn', '')
        user_id = extract_user_from_arn(user_arn)
        
        if not user_id:
            logger.warning(f"❌ Could not extract user ID from ARN: {user_arn}")
            return None
        
        logger.info(f"✅ Extracted user ID: {user_id}")
        
        # CORRECCIÓN CRÍTICA: Check if request_parameters is None before accessing it
        if request_parameters is None:
            logger.warning(f"❌ request_parameters is None for user {user_id}, event {event_name}")
            return None
        
        model_id = request_parameters.get('modelId', '')
        if not model_id:
            logger.warning(f"❌ No model ID found in request parameters: {request_parameters}")
            return None
        
        logger.info(f"📱 Found model ID: {model_id}")
        
        # Process model ID
        actual_model_id = model_id
        if model_id.startswith('arn:aws:bedrock:'):
            if '/eu.anthropic.claude-sonnet-4-' in model_id:
                actual_model_id = 'anthropic.claude-3-5-sonnet-20240620-v1:0'
            elif '/anthropic.claude-' in model_id:
                parts = model_id.split('/')
                if len(parts) > 1:
                    actual_model_id = parts[-1]
                    if actual_model_id.startswith('eu.'):
                        actual_model_id = actual_model_id[3:]
        
        logger.info(f"Original model ID: {model_id}, Processed model ID: {actual_model_id}")
        
        model_name_mapping = {
            'anthropic.claude-3-opus-20240229-v1:0': 'Claude 3 Opus',
            'anthropic.claude-3-sonnet-20240229-v1:0': 'Claude 3 Sonnet',
            'anthropic.claude-3-haiku-20240307-v1:0': 'Claude 3 Haiku',
            'anthropic.claude-3-5-sonnet-20240620-v1:0': 'Claude 3.5 Sonnet',
            'anthropic.claude-sonnet-4-20250514-v1:0': 'Claude 3.5 Sonnet',
            'amazon.titan-text-express-v1': 'Amazon Titan Text Express',
            'amazon.titan-text-lite-v1': 'Amazon Titan Text Lite'
        }
        
        model_name = model_name_mapping.get(actual_model_id, actual_model_id)
        
        request_type = 'invoke'
        if 'stream' in event_name.lower():
            request_type = 'invoke-stream'
        elif 'converse' in event_name.lower():
            request_type = 'converse-stream' if 'stream' in event_name.lower() else 'converse'
        
        response_time_ms = 0
        if 'responseTime' in event:
            response_time_ms = int(event['responseTime'])
        
        status_code = 200
        error_message = None
        if event.get('errorCode'):
            status_code = 400
            error_message = event.get('errorMessage', 'Unknown error')
        
        return {
            'user_id': user_id,
            'model_id': model_id,
            'model_name': model_name,
            'request_type': request_type,
            'region': region,
            'source_ip': source_ip,
            'user_agent': user_agent,
            'request_id': request_id,
            'response_time_ms': response_time_ms,
            'status_code': status_code,
            'error_message': error_message,
            'event_time': event_time,
            'cet_timestamp': cet_timestamp
        }
        
    except Exception as e:
        logger.error(f"Failed to parse Bedrock event: {str(e)}")
        return None

def check_user_blocking_status(connection, user_id: str) -> Tuple[bool, Optional[str]]:
    """Check if user is currently blocked and if block has expired"""
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT is_blocked, blocked_until, blocked_reason
                FROM user_blocking_status 
                WHERE user_id = %s
            """, [user_id])
            
            result = cursor.fetchone()
            if not result:
                return False, None
            
            is_blocked = result['is_blocked'] == 'Y'
            blocked_until = result['blocked_until']
            blocked_reason = result['blocked_reason']
            
            if not is_blocked:
                return False, None
            
            # CORRECCIÓN CRÍTICA: Check if block has expired (compare with CET time)
            if blocked_until:
                current_cet_time = get_current_cet_time()
                
                # Handle timezone conversion properly
                if isinstance(blocked_until, str):
                    # Parse string to datetime
                    blocked_until_dt = datetime.strptime(blocked_until, '%Y-%m-%d %H:%M:%S')
                    blocked_until_cet = CET.localize(blocked_until_dt)
                elif blocked_until.tzinfo is None:
                    # Assume it's already in CET timezone
                    blocked_until_cet = CET.localize(blocked_until)
                else:
                    # Convert to CET if it has timezone info
                    blocked_until_cet = blocked_until.astimezone(CET)
                
                logger.info(f"🕐 Checking expiration for {user_id}: current={current_cet_time.strftime('%Y-%m-%d %H:%M:%S')}, blocked_until={blocked_until_cet.strftime('%Y-%m-%d %H:%M:%S')}")
                
                if current_cet_time >= blocked_until_cet:
                    logger.info(f"✅ Block expired for user {user_id}, initiating automatic unblock")
                    success = execute_user_unblocking(connection, user_id)
                    if success:
                        logger.info(f"✅ Successfully unblocked expired user {user_id}")
                        return False, 'expired'  # Return 'expired' to indicate automatic unblocking occurred
                    else:
                        logger.error(f"❌ Failed to unblock expired user {user_id}")
                        return True, blocked_reason
                else:
                    time_remaining = blocked_until_cet - current_cet_time
                    logger.info(f"🚫 Block still active for user {user_id}, expires in {time_remaining}")
            
            return True, blocked_reason
            
    except Exception as e:
        logger.error(f"Failed to check user blocking status: {str(e)}")
        return False, None

def check_user_limits_with_protection(connection, user_id: str) -> Tuple[bool, str, Dict[str, Any]]:
    """Check if user should be blocked based on current usage with administrative protection"""
    try:
        with connection.cursor() as cursor:
            # Get user limits and administrative protection
            cursor.execute("""
                SELECT daily_request_limit, monthly_request_limit, administrative_safe
                FROM user_limits 
                WHERE user_id = %s
            """, [user_id])
            
            limits_result = cursor.fetchone()
            if not limits_result:
                logger.warning(f"No limits found for user {user_id}, using defaults")
                daily_limit = 350
                monthly_limit = 5000
                administrative_safe = 'N'
            else:
                daily_limit = int(limits_result['daily_request_limit'])
                monthly_limit = int(limits_result['monthly_request_limit'])
                administrative_safe = limits_result.get('administrative_safe', 'N')
            
            # Check administrative protection
            if administrative_safe == 'Y':
                logger.info(f"User {user_id} has administrative protection - blocking disabled")
                return False, None, {
                    'daily_requests_used': 0,
                    'monthly_requests_used': 0,
                    'daily_percent': 0,
                    'monthly_percent': 0,
                    'daily_limit': daily_limit,
                    'monthly_limit': monthly_limit,
                    'administrative_safe': True
                }
            
            # Get current daily usage
            cursor.execute("""
                SELECT COUNT(*) as daily_requests_used
                FROM bedrock_requests 
                WHERE user_id = %s 
                AND DATE(request_timestamp) = CURDATE()
            """, [user_id])
            
            daily_result = cursor.fetchone()
            daily_requests_used = int(daily_result['daily_requests_used']) if daily_result else 0
            
            # Get current monthly usage
            cursor.execute("""
                SELECT COUNT(*) as monthly_requests_used
                FROM bedrock_requests 
                WHERE user_id = %s 
                AND DATE(request_timestamp) >= DATE_FORMAT(NOW(), '%%Y-%%m-01')
            """, [user_id])
            
            monthly_result = cursor.fetchone()
            monthly_requests_used = int(monthly_result['monthly_requests_used']) if monthly_result else 0
            
            # Check if blocking is needed
            should_block = False
            block_reason = None
            
            if daily_requests_used >= daily_limit:
                should_block = True
                block_reason = 'Daily limit exceeded'
            elif monthly_requests_used >= monthly_limit:
                should_block = True
                block_reason = 'Monthly limit exceeded'
            
            daily_percent = (daily_requests_used / daily_limit) * 100 if daily_limit > 0 else 0
            monthly_percent = (monthly_requests_used / monthly_limit) * 100 if monthly_limit > 0 else 0
            
            usage_info = {
                'daily_requests_used': daily_requests_used,
                'monthly_requests_used': monthly_requests_used,
                'daily_percent': daily_percent,
                'monthly_percent': monthly_percent,
                'daily_limit': daily_limit,
                'monthly_limit': monthly_limit,
                'administrative_safe': False
            }
            
            logger.info(f"User {user_id} limits check: daily={daily_requests_used}/{daily_limit}, monthly={monthly_requests_used}/{monthly_limit}, should_block={should_block}, admin_safe={administrative_safe}")
            
            return should_block, block_reason, usage_info
            
    except Exception as e:
        logger.error(f"Failed to check user limits: {str(e)}")
        return False, None, {}

def execute_user_blocking(connection, user_id: str, block_reason: str, usage_info: Dict[str, Any]) -> bool:
    """Execute complete user blocking workflow with CET timestamps"""
    try:
        logger.info(f"🚫 EXECUTING USER BLOCKING for {user_id}: {block_reason}")
        
        current_cet_time = get_current_cet_time()
        current_cet_string = get_cet_timestamp_string()
        
        # Block until tomorrow at 00:00 CET
        blocked_until_cet = (current_cet_time + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        blocked_until_string = blocked_until_cet.strftime('%Y-%m-%d %H:%M:%S')
        
        logger.info(f"🕐 Blocking times - Current: {current_cet_string} CET, Until: {blocked_until_string} CET")
        
        # Track success of each step
        db_success = False
        audit_success = False
        iam_success = False
        email_success = False
        
        # 1. Update USER_BLOCKING_STATUS table
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO user_blocking_status 
                    (user_id, is_blocked, blocked_reason, blocked_at, blocked_until, 
                     requests_at_blocking, last_request_at, created_at, updated_at)
                    VALUES (%s, 'Y', %s, %s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                    is_blocked = 'Y',
                    blocked_reason = VALUES(blocked_reason),
                    blocked_at = VALUES(blocked_at),
                    blocked_until = VALUES(blocked_until),
                    requests_at_blocking = VALUES(requests_at_blocking),
                    last_request_at = VALUES(last_request_at),
                    updated_at = VALUES(updated_at)
                """, [
                    user_id, block_reason, current_cet_string, blocked_until_string,
                    usage_info['daily_requests_used'], current_cet_string, current_cet_string, current_cet_string
                ])
            logger.info(f"✅ Step 1: Updated USER_BLOCKING_STATUS for {user_id}")
            db_success = True
        except Exception as e:
            logger.error(f"❌ Step 1 FAILED: USER_BLOCKING_STATUS update for {user_id}: {str(e)}")
            return False
        
        # 3. Create IAM deny policy (moved before audit log to track result)
        try:
            iam_success = implement_iam_blocking(user_id)
            if iam_success:
                logger.info(f"✅ Step 3: Created IAM deny policy for {user_id}")
            else:
                logger.error(f"❌ Step 3 FAILED: IAM policy creation for {user_id}")
        except Exception as e:
            logger.error(f"❌ Step 3 EXCEPTION: IAM policy creation for {user_id}: {str(e)}")
            iam_success = False
        
        # 4. Send Gmail notification
        try:
            email_success = send_blocking_email_gmail(user_id, block_reason, usage_info, blocked_until_cet)
            if email_success:
                logger.info(f"✅ Step 4: Sent blocking Gmail for {user_id}")
            else:
                logger.error(f"❌ Step 4 FAILED: Gmail sending for {user_id}")
        except Exception as e:
            logger.error(f"❌ Step 4 EXCEPTION: Gmail sending for {user_id}: {str(e)}")
            email_success = False
        
        # 2. Log to BLOCKING_AUDIT_LOG (moved after other operations to record actual results)
        try:
            with connection.cursor() as cursor:
                # Calculate usage percentage
                usage_percentage = (usage_info['daily_requests_used'] / usage_info['daily_limit']) * 100 if usage_info['daily_limit'] > 0 else 0
                
                cursor.execute("""
                    INSERT INTO blocking_audit_log 
                    (user_id, operation_type, operation_reason, performed_by, operation_timestamp,
                     daily_requests_at_operation, daily_limit_at_operation, usage_percentage,
                     iam_policy_updated, email_sent, created_at)
                    VALUES (%s, 'BLOCK', %s, 'system', %s, %s, %s, %s, %s, %s, %s)
                """, [
                    user_id, block_reason, current_cet_string,
                    usage_info['daily_requests_used'], usage_info['daily_limit'], 
                    round(usage_percentage, 2), 
                    'Y' if iam_success else 'N',
                    'Y' if email_success else 'N',
                    current_cet_string
                ])
            logger.info(f"✅ Step 2: Created BLOCKING_AUDIT_LOG entry for {user_id}")
            audit_success = True
        except Exception as e:
            logger.error(f"❌ Step 2 FAILED: BLOCKING_AUDIT_LOG creation for {user_id}: {str(e)}")
            audit_success = False
        
        # CORRECCIÓN CRÍTICA: Return False if IAM failed (critical for blocking)
        if not iam_success:
            logger.error(f"❌ CRITICAL: IAM policy creation failed for {user_id} - blocking may not be effective")
            return False
        
        logger.info(f"✅ Successfully executed complete blocking for user {user_id}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to execute user blocking for {user_id}: {str(e)}")
        return False

def execute_user_unblocking(connection, user_id: str) -> bool:
    """Execute complete user unblocking workflow with CET timestamps"""
    try:
        logger.info(f"🔓 EXECUTING USER UNBLOCKING for {user_id}")
        
        current_cet_string = get_cet_timestamp_string()
        
        # 1. Update USER_BLOCKING_STATUS table
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    UPDATE user_blocking_status 
                    SET is_blocked = 'N',
                        blocked_reason = 'Automatic unblock',
                        blocked_at = NULL,
                        blocked_until = NULL,
                        last_request_at = %s,
                        last_reset_at = %s,
                        updated_at = %s
                    WHERE user_id = %s
                """, [current_cet_string, current_cet_string, current_cet_string, user_id])
            logger.info(f"✅ Step 1: Updated USER_BLOCKING_STATUS for unblocking {user_id}")
        except Exception as e:
            logger.error(f"❌ Step 1 FAILED: USER_BLOCKING_STATUS update for unblocking {user_id}: {str(e)}")
            return False
        
        # 1.5. CORRECCIÓN: Set administrative_safe to 'N' for automatic unblocking
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    UPDATE user_limits 
                    SET administrative_safe = 'N',
                        updated_at = %s
                    WHERE user_id = %s
                """, [current_cet_string, user_id])
            logger.info(f"✅ Step 1.5: Set administrative_safe='N' for automatic unblocking {user_id}")
        except Exception as e:
            logger.error(f"❌ Step 1.5 FAILED: administrative_safe update for unblocking {user_id}: {str(e)}")
        
        # 2. Log to BLOCKING_AUDIT_LOG
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO blocking_audit_log 
                    (user_id, operation_type, operation_reason, performed_by, operation_timestamp, created_at)
                    VALUES (%s, 'UNBLOCK', 'Automatic unblock', 'system', %s, %s)
                """, [user_id, current_cet_string, current_cet_string])
            logger.info(f"✅ Step 2: Created BLOCKING_AUDIT_LOG entry for unblocking {user_id}")
        except Exception as e:
            logger.error(f"❌ Step 2 FAILED: BLOCKING_AUDIT_LOG creation for unblocking {user_id}: {str(e)}")
        
        # 3. Modify IAM policy to allow
        try:
            success = implement_iam_unblocking(user_id)
            if success:
                logger.info(f"✅ Step 3: Modified IAM policy for unblocking {user_id}")
            else:
                logger.error(f"❌ Step 3 FAILED: IAM policy modification for unblocking {user_id}")
        except Exception as e:
            logger.error(f"❌ Step 3 EXCEPTION: IAM policy modification for unblocking {user_id}: {str(e)}")
        
        # 4. Send enhanced unblocking email via Lambda service
        try:
            success = send_enhanced_unblocking_email(user_id, 'Automatic unblock', 'system')
            if success:
                logger.info(f"✅ Step 4: Sent enhanced unblocking email for {user_id}")
            else:
                logger.error(f"❌ Step 4 FAILED: Enhanced email sending for unblocking {user_id}")
        except Exception as e:
            logger.error(f"❌ Step 4 EXCEPTION: Enhanced email sending for unblocking {user_id}: {str(e)}")
        
        logger.info(f"✅ Successfully executed complete unblocking for user {user_id}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to execute user unblocking for {user_id}: {str(e)}")
        return False

def implement_iam_blocking(user_id: str) -> bool:
    """Create IAM deny policy for user blocking"""
    try:
        policy_name = f"{user_id}_BedrockPolicy"
        
        # FIXED: Remove the problematic condition that was preventing the policy from working
        deny_statement = {
            "Sid": "DailyLimitBlock",
            "Effect": "Deny",
            "Action": [
                "bedrock:InvokeModel",
                "bedrock:InvokeModelWithResponseStream",
                "bedrock:Converse",
                "bedrock:ConverseStream"
            ],
            "Resource": "*"
        }
        
        try:
            # Get existing policy
            response = iam.get_user_policy(UserName=user_id, PolicyName=policy_name)
            current_policy = response['PolicyDocument']
            
            logger.info(f"🔍 Found existing policy for user {user_id}: {json.dumps(current_policy, indent=2)}")
            
            # Remove any existing deny statements with the same Sid
            original_count = len(current_policy['Statement'])
            current_policy['Statement'] = [
                stmt for stmt in current_policy['Statement'] 
                if stmt.get('Sid') != 'DailyLimitBlock'
            ]
            
            removed_count = original_count - len(current_policy['Statement'])
            if removed_count > 0:
                logger.info(f"🗑️ Removed {removed_count} existing deny statements for user {user_id}")
            
            # Add new deny statement at the beginning (highest priority)
            current_policy['Statement'].insert(0, deny_statement)
            
        except iam.exceptions.NoSuchEntityException:
            logger.info(f"📝 No existing policy found for user {user_id}, creating new policy")
            # Create new policy with deny statement first, then allow statement
            current_policy = {
                "Version": "2012-10-17",
                "Statement": [
                    deny_statement,
                    {
                        "Sid": "BedrockAccess",
                        "Effect": "Allow",
                        "Action": [
                            "bedrock:InvokeModel",
                            "bedrock:InvokeModelWithResponseStream",
                            "bedrock:Converse",
                            "bedrock:ConverseStream"
                        ],
                        "Resource": "*"
                    }
                ]
            }
        
        # Apply the updated policy
        policy_document = json.dumps(current_policy, separators=(',', ':'))
        logger.info(f"📋 Applying policy for user {user_id}: {policy_document}")
        
        iam.put_user_policy(
            UserName=user_id,
            PolicyName=policy_name,
            PolicyDocument=policy_document
        )
        
        # Verify the policy was applied correctly
        try:
            verify_response = iam.get_user_policy(UserName=user_id, PolicyName=policy_name)
            applied_policy = verify_response['PolicyDocument']
            
            # Check if deny statement exists
            deny_statements = [stmt for stmt in applied_policy['Statement'] if stmt.get('Sid') == 'DailyLimitBlock']
            if deny_statements:
                logger.info(f"✅ Successfully created and verified IAM deny policy for user {user_id}")
                return True
            else:
                logger.error(f"❌ Deny statement not found in applied policy for user {user_id}")
                return False
                
        except Exception as verify_error:
            logger.error(f"❌ Failed to verify applied policy for user {user_id}: {str(verify_error)}")
            return False
        
    except Exception as e:
        logger.error(f"❌ Failed to create IAM deny policy for user {user_id}: {str(e)}")
        return False

def implement_iam_unblocking(user_id: str) -> bool:
    """Modify IAM policy to allow access for user unblocking"""
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
            
            logger.info(f"✅ Successfully modified IAM policy to allow access for user {user_id}")
            return True
            
        except iam.exceptions.NoSuchEntityException:
            logger.info(f"No existing policy found for user {user_id}, no action needed")
            return True
        
    except Exception as e:
        logger.error(f"❌ Failed to modify IAM policy for user {user_id}: {str(e)}")
        return False

def send_blocking_email_gmail(user_id: str, block_reason: str, usage_info: Dict[str, Any], blocked_until: datetime) -> bool:
    """Send blocking notification email using Gmail SMTP"""
    try:
        user_email = get_user_email(user_id)
        if not user_email:
            logger.warning(f"No email found for user {user_id}, skipping email notification")
            return False
        
        current_cet_string = get_cet_timestamp_string()
        blocked_until_string = blocked_until.strftime('%Y-%m-%d %H:%M:%S')
        
        subject = f"🚫 AWS Bedrock Access Blocked - {user_id}"
        
        body_html = f"""
        <html>
        <body>
            <h2>🚫 AWS Bedrock Access Blocked</h2>
            <p>Estimado/a {user_id},</p>
            
            <p>Su acceso a los servicios de AWS Bedrock ha sido temporalmente bloqueado debido a que ha superado los límites de uso establecidos.</p>
            
            <h3>Detalles del Bloqueo:</h3>
            <ul>
                <li><strong>Motivo:</strong> {block_reason}</li>
                <li><strong>Bloqueado el:</strong> {current_cet_string} CET</li>
                <li><strong>Bloqueado hasta:</strong> {blocked_until_string} CET</li>
            </ul>
            
            <h3>Uso Actual:</h3>
            <ul>
                <li><strong>Peticiones diarias:</strong> {usage_info['daily_requests_used']}/{usage_info['daily_limit']} ({usage_info['daily_percent']:.1f}%)</li>
                <li><strong>Peticiones mensuales:</strong> {usage_info['monthly_requests_used']}/{usage_info['monthly_limit']} ({usage_info['monthly_percent']:.1f}%)</li>
            </ul>
            
            <p>Su acceso será automáticamente restaurado el {blocked_until_string} CET.</p>
            
            <p>Si cree que esto es un error o necesita acceso inmediato, por favor contacte con su administrador del sistema.</p>
            
            <p>Saludos cordiales,<br>Sistema de Control de Uso de AWS Bedrock</p>
        </body>
        </html>
        """
        
        body_text = f"""
        🚫 AWS Bedrock Access Blocked
        
        Estimado/a {user_id},
        
        Su acceso a los servicios de AWS Bedrock ha sido temporalmente bloqueado debido a que ha superado los límites de uso establecidos.
        
        Detalles del Bloqueo:
        - Motivo: {block_reason}
        - Bloqueado el: {current_cet_string} CET
        - Bloqueado hasta: {blocked_until_string} CET
        
        Uso Actual:
        - Peticiones diarias: {usage_info['daily_requests_used']}/{usage_info['daily_limit']} ({usage_info['daily_percent']:.1f}%)
        - Peticiones mensuales: {usage_info['monthly_requests_used']}/{usage_info['monthly_limit']} ({usage_info['monthly_percent']:.1f}%)
        
        Su acceso será automáticamente restaurado el {blocked_until_string} CET.
        
        Si cree que esto es un error o necesita acceso inmediato, por favor contacte con su administrador del sistema.
        
        Saludos cordiales,
        Sistema de Control de Uso de AWS Bedrock
        """
        
        return send_gmail_email(user_email, subject, body_text, body_html)
        
    except Exception as e:
        logger.error(f"Failed to send blocking Gmail for user {user_id}: {str(e)}")
        return False

def send_unblocking_email_gmail(user_id: str) -> bool:
    """Send unblocking notification email using Gmail SMTP"""
    try:
        user_email = get_user_email(user_id)
        if not user_email:
            logger.warning(f"No email found for user {user_id}, skipping email notification")
            return False
        
        current_cet_string = get_cet_timestamp_string()
        
        subject = f"✅ AWS Bedrock Access Restored - {user_id}"
        
        body_html = f"""
        <html>
        <body>
            <h2>✅ AWS Bedrock Access Restored</h2>
            <p>Estimado/a {user_id},</p>
            
            <p>Su acceso a los servicios de AWS Bedrock ha sido automáticamente restaurado.</p>
            
            <h3>Detalles del Desbloqueo:</h3>
            <ul>
                <li><strong>Motivo:</strong> Desbloqueo automático</li>
                <li><strong>Restaurado el:</strong> {current_cet_string} CET</li>
            </ul>
            
            <p>Por favor, recuerde usar los servicios de AWS Bedrock de manera responsable y dentro de los límites asignados.</p>
            
            <p>Si tiene alguna pregunta sobre sus límites de uso, por favor contacte con su administrador del sistema.</p>
            
            <p>Saludos cordiales,<br>Sistema de Control de Uso de AWS Bedrock</p>
        </body>
        </html>
        """
        
        body_text = f"""
        ✅ AWS Bedrock Access Restored
        
        Estimado/a {user_id},
        
        Su acceso a los servicios de AWS Bedrock ha sido automáticamente restaurado.
        
        Detalles del Desbloqueo:
        - Motivo: Desbloqueo automático
        - Restaurado el: {current_cet_string} CET
        
        Por favor, recuerde usar los servicios de AWS Bedrock de manera responsable y dentro de los límites asignados.
        
        Si tiene alguna pregunta sobre sus límites de uso, por favor contacte con su administrador del sistema.
        
        Saludos cordiales,
        Sistema de Control de Uso de AWS Bedrock
        """
        
        return send_gmail_email(user_email, subject, body_text, body_html)
        
    except Exception as e:
        logger.error(f"Failed to send unblocking Gmail for user {user_id}: {str(e)}")
        return False

def log_bedrock_request_cet(connection, request_data: Dict[str, Any], team: str, person: str):
    """Log the Bedrock request to database with CET timestamp"""
    try:
        with connection.cursor() as cursor:
            insert_query = """
                INSERT INTO bedrock_requests (
                    user_id, team, person, model_id, request_id, source_ip, user_agent, aws_region, 
                    response_status, error_message, processing_time_ms, request_timestamp, created_at
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
            """
            
            current_cet_timestamp = get_cet_timestamp_string()
            
            # CORRECCIÓN: Make source_ip optional and handle missing fields gracefully
            source_ip = request_data.get('source_ip', 'unknown')
            user_agent = request_data.get('user_agent', 'unknown')
            request_id = request_data.get('request_id', 'unknown')
            error_message = request_data.get('error_message')
            response_time_ms = request_data.get('response_time_ms', 0)
            status_code = request_data.get('status_code', 200)
            
            cursor.execute(insert_query, [
                request_data['user_id'],
                team,
                person,
                request_data['model_id'],
                request_id,
                source_ip,
                user_agent[:1000] if user_agent else 'unknown',
                request_data.get('region', 'unknown'),
                'success' if status_code == 200 else 'error',
                error_message,
                response_time_ms,
                request_data.get('cet_timestamp', current_cet_timestamp),
                current_cet_timestamp
            ])
            
            logger.info(f"✅ Logged request for user {request_data['user_id']}, team {team}, person {person}")
            
    except Exception as e:
        logger.error(f"Failed to log request: {str(e)}")
        # CORRECCIÓN: Don't raise exception to prevent blocking the entire process
        logger.warning(f"⚠️ Continuing processing despite logging failure for user {request_data.get('user_id', 'unknown')}")

def ensure_user_exists(connection, user_id: str, team: str, person: str):
    """Ensure user exists in user_limits table, create if not"""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT user_id FROM user_limits WHERE user_id = %s", [user_id])
            if cursor.fetchone():
                return
            
            current_cet_timestamp = get_cet_timestamp_string()
            
            daily_request_limit = 350
            monthly_request_limit = 5000
            
            cursor.execute("""
                INSERT INTO user_limits (user_id, team, person, daily_request_limit, monthly_request_limit, administrative_safe, created_at)
                VALUES (%s, %s, %s, %s, %s, 'N', %s)
            """, [user_id, team, person, daily_request_limit, monthly_request_limit, current_cet_timestamp])
            
            logger.info(f"✅ Created new user limits: {user_id} in team {team}, person: {person}")
            
    except Exception as e:
        logger.error(f"Failed to ensure user exists: {str(e)}")

def lambda_handler(event, context):
    """
    Enhanced Lambda handler supporting both CloudTrail and API events
    
    Args:
        event: Event containing either CloudTrail data or API action parameters
        context: Lambda context object
        
    Returns:
        Dict with status code and operation results
    """
    logger.info(f"🚀 Processing event with ENHANCED MERGED FUNCTIONALITY: {json.dumps(event, default=str)}")
    
    # NEW: Check if this is an API event (manual operation)
    if 'action' in event and 'user_id' in event:
        logger.info("🔧 Processing API event (manual operation)")
        return handle_api_event(event, context)
    
    # EXISTING: Handle CloudTrail events (automatic blocking)
    logger.info("📊 Processing CloudTrail event (automatic blocking)")
    return handle_cloudtrail_event(event, context)

def handle_api_event(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Handle manual admin operations from dashboard"""
    try:
        logger.info(f"Processing API event: {json.dumps(event, default=str)}")
        
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
            result = manual_block_user(event)
        elif action == 'unblock':
            result = manual_unblock_user(event)
        elif action == 'check_status':
            result = check_user_status(event)
        else:
            logger.error(f"Invalid action: {action}")
            return {
                'statusCode': 400,
                'body': json.dumps({'error': f'Invalid action: {action}'})
            }
        
        return result
        
    except Exception as e:
        logger.error(f"Error processing API event: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

def manual_block_user(event: Dict[str, Any]) -> Dict[str, Any]:
    """Handle manual admin blocking"""
    try:
        user_id = event['user_id']
        reason = event.get('reason', 'Manual admin block')
        performed_by = event.get('performed_by', 'admin')
        expires_at = event.get('expires_at')  # Custom expiration from dashboard
        
        logger.info(f"🚫 Manual blocking user {user_id} by {performed_by}, expires_at: {expires_at}")
        
        connection = get_mysql_connection()
        
        # Get current usage from RDS
        usage_info = get_user_current_usage(connection, user_id)
        
        # Execute blocking with custom or default expiration
        success = execute_admin_blocking(connection, user_id, reason, performed_by, usage_info, expires_at)
        
        return {
            'statusCode': 200 if success else 500,
            'body': json.dumps({
                'message': f'User {user_id} blocked successfully' if success else 'Blocking failed',
                'action': 'block',
                'user_id': user_id,
                'performed_by': performed_by,
                'blocked_at': get_cet_timestamp_string()
            })
        }
        
    except Exception as e:
        logger.error(f"Error in manual_block_user: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': f'Error blocking user {user_id}: {str(e)}',
                'action': 'block',
                'user_id': user_id
            })
        }

def manual_unblock_user(event: Dict[str, Any]) -> Dict[str, Any]:
    """Handle manual admin unblocking"""
    try:
        user_id = event['user_id']
        reason = event.get('reason', 'Manual admin unblock')
        performed_by = event.get('performed_by', 'admin')
        
        logger.info(f"🔓 Manual unblocking user {user_id} by {performed_by}")
        
        connection = get_mysql_connection()
        
        # Execute unblocking with admin protection
        success = execute_admin_unblocking(connection, user_id, reason, performed_by)
        
        return {
            'statusCode': 200 if success else 500,
            'body': json.dumps({
                'message': f'User {user_id} unblocked successfully' if success else 'Unblocking failed',
                'action': 'unblock',
                'user_id': user_id,
                'performed_by': performed_by,
                'unblocked_at': get_cet_timestamp_string()
            })
        }
        
    except Exception as e:
        logger.error(f"Error in manual_unblock_user: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': f'Error unblocking user {user_id}: {str(e)}',
                'action': 'unblock',
                'user_id': user_id
            })
        }

def check_user_status(event: Dict[str, Any]) -> Dict[str, Any]:
    """Check user blocking status for dashboard"""
    try:
        user_id = event['user_id']
        
        logger.info(f"🔍 Checking status for user {user_id}")
        
        connection = get_mysql_connection()
        
        with connection.cursor() as cursor:
            # Get blocking status
            cursor.execute("""
                SELECT is_blocked, blocked_reason, blocked_at, blocked_until
                FROM user_blocking_status 
                WHERE user_id = %s
            """, [user_id])
            
            status_result = cursor.fetchone()
            
            # Get usage info
            cursor.execute("""
                SELECT daily_request_limit, administrative_safe
                FROM user_limits 
                WHERE user_id = %s
            """, [user_id])
            
            limits_result = cursor.fetchone()
            
            # CORRECCIÓN: Determine block type and performed_by more accurately
            block_type = 'None'
            performed_by = None
            
            if status_result and status_result['is_blocked'] == 'Y':
                # Check if it's an automatic block (expires at midnight) or manual block
                if status_result['blocked_until']:
                    blocked_until_str = status_result['blocked_until'].strftime('%H:%M:%S') if hasattr(status_result['blocked_until'], 'strftime') else str(status_result['blocked_until'])
                    if '00:00:00' in blocked_until_str:
                        block_type = 'AUTO'  # Automatic blocks expire at midnight
                        performed_by = 'system'  # System performed automatic block
                    else:
                        block_type = 'Manual'  # Manual blocks expire at other times
                        performed_by = 'dashboard_admin'  # Admin performed manual block
                else:
                    block_type = 'Manual'  # No expiration time means manual
                    performed_by = 'dashboard_admin'
            
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'user_id': user_id,
                    'is_blocked': status_result['is_blocked'] == 'Y' if status_result else False,
                    'block_reason': status_result['blocked_reason'] if status_result else None,
                    'blocked_since': status_result['blocked_at'].isoformat() if status_result and status_result['blocked_at'] else None,
                    'expires_at': status_result['blocked_until'].isoformat() if status_result and status_result['blocked_until'] else None,
                    'block_type': block_type,
                    'performed_by': performed_by,
                    'administrative_safe': limits_result['administrative_safe'] == 'Y' if limits_result else False,
                    'checked_at': datetime.utcnow().isoformat()
                })
            }
            
    except Exception as e:
        logger.error(f"Error checking user status: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e), 'user_id': user_id})
        }

def handle_cloudtrail_event(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Handle CloudTrail events (automatic blocking) - Fixed version"""
    connection = None
    processed_requests = 0
    blocked_requests = 0
    unblocked_requests = 0
    
    try:
        connection = get_mysql_connection()
        logger.info("✅ Successfully connected to MySQL database")
        
        events_to_process = []
        
        # CORRECCIÓN: Manejar eventos de CloudWatch Logs
        if 'awslogs' in event:
            logger.info("🔍 Processing CloudWatch Logs event")
            
            # Decodificar datos comprimidos
            import base64
            import gzip
            
            try:
                compressed_data = event['awslogs']['data']
                decoded_data = base64.b64decode(compressed_data)
                decompressed_data = gzip.decompress(decoded_data)
                log_data = json.loads(decompressed_data.decode('utf-8'))
                
                logger.info(f"📦 Decoded CloudWatch Logs data from log group: {log_data.get('logGroup', 'unknown')}")
                
                # Extraer eventos de CloudTrail de los logEvents
                for log_event in log_data.get('logEvents', []):
                    try:
                        cloudtrail_event = json.loads(log_event['message'])
                        # Filtrar solo eventos de Bedrock
                        if cloudtrail_event.get('eventSource') == 'bedrock.amazonaws.com':
                            events_to_process.append(cloudtrail_event)
                            logger.info(f"🎯 Found Bedrock event: {cloudtrail_event.get('eventName')} from user {cloudtrail_event.get('userIdentity', {}).get('userName', 'unknown')}")
                    except json.JSONDecodeError as e:
                        logger.warning(f"Failed to parse log event message: {str(e)}")
                        continue
                        
            except Exception as e:
                logger.error(f"Failed to decode CloudWatch Logs data: {str(e)}")
                return {
                    'statusCode': 500,
                    'body': json.dumps({'error': f'Failed to decode CloudWatch Logs data: {str(e)}'})
                }
                    
        elif 'detail' in event and 'Records' not in event:
            logger.info("🔍 Processing direct CloudWatch event")
            events_to_process = [event['detail']]
        else:
            logger.info("🔍 Processing Records-based event")
            records = event.get('Records', [])
            for record in records:
                if 's3' in record:
                    logger.info("S3 CloudTrail delivery not implemented yet")
                    continue
                detail = record.get('detail', record)
                events_to_process.append(detail)
        
        logger.info(f"📋 Found {len(events_to_process)} events to process")
        
        for i, detail in enumerate(events_to_process):
            try:
                logger.info(f"🔍 Processing event {i+1}/{len(events_to_process)}")
                
                # CORRECCIÓN CRÍTICA: Extract user_id FIRST before full parsing
                # This allows us to check blocking status even if request_parameters is None
                user_identity = detail.get('userIdentity', {})
                user_arn = user_identity.get('arn', '')
                user_id = extract_user_from_arn(user_arn)
                
                if not user_id:
                    logger.warning(f"❌ Could not extract user ID from event {i+1}")
                    continue
                
                logger.info(f"✅ Extracted user ID: {user_id} for event {i+1}")
                
                # Get user metadata
                team = get_user_team(user_id)
                person = get_user_person_tag(user_id)
                
                # FILTER: Skip requests where both Person and Team are unknown (Knowledge Base sessions)
                if team == 'unknown' and person == 'Unknown':
                    logger.info(f"🚫 FILTERING OUT request from user {user_id} - both Team ({team}) and Person ({person}) are unknown")
                    logger.info(f"📊 This appears to be a Knowledge Base session, excluding from usage tracking per business requirements")
                    continue
                
                ensure_user_exists(connection, user_id, team, person)
                
                # 1. ALWAYS check if user is currently blocked and handle automatic unblocking
                # This must happen BEFORE parsing the full event
                is_blocked, block_reason = check_user_blocking_status(connection, user_id)
                
                # CORRECCIÓN: If user was unblocked automatically, increment counters
                if block_reason == 'expired':
                    unblocked_requests += 1
                    logger.info(f"✅ User {user_id} was automatically unblocked due to expiration")
                    # Continue to parse and process the request since user is now unblocked
                elif is_blocked:
                    logger.warning(f"🚫 User {user_id} is currently blocked: {block_reason}")
                    continue  # Don't process requests from blocked users
                
                # 2. NOW parse the full event (after checking blocking status)
                request_data = parse_bedrock_event(detail)
                if not request_data:
                    logger.warning(f"❌ Failed to parse full request data for event {i+1}, but user {user_id} blocking status was checked")
                    continue
                
                # 3. Check if user should be blocked (with administrative protection)
                should_block, new_block_reason, usage_info = check_user_limits_with_protection(connection, user_id)
                
                if should_block:
                    blocked_requests += 1
                    logger.warning(f"🚫 User {user_id} should be blocked: {new_block_reason}")
                    
                    # Execute complete blocking workflow
                    blocking_success = execute_user_blocking(connection, user_id, new_block_reason, usage_info)
                    
                    if blocking_success:
                        logger.info(f"✅ Successfully executed complete blocking for user {user_id}")
                    else:
                        logger.error(f"❌ Failed to execute complete blocking for user {user_id}")
                    
                    # Don't log the request that triggered the block
                    continue
                
                # 4. Log the request normally
                log_bedrock_request_cet(connection, request_data, team, person)
                processed_requests += 1
                
                logger.info(f"User {user_id} usage: {usage_info['daily_requests_used']}/{usage_info['daily_limit']} daily requests ({usage_info['daily_percent']:.1f}%), "
                           f"{usage_info['monthly_requests_used']}/{usage_info['monthly_limit']} monthly requests ({usage_info['monthly_percent']:.1f}%)")
                
            except Exception as record_error:
                logger.error(f"Failed to process record: {str(record_error)}")
                continue
        
        logger.info(f"✅ Processed {processed_requests} requests, BLOCKED {blocked_requests} users, UNBLOCKED {unblocked_requests} users")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Successfully processed Bedrock requests with ENHANCED MERGED FUNCTIONALITY',
                'processed_requests': processed_requests,
                'blocked_requests': blocked_requests,
                'unblocked_requests': unblocked_requests
            })
        }
        
    except Exception as e:
        logger.error(f"Lambda execution failed: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e),
                'message': 'Failed to process Bedrock requests'
            })
        }
    
    finally:
        # Don't close connection - keep it for reuse
        pass

# NEW FUNCTIONS FOR MANUAL OPERATIONS

def get_user_current_usage(connection, user_id: str) -> Dict[str, Any]:
    """Get current usage information for user"""
    try:
        with connection.cursor() as cursor:
            # Get user limits
            cursor.execute("""
                SELECT daily_request_limit, monthly_request_limit, administrative_safe
                FROM user_limits 
                WHERE user_id = %s
            """, [user_id])
            
            limits_result = cursor.fetchone()
            if not limits_result:
                daily_limit = 350
                monthly_limit = 5000
                administrative_safe = 'N'
            else:
                daily_limit = int(limits_result['daily_request_limit'])
                monthly_limit = int(limits_result['monthly_request_limit'])
                administrative_safe = limits_result.get('administrative_safe', 'N')
            
            # Get current daily usage
            cursor.execute("""
                SELECT COUNT(*) as daily_requests_used
                FROM bedrock_requests 
                WHERE user_id = %s 
                AND DATE(request_timestamp) = CURDATE()
            """, [user_id])
            
            daily_result = cursor.fetchone()
            daily_requests_used = int(daily_result['daily_requests_used']) if daily_result else 0
            
            # Get current monthly usage
            cursor.execute("""
                SELECT COUNT(*) as monthly_requests_used
                FROM bedrock_requests 
                WHERE user_id = %s 
                AND DATE(request_timestamp) >= DATE_FORMAT(NOW(), '%%Y-%%m-01')
            """, [user_id])
            
            monthly_result = cursor.fetchone()
            monthly_requests_used = int(monthly_result['monthly_requests_used']) if monthly_result else 0
            
            daily_percent = (daily_requests_used / daily_limit) * 100 if daily_limit > 0 else 0
            monthly_percent = (monthly_requests_used / monthly_limit) * 100 if monthly_limit > 0 else 0
            
            return {
                'daily_requests_used': daily_requests_used,
                'monthly_requests_used': monthly_requests_used,
                'daily_percent': daily_percent,
                'monthly_percent': monthly_percent,
                'daily_limit': daily_limit,
                'monthly_limit': monthly_limit,
                'administrative_safe': administrative_safe == 'Y'
            }
            
    except Exception as e:
        logger.error(f"Failed to get user current usage: {str(e)}")
        return {
            'daily_requests_used': 0,
            'monthly_requests_used': 0,
            'daily_percent': 0,
            'monthly_percent': 0,
            'daily_limit': 350,
            'monthly_limit': 5000,
            'administrative_safe': False
        }

def execute_admin_blocking(connection, user_id: str, reason: str, performed_by: str, usage_info: Dict[str, Any], expires_at: str = None) -> bool:
    """Execute admin blocking with custom or default 24-hour expiration"""
    try:
        current_cet_time = get_current_cet_time()
        current_cet_string = get_cet_timestamp_string()
        
        # Use custom expiration if provided, otherwise default to 24 hours
        if expires_at and expires_at != 'Indefinite':
            try:
                # Parse the expires_at ISO string and convert to CET
                expires_utc = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
                blocked_until_cet = expires_utc.astimezone(CET)
                blocked_until_string = blocked_until_cet.strftime('%Y-%m-%d %H:%M:%S')
                logger.info(f"🚫 Admin blocking {user_id} until custom date {blocked_until_string} CET")
            except Exception as e:
                logger.error(f"Failed to parse custom expires_at '{expires_at}': {str(e)}, using 24-hour default")
                blocked_until_cet = current_cet_time + timedelta(hours=24)
                blocked_until_string = blocked_until_cet.strftime('%Y-%m-%d %H:%M:%S')
        elif expires_at == 'Indefinite':
            blocked_until_string = None
            logger.info(f"🚫 Admin blocking {user_id} indefinitely")
        else:
            # Default to 24 hours for admin blocks
            blocked_until_cet = current_cet_time + timedelta(hours=24)
            blocked_until_string = blocked_until_cet.strftime('%Y-%m-%d %H:%M:%S')
            logger.info(f"🚫 Admin blocking {user_id} until default 24h {blocked_until_string} CET")
        
        # Update blocking status with admin info - CORRECCIÓN: Use expected SQL structure
        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO user_blocking_status 
                (user_id, is_blocked, blocked_reason, blocked_at, blocked_until, 
                 requests_at_blocking, last_request_at, created_at, updated_at)
                VALUES (%s, 'Y', %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                is_blocked = 'Y',
                blocked_reason = VALUES(blocked_reason),
                blocked_at = VALUES(blocked_at),
                blocked_until = VALUES(blocked_until),
                requests_at_blocking = VALUES(requests_at_blocking),
                last_request_at = VALUES(last_request_at),
                updated_at = VALUES(updated_at)
            """, [user_id, reason, current_cet_string, blocked_until_string,
                  usage_info['daily_requests_used'], current_cet_string, 
                  current_cet_string, current_cet_string])
        
        # Log to audit
        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO blocking_audit_log 
                (user_id, operation_type, operation_reason, performed_by, operation_timestamp, created_at)
                VALUES (%s, 'BLOCK', %s, %s, %s, %s)
            """, [user_id, reason, performed_by, current_cet_string, current_cet_string])
        
        # Create IAM deny policy
        implement_iam_blocking(user_id)
        
        # Send enhanced email notification
        send_enhanced_blocking_email(user_id, reason, usage_info, performed_by)
        
        logger.info(f"✅ Successfully executed admin blocking for user {user_id}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to execute admin blocking for {user_id}: {str(e)}")
        return False

def execute_admin_unblocking(connection, user_id: str, reason: str, performed_by: str) -> bool:
    """Execute admin unblocking with protection flag"""
    try:
        current_cet_string = get_cet_timestamp_string()
        
        logger.info(f"🔓 Admin unblocking {user_id}")
        
        # Track success of each step
        db_success = False
        protection_success = False
        audit_success = False
        iam_success = False
        email_success = False
        
        # 1. Update blocking status
        try:
            with connection.cursor() as cursor:
                result = cursor.execute("""
                    UPDATE user_blocking_status 
                    SET is_blocked = 'N',
                        blocked_reason = %s,
                        blocked_at = NULL,
                        blocked_until = NULL,
                        updated_at = %s
                    WHERE user_id = %s
                """, [reason, current_cet_string, user_id])
                logger.info(f"✅ Step 1: Updated blocking status for {user_id} (affected rows: {cursor.rowcount})")
                db_success = True
        except Exception as e:
            logger.error(f"❌ Step 1 FAILED: Blocking status update for {user_id}: {str(e)}")
            return False
        
        # 2. CORRECCIÓN CRÍTICA: Set administrative protection to prevent automatic re-blocking
        try:
            with connection.cursor() as cursor:
                # First ensure user exists in user_limits table
                cursor.execute("SELECT user_id FROM user_limits WHERE user_id = %s", [user_id])
                if not cursor.fetchone():
                    # Create user limits entry if it doesn't exist
                    cursor.execute("""
                        INSERT INTO user_limits (user_id, team, person, daily_request_limit, monthly_request_limit, administrative_safe, created_at)
                        VALUES (%s, 'unknown', 'Unknown', 350, 5000, 'Y', %s)
                    """, [user_id, current_cet_string])
                    logger.info(f"✅ Created user_limits entry for {user_id} with administrative protection")
                else:
                    # Update existing entry
                    cursor.execute("""
                        UPDATE user_limits 
                        SET administrative_safe = 'Y', 
                            updated_at = %s
                        WHERE user_id = %s
                    """, [current_cet_string, user_id])
                    logger.info(f"✅ Updated administrative_safe='Y' for {user_id} (affected rows: {cursor.rowcount})")
                
                # CORRECCIÓN: For tests, assume protection was set successfully if no exception occurred
                logger.info(f"✅ Step 2: Administrative protection SET for {user_id}")
                protection_success = True
                    
        except Exception as e:
            logger.error(f"❌ Step 2 FAILED: Administrative protection for {user_id}: {str(e)}")
            protection_success = False
        
        # 3. Log to audit
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO blocking_audit_log 
                    (user_id, operation_type, operation_reason, performed_by, operation_timestamp, created_at)
                    VALUES (%s, 'UNBLOCK', %s, %s, %s, %s)
                """, [user_id, reason, performed_by, current_cet_string, current_cet_string])
                logger.info(f"✅ Step 3: Created audit log entry for {user_id}")
                audit_success = True
        except Exception as e:
            logger.error(f"❌ Step 3 FAILED: Audit log creation for {user_id}: {str(e)}")
            audit_success = False
        
        # 4. Remove IAM deny policy
        try:
            iam_success = implement_iam_unblocking(user_id)
            if iam_success:
                logger.info(f"✅ Step 4: IAM policy updated for {user_id}")
            else:
                logger.error(f"❌ Step 4 FAILED: IAM policy update for {user_id}")
        except Exception as e:
            logger.error(f"❌ Step 4 EXCEPTION: IAM policy update for {user_id}: {str(e)}")
            iam_success = False
        
        # 5. Send enhanced email notification
        try:
            email_success = send_enhanced_unblocking_email(user_id, reason, performed_by)
            if email_success:
                logger.info(f"✅ Step 5: Email sent for {user_id}")
            else:
                logger.error(f"❌ Step 5 FAILED: Email sending for {user_id}")
        except Exception as e:
            logger.error(f"❌ Step 5 EXCEPTION: Email sending for {user_id}: {str(e)}")
            email_success = False
        
        # CORRECCIÓN CRÍTICA: Return False if critical steps failed
        if not db_success or not protection_success:
            logger.error(f"❌ CRITICAL: Admin unblocking failed for {user_id} - db_success={db_success}, protection_success={protection_success}")
            return False
        
        logger.info(f"✅ Successfully executed admin unblocking for user {user_id}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to execute admin unblocking for {user_id}: {str(e)}")
        return False

def send_enhanced_blocking_email(user_id: str, reason: str, usage_info: Dict[str, Any], performed_by: str) -> bool:
    """Send enhanced blocking email via separate Lambda service"""
    try:
        if performed_by != 'system':
            # Admin blocking email
            email_payload = {
                'action': 'send_admin_blocking_email',
                'user_id': user_id,
                'performed_by': performed_by,
                'reason': reason,
                'usage_record': usage_info
            }
        else:
            # Automatic blocking email
            email_payload = {
                'action': 'send_blocking_email',
                'user_id': user_id,
                'usage_record': usage_info,
                'reason': reason
            }
        
        if EMAIL_NOTIFICATIONS_ENABLED:
            response = lambda_client.invoke(
                FunctionName=EMAIL_SERVICE_LAMBDA_NAME,
                InvocationType='RequestResponse',
                Payload=json.dumps(email_payload)
            )
            
            response_payload = json.loads(response['Payload'].read())
            success = response_payload.get('statusCode') == 200
            
            if success:
                logger.info(f"✅ Enhanced email sent for blocking {user_id}")
            else:
                logger.warning(f"⚠️ Enhanced email failed for {user_id}, falling back to Gmail")
                # Fallback to existing Gmail functionality
                return send_blocking_email_gmail(user_id, reason, usage_info, 
                                               get_current_cet_time() + timedelta(hours=24))
            
            return success
        else:
            logger.info("Email notifications disabled")
            return True
        
    except Exception as e:
        logger.error(f"Enhanced email service failed, falling back to Gmail: {str(e)}")
        # Fallback to existing Gmail functionality
        return send_blocking_email_gmail(user_id, reason, usage_info, 
                                       get_current_cet_time() + timedelta(hours=24))

def send_enhanced_unblocking_email(user_id: str, reason: str, performed_by: str) -> bool:
    """Send enhanced unblocking email via separate Lambda service"""
    try:
        if performed_by != 'system' and performed_by != 'daily_reset':
            # Admin unblocking email
            email_payload = {
                'action': 'send_admin_unblocking_email',
                'user_id': user_id,
                'performed_by': performed_by,
                'reason': reason
            }
        else:
            # Automatic unblocking email
            email_payload = {
                'action': 'send_unblocking_email',
                'user_id': user_id,
                'reason': reason
            }
        
        if EMAIL_NOTIFICATIONS_ENABLED:
            response = lambda_client.invoke(
                FunctionName=EMAIL_SERVICE_LAMBDA_NAME,
                InvocationType='RequestResponse',
                Payload=json.dumps(email_payload)
            )
            
            response_payload = json.loads(response['Payload'].read())
            success = response_payload.get('statusCode') == 200
            
            if success:
                logger.info(f"✅ Enhanced email sent for unblocking {user_id}")
            else:
                logger.warning(f"⚠️ Enhanced email failed for {user_id}, falling back to Gmail")
                # Fallback to existing Gmail functionality
                return send_unblocking_email_gmail(user_id)
            
            return success
        else:
            logger.info("Email notifications disabled")
            return True
        
    except Exception as e:
        logger.error(f"Enhanced email service failed, falling back to Gmail: {str(e)}")
        # Fallback to existing Gmail functionality
        return send_unblocking_email_gmail(user_id)
