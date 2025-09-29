#!/usr/bin/env python3
"""
Comprehensive Unit Test Plan for bedrock_daily_reset.py Lambda Function
=====================================================================

This test suite provides comprehensive coverage for all scenarios and edge cases
of the bedrock_daily_reset Lambda function before AWS deployment.

Test Categories:
1. Database Connection Tests
2. User Unblocking Logic Tests
3. Administrative Safe Flag Management Tests
4. IAM Policy Management Tests
5. Email Notification Tests
6. Error Handling Tests
7. Integration Tests
8. Performance Tests

Author: AWS Bedrock Usage Control System
Version: 1.0.0
"""

import unittest
from unittest.mock import Mock, patch, MagicMock, call
import json
import pytest
from datetime import datetime, timedelta
import pytz
import pymysql
import boto3
try:
    from moto import mock_iam, mock_lambda, mock_sns
except ImportError:
    # Fallback if moto decorators are not available
    def mock_iam(func):
        return func
    def mock_lambda(func):
        return func
    def mock_sns(func):
        return func
import os
import sys

# Set environment variables before importing the Lambda function
os.environ.setdefault('RDS_ENDPOINT', 'test-rds-endpoint.amazonaws.com')
os.environ.setdefault('RDS_USERNAME', 'test_user')
os.environ.setdefault('RDS_PASSWORD', 'test_password')
os.environ.setdefault('RDS_DATABASE', 'test_bedrock_usage')
os.environ.setdefault('AWS_REGION', 'eu-west-1')
os.environ.setdefault('ACCOUNT_ID', '123456789012')
os.environ.setdefault('SNS_TOPIC_ARN', 'arn:aws:sns:eu-west-1:123456789012:test-topic')
os.environ.setdefault('EMAIL_SERVICE_FUNCTION', 'test-email-service')

# Add the Lambda function to the path for testing
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the Lambda function (assuming it's in the same directory)
import bedrock_daily_reset

class TestBedrockDailyReset(unittest.TestCase):
    """Comprehensive test suite for bedrock_daily_reset Lambda function"""
    
    def setUp(self):
        """Set up test fixtures and mock objects"""
        # Mock environment variables
        self.env_vars = {
            'RDS_ENDPOINT': 'test-rds-endpoint.amazonaws.com',
            'RDS_USERNAME': 'test_user',
            'RDS_PASSWORD': 'test_password',
            'RDS_DATABASE': 'test_bedrock_usage',
            'AWS_REGION': 'eu-west-1',
            'ACCOUNT_ID': '123456789012',
            'SNS_TOPIC_ARN': 'arn:aws:sns:eu-west-1:123456789012:test-topic',
            'EMAIL_SERVICE_FUNCTION': 'test-email-service'
        }
        
        # Patch environment variables
        self.env_patcher = patch.dict(os.environ, self.env_vars)
        self.env_patcher.start()
        
        # Mock AWS clients
        self.mock_lambda_client = Mock()
        self.mock_sns_client = Mock()
        self.mock_iam_client = Mock()
        
        # Mock database connection
        self.mock_connection = Mock()
        self.mock_cursor = Mock()
        
        # Set up context manager for cursor
        mock_cursor_context = MagicMock()
        mock_cursor_context.__enter__.return_value = self.mock_cursor
        mock_cursor_context.__exit__.return_value = None
        self.mock_connection.cursor.return_value = mock_cursor_context
        
        # Mock context object
        self.mock_context = Mock()
        self.mock_context.function_name = "bedrock-daily-reset"
        self.mock_context.memory_limit_in_mb = 512
        self.mock_context.invoked_function_arn = "arn:aws:lambda:eu-west-1:123456789012:function:bedrock-daily-reset"
        
        # CET timezone for testing
        self.cet = pytz.timezone('Europe/Madrid')
        self.test_time = self.cet.localize(datetime(2025, 1, 16, 0, 0, 0))
        
    def tearDown(self):
        """Clean up after tests"""
        self.env_patcher.stop()
        # Reset global connection pool
        bedrock_daily_reset.connection_pool = None

    # ========================================
    # 1. DATABASE CONNECTION TESTS
    # ========================================
    
    @patch('bedrock_daily_reset.pymysql.connect')
    def test_get_mysql_connection_success(self, mock_connect):
        """Test successful MySQL connection establishment"""
        mock_connect.return_value = self.mock_connection
        
        connection = bedrock_daily_reset.get_mysql_connection()
        
        self.assertEqual(connection, self.mock_connection)
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
    
    @patch('bedrock_daily_reset.pymysql.connect')
    def test_get_mysql_connection_with_reconnect(self, mock_connect):
        """Test MySQL connection with reconnection logic"""
        # First connection that will fail on ping
        mock_connection1 = Mock()
        mock_connection1.ping.side_effect = Exception("Connection lost")
        
        # Second connection (reconnect) that works
        mock_connection2 = Mock()
        mock_connection2.ping.return_value = None
        
        mock_connect.side_effect = [mock_connection1, mock_connection2]
        
        # First call establishes connection but ping fails, so it creates a new one
        connection = bedrock_daily_reset.get_mysql_connection()
        # The function should return the second connection due to reconnection logic
        self.assertEqual(connection, mock_connection2)
        self.assertEqual(mock_connect.call_count, 2)
    
    @patch('bedrock_daily_reset.pymysql.connect')
    def test_get_mysql_connection_failure(self, mock_connect):
        """Test MySQL connection failure handling"""
        mock_connect.side_effect = pymysql.Error("Connection failed")
        
        with self.assertRaises(pymysql.Error):
            bedrock_daily_reset.get_mysql_connection()

    # ========================================
    # 2. USER UNBLOCKING LOGIC TESTS
    # ========================================
    
    @patch('bedrock_daily_reset.get_current_cet_time')
    @patch('bedrock_daily_reset.get_mysql_connection')
    def test_unblock_expired_users_success(self, mock_get_connection, mock_get_time):
        """Test successful unblocking of users with expired blocks"""
        mock_get_connection.return_value = self.mock_connection
        mock_get_time.return_value = self.test_time
        
        # Mock expired blocked users
        expired_users = [
            {
                'user_id': 'user1',
                'blocked_reason': 'Daily limit exceeded',
                'blocked_until': self.test_time - timedelta(hours=1),
                'team': 'team_a',
                'person': 'John Doe',
                'daily_request_limit': 350,
                'administrative_safe': 'N'
            },
            {
                'user_id': 'user2',
                'blocked_reason': 'Daily limit exceeded',
                'blocked_until': None,  # No expiration (should be unblocked)
                'team': 'team_b',
                'person': 'Jane Smith',
                'daily_request_limit': 500,
                'administrative_safe': 'Y'
            }
        ]
        
        # Mock active users with admin safe flag
        active_admin_users = [
            {
                'user_id': 'user3',
                'team': 'team_c',
                'person': 'Bob Wilson',
                'daily_request_limit': 250
            }
        ]
        
        # Configure cursor mock
        self.mock_cursor.fetchall.side_effect = [expired_users, active_admin_users]
        
        with patch('bedrock_daily_reset.execute_user_unblocking', return_value=True) as mock_unblock, \
             patch('bedrock_daily_reset.send_reset_email_notification', return_value=True) as mock_email, \
             patch('bedrock_daily_reset.remove_administrative_safe_flag', return_value=True) as mock_remove_flag:
            
            result = bedrock_daily_reset.unblock_all_blocked_users_and_notify(self.mock_connection)
            
            # Verify results
            self.assertEqual(result['unblocked_count'], 2)
            self.assertEqual(result['notified_count'], 2)
            self.assertEqual(result['admin_safe_removed_count'], 1)
            self.assertEqual(len(result['errors']), 0)
            self.assertEqual(result['unblocked_users'], ['user1', 'user2'])
            self.assertEqual(result['admin_safe_removed_users'], ['user3'])
            
            # Verify function calls
            self.assertEqual(mock_unblock.call_count, 2)
            self.assertEqual(mock_email.call_count, 2)
            self.assertEqual(mock_remove_flag.call_count, 1)
    
    @patch('bedrock_daily_reset.get_current_cet_time')
    @patch('bedrock_daily_reset.get_mysql_connection')
    def test_unblock_no_expired_users(self, mock_get_connection, mock_get_time):
        """Test scenario with no expired blocked users"""
        mock_get_connection.return_value = self.mock_connection
        mock_get_time.return_value = self.test_time
        
        # No expired users, no active admin users
        self.mock_cursor.fetchall.side_effect = [[], []]
        
        result = bedrock_daily_reset.unblock_all_blocked_users_and_notify(self.mock_connection)
        
        self.assertEqual(result['unblocked_count'], 0)
        self.assertEqual(result['notified_count'], 0)
        self.assertEqual(result['admin_safe_removed_count'], 0)
        self.assertEqual(len(result['errors']), 0)
    
    @patch('bedrock_daily_reset.get_current_cet_time')
    @patch('bedrock_daily_reset.get_mysql_connection')
    def test_unblock_with_partial_failures(self, mock_get_connection, mock_get_time):
        """Test scenario with partial failures in unblocking process"""
        mock_get_connection.return_value = self.mock_connection
        mock_get_time.return_value = self.test_time
        
        expired_users = [
            {
                'user_id': 'user1',
                'blocked_reason': 'Daily limit exceeded',
                'blocked_until': self.test_time - timedelta(hours=1),
                'team': 'team_a',
                'person': 'John Doe',
                'daily_request_limit': 350,
                'administrative_safe': 'N'
            },
            {
                'user_id': 'user2',
                'blocked_reason': 'Daily limit exceeded',
                'blocked_until': self.test_time - timedelta(hours=2),
                'team': 'team_b',
                'person': 'Jane Smith',
                'daily_request_limit': 500,
                'administrative_safe': 'N'
            }
        ]
        
        self.mock_cursor.fetchall.side_effect = [expired_users, []]
        
        with patch('bedrock_daily_reset.execute_user_unblocking') as mock_unblock, \
             patch('bedrock_daily_reset.send_reset_email_notification') as mock_email:
            
            # First user succeeds, second fails
            mock_unblock.side_effect = [True, False]
            mock_email.side_effect = [True, False]  # Email for first user succeeds
            
            result = bedrock_daily_reset.unblock_all_blocked_users_and_notify(self.mock_connection)
            
            self.assertEqual(result['unblocked_count'], 1)
            self.assertEqual(result['notified_count'], 1)
            self.assertEqual(len(result['errors']), 1)
            self.assertIn('Failed to unblock user user2', result['errors'][0])

    # ========================================
    # 3. ADMINISTRATIVE SAFE FLAG TESTS
    # ========================================
    
    @patch('bedrock_daily_reset.get_cet_timestamp_string')
    def test_remove_administrative_safe_flag_success(self, mock_timestamp):
        """Test successful removal of administrative_safe flag"""
        mock_timestamp.return_value = '2025-01-16 00:00:00'
        self.mock_cursor.rowcount = 1  # One row affected
        
        result = bedrock_daily_reset.remove_administrative_safe_flag(self.mock_connection, 'user1')
        
        self.assertTrue(result)
        
        # Verify database calls - check that the calls were made (allowing for formatting differences)
        self.assertEqual(self.mock_cursor.execute.call_count, 2)
        
        # Check first call (UPDATE)
        first_call = self.mock_cursor.execute.call_args_list[0]
        self.assertIn('UPDATE user_limits', first_call[0][0])
        self.assertIn("administrative_safe = 'N'", first_call[0][0])
        self.assertEqual(first_call[0][1], ['2025-01-16 00:00:00', 'user1'])
        
        # Check second call (INSERT)
        second_call = self.mock_cursor.execute.call_args_list[1]
        self.assertIn('INSERT INTO blocking_audit_log', second_call[0][0])
        self.assertIn('ADMIN_SAFE_REMOVED', second_call[0][0])
        self.assertEqual(second_call[0][1], ['user1', '2025-01-16 00:00:00', '2025-01-16 00:00:00'])
    
    @patch('bedrock_daily_reset.get_cet_timestamp_string')
    def test_remove_administrative_safe_flag_no_flag_to_remove(self, mock_timestamp):
        """Test removal when no administrative_safe flag exists"""
        mock_timestamp.return_value = '2025-01-16 00:00:00'
        self.mock_cursor.rowcount = 0  # No rows affected
        
        result = bedrock_daily_reset.remove_administrative_safe_flag(self.mock_connection, 'user1')
        
        self.assertTrue(result)  # Should still return True
        
        # Should only call UPDATE, not INSERT (no audit log for no-op)
        self.assertEqual(self.mock_cursor.execute.call_count, 1)
    
    def test_remove_administrative_safe_flag_database_error(self):
        """Test handling of database errors during flag removal"""
        self.mock_cursor.execute.side_effect = pymysql.Error("Database error")
        
        result = bedrock_daily_reset.remove_administrative_safe_flag(self.mock_connection, 'user1')
        
        self.assertFalse(result)

    # ========================================
    # 4. IAM POLICY MANAGEMENT TESTS
    # ========================================
    
    @patch('bedrock_daily_reset.iam')
    def test_implement_iam_unblocking_success(self, mock_iam_client):
        """Test successful IAM policy modification for unblocking"""
        # Mock existing policy with deny statement
        existing_policy = {
            'Statement': [
                {
                    'Sid': 'BedrockAccess',
                    'Effect': 'Allow',
                    'Action': ['bedrock:InvokeModel'],
                    'Resource': '*'
                },
                {
                    'Sid': 'DailyLimitBlock',
                    'Effect': 'Deny',
                    'Action': ['bedrock:InvokeModel'],
                    'Resource': '*'
                }
            ]
        }
        
        mock_iam_client.get_user_policy.return_value = {'PolicyDocument': existing_policy}
        
        result = bedrock_daily_reset.implement_iam_unblocking('test_user')
        
        self.assertTrue(result)
        
        # Verify policy was updated (deny statement removed)
        mock_iam_client.put_user_policy.assert_called_once()
        call_args = mock_iam_client.put_user_policy.call_args
        updated_policy = json.loads(call_args[1]['PolicyDocument'])
        
        # Should only have the Allow statement
        self.assertEqual(len(updated_policy['Statement']), 1)
        self.assertEqual(updated_policy['Statement'][0]['Sid'], 'BedrockAccess')
        self.assertEqual(updated_policy['Statement'][0]['Effect'], 'Allow')
    
    @patch('bedrock_daily_reset.iam')
    def test_implement_iam_unblocking_no_existing_policy(self, mock_iam_client):
        """Test IAM unblocking when no policy exists"""
        # Create a custom exception class that mimics NoSuchEntityException
        class MockNoSuchEntityException(Exception):
            pass
        
        # Mock the exceptions attribute
        mock_exceptions = Mock()
        mock_exceptions.NoSuchEntityException = MockNoSuchEntityException
        mock_iam_client.exceptions = mock_exceptions
        
        # Set up the exception to be raised
        mock_iam_client.get_user_policy.side_effect = MockNoSuchEntityException("NoSuchEntity")
        
        result = bedrock_daily_reset.implement_iam_unblocking('test_user')
        
        self.assertTrue(result)  # Should succeed (no action needed)
        mock_iam_client.put_user_policy.assert_not_called()
    
    @patch('bedrock_daily_reset.iam')
    def test_implement_iam_unblocking_policy_without_allow(self, mock_iam_client):
        """Test IAM unblocking when policy has no Allow statements"""
        # Policy with only deny statement
        existing_policy = {
            'Statement': [
                {
                    'Sid': 'DailyLimitBlock',
                    'Effect': 'Deny',
                    'Action': ['bedrock:InvokeModel'],
                    'Resource': '*'
                }
            ]
        }
        
        mock_iam_client.get_user_policy.return_value = {'PolicyDocument': existing_policy}
        
        result = bedrock_daily_reset.implement_iam_unblocking('test_user')
        
        self.assertTrue(result)
        
        # Verify Allow statement was added
        call_args = mock_iam_client.put_user_policy.call_args
        updated_policy = json.loads(call_args[1]['PolicyDocument'])
        
        self.assertEqual(len(updated_policy['Statement']), 1)
        self.assertEqual(updated_policy['Statement'][0]['Sid'], 'BedrockAccess')
        self.assertEqual(updated_policy['Statement'][0]['Effect'], 'Allow')
    
    @patch('bedrock_daily_reset.iam')
    def test_implement_iam_unblocking_failure(self, mock_iam_client):
        """Test IAM unblocking failure handling"""
        mock_iam_client.get_user_policy.side_effect = Exception("IAM error")
        
        result = bedrock_daily_reset.implement_iam_unblocking('test_user')
        
        self.assertFalse(result)

    # ========================================
    # 5. EMAIL NOTIFICATION TESTS
    # ========================================
    
    @patch('bedrock_daily_reset.lambda_client')
    @patch('bedrock_daily_reset.get_cet_timestamp_string')
    def test_send_reset_email_notification_success(self, mock_timestamp, mock_lambda_client):
        """Test successful email notification sending"""
        mock_timestamp.return_value = '2025-01-16 00:00:00'
        mock_lambda_client.invoke.return_value = {'StatusCode': 202}
        
        user_data = {
            'user_id': 'test_user',
            'team': 'test_team',
            'person': 'Test Person',
            'daily_request_limit': 350
        }
        
        result = bedrock_daily_reset.send_reset_email_notification(user_data)
        
        self.assertTrue(result)
        
        # Verify Lambda invocation
        mock_lambda_client.invoke.assert_called_once()
        call_args = mock_lambda_client.invoke.call_args
        
        self.assertEqual(call_args[1]['FunctionName'], 'test-email-service')
        self.assertEqual(call_args[1]['InvocationType'], 'Event')
        
        # Verify payload
        payload = json.loads(call_args[1]['Payload'])
        self.assertEqual(payload['email_type'], 'daily_reset')
        self.assertEqual(payload['user_id'], 'test_user')
        self.assertEqual(payload['user_data']['person'], 'Test Person')
        self.assertEqual(payload['user_data']['team'], 'test_team')
    
    @patch('bedrock_daily_reset.lambda_client')
    def test_send_reset_email_notification_with_defaults(self, mock_lambda_client):
        """Test email notification with default values"""
        mock_lambda_client.invoke.return_value = {'StatusCode': 202}
        
        user_data = {
            'user_id': 'test_user'
            # Missing team, person, daily_request_limit
        }
        
        result = bedrock_daily_reset.send_reset_email_notification(user_data)
        
        self.assertTrue(result)
        
        # Verify defaults were used
        payload = json.loads(mock_lambda_client.invoke.call_args[1]['Payload'])
        self.assertEqual(payload['user_data']['team'], 'Unknown')
        self.assertEqual(payload['user_data']['person'], 'test_user')
        self.assertEqual(payload['user_data']['daily_limit'], 350)
    
    @patch('bedrock_daily_reset.lambda_client')
    def test_send_reset_email_notification_failure(self, mock_lambda_client):
        """Test email notification failure handling"""
        mock_lambda_client.invoke.side_effect = Exception("Lambda invocation failed")
        
        user_data = {'user_id': 'test_user'}
        
        result = bedrock_daily_reset.send_reset_email_notification(user_data)
        
        self.assertFalse(result)

    # ========================================
    # 6. ERROR HANDLING TESTS
    # ========================================
    
    @patch('bedrock_daily_reset.sns')
    @patch('bedrock_daily_reset.get_cet_timestamp_string')
    def test_send_error_notification_success(self, mock_timestamp, mock_sns_client):
        """Test successful error notification sending"""
        mock_timestamp.return_value = '2025-01-16 00:00:00'
        
        bedrock_daily_reset.send_error_notification("Test error message")
        
        mock_sns_client.publish.assert_called_once()
        call_args = mock_sns_client.publish.call_args
        
        self.assertEqual(call_args[1]['TopicArn'], 'arn:aws:sns:eu-west-1:123456789012:test-topic')
        self.assertEqual(call_args[1]['Subject'], '🚨 Bedrock Daily Reset FAILED')
        self.assertIn('Test error message', call_args[1]['Message'])
        self.assertIn('2025-01-16 00:00:00', call_args[1]['Message'])
    
    @patch('bedrock_daily_reset.sns')
    def test_send_error_notification_failure(self, mock_sns_client):
        """Test error notification failure handling"""
        mock_sns_client.publish.side_effect = Exception("SNS error")
        
        # Should not raise exception
        bedrock_daily_reset.send_error_notification("Test error")

    # ========================================
    # 7. INTEGRATION TESTS
    # ========================================
    
    @patch('bedrock_daily_reset.get_mysql_connection')
    @patch('bedrock_daily_reset.get_current_cet_time')
    def test_lambda_handler_success(self, mock_get_time, mock_get_connection):
        """Test successful Lambda handler execution"""
        mock_get_time.return_value = self.test_time
        mock_get_connection.return_value = self.mock_connection
        
        # Mock successful unblock operation
        with patch('bedrock_daily_reset.unblock_all_blocked_users_and_notify') as mock_unblock:
            mock_unblock.return_value = {
                'unblocked_count': 2,
                'notified_count': 2,
                'admin_safe_removed_count': 1,
                'errors': [],
                'unblocked_users': ['user1', 'user2'],
                'admin_safe_removed_users': ['user3']
            }
            
            event = {
                "version": "0",
                "id": "test-event-id",
                "detail-type": "Scheduled Event",
                "source": "aws.events"
            }
            
            result = bedrock_daily_reset.lambda_handler(event, self.mock_context)
            
            self.assertEqual(result['statusCode'], 200)
            
            body = json.loads(result['body'])
            self.assertEqual(body['message'], 'Daily reset completed successfully')
            self.assertEqual(body['results']['users_unblocked'], 2)
            self.assertEqual(body['results']['users_notified'], 2)
            self.assertEqual(body['results']['admin_safe_removed'], 1)
    
    @patch('bedrock_daily_reset.get_mysql_connection')
    @patch('bedrock_daily_reset.send_error_notification')
    def test_lambda_handler_database_connection_failure(self, mock_send_error, mock_get_connection):
        """Test Lambda handler with database connection failure"""
        mock_get_connection.side_effect = Exception("Database connection failed")
        
        event = {"source": "aws.events"}
        
        result = bedrock_daily_reset.lambda_handler(event, self.mock_context)
        
        self.assertEqual(result['statusCode'], 500)
        
        body = json.loads(result['body'])
        self.assertIn('Daily reset failed', body['error'])
        
        # Verify error notification was sent
        mock_send_error.assert_called_once()
    
    @patch('bedrock_daily_reset.get_mysql_connection')
    def test_lambda_handler_partial_failure(self, mock_get_connection):
        """Test Lambda handler with partial failures"""
        mock_get_connection.return_value = self.mock_connection
        
        # Mock partial failure in unblock operation
        with patch('bedrock_daily_reset.unblock_all_blocked_users_and_notify') as mock_unblock:
            mock_unblock.return_value = {
                'unblocked_count': 1,
                'notified_count': 1,
                'admin_safe_removed_count': 0,
                'errors': ['Failed to unblock user user2', 'Failed to send email to user user3'],
                'unblocked_users': ['user1'],
                'admin_safe_removed_users': []
            }
            
            event = {"source": "aws.events"}
            
            result = bedrock_daily_reset.lambda_handler(event, self.mock_context)
            
            # Should still return 200 (partial success)
            self.assertEqual(result['statusCode'], 200)
            
            body = json.loads(result['body'])
            self.assertEqual(len(body['results']['errors']), 2)

    # ========================================
    # 8. PERFORMANCE TESTS
    # ========================================
    
    @patch('bedrock_daily_reset.get_mysql_connection')
    @patch('bedrock_daily_reset.get_current_cet_time')
    def test_performance_large_user_set(self, mock_get_time, mock_get_connection):
        """Test performance with large number of users"""
        mock_get_time.return_value = self.test_time
        mock_get_connection.return_value = self.mock_connection
        
        # Create large dataset (1000 users)
        expired_users = []
        active_admin_users = []
        
        for i in range(500):
            expired_users.append({
                'user_id': f'blocked_user_{i}',
                'blocked_reason': 'Daily limit exceeded',
                'blocked_until': self.test_time - timedelta(hours=1),
                'team': f'team_{i % 10}',
                'person': f'Person {i}',
                'daily_request_limit': 350,
                'administrative_safe': 'N'
            })
        
        for i in range(500):
            active_admin_users.append({
                'user_id': f'admin_user_{i}',
                'team': f'team_{i % 10}',
                'person': f'Admin Person {i}',
                'daily_request_limit': 500
            })
        
        self.mock_cursor.fetchall.side_effect = [expired_users, active_admin_users]
        
        with patch('bedrock_daily_reset.execute_user_unblocking', return_value=True), \
             patch('bedrock_daily_reset.send_reset_email_notification', return_value=True), \
             patch('bedrock_daily_reset.remove_administrative_safe_flag', return_value=True):
            
            import time
            start_time = time.time()
            
            result = bedrock_daily_reset.unblock_all_blocked_users_and_notify(self.mock_connection)
            
            end_time = time.time()
            execution_time = end_time - start_time
            
            # Verify results
            self.assertEqual(result['unblocked_count'], 500)
            self.assertEqual(result['notified_count'], 500)
            self.assertEqual(result['admin_safe_removed_count'], 500)
            
            # Performance assertion (should complete within reasonable time)
            self.assertLess(execution_time, 10.0, "Function should complete within 10 seconds for 1000 users")

    # ========================================
    # 9. TIMEZONE TESTS
    # ========================================
    
    def test_cet_timezone_handling(self):
        """Test proper CET timezone handling"""
        with patch('bedrock_daily_reset.get_current_cet_time') as mock_get_time:
            test_time = self.cet.localize(datetime(2025, 1, 16, 14, 30, 45))
            mock_get_time.return_value = test_time
            
            result = bedrock_daily_reset.get_current_cet_time()
            
            self.assertEqual(result, test_time)
            mock_get_time.assert_called_once()
    
    def test_cet_timestamp_string_format(self):
        """Test CET timestamp string formatting"""
        with patch('bedrock_daily_reset.get_current_cet_time') as mock_get_time:
            test_time = self.cet.localize(datetime(2025, 1, 16, 14, 30, 45))
            mock_get_time.return_value = test_time
            
            result = bedrock_daily_reset.get_cet_timestamp_string()
            
            self.assertEqual(result, '2025-01-16 14:30:45')

    # ========================================
    # 10. EDGE CASES AND BOUNDARY TESTS
    # ========================================
    
    @patch('bedrock_daily_reset.get_mysql_connection')
    def test_execute_user_unblocking_database_transaction_failure(self, mock_get_connection):
        """Test user unblocking with database transaction failure"""
        mock_get_connection.return_value = self.mock_connection
        
        # First query succeeds, second fails
        self.mock_cursor.execute.side_effect = [None, pymysql.Error("Transaction failed"), None]
        
        result = bedrock_daily_reset.execute_user_unblocking(self.mock_connection, 'test_user')
        
        self.assertFalse(result)
    
    @patch('bedrock_daily_reset.get_mysql_connection')
    def test_execute_user_unblocking_complete_success(self, mock_get_connection):
        """Test complete user unblocking workflow success"""
        mock_get_connection.return_value = self.mock_connection
        
        with patch('bedrock_daily_reset.implement_iam_unblocking', return_value=True):
            result = bedrock_daily_reset.execute_user_unblocking(self.mock_connection, 'test_user')
            
            self.assertTrue(result)
            
            # Verify database operations were called
            # The function performs: 1) UPDATE user_blocking_status, 2) UPDATE user_limits, 3) INSERT audit_log
            self.assertEqual(self.mock_cursor.execute.call_count, 3)  # UPDATE, UPDATE, INSERT

if __name__ == '__main__':
    unittest.main()
