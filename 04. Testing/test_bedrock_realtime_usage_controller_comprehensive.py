#!/usr/bin/env python3
"""
Comprehensive Unit Test Plan for bedrock-realtime-usage-controller

This test suite validates the merged functionality of:
1. CloudTrail event processing (automatic blocking)
2. API event handling (manual operations)
3. Database operations with RDS MySQL
4. Enhanced email service integration
5. Administrative protection workflows
6. IAM policy management
7. CET timezone handling

Test Coverage:
- CloudTrail event parsing and processing
- Automatic blocking/unblocking workflows
- Manual admin operations (block/unblock/status)
- Database CRUD operations
- Email notifications (enhanced service + Gmail fallback)
- IAM policy creation and modification
- Administrative protection mechanisms
- Error handling and edge cases
- Timezone conversions (UTC to CET)

Author: AWS Bedrock Usage Control System
Version: 1.0.0
"""

import unittest
import json
import boto3
import pymysql
from unittest.mock import Mock, patch, MagicMock, call
from datetime import datetime, timezone, timedelta
import pytz
import sys
import os

# Set up environment variables before importing lambda_function
os.environ.update({
    'RDS_ENDPOINT': 'test-rds-endpoint.amazonaws.com',
    'RDS_USERNAME': 'test_user',
    'RDS_PASSWORD': 'test_password',
    'RDS_DATABASE': 'test_bedrock_usage',
    'SNS_TOPIC_ARN': 'arn:aws:sns:eu-west-1:123456789012:test-topic',
    'EMAIL_SERVICE_LAMBDA_NAME': 'test-bedrock-email-service',
    'EMAIL_NOTIFICATIONS_ENABLED': 'true'
})

# Add the Lambda Functions directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '02. Source', 'Lambda Functions'))

# Import the function under test using importlib for hyphenated filename
import importlib.util
spec = importlib.util.spec_from_file_location("lambda_function", os.path.join(os.path.dirname(__file__), '..', '02. Source', 'Lambda Functions', 'bedrock-realtime-usage-controller.py'))
lambda_function = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lambda_function)

# Add the module to sys.modules so patch decorators can find it
sys.modules['lambda_function'] = lambda_function

class TestBedrockRealtimeUsageController(unittest.TestCase):
    """Comprehensive test suite for the merged Lambda function"""
    
    def setUp(self):
        """Set up test fixtures and mocks"""
        self.maxDiff = None
        
        # Mock environment variables
        self.env_patcher = patch.dict(os.environ, {
            'RDS_ENDPOINT': 'test-rds-endpoint.amazonaws.com',
            'RDS_USERNAME': 'test_user',
            'RDS_PASSWORD': 'test_password',
            'RDS_DATABASE': 'test_bedrock_usage',
            'SNS_TOPIC_ARN': 'arn:aws:sns:eu-west-1:123456789012:test-topic',
            'EMAIL_SERVICE_LAMBDA_NAME': 'test-bedrock-email-service',
            'EMAIL_NOTIFICATIONS_ENABLED': 'true'
        })
        self.env_patcher.start()
        
        # Mock AWS clients
        self.iam_mock = Mock()
        self.sns_mock = Mock()
        self.lambda_client_mock = Mock()
        
        # Mock database connection
        self.connection_mock = Mock()
        self.cursor_mock = Mock()
        self.cursor_context_mock = Mock()
        self.cursor_context_mock.__enter__ = Mock(return_value=self.cursor_mock)
        self.cursor_context_mock.__exit__ = Mock(return_value=None)
        self.connection_mock.cursor.return_value = self.cursor_context_mock
        
        # Sample test data
        self.sample_cloudtrail_event = {
            'eventName': 'InvokeModel',
            'eventTime': '2024-01-15T10:30:00Z',
            'userIdentity': {
                'type': 'IAMUser',
                'arn': 'arn:aws:iam::123456789012:user/test-user',
                'userName': 'test-user'
            },
            'requestParameters': {
                'modelId': 'anthropic.claude-3-5-sonnet-20240620-v1:0'
            },
            'sourceIPAddress': '192.168.1.100',
            'userAgent': 'aws-cli/2.0.0',
            'requestID': 'test-request-id-123',
            'awsRegion': 'eu-west-1'
        }
        
        self.sample_api_event = {
            'action': 'block',
            'user_id': 'test-user',
            'reason': 'Manual admin block',
            'performed_by': 'admin-user'
        }
        
        self.sample_usage_info = {
            'daily_requests_used': 300,
            'monthly_requests_used': 2500,
            'daily_percent': 85.7,
            'monthly_percent': 50.0,
            'daily_limit': 350,
            'monthly_limit': 5000,
            'administrative_safe': False
        }
    
    def tearDown(self):
        """Clean up after tests"""
        self.env_patcher.stop()
        # Reset any global state
        lambda_function.connection_pool = None

class TestEventRouting(TestBedrockRealtimeUsageController):
    """Test event routing between CloudTrail and API events"""
    
    @patch('lambda_function.handle_api_event')
    @patch('lambda_function.handle_cloudtrail_event')
    def test_lambda_handler_routes_api_event(self, mock_cloudtrail, mock_api):
        """Test that API events are routed to handle_api_event"""
        mock_api.return_value = {'statusCode': 200, 'body': '{"success": true}'}
        
        result = lambda_function.lambda_handler(self.sample_api_event, {})
        
        mock_api.assert_called_once_with(self.sample_api_event, {})
        mock_cloudtrail.assert_not_called()
        self.assertEqual(result['statusCode'], 200)
    
    @patch('lambda_function.handle_api_event')
    @patch('lambda_function.handle_cloudtrail_event')
    def test_lambda_handler_routes_cloudtrail_event(self, mock_cloudtrail, mock_api):
        """Test that CloudTrail events are routed to handle_cloudtrail_event"""
        cloudtrail_event = {'detail': self.sample_cloudtrail_event}
        mock_cloudtrail.return_value = {'statusCode': 200, 'body': '{"processed": 1}'}
        
        result = lambda_function.lambda_handler(cloudtrail_event, {})
        
        mock_cloudtrail.assert_called_once_with(cloudtrail_event, {})
        mock_api.assert_not_called()
        self.assertEqual(result['statusCode'], 200)

class TestCloudTrailEventProcessing(TestBedrockRealtimeUsageController):
    """Test CloudTrail event parsing and processing"""
    
    def test_parse_bedrock_event_success(self):
        """Test successful parsing of CloudTrail Bedrock event"""
        result = lambda_function.parse_bedrock_event(self.sample_cloudtrail_event)
        
        self.assertIsNotNone(result)
        self.assertEqual(result['user_id'], 'test-user')
        self.assertEqual(result['model_id'], 'anthropic.claude-3-5-sonnet-20240620-v1:0')
        self.assertEqual(result['model_name'], 'Claude 3.5 Sonnet')
        self.assertEqual(result['request_type'], 'invoke')
        self.assertEqual(result['region'], 'eu-west-1')
        self.assertEqual(result['source_ip'], '192.168.1.100')
        self.assertEqual(result['request_id'], 'test-request-id-123')
        self.assertIn('cet_timestamp', result)
    
    def test_parse_bedrock_event_with_arn_model_id(self):
        """Test parsing event with ARN-format model ID"""
        event = self.sample_cloudtrail_event.copy()
        event['requestParameters']['modelId'] = 'arn:aws:bedrock:eu-west-1:123456789012:foundation-model/eu.anthropic.claude-sonnet-4-20250514-v1:0'
        
        result = lambda_function.parse_bedrock_event(event)
        
        self.assertEqual(result['model_id'], 'arn:aws:bedrock:eu-west-1:123456789012:foundation-model/eu.anthropic.claude-sonnet-4-20250514-v1:0')
        self.assertEqual(result['model_name'], 'Claude 3.5 Sonnet')
    
    def test_parse_bedrock_event_missing_user_arn(self):
        """Test parsing event with missing user ARN"""
        event = self.sample_cloudtrail_event.copy()
        event['userIdentity']['arn'] = ''
        
        result = lambda_function.parse_bedrock_event(event)
        
        self.assertIsNone(result)
    
    def test_parse_bedrock_event_missing_model_id(self):
        """Test parsing event with missing model ID"""
        event = self.sample_cloudtrail_event.copy()
        event['requestParameters'] = {}
        
        result = lambda_function.parse_bedrock_event(event)
        
        self.assertIsNone(result)
    
    def test_extract_user_from_arn_iam_user(self):
        """Test extracting username from IAM user ARN"""
        arn = 'arn:aws:iam::123456789012:user/test-user'
        result = lambda_function.extract_user_from_arn(arn)
        self.assertEqual(result, 'test-user')
    
    def test_extract_user_from_arn_assumed_role(self):
        """Test extracting username from assumed role ARN"""
        arn = 'arn:aws:sts::123456789012:assumed-role/test-role/test-user'
        result = lambda_function.extract_user_from_arn(arn)
        self.assertEqual(result, 'test-user')
    
    def test_extract_user_from_arn_invalid(self):
        """Test extracting username from invalid ARN"""
        result = lambda_function.extract_user_from_arn('invalid-arn')
        self.assertIsNone(result)

class TestTimezoneHandling(TestBedrockRealtimeUsageController):
    """Test CET timezone conversion and handling"""
    
    def test_get_current_cet_time(self):
        """Test getting current CET time"""
        result = lambda_function.get_current_cet_time()
        self.assertIsInstance(result, datetime)
        self.assertEqual(result.tzinfo.zone, 'Europe/Madrid')
    
    def test_convert_utc_to_cet(self):
        """Test UTC to CET timestamp conversion"""
        utc_timestamp = '2024-01-15T10:30:00Z'
        result = lambda_function.convert_utc_to_cet(utc_timestamp)
        
        # Should convert to CET (UTC+1 in winter, UTC+2 in summer)
        self.assertIsInstance(result, str)
        self.assertRegex(result, r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}')
    
    def test_convert_utc_to_cet_invalid_format(self):
        """Test UTC to CET conversion with invalid format"""
        with patch('lambda_function.get_cet_timestamp_string') as mock_get_cet:
            mock_get_cet.return_value = '2024-01-15 12:00:00'
            result = lambda_function.convert_utc_to_cet('invalid-timestamp')
            self.assertEqual(result, '2024-01-15 12:00:00')

class TestDatabaseOperations(TestBedrockRealtimeUsageController):
    """Test database connection and operations"""
    
    @patch('lambda_function.pymysql.connect')
    def test_get_mysql_connection_new(self, mock_connect):
        """Test creating new MySQL connection"""
        mock_connection = Mock()
        mock_connect.return_value = mock_connection
        lambda_function.connection_pool = None
        
        result = lambda_function.get_mysql_connection()
        
        mock_connect.assert_called_once_with(
            host='test-rds-endpoint.amazonaws.com',
            user='test_user',
            password='test_password',
            database='test_bedrock_usage',
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor,
            autocommit=True,
            connect_timeout=5,
            read_timeout=5,
            write_timeout=5
        )
        self.assertEqual(result, mock_connection)
    
    @patch('lambda_function.pymysql.connect')
    def test_get_mysql_connection_reuse(self, mock_connect):
        """Test reusing existing MySQL connection"""
        mock_connection = Mock()
        mock_connection.ping.return_value = None
        lambda_function.connection_pool = mock_connection
        
        result = lambda_function.get_mysql_connection()
        
        mock_connect.assert_not_called()
        mock_connection.ping.assert_called_once_with(reconnect=True)
        self.assertEqual(result, mock_connection)
    
    @patch('lambda_function.get_mysql_connection')
    def test_ensure_user_exists_new_user(self, mock_get_connection):
        """Test creating new user in user_limits table"""
        mock_get_connection.return_value = self.connection_mock
        self.cursor_mock.fetchone.return_value = None
        
        lambda_function.ensure_user_exists(self.connection_mock, 'test-user', 'test-team', 'Test Person')
        
        # Verify SELECT query
        select_call = call("SELECT user_id FROM user_limits WHERE user_id = %s", ['test-user'])
        # Verify INSERT query - match the exact formatting from the actual function
        insert_call = call(
            "\n                INSERT INTO user_limits (user_id, team, person, daily_request_limit, monthly_request_limit, administrative_safe, created_at)\n                VALUES (%s, %s, %s, %s, %s, 'N', %s)\n            ",
            ['test-user', 'test-team', 'Test Person', 350, 5000, unittest.mock.ANY]
        )
        
        self.cursor_mock.execute.assert_has_calls([select_call, insert_call])
    
    @patch('lambda_function.get_mysql_connection')
    def test_ensure_user_exists_existing_user(self, mock_get_connection):
        """Test handling existing user in user_limits table"""
        mock_get_connection.return_value = self.connection_mock
        self.cursor_mock.fetchone.return_value = {'user_id': 'test-user'}
        
        lambda_function.ensure_user_exists(self.connection_mock, 'test-user', 'test-team', 'Test Person')
        
        # Should only execute SELECT, not INSERT
        self.cursor_mock.execute.assert_called_once_with(
            "SELECT user_id FROM user_limits WHERE user_id = %s", ['test-user']
        )

class TestUserLimitsAndBlocking(TestBedrockRealtimeUsageController):
    """Test user limits checking and blocking logic"""
    
    def test_check_user_limits_with_protection_no_limits(self):
        """Test checking limits for user without configured limits"""
        with patch('lambda_function.get_mysql_connection') as mock_get_connection:
            mock_get_connection.return_value = self.connection_mock
            self.cursor_mock.fetchone.side_effect = [
                None,  # No limits found
                {'daily_requests_used': 100},  # Daily usage
                {'monthly_requests_used': 1000}  # Monthly usage
            ]
            
            should_block, reason, usage_info = lambda_function.check_user_limits_with_protection(
                self.connection_mock, 'test-user'
            )
            
            self.assertFalse(should_block)
            self.assertIsNone(reason)
            self.assertEqual(usage_info['daily_limit'], 350)
            self.assertEqual(usage_info['monthly_limit'], 5000)
    
    def test_check_user_limits_with_protection_admin_safe(self):
        """Test checking limits for user with administrative protection"""
        with patch('lambda_function.get_mysql_connection') as mock_get_connection:
            mock_get_connection.return_value = self.connection_mock
            self.cursor_mock.fetchone.side_effect = [
                {
                    'daily_request_limit': 350,
                    'monthly_request_limit': 5000,
                    'administrative_safe': 'Y'
                }
            ]
            
            should_block, reason, usage_info = lambda_function.check_user_limits_with_protection(
                self.connection_mock, 'test-user'
            )
            
            self.assertFalse(should_block)
            self.assertIsNone(reason)
            self.assertTrue(usage_info['administrative_safe'])
    
    def test_check_user_limits_with_protection_daily_exceeded(self):
        """Test checking limits when daily limit is exceeded"""
        with patch('lambda_function.get_mysql_connection') as mock_get_connection:
            mock_get_connection.return_value = self.connection_mock
            self.cursor_mock.fetchone.side_effect = [
                {
                    'daily_request_limit': 350,
                    'monthly_request_limit': 5000,
                    'administrative_safe': 'N'
                },
                {'daily_requests_used': 351},  # Exceeded daily limit
                {'monthly_requests_used': 1000}
            ]
            
            should_block, reason, usage_info = lambda_function.check_user_limits_with_protection(
                self.connection_mock, 'test-user'
            )
            
            self.assertTrue(should_block)
            self.assertEqual(reason, 'Daily limit exceeded')
            self.assertEqual(usage_info['daily_requests_used'], 351)
    
    def test_check_user_limits_with_protection_monthly_exceeded(self):
        """Test checking limits when monthly limit is exceeded"""
        with patch('lambda_function.get_mysql_connection') as mock_get_connection:
            mock_get_connection.return_value = self.connection_mock
            self.cursor_mock.fetchone.side_effect = [
                {
                    'daily_request_limit': 350,
                    'monthly_request_limit': 5000,
                    'administrative_safe': 'N'
                },
                {'daily_requests_used': 300},
                {'monthly_requests_used': 5001}  # Exceeded monthly limit
            ]
            
            should_block, reason, usage_info = lambda_function.check_user_limits_with_protection(
                self.connection_mock, 'test-user'
            )
            
            self.assertTrue(should_block)
            self.assertEqual(reason, 'Monthly limit exceeded')
            self.assertEqual(usage_info['monthly_requests_used'], 5001)

class TestBlockingWorkflow(TestBedrockRealtimeUsageController):
    """Test complete blocking workflow"""
    
    @patch('lambda_function.send_blocking_email_gmail')
    @patch('lambda_function.implement_iam_blocking')
    @patch('lambda_function.get_cet_timestamp_string')
    @patch('lambda_function.get_current_cet_time')
    def test_execute_user_blocking_success(self, mock_get_cet_time, mock_get_cet_string, 
                                         mock_iam_blocking, mock_send_email):
        """Test successful user blocking workflow"""
        # Setup mocks
        mock_cet_time = datetime(2024, 1, 15, 12, 0, 0, tzinfo=pytz.timezone('Europe/Madrid'))
        mock_get_cet_time.return_value = mock_cet_time
        mock_get_cet_string.return_value = '2024-01-15 12:00:00'
        mock_iam_blocking.return_value = True
        mock_send_email.return_value = True
        
        result = lambda_function.execute_user_blocking(
            self.connection_mock, 'test-user', 'Daily limit exceeded', self.sample_usage_info
        )
        
        self.assertTrue(result)
        
        # Verify database operations
        expected_calls = [
            call("""
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
                """, ['test-user', 'Daily limit exceeded', '2024-01-15 12:00:00', 
                      '2024-01-16 00:00:00', 300, '2024-01-15 12:00:00', 
                      '2024-01-15 12:00:00', '2024-01-15 12:00:00']),
            call("""
                    INSERT INTO blocking_audit_log 
                    (user_id, operation_type, operation_reason, performed_by, operation_timestamp,
                     daily_requests_at_operation, daily_limit_at_operation, usage_percentage,
                     iam_policy_updated, email_sent, created_at)
                    VALUES (%s, 'BLOCK', %s, 'system', %s, %s, %s, %s, 'Y', 'Y', %s)
                """, ['test-user', 'Daily limit exceeded', '2024-01-15 12:00:00', 
                      300, 350, 85.71, '2024-01-15 12:00:00'])
        ]
        
        self.cursor_mock.execute.assert_has_calls(expected_calls)
        mock_iam_blocking.assert_called_once_with('test-user')
        mock_send_email.assert_called_once()

class TestUnblockingWorkflow(TestBedrockRealtimeUsageController):
    """Test complete unblocking workflow"""
    
    @patch('lambda_function.send_unblocking_email_gmail')
    @patch('lambda_function.implement_iam_unblocking')
    @patch('lambda_function.get_cet_timestamp_string')
    def test_execute_user_unblocking_success(self, mock_get_cet_string, 
                                           mock_iam_unblocking, mock_send_email):
        """Test successful user unblocking workflow"""
        mock_get_cet_string.return_value = '2024-01-15 12:00:00'
        mock_iam_unblocking.return_value = True
        mock_send_email.return_value = True
        
        result = lambda_function.execute_user_unblocking(self.connection_mock, 'test-user')
        
        self.assertTrue(result)
        
        # Verify database operations
        expected_calls = [
            call("""
                    UPDATE user_blocking_status 
                    SET is_blocked = 'N',
                        blocked_reason = 'Automatic unblock',
                        blocked_until = NULL,
                        last_request_at = %s,
                        last_reset_at = %s,
                        updated_at = %s
                    WHERE user_id = %s
                """, ['2024-01-15 12:00:00', '2024-01-15 12:00:00', 
                      '2024-01-15 12:00:00', 'test-user']),
            call("""
                    INSERT INTO blocking_audit_log 
                    (user_id, operation_type, operation_reason, performed_by, operation_timestamp, created_at)
                    VALUES (%s, 'UNBLOCK', 'Automatic unblock', 'system', %s, %s)
                """, ['test-user', '2024-01-15 12:00:00', '2024-01-15 12:00:00'])
        ]
        
        self.cursor_mock.execute.assert_has_calls(expected_calls)
        mock_iam_unblocking.assert_called_once_with('test-user')
        mock_send_email.assert_called_once_with('test-user')

class TestIAMPolicyManagement(TestBedrockRealtimeUsageController):
    """Test IAM policy creation and modification"""
    
    @patch('lambda_function.iam')
    def test_implement_iam_blocking_new_policy(self, mock_iam):
        """Test creating new IAM deny policy"""
        # Create a proper mock exception class
        class MockNoSuchEntityException(Exception):
            pass
        
        # Set up the mock IAM client with proper exception handling
        mock_iam.exceptions.NoSuchEntityException = MockNoSuchEntityException
        mock_iam.get_user_policy.side_effect = MockNoSuchEntityException()
        
        result = lambda_function.implement_iam_blocking('test-user')
        
        self.assertTrue(result)
        
        # Verify policy creation
        mock_iam.put_user_policy.assert_called_once()
        call_args = mock_iam.put_user_policy.call_args
        
        self.assertEqual(call_args[1]['UserName'], 'test-user')
        self.assertEqual(call_args[1]['PolicyName'], 'test-user_BedrockPolicy')
        
        # Verify policy document structure
        policy_doc = json.loads(call_args[1]['PolicyDocument'])
        self.assertEqual(policy_doc['Version'], '2012-10-17')
        self.assertEqual(len(policy_doc['Statement']), 2)
        self.assertEqual(policy_doc['Statement'][0]['Effect'], 'Deny')
        self.assertEqual(policy_doc['Statement'][0]['Sid'], 'DailyLimitBlock')
    
    @patch('lambda_function.iam')
    def test_implement_iam_blocking_existing_policy(self, mock_iam):
        """Test modifying existing IAM policy to add deny statement"""
        existing_policy = {
            'Version': '2012-10-17',
            'Statement': [
                {
                    'Sid': 'BedrockAccess',
                    'Effect': 'Allow',
                    'Action': ['bedrock:InvokeModel'],
                    'Resource': '*'
                }
            ]
        }
        
        mock_iam.get_user_policy.return_value = {'PolicyDocument': existing_policy}
        
        result = lambda_function.implement_iam_blocking('test-user')
        
        self.assertTrue(result)
        
        # Verify policy update
        mock_iam.put_user_policy.assert_called_once()
        call_args = mock_iam.put_user_policy.call_args
        
        policy_doc = json.loads(call_args[1]['PolicyDocument'])
        self.assertEqual(len(policy_doc['Statement']), 2)
        self.assertEqual(policy_doc['Statement'][0]['Effect'], 'Deny')  # Deny statement first
        self.assertEqual(policy_doc['Statement'][1]['Effect'], 'Allow')  # Original allow statement
    
    @patch('lambda_function.iam')
    def test_implement_iam_unblocking_success(self, mock_iam):
        """Test removing deny statement from IAM policy"""
        existing_policy = {
            'Version': '2012-10-17',
            'Statement': [
                {
                    'Sid': 'DailyLimitBlock',
                    'Effect': 'Deny',
                    'Action': ['bedrock:InvokeModel'],
                    'Resource': '*'
                },
                {
                    'Sid': 'BedrockAccess',
                    'Effect': 'Allow',
                    'Action': ['bedrock:InvokeModel'],
                    'Resource': '*'
                }
            ]
        }
        
        mock_iam.get_user_policy.return_value = {'PolicyDocument': existing_policy}
        
        result = lambda_function.implement_iam_unblocking('test-user')
        
        self.assertTrue(result)
        
        # Verify deny statement removal
        call_args = mock_iam.put_user_policy.call_args
        policy_doc = json.loads(call_args[1]['PolicyDocument'])
        
        self.assertEqual(len(policy_doc['Statement']), 1)
        self.assertEqual(policy_doc['Statement'][0]['Effect'], 'Allow')
        self.assertNotEqual(policy_doc['Statement'][0]['Sid'], 'DailyLimitBlock')

class TestAPIEventHandling(TestBedrockRealtimeUsageController):
    """Test API event handling for manual operations"""
    
    def test_handle_api_event_missing_parameters(self):
        """Test API event handling with missing parameters"""
        invalid_event = {'action': 'block'}  # Missing user_id
        
        result = lambda_function.handle_api_event(invalid_event, {})
        
        self.assertEqual(result['statusCode'], 400)
        body = json.loads(result['body'])
        self.assertIn('Missing required parameters', body['error'])
    
    def test_handle_api_event_invalid_action(self):
        """Test API event handling with invalid action"""
        invalid_event = {
            'action': 'invalid_action',
            'user_id': 'test-user'
        }
        
        result = lambda_function.handle_api_event(invalid_event, {})
        
        self.assertEqual(result['statusCode'], 400)
        body = json.loads(result['body'])
        self.assertIn('Invalid action', body['error'])
    
    @patch('lambda_function.manual_block_user')
    def test_handle_api_event_block_action(self, mock_manual_block):
        """Test API event routing to manual block"""
        mock_manual_block.return_value = {'statusCode': 200, 'body': '{"success": true}'}
        
        result = lambda_function.handle_api_event(self.sample_api_event, {})
        
        mock_manual_block.assert_called_once_with(self.sample_api_event)
        self.assertEqual(result['statusCode'], 200)
    
    @patch('lambda_function.manual_unblock_user')
    def test_handle_api_event_unblock_action(self, mock_manual_unblock):
        """Test API event routing to manual unblock"""
        unblock_event = self.sample_api_event.copy()
        unblock_event['action'] = 'unblock'
        
        mock_manual_unblock.return_value = {'statusCode': 200, 'body': '{"success": true}'}
        
        result = lambda_function.handle_api_event(unblock_event, {})
        
        mock_manual_unblock.assert_called_once_with(unblock_event)
        self.assertEqual(result['statusCode'], 200)
    
    @patch('lambda_function.check_user_status')
    def test_handle_api_event_status_action(self, mock_check_status):
        """Test API event routing to status check"""
        status_event = self.sample_api_event.copy()
        status_event['action'] = 'check_status'
        
        mock_check_status.return_value = {'statusCode': 200, 'body': '{"status": "active"}'}
        
        result = lambda_function.handle_api_event(status_event, {})
        
        mock_check_status.assert_called_once_with(status_event)
        self.assertEqual(result['statusCode'], 200)

class TestManualOperations(TestBedrockRealtimeUsageController):
    """Test manual blocking/unblocking operations"""
    
    @patch('lambda_function.execute_admin_blocking')
    @patch('lambda_function.get_user_current_usage')
    @patch('lambda_function.get_mysql_connection')
    def test_manual_block_user_success(self, mock_get_connection, mock_get_usage, mock_execute_blocking):
        """Test successful manual user blocking"""
        mock_get_connection.return_value = self.connection_mock
        mock_get_usage.return_value = self.sample_usage_info
        mock_execute_blocking.return_value = True
        
        result = lambda_function.manual_block_user(self.sample_api_event)
        
        self.assertEqual(result['statusCode'], 200)
        body = json.loads(result['body'])
        self.assertIn('blocked successfully', body['message'])
        self.assertEqual(body['user_id'], 'test-user')
        self.assertEqual(body['performed_by'], 'admin-user')
        
        mock_execute_blocking.assert_called_once_with(
            self.connection_mock, 'test-user', 'Manual admin block', 'admin-user', self.sample_usage_info
        )
    
    @patch('lambda_function.execute_admin_blocking')
    @patch('lambda_function.get_user_current_usage')
    @patch('lambda_function.get_mysql_connection')
    def test_manual_block_user_failure(self, mock_get_connection, mock_get_usage, mock_execute_blocking):
        """Test failed manual user blocking"""
        mock_get_connection.return_value = self.connection_mock
        mock_get_usage.return_value = self.sample_usage_info
        mock_execute_blocking.return_value = False
        
        result = lambda_function.manual_block_user(self.sample_api_event)
        
        self.assertEqual(result['statusCode'], 500)
        body = json.loads(result['body'])
        self.assertIn('Blocking failed', body['message'])
    
    @patch('lambda_function.execute_admin_unblocking')
    @patch('lambda_function.get_mysql_connection')
    def test_manual_unblock_user_success(self, mock_get_connection, mock_execute_unblocking):
        """Test successful manual user unblocking"""
        mock_get_connection.return_value = self.connection_mock
        mock_execute_unblocking.return_value = True
        
        unblock_event = self.sample_api_event.copy()
        unblock_event['action'] = 'unblock'
        unblock_event['reason'] = 'Manual admin unblock'
        
        result = lambda_function.manual_unblock_user(unblock_event)
        
        self.assertEqual(result['statusCode'], 200)
        body = json.loads(result['body'])
        self.assertIn('unblocked successfully', body['message'])
        self.assertEqual(body['user_id'], 'test-user')
        self.assertEqual(body['performed_by'], 'admin-user')
        
        mock_execute_unblocking.assert_called_once_with(
            self.connection_mock, 'test-user', 'Manual admin unblock', 'admin-user'
        )
    
    @patch('lambda_function.get_mysql_connection')
    def test_check_user_status_blocked(self, mock_get_connection):
        """Test checking status of blocked user"""
        mock_get_connection.return_value = self.connection_mock
        
        # Mock database responses
        blocked_time = datetime(2024, 1, 15, 12, 0, 0)
        expires_time = datetime(2024, 1, 16, 0, 0, 0)
        
        self.cursor_mock.fetchone.side_effect = [
            {
                'is_blocked': 'Y',
                'blocked_reason': 'Daily limit exceeded',
                'blocked_at': blocked_time,
                'blocked_until': expires_time,
                'performed_by': 'system',
                'block_type': 'AUTO'
            },
            {
                'administrative_safe': 'N'
            }
        ]
        
        status_event = {'action': 'check_status', 'user_id': 'test-user'}
        result = lambda_function.check_user_status(status_event)
        
        self.assertEqual(result['statusCode'], 200)
        body = json.loads(result['body'])
        self.assertTrue(body['is_blocked'])
        self.assertEqual(body['block_reason'], 'Daily limit exceeded')
        self.assertEqual(body['block_type'], 'AUTO')
        self.assertEqual(body['performed_by'], 'system')

class TestEmailNotifications(TestBedrockRealtimeUsageController):
    """Test email notification functionality"""
    
    @patch('lambda_function.get_user_email')
    @patch('lambda_function.send_gmail_email')
    def test_send_blocking_email_gmail_success(self, mock_send_gmail, mock_get_email):
        """Test successful blocking email via Gmail"""
        mock_get_email.return_value = 'test@example.com'
        mock_send_gmail.return_value = True
        
        blocked_until = datetime(2024, 1, 16, 0, 0, 0, tzinfo=pytz.timezone('Europe/Madrid'))
        
        result = lambda_function.send_blocking_email_gmail(
            'test-user', 'Daily limit exceeded', self.sample_usage_info, blocked_until
        )
        
        self.assertTrue(result)
        mock_send_gmail.assert_called_once()
        
        # Verify email content
        call_args = mock_send_gmail.call_args
        self.assertEqual(call_args[0][0], 'test@example.com')  # to_email
        self.assertIn('Bedrock Access Blocked', call_args[0][1])  # subject
        self.assertIn('Daily limit exceeded', call_args[0][2])  # body_text
        self.assertIn('Daily limit exceeded', call_args[0][3])  # body_html
    
    @patch('lambda_function.lambda_client')
    @patch('lambda_function.send_blocking_email_gmail')
    def test_send_enhanced_blocking_email_success(self, mock_gmail_fallback, mock_lambda_client):
        """Test enhanced blocking email via Lambda service"""
        # Mock successful Lambda response
        mock_response = {
            'Payload': Mock()
        }
        mock_response['Payload'].read.return_value = json.dumps({'statusCode': 200}).encode()
        mock_lambda_client.invoke.return_value = mock_response
        
        result = lambda_function.send_enhanced_blocking_email(
            'test-user', 'Daily limit exceeded', self.sample_usage_info, 'system'
        )
        
        self.assertTrue(result)
        mock_lambda_client.invoke.assert_called_once()
        mock_gmail_fallback.assert_not_called()

class TestUserMetadataRetrieval(TestBedrockRealtimeUsageController):
    """Test user metadata retrieval from IAM"""
    
    @patch('lambda_function.iam')
    def test_get_user_team_from_tag(self, mock_iam):
        """Test getting user team from IAM tag"""
        mock_iam.list_user_tags.return_value = {
            'Tags': [
                {'Key': 'Team', 'Value': 'yo_leo_engineering'},
                {'Key': 'Department', 'Value': 'IT'}
            ]
        }
        
        result = lambda_function.get_user_team('test-user')
        
        self.assertEqual(result, 'yo_leo_engineering')
        mock_iam.list_user_tags.assert_called_once_with(UserName='test-user')
    
    @patch('lambda_function.iam')
    def test_get_user_email(self, mock_iam):
        """Test getting user email from IAM tag"""
        mock_iam.list_user_tags.return_value = {
            'Tags': [
                {'Key': 'Email', 'Value': 'test@example.com'},
                {'Key': 'Team', 'Value': 'engineering'}
            ]
        }
        
        result = lambda_function.get_user_email('test-user')
        
        self.assertEqual(result, 'test@example.com')

class TestErrorHandling(TestBedrockRealtimeUsageController):
    """Test error handling and edge cases"""
    
    @patch('lambda_function.get_mysql_connection')
    def test_database_connection_failure(self, mock_get_connection):
        """Test handling database connection failure"""
        mock_get_connection.side_effect = Exception("Database connection failed")
        
        # Test with CloudTrail event
        cloudtrail_event = {'detail': self.sample_cloudtrail_event}
        result = lambda_function.handle_cloudtrail_event(cloudtrail_event, {})
        
        self.assertEqual(result['statusCode'], 500)
        body = json.loads(result['body'])
        self.assertIn('error', body)
    
    def test_parse_bedrock_event_exception(self):
        """Test parse_bedrock_event with malformed data"""
        malformed_event = {
            'eventName': 'InvokeModel',
            'userIdentity': None,  # This should cause an exception
            'requestParameters': {'modelId': 'test-model'}
        }
        
        result = lambda_function.parse_bedrock_event(malformed_event)
        
        self.assertIsNone(result)

class TestIntegrationScenarios(TestBedrockRealtimeUsageController):
    """Test complete integration scenarios"""
    
    @patch('lambda_function.execute_user_blocking')
    @patch('lambda_function.check_user_limits_with_protection')
    @patch('lambda_function.check_user_blocking_status')
    @patch('lambda_function.ensure_user_exists')
    @patch('lambda_function.get_user_person_tag')
    @patch('lambda_function.get_user_team')
    @patch('lambda_function.parse_bedrock_event')
    @patch('lambda_function.get_mysql_connection')
    def test_complete_cloudtrail_blocking_scenario(self, mock_get_connection, mock_parse_event,
                                                 mock_get_team, mock_get_person, mock_ensure_user,
                                                 mock_check_blocking, mock_check_limits, mock_execute_blocking):
        """Test complete CloudTrail event processing leading to blocking"""
        # Setup mocks
        mock_get_connection.return_value = self.connection_mock
        mock_parse_event.return_value = {
            'user_id': 'test-user',
            'model_id': 'anthropic.claude-3-5-sonnet-20240620-v1:0',
            'request_id': 'test-request-123',
            'cet_timestamp': '2024-01-15 12:00:00'
        }
        mock_get_team.return_value = 'yo_leo_engineering'
        mock_get_person.return_value = 'John Doe'
        mock_check_blocking.return_value = (False, None)  # Not currently blocked
        mock_check_limits.return_value = (True, 'Daily limit exceeded', self.sample_usage_info)  # Should block
        mock_execute_blocking.return_value = True
        
        # Execute test
        cloudtrail_event = {'detail': self.sample_cloudtrail_event}
        result = lambda_function.handle_cloudtrail_event(cloudtrail_event, {})
        
        # Verify results
        self.assertEqual(result['statusCode'], 200)
        body = json.loads(result['body'])
        self.assertEqual(body['blocked_requests'], 1)
        
        # Verify function calls
        mock_parse_event.assert_called_once()
        mock_get_team.assert_called_once_with('test-user')
        mock_get_person.assert_called_once_with('test-user')
        mock_ensure_user.assert_called_once_with(self.connection_mock, 'test-user', 'yo_leo_engineering', 'John Doe')
        mock_check_blocking.assert_called_once_with(self.connection_mock, 'test-user')
        mock_check_limits.assert_called_once_with(self.connection_mock, 'test-user')
        mock_execute_blocking.assert_called_once_with(self.connection_mock, 'test-user', 'Daily limit exceeded', self.sample_usage_info)


# Test execution and documentation
if __name__ == '__main__':
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add all test classes
    test_classes = [
        TestEventRouting,
        TestCloudTrailEventProcessing,
        TestTimezoneHandling,
        TestDatabaseOperations,
        TestUserLimitsAndBlocking,
        TestBlockingWorkflow,
        TestUnblockingWorkflow,
        TestIAMPolicyManagement,
        TestAPIEventHandling,
        TestManualOperations,
        TestEmailNotifications,
        TestUserMetadataRetrieval,
        TestErrorHandling,
        TestIntegrationScenarios
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests with detailed output
    runner = unittest.TextTestRunner(verbosity=2, buffer=True)
    result = runner.run(test_suite)
    
    # Print summary
    print(f"\n{'='*60}")
    print("TEST EXECUTION SUMMARY")
    print(f"{'='*60}")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    if result.failures:
        print(f"\nFAILURES ({len(result.failures)}):")
        for test, traceback in result.failures:
            error_msg = traceback.split('AssertionError: ')[-1].split('\n')[0]
            print(f"- {test}: {error_msg}")
    
    if result.errors:
        print(f"\nERRORS ({len(result.errors)}):")
        for test, traceback in result.errors:
            error_msg = traceback.split('\n')[-2]
            print(f"- {test}: {error_msg}")
    
    print(f"\n{'='*60}")
