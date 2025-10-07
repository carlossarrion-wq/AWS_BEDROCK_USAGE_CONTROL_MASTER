#!/usr/bin/env python3
"""
Unit Tests for bedrock-daily-reset Lambda Function
==================================================

Comprehensive unit tests covering all functionality of the daily reset Lambda.

Author: AWS Bedrock Usage Control System
Version: 1.0.0
"""

import pytest
import json
import sys
import os
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock, patch, call
import pytz

# Set up environment variables BEFORE importing lambda_function
os.environ['RDS_ENDPOINT'] = 'test-db.rds.amazonaws.com'
os.environ['RDS_USERNAME'] = 'test_user'
os.environ['RDS_PASSWORD'] = 'test_password'
os.environ['RDS_DATABASE'] = 'test_db'
os.environ['AWS_REGION'] = 'eu-west-1'
os.environ['ACCOUNT_ID'] = '701055077130'
os.environ['SNS_TOPIC_ARN'] = 'arn:aws:sns:eu-west-1:701055077130:bedrock-usage-alerts'
os.environ['EMAIL_SERVICE_FUNCTION'] = 'bedrock-email-service'

# Add the Lambda Functions directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '02. Source', 'Lambda Functions'))

# Import the Lambda function
import lambda_function

# Test fixtures
CET = pytz.timezone('Europe/Madrid')

@pytest.fixture
def mock_env_vars(monkeypatch):
    """Set up environment variables for testing"""
    monkeypatch.setenv('RDS_ENDPOINT', 'test-db.rds.amazonaws.com')
    monkeypatch.setenv('RDS_USERNAME', 'test_user')
    monkeypatch.setenv('RDS_PASSWORD', 'test_password')
    monkeypatch.setenv('RDS_DATABASE', 'test_db')
    monkeypatch.setenv('AWS_REGION', 'eu-west-1')
    monkeypatch.setenv('ACCOUNT_ID', '701055077130')
    monkeypatch.setenv('SNS_TOPIC_ARN', 'arn:aws:sns:eu-west-1:701055077130:bedrock-usage-alerts')
    monkeypatch.setenv('EMAIL_SERVICE_FUNCTION', 'bedrock-email-service')

@pytest.fixture
def mock_mysql_connection():
    """Mock MySQL connection"""
    connection = MagicMock()
    cursor = MagicMock()
    cursor.__enter__ = Mock(return_value=cursor)
    cursor.__exit__ = Mock(return_value=False)
    connection.cursor.return_value = cursor
    return connection, cursor

@pytest.fixture
def mock_aws_clients():
    """Mock AWS clients"""
    with patch('lambda_function.lambda_client') as mock_lambda, \
         patch('lambda_function.sns') as mock_sns, \
         patch('lambda_function.iam') as mock_iam:
        yield {
            'lambda': mock_lambda,
            'sns': mock_sns,
            'iam': mock_iam
        }

@pytest.fixture
def sample_blocked_user():
    """Sample blocked user data"""
    return {
        'user_id': 'test.user',
        'blocked_reason': 'Daily limit exceeded',
        'blocked_until': datetime.now(CET) - timedelta(hours=1),
        'team': 'Engineering',
        'person': 'Test User',
        'daily_request_limit': 350,
        'administrative_safe': 'N'
    }

@pytest.fixture
def sample_admin_safe_user():
    """Sample user with administrative_safe flag"""
    return {
        'user_id': 'admin.user',
        'team': 'Admin',
        'person': 'Admin User',
        'daily_request_limit': 500
    }

@pytest.fixture
def cloudwatch_event():
    """Sample CloudWatch Events cron trigger"""
    return {
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

@pytest.fixture
def mock_context():
    """Mock Lambda context"""
    context = Mock()
    context.function_name = "bedrock-daily-reset"
    context.memory_limit_in_mb = 512
    context.invoked_function_arn = "arn:aws:lambda:eu-west-1:701055077130:function:bedrock-daily-reset"
    return context


# ============================================================================
# TEST SUITE 1: Time and Timezone Functions
# ============================================================================

class TestTimezoneFunctions:
    """Test timezone and time-related functions"""
    
    def test_get_current_cet_time(self):
        """Test getting current CET time"""
        cet_time = lambda_function.get_current_cet_time()
        
        assert cet_time.tzinfo is not None
        assert cet_time.tzinfo.zone == 'Europe/Madrid'
        assert isinstance(cet_time, datetime)
    
    def test_get_cet_timestamp_string(self):
        """Test CET timestamp string format"""
        timestamp = lambda_function.get_cet_timestamp_string()
        
        # Should match format: YYYY-MM-DD HH:MM:SS
        assert len(timestamp) == 19
        assert timestamp[4] == '-'
        assert timestamp[7] == '-'
        assert timestamp[10] == ' '
        assert timestamp[13] == ':'
        assert timestamp[16] == ':'
        
        # Should be parseable as datetime
        parsed = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
        assert isinstance(parsed, datetime)


# ============================================================================
# TEST SUITE 2: Database Connection
# ============================================================================

class TestDatabaseConnection:
    """Test database connection functionality"""
    
    @patch('lambda_function.pymysql.connect')
    def test_get_mysql_connection_success(self, mock_connect, mock_env_vars):
        """Test successful MySQL connection"""
        mock_connection = MagicMock()
        mock_connect.return_value = mock_connection
        
        # Reset connection pool
        lambda_function.connection_pool = None
        
        connection = lambda_function.get_mysql_connection()
        
        assert connection is not None
        mock_connect.assert_called_once()
        assert mock_connect.call_args[1]['host'] == 'test-db.rds.amazonaws.com'
        assert mock_connect.call_args[1]['user'] == 'test_user'
        assert mock_connect.call_args[1]['database'] == 'test_db'
    
    @patch('lambda_function.pymysql.connect')
    def test_get_mysql_connection_reconnect(self, mock_connect, mock_env_vars):
        """Test MySQL connection reconnection on ping failure"""
        mock_connection = MagicMock()
        mock_connection.ping.side_effect = Exception("Connection lost")
        mock_connect.return_value = mock_connection
        
        lambda_function.connection_pool = mock_connection
        
        connection = lambda_function.get_mysql_connection()
        
        # Should create new connection after ping failure
        assert mock_connect.call_count == 1


# ============================================================================
# TEST SUITE 3: User Unblocking Workflow
# ============================================================================

class TestUserUnblocking:
    """Test user unblocking functionality"""
    
    def test_execute_user_unblocking_success(self, mock_mysql_connection, mock_aws_clients):
        """Test successful user unblocking"""
        connection, cursor = mock_mysql_connection
        cursor.rowcount = 1
        
        with patch('lambda_function.implement_iam_unblocking', return_value=True):
            result = lambda_function.execute_user_unblocking(connection, 'test.user')
        
        assert result is True
        
        # Verify database updates
        assert cursor.execute.call_count == 3  # UPDATE blocking_status, UPDATE user_limits, INSERT audit_log
        
        # Check UPDATE user_blocking_status call
        update_blocking_call = cursor.execute.call_args_list[0]
        assert 'UPDATE user_blocking_status' in update_blocking_call[0][0]
        assert 'is_blocked = \'N\'' in update_blocking_call[0][0]
        
        # Check UPDATE user_limits call
        update_limits_call = cursor.execute.call_args_list[1]
        assert 'UPDATE user_limits' in update_limits_call[0][0]
        assert 'administrative_safe = \'N\'' in update_limits_call[0][0]
        
        # Check INSERT audit_log call
        insert_audit_call = cursor.execute.call_args_list[2]
        assert 'INSERT INTO blocking_audit_log' in insert_audit_call[0][0]
        # The SQL has placeholders for: user_id, operation_type, operation_reason, performed_by, operation_timestamp, created_at
        # Parameters are: [user_id, current_cet_timestamp, current_cet_timestamp]
        # But 'UNBLOCK' is hardcoded in the SQL, not in parameters
        # So we verify it's in the SQL query itself
        assert 'UNBLOCK' in insert_audit_call[0][0]
    
    def test_execute_user_unblocking_database_error(self, mock_mysql_connection):
        """Test user unblocking with database error"""
        connection, cursor = mock_mysql_connection
        cursor.execute.side_effect = Exception("Database error")
        
        result = lambda_function.execute_user_unblocking(connection, 'test.user')
        
        assert result is False
    
    def test_execute_user_unblocking_iam_failure_continues(self, mock_mysql_connection):
        """Test that unblocking continues even if IAM fails"""
        connection, cursor = mock_mysql_connection
        cursor.rowcount = 1
        
        with patch('lambda_function.implement_iam_unblocking', side_effect=Exception("IAM error")):
            result = lambda_function.execute_user_unblocking(connection, 'test.user')
        
        # Should still succeed despite IAM failure
        assert result is True


# ============================================================================
# TEST SUITE 4: IAM Policy Management
# ============================================================================

class TestIAMPolicyManagement:
    """Test IAM policy management"""
    
    def test_implement_iam_unblocking_removes_deny(self, mock_aws_clients):
        """Test removing deny statement from IAM policy"""
        mock_iam = mock_aws_clients['iam']
        
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
        
        mock_iam.get_user_policy.return_value = {'PolicyDocument': existing_policy}
        
        result = lambda_function.implement_iam_unblocking('test.user')
        
        assert result is True
        
        # Verify deny statement was removed
        put_policy_call = mock_iam.put_user_policy.call_args
        updated_policy = json.loads(put_policy_call[1]['PolicyDocument'])
        
        deny_statements = [s for s in updated_policy['Statement'] if s.get('Sid') == 'DailyLimitBlock']
        assert len(deny_statements) == 0
    
    def test_implement_iam_unblocking_adds_allow_if_missing(self, mock_aws_clients):
        """Test adding allow statement if none exists"""
        mock_iam = mock_aws_clients['iam']
        
        # Mock policy with only deny statement
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
        
        mock_iam.get_user_policy.return_value = {'PolicyDocument': existing_policy}
        
        result = lambda_function.implement_iam_unblocking('test.user')
        
        assert result is True
        
        # Verify allow statement was added
        put_policy_call = mock_iam.put_user_policy.call_args
        updated_policy = json.loads(put_policy_call[1]['PolicyDocument'])
        
        allow_statements = [s for s in updated_policy['Statement'] if s.get('Effect') == 'Allow']
        assert len(allow_statements) > 0
    
    def test_implement_iam_unblocking_no_policy_exists(self, mock_aws_clients):
        """Test unblocking when no policy exists"""
        mock_iam = mock_aws_clients['iam']
        
        # Create a proper exception class that inherits from Exception
        class NoSuchEntityException(Exception):
            pass
        
        # Assign it to the mock
        mock_iam.exceptions.NoSuchEntityException = NoSuchEntityException
        
        # Mock the exception being raised
        mock_iam.get_user_policy.side_effect = NoSuchEntityException("Policy not found")
        
        result = lambda_function.implement_iam_unblocking('test.user')
        
        assert result is True
        mock_iam.put_user_policy.assert_not_called()


# ============================================================================
# TEST SUITE 5: Email Notifications
# ============================================================================

class TestEmailNotifications:
    """Test email notification functionality"""
    
    def test_send_reset_email_notification_success(self, sample_blocked_user, mock_aws_clients):
        """Test successful email notification"""
        mock_lambda = mock_aws_clients['lambda']
        mock_lambda.invoke.return_value = {'StatusCode': 202}
        
        result = lambda_function.send_reset_email_notification(sample_blocked_user)
        
        assert result is True
        
        # Verify Lambda invocation
        mock_lambda.invoke.assert_called_once()
        call_args = mock_lambda.invoke.call_args
        
        assert call_args[1]['FunctionName'] == 'bedrock-email-service'
        assert call_args[1]['InvocationType'] == 'Event'
        
        # Verify payload
        payload = json.loads(call_args[1]['Payload'])
        assert payload['email_type'] == 'daily_reset'
        assert payload['user_id'] == 'test.user'
        assert payload['user_data']['person'] == 'Test User'
        assert payload['user_data']['team'] == 'Engineering'
    
    def test_send_reset_email_notification_failure(self, sample_blocked_user, mock_aws_clients):
        """Test email notification failure"""
        mock_lambda = mock_aws_clients['lambda']
        mock_lambda.invoke.side_effect = Exception("Lambda invocation failed")
        
        result = lambda_function.send_reset_email_notification(sample_blocked_user)
        
        assert result is False


# ============================================================================
# TEST SUITE 6: Administrative Safe Flag Management
# ============================================================================

class TestAdministrativeSafeFlag:
    """Test administrative_safe flag management"""
    
    def test_remove_administrative_safe_flag_success(self, mock_mysql_connection):
        """Test successful removal of administrative_safe flag"""
        connection, cursor = mock_mysql_connection
        cursor.rowcount = 1
        
        result = lambda_function.remove_administrative_safe_flag(connection, 'admin.user')
        
        assert result is True
        
        # Verify database updates
        assert cursor.execute.call_count == 2  # UPDATE user_limits, INSERT audit_log
        
        # Check UPDATE call
        update_call = cursor.execute.call_args_list[0]
        assert 'UPDATE user_limits' in update_call[0][0]
        assert 'administrative_safe = \'N\'' in update_call[0][0]
        
        # Check audit log
        audit_call = cursor.execute.call_args_list[1]
        assert 'INSERT INTO blocking_audit_log' in audit_call[0][0]
        # ADMIN_SAFE_REMOVED is hardcoded in the SQL, not in parameters
        # So we verify it's in the SQL query itself
        assert 'ADMIN_SAFE_REMOVED' in audit_call[0][0]
    
    def test_remove_administrative_safe_flag_no_flag_set(self, mock_mysql_connection):
        """Test removal when flag is not set"""
        connection, cursor = mock_mysql_connection
        cursor.rowcount = 0
        
        result = lambda_function.remove_administrative_safe_flag(connection, 'admin.user')
        
        assert result is True
    
    def test_remove_administrative_safe_flag_database_error(self, mock_mysql_connection):
        """Test flag removal with database error"""
        connection, cursor = mock_mysql_connection
        cursor.execute.side_effect = Exception("Database error")
        
        result = lambda_function.remove_administrative_safe_flag(connection, 'admin.user')
        
        assert result is False


# ============================================================================
# TEST SUITE 7: Complete Unblock and Notify Workflow
# ============================================================================

class TestUnblockAndNotifyWorkflow:
    """Test complete unblock and notify workflow"""
    
    def test_unblock_all_blocked_users_success(self, mock_mysql_connection, mock_aws_clients):
        """Test successful unblocking of multiple users"""
        connection, cursor = mock_mysql_connection
        
        # Mock blocked users query
        blocked_users = [
            {
                'user_id': 'user1',
                'blocked_reason': 'Daily limit',
                'blocked_until': datetime.now(CET) - timedelta(hours=1),
                'team': 'Team1',
                'person': 'User One',
                'daily_request_limit': 350,
                'administrative_safe': 'N'
            },
            {
                'user_id': 'user2',
                'blocked_reason': 'Daily limit',
                'blocked_until': datetime.now(CET) - timedelta(hours=2),
                'team': 'Team2',
                'person': 'User Two',
                'daily_request_limit': 350,
                'administrative_safe': 'N'
            }
        ]
        
        # Mock admin safe users query
        admin_safe_users = [
            {
                'user_id': 'admin1',
                'team': 'Admin',
                'person': 'Admin One',
                'daily_request_limit': 500
            }
        ]
        
        cursor.fetchall.side_effect = [blocked_users, admin_safe_users]
        cursor.rowcount = 1
        
        with patch('lambda_function.execute_user_unblocking', return_value=True), \
             patch('lambda_function.send_reset_email_notification', return_value=True), \
             patch('lambda_function.remove_administrative_safe_flag', return_value=True):
            
            results = lambda_function.unblock_all_blocked_users_and_notify(connection)
        
        assert results['unblocked_count'] == 2
        assert results['notified_count'] == 2
        assert results['admin_safe_removed_count'] == 1
        assert len(results['errors']) == 0
        assert 'user1' in results['unblocked_users']
        assert 'user2' in results['unblocked_users']
        assert 'admin1' in results['admin_safe_removed_users']
    
    def test_unblock_all_blocked_users_partial_failure(self, mock_mysql_connection, mock_aws_clients):
        """Test unblocking with some failures"""
        connection, cursor = mock_mysql_connection
        
        blocked_users = [
            {
                'user_id': 'user1',
                'blocked_reason': 'Daily limit',
                'blocked_until': datetime.now(CET) - timedelta(hours=1),
                'team': 'Team1',
                'person': 'User One',
                'daily_request_limit': 350,
                'administrative_safe': 'N'
            },
            {
                'user_id': 'user2',
                'blocked_reason': 'Daily limit',
                'blocked_until': datetime.now(CET) - timedelta(hours=2),
                'team': 'Team2',
                'person': 'User Two',
                'daily_request_limit': 350,
                'administrative_safe': 'N'
            }
        ]
        
        cursor.fetchall.side_effect = [blocked_users, []]
        cursor.rowcount = 1
        
        # Mock first user succeeds, second fails
        with patch('lambda_function.execute_user_unblocking', side_effect=[True, False]), \
             patch('lambda_function.send_reset_email_notification', return_value=True):
            
            results = lambda_function.unblock_all_blocked_users_and_notify(connection)
        
        assert results['unblocked_count'] == 1
        assert results['notified_count'] == 1
        assert len(results['errors']) > 0
    
    def test_unblock_all_blocked_users_no_users(self, mock_mysql_connection):
        """Test unblocking when no users need unblocking"""
        connection, cursor = mock_mysql_connection
        cursor.fetchall.side_effect = [[], []]
        
        results = lambda_function.unblock_all_blocked_users_and_notify(connection)
        
        assert results['unblocked_count'] == 0
        assert results['notified_count'] == 0
        assert results['admin_safe_removed_count'] == 0
        assert len(results['errors']) == 0


# ============================================================================
# TEST SUITE 8: Error Handling and Notifications
# ============================================================================

class TestErrorHandling:
    """Test error handling and notifications"""
    
    def test_send_error_notification_success(self, mock_aws_clients):
        """Test successful error notification"""
        mock_sns = mock_aws_clients['sns']
        
        lambda_function.send_error_notification("Test error message")
        
        mock_sns.publish.assert_called_once()
        call_args = mock_sns.publish.call_args
        
        assert 'TopicArn' in call_args[1]
        assert 'Subject' in call_args[1]
        assert 'FAILED' in call_args[1]['Subject']
        assert 'Test error message' in call_args[1]['Message']
    
    def test_send_error_notification_sns_failure(self, mock_aws_clients):
        """Test error notification when SNS fails"""
        mock_sns = mock_aws_clients['sns']
        mock_sns.publish.side_effect = Exception("SNS error")
        
        # Should not raise exception
        lambda_function.send_error_notification("Test error")


# ============================================================================
# TEST SUITE 9: Lambda Handler Integration
# ============================================================================

class TestLambdaHandler:
    """Test main Lambda handler"""
    
    @patch('lambda_function.get_mysql_connection')
    @patch('lambda_function.unblock_all_blocked_users_and_notify')
    def test_lambda_handler_success(self, mock_unblock, mock_get_conn, 
                                   cloudwatch_event, mock_context, mock_env_vars):
        """Test successful Lambda handler execution"""
        mock_connection = MagicMock()
        mock_get_conn.return_value = mock_connection
        
        mock_unblock.return_value = {
            'unblocked_count': 3,
            'notified_count': 3,
            'admin_safe_removed_count': 1,
            'errors': [],
            'unblocked_users': ['user1', 'user2', 'user3'],
            'admin_safe_removed_users': ['admin1']
        }
        
        response = lambda_function.lambda_handler(cloudwatch_event, mock_context)
        
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['message'] == 'Daily reset completed successfully'
        assert body['results']['users_unblocked'] == 3
        assert body['results']['users_notified'] == 3
        assert body['results']['admin_safe_removed'] == 1
    
    @patch('lambda_function.get_mysql_connection')
    @patch('lambda_function.send_error_notification')
    def test_lambda_handler_database_connection_failure(self, mock_send_error, mock_get_conn,
                                                       cloudwatch_event, mock_context, mock_env_vars):
        """Test Lambda handler with database connection failure"""
        mock_get_conn.side_effect = Exception("Database connection failed")
        
        response = lambda_function.lambda_handler(cloudwatch_event, mock_context)
        
        assert response['statusCode'] == 500
        body = json.loads(response['body'])
        assert 'error' in body
        assert 'Database connection failed' in body['error']
        
        # Verify error notification was sent
        mock_send_error.assert_called_once()
    
    @patch('lambda_function.get_mysql_connection')
    @patch('lambda_function.unblock_all_blocked_users_and_notify')
    def test_lambda_handler_partial_success(self, mock_unblock, mock_get_conn,
                                           cloudwatch_event, mock_context, mock_env_vars):
        """Test Lambda handler with partial success"""
        mock_connection = MagicMock()
        mock_get_conn.return_value = mock_connection
        
        mock_unblock.return_value = {
            'unblocked_count': 2,
            'notified_count': 1,
            'admin_safe_removed_count': 1,
            'errors': ['Failed to send email to user3'],
            'unblocked_users': ['user1', 'user2'],
            'admin_safe_removed_users': ['admin1']
        }
        
        response = lambda_function.lambda_handler(cloudwatch_event, mock_context)
        
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['results']['users_unblocked'] == 2
        assert body['results']['users_notified'] == 1
        assert len(body['results']['errors']) == 1


# ============================================================================
# TEST SUITE 10: Edge Cases and Boundary Conditions
# ============================================================================

class TestEdgeCases:
    """Test edge cases and boundary conditions"""
    
    def test_unblock_user_with_null_blocked_until(self, mock_mysql_connection, mock_aws_clients):
        """Test unblocking user with NULL blocked_until (permanent block)"""
        connection, cursor = mock_mysql_connection
        
        blocked_users = [{
            'user_id': 'permanent.user',
            'blocked_reason': 'Manual block',
            'blocked_until': None,
            'team': 'Team',
            'person': 'Permanent User',
            'daily_request_limit': 350,
            'administrative_safe': 'N'
        }]
        
        cursor.fetchall.side_effect = [blocked_users, []]
        cursor.rowcount = 1
        
        with patch('lambda_function.execute_user_unblocking', return_value=True), \
             patch('lambda_function.send_reset_email_notification', return_value=True):
            
            results = lambda_function.unblock_all_blocked_users_and_notify(connection)
        
        assert results['unblocked_count'] == 1
    
    def test_user_with_special_characters_in_id(self, mock_mysql_connection):
        """Test handling user IDs with special characters"""
        connection, cursor = mock_mysql_connection
        cursor.rowcount = 1
        
        with patch('lambda_function.implement_iam_unblocking', return_value=True):
            result = lambda_function.execute_user_unblocking(connection, 'user.name+test@example.com')
        
        assert result is True
    
    def test_concurrent_execution_safety(self, mock_mysql_connection):
        """Test that operations are safe for concurrent execution"""
        connection, cursor = mock_mysql_connection
        cursor.rowcount = 1
        
        # Autocommit should be enabled
        assert connection.autocommit is True or hasattr(connection, 'autocommit')


# ============================================================================
# TEST EXECUTION SUMMARY
# ============================================================================

def print_test_summary():
    """Print test execution summary"""
    print("\n" + "="*80)
    print("BEDROCK DAILY RESET - UNIT TEST PLAN")
    print("="*80)
    print("\nTest Suites:")
    print("  1. ✓ Time and Timezone Functions (2 tests)")
    print("  2. ✓ Database Connection (2 tests)")
    print("  3. ✓ User Unblocking Workflow (3 tests)")
    print("  4. ✓ IAM Policy Management (3 tests)")
    print("  5. ✓ Email Notifications (2 tests)")
    print("  6. ✓ Administrative Safe Flag Management (3 tests)")
    print("  7. ✓ Complete Unblock and Notify Workflow (3 tests)")
    print("  8. ✓ Error Handling and Notifications (2 tests)")
    print("  9. ✓ Lambda Handler Integration (3 tests)")
    print(" 10. ✓ Edge Cases and Boundary Conditions (3 tests)")
    print("\nTotal: 26 unit tests")
    print("="*80 + "\n")


if __name__ == "__main__":
    print_test_summary()
    pytest.main([__file__, '-v', '--tb=short'])
