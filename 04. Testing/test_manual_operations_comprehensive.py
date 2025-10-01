#!/usr/bin/env python3
"""
Comprehensive Unit Tests for Manual Operations - Grupo 8
bedrock-realtime-usage-controller Lambda Function

This test suite covers all manual operations performed by administrators:
- Manual blocking with different durations
- Manual unblocking with administrative protection
- User status checking
- Edge cases and error handling

Author: AWS Bedrock Usage Control System
Version: 1.0.0
"""

import pytest
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock, call
import pytz
import sys
import os

# Mock environment variables BEFORE importing lambda_function
os.environ['RDS_ENDPOINT'] = 'test-db.amazonaws.com'
os.environ['RDS_USERNAME'] = 'test_user'
os.environ['RDS_PASSWORD'] = 'test_password'
os.environ['RDS_DATABASE'] = 'test_database'
os.environ['SNS_TOPIC_ARN'] = 'arn:aws:sns:eu-west-1:123456789012:test-topic'
os.environ['EMAIL_SERVICE_LAMBDA_NAME'] = 'test-email-service'
os.environ['EMAIL_NOTIFICATIONS_ENABLED'] = 'true'

# Add the Lambda function directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '02. Source', 'Lambda Functions', 'bedrock-realtime-usage-controller-aws-20250923'))

# Import the Lambda function
import lambda_function

# CET timezone
CET = pytz.timezone('Europe/Madrid')


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def mock_mysql_connection():
    """Mock MySQL connection with cursor"""
    connection = MagicMock()
    cursor = MagicMock()
    cursor.__enter__ = Mock(return_value=cursor)
    cursor.__exit__ = Mock(return_value=False)
    connection.cursor.return_value = cursor
    return connection, cursor


@pytest.fixture
def mock_iam_client():
    """Mock IAM client"""
    with patch('lambda_function.iam') as mock_iam:
        yield mock_iam


@pytest.fixture
def mock_lambda_client():
    """Mock Lambda client for email service"""
    with patch('lambda_function.lambda_client') as mock_lambda:
        yield mock_lambda


@pytest.fixture
def sample_usage_info():
    """Sample usage information"""
    return {
        'daily_requests_used': 250,
        'monthly_requests_used': 3500,
        'daily_percent': 71.4,
        'monthly_percent': 70.0,
        'daily_limit': 350,
        'monthly_limit': 5000,
        'administrative_safe': False
    }


@pytest.fixture
def mock_current_time():
    """Mock current CET time"""
    current_time = datetime(2025, 1, 10, 14, 30, 0, tzinfo=CET)
    with patch('lambda_function.get_current_cet_time', return_value=current_time):
        with patch('lambda_function.get_cet_timestamp_string', return_value='2025-01-10 14:30:00'):
            yield current_time


# ============================================================================
# TEST CLASS: MANUAL BLOCKING OPERATIONS
# ============================================================================

class TestManualBlockingOperations:
    """Tests for manual blocking operations by administrators"""
    
    def test_manual_block_user_success_1day(self, mock_mysql_connection, mock_iam_client, 
                                            mock_lambda_client, sample_usage_info, mock_current_time):
        """Test successful manual blocking with 1-day duration"""
        connection, cursor = mock_mysql_connection
        
        # Mock get_mysql_connection
        with patch('lambda_function.get_mysql_connection', return_value=connection):
            # Mock get_user_current_usage
            with patch('lambda_function.get_user_current_usage', return_value=sample_usage_info):
                # Mock execute_admin_blocking
                with patch('lambda_function.execute_admin_blocking', return_value=True) as mock_blocking:
                    
                    event = {
                        'action': 'block',
                        'user_id': 'test_user',
                        'reason': 'Manual admin block for testing',
                        'performed_by': 'admin_user',
                        'duration': '1day'
                    }
                    
                    result = lambda_function.manual_block_user(event)
                    
                    # Verify response
                    assert result['statusCode'] == 200
                    body = json.loads(result['body'])
                    assert body['message'] == 'User test_user blocked successfully'
                    assert body['action'] == 'block'
                    assert body['user_id'] == 'test_user'
                    assert body['performed_by'] == 'admin_user'
                    assert 'blocked_at' in body
                    
                    # Verify execute_admin_blocking was called correctly
                    mock_blocking.assert_called_once()
                    call_args = mock_blocking.call_args
                    assert call_args[0][1] == 'test_user'
                    assert call_args[0][2] == 'Manual admin block for testing'
                    assert call_args[0][3] == 'admin_user'
                    assert call_args[0][4] == sample_usage_info
                    assert call_args[0][5] == '1day'
    
    def test_manual_block_user_success_30days(self, mock_mysql_connection, mock_iam_client, 
                                               mock_lambda_client, sample_usage_info, mock_current_time):
        """Test successful manual blocking with 30-day duration"""
        connection, cursor = mock_mysql_connection
        
        with patch('lambda_function.get_mysql_connection', return_value=connection):
            with patch('lambda_function.get_user_current_usage', return_value=sample_usage_info):
                with patch('lambda_function.execute_admin_blocking', return_value=True) as mock_blocking:
                    
                    event = {
                        'action': 'block',
                        'user_id': 'test_user',
                        'reason': 'Extended block period',
                        'performed_by': 'admin_user',
                        'duration': '30days'
                    }
                    
                    result = lambda_function.manual_block_user(event)
                    
                    assert result['statusCode'] == 200
                    body = json.loads(result['body'])
                    assert 'blocked successfully' in body['message']
                    
                    # Verify duration parameter
                    call_args = mock_blocking.call_args
                    assert call_args[0][5] == '30days'
    
    def test_manual_block_user_success_90days(self, mock_mysql_connection, mock_iam_client, 
                                               mock_lambda_client, sample_usage_info, mock_current_time):
        """Test successful manual blocking with 90-day duration"""
        connection, cursor = mock_mysql_connection
        
        with patch('lambda_function.get_mysql_connection', return_value=connection):
            with patch('lambda_function.get_user_current_usage', return_value=sample_usage_info):
                with patch('lambda_function.execute_admin_blocking', return_value=True) as mock_blocking:
                    
                    event = {
                        'action': 'block',
                        'user_id': 'test_user',
                        'reason': 'Long-term suspension',
                        'performed_by': 'admin_user',
                        'duration': '90days'
                    }
                    
                    result = lambda_function.manual_block_user(event)
                    
                    assert result['statusCode'] == 200
                    call_args = mock_blocking.call_args
                    assert call_args[0][5] == '90days'
    
    def test_manual_block_user_success_indefinite(self, mock_mysql_connection, mock_iam_client, 
                                                   mock_lambda_client, sample_usage_info, mock_current_time):
        """Test successful manual blocking with indefinite duration"""
        connection, cursor = mock_mysql_connection
        
        with patch('lambda_function.get_mysql_connection', return_value=connection):
            with patch('lambda_function.get_user_current_usage', return_value=sample_usage_info):
                with patch('lambda_function.execute_admin_blocking', return_value=True) as mock_blocking:
                    
                    event = {
                        'action': 'block',
                        'user_id': 'test_user',
                        'reason': 'Permanent suspension',
                        'performed_by': 'admin_user',
                        'duration': 'indefinite'
                    }
                    
                    result = lambda_function.manual_block_user(event)
                    
                    assert result['statusCode'] == 200
                    call_args = mock_blocking.call_args
                    assert call_args[0][5] == 'indefinite'
    
    def test_manual_block_user_success_custom_duration(self, mock_mysql_connection, mock_iam_client, 
                                                        mock_lambda_client, sample_usage_info, mock_current_time):
        """Test successful manual blocking with custom expiration date"""
        connection, cursor = mock_mysql_connection
        
        with patch('lambda_function.get_mysql_connection', return_value=connection):
            with patch('lambda_function.get_user_current_usage', return_value=sample_usage_info):
                with patch('lambda_function.execute_admin_blocking', return_value=True) as mock_blocking:
                    
                    custom_date = '2025-02-15T10:00:00Z'
                    event = {
                        'action': 'block',
                        'user_id': 'test_user',
                        'reason': 'Custom duration block',
                        'performed_by': 'admin_user',
                        'duration': 'custom',
                        'expires_at': custom_date
                    }
                    
                    result = lambda_function.manual_block_user(event)
                    
                    assert result['statusCode'] == 200
                    call_args = mock_blocking.call_args
                    assert call_args[0][5] == 'custom'
                    assert call_args[0][6] == custom_date
    
    def test_manual_block_user_failure(self, mock_mysql_connection, mock_iam_client, 
                                       mock_lambda_client, sample_usage_info, mock_current_time):
        """Test manual blocking failure"""
        connection, cursor = mock_mysql_connection
        
        with patch('lambda_function.get_mysql_connection', return_value=connection):
            with patch('lambda_function.get_user_current_usage', return_value=sample_usage_info):
                with patch('lambda_function.execute_admin_blocking', return_value=False):
                    
                    event = {
                        'action': 'block',
                        'user_id': 'test_user',
                        'reason': 'Test block',
                        'performed_by': 'admin_user',
                        'duration': '1day'
                    }
                    
                    result = lambda_function.manual_block_user(event)
                    
                    assert result['statusCode'] == 500
                    body = json.loads(result['body'])
                    assert 'failed' in body['message'].lower()
    
    def test_manual_block_user_exception(self, mock_mysql_connection, mock_iam_client, 
                                         mock_lambda_client, sample_usage_info, mock_current_time):
        """Test manual blocking with exception"""
        connection, cursor = mock_mysql_connection
        
        with patch('lambda_function.get_mysql_connection', return_value=connection):
            with patch('lambda_function.get_user_current_usage', side_effect=Exception('Database error')):
                
                event = {
                    'action': 'block',
                    'user_id': 'test_user',
                    'reason': 'Test block',
                    'performed_by': 'admin_user',
                    'duration': '1day'
                }
                
                result = lambda_function.manual_block_user(event)
                
                assert result['statusCode'] == 500
                body = json.loads(result['body'])
                assert 'error' in body
                assert 'Database error' in body['error']


# ============================================================================
# TEST CLASS: MANUAL UNBLOCKING OPERATIONS
# ============================================================================

class TestManualUnblockingOperations:
    """Tests for manual unblocking operations by administrators"""
    
    def test_manual_unblock_user_success(self, mock_mysql_connection, mock_iam_client, 
                                         mock_lambda_client, mock_current_time):
        """Test successful manual unblocking"""
        connection, cursor = mock_mysql_connection
        
        with patch('lambda_function.get_mysql_connection', return_value=connection):
            with patch('lambda_function.execute_admin_unblocking', return_value=True) as mock_unblocking:
                
                event = {
                    'action': 'unblock',
                    'user_id': 'test_user',
                    'reason': 'Manual admin unblock',
                    'performed_by': 'admin_user'
                }
                
                result = lambda_function.manual_unblock_user(event)
                
                # Verify response
                assert result['statusCode'] == 200
                body = json.loads(result['body'])
                assert body['message'] == 'User test_user unblocked successfully'
                assert body['action'] == 'unblock'
                assert body['user_id'] == 'test_user'
                assert body['performed_by'] == 'admin_user'
                assert 'unblocked_at' in body
                
                # Verify execute_admin_unblocking was called correctly
                mock_unblocking.assert_called_once_with(
                    connection, 'test_user', 'Manual admin unblock', 'admin_user'
                )
    
    def test_manual_unblock_user_with_custom_reason(self, mock_mysql_connection, mock_iam_client, 
                                                     mock_lambda_client, mock_current_time):
        """Test manual unblocking with custom reason"""
        connection, cursor = mock_mysql_connection
        
        with patch('lambda_function.get_mysql_connection', return_value=connection):
            with patch('lambda_function.execute_admin_unblocking', return_value=True) as mock_unblocking:
                
                event = {
                    'action': 'unblock',
                    'user_id': 'test_user',
                    'reason': 'Issue resolved, restoring access',
                    'performed_by': 'senior_admin'
                }
                
                result = lambda_function.manual_unblock_user(event)
                
                assert result['statusCode'] == 200
                mock_unblocking.assert_called_once_with(
                    connection, 'test_user', 'Issue resolved, restoring access', 'senior_admin'
                )
    
    def test_manual_unblock_user_failure(self, mock_mysql_connection, mock_iam_client, 
                                         mock_lambda_client, mock_current_time):
        """Test manual unblocking failure"""
        connection, cursor = mock_mysql_connection
        
        with patch('lambda_function.get_mysql_connection', return_value=connection):
            with patch('lambda_function.execute_admin_unblocking', return_value=False):
                
                event = {
                    'action': 'unblock',
                    'user_id': 'test_user',
                    'reason': 'Test unblock',
                    'performed_by': 'admin_user'
                }
                
                result = lambda_function.manual_unblock_user(event)
                
                assert result['statusCode'] == 500
                body = json.loads(result['body'])
                assert 'failed' in body['message'].lower()
    
    def test_manual_unblock_user_exception(self, mock_mysql_connection, mock_iam_client, 
                                           mock_lambda_client, mock_current_time):
        """Test manual unblocking with exception"""
        connection, cursor = mock_mysql_connection
        
        with patch('lambda_function.get_mysql_connection', side_effect=Exception('Connection failed')):
            
            event = {
                'action': 'unblock',
                'user_id': 'test_user',
                'reason': 'Test unblock',
                'performed_by': 'admin_user'
            }
            
            result = lambda_function.manual_unblock_user(event)
            
            assert result['statusCode'] == 500
            body = json.loads(result['body'])
            assert 'error' in body
            assert 'Connection failed' in body['error']


# ============================================================================
# TEST CLASS: USER STATUS CHECKING
# ============================================================================

class TestUserStatusChecking:
    """Tests for checking user blocking status"""
    
    def test_check_user_status_blocked_automatic(self, mock_mysql_connection, mock_current_time):
        """Test checking status of automatically blocked user"""
        connection, cursor = mock_mysql_connection
        
        # Mock database responses
        blocked_until = datetime(2025, 1, 11, 0, 0, 0, tzinfo=CET)  # Midnight = automatic
        cursor.fetchone.side_effect = [
            {
                'is_blocked': 'Y',
                'blocked_reason': 'Daily limit exceeded',
                'blocked_at': datetime(2025, 1, 10, 14, 30, 0, tzinfo=CET),
                'blocked_until': blocked_until
            },
            {
                'daily_request_limit': 350,
                'administrative_safe': 'N'
            }
        ]
        
        with patch('lambda_function.get_mysql_connection', return_value=connection):
            
            event = {
                'action': 'check_status',
                'user_id': 'test_user'
            }
            
            result = lambda_function.check_user_status(event)
            
            assert result['statusCode'] == 200
            body = json.loads(result['body'])
            assert body['user_id'] == 'test_user'
            assert body['is_blocked'] is True
            assert body['block_reason'] == 'Daily limit exceeded'
            assert body['block_type'] == 'AUTO'
            assert body['performed_by'] == 'system'
            assert body['administrative_safe'] is False
            assert 'blocked_since' in body
            assert 'expires_at' in body
    
    def test_check_user_status_blocked_manual(self, mock_mysql_connection, mock_current_time):
        """Test checking status of manually blocked user"""
        connection, cursor = mock_mysql_connection
        
        # Mock database responses - manual block expires at non-midnight time
        blocked_until = datetime(2025, 1, 15, 10, 0, 0, tzinfo=CET)
        cursor.fetchone.side_effect = [
            {
                'is_blocked': 'Y',
                'blocked_reason': 'Manual admin block',
                'blocked_at': datetime(2025, 1, 10, 14, 30, 0, tzinfo=CET),
                'blocked_until': blocked_until
            },
            {
                'daily_request_limit': 350,
                'administrative_safe': 'Y'
            }
        ]
        
        with patch('lambda_function.get_mysql_connection', return_value=connection):
            
            event = {
                'action': 'check_status',
                'user_id': 'test_user'
            }
            
            result = lambda_function.check_user_status(event)
            
            assert result['statusCode'] == 200
            body = json.loads(result['body'])
            assert body['is_blocked'] is True
            assert body['block_type'] == 'Manual'
            assert body['performed_by'] == 'dashboard_admin'
            assert body['administrative_safe'] is True
    
    def test_check_user_status_blocked_indefinite(self, mock_mysql_connection, mock_current_time):
        """Test checking status of indefinitely blocked user"""
        connection, cursor = mock_mysql_connection
        
        cursor.fetchone.side_effect = [
            {
                'is_blocked': 'Y',
                'blocked_reason': 'Permanent suspension',
                'blocked_at': datetime(2025, 1, 10, 14, 30, 0, tzinfo=CET),
                'blocked_until': None  # No expiration
            },
            {
                'daily_request_limit': 350,
                'administrative_safe': 'Y'
            }
        ]
        
        with patch('lambda_function.get_mysql_connection', return_value=connection):
            
            event = {
                'action': 'check_status',
                'user_id': 'test_user'
            }
            
            result = lambda_function.check_user_status(event)
            
            assert result['statusCode'] == 200
            body = json.loads(result['body'])
            assert body['is_blocked'] is True
            assert body['block_type'] == 'Manual'
            assert body['expires_at'] is None
    
    def test_check_user_status_not_blocked(self, mock_mysql_connection, mock_current_time):
        """Test checking status of non-blocked user"""
        connection, cursor = mock_mysql_connection
        
        cursor.fetchone.side_effect = [
            {
                'is_blocked': 'N',
                'blocked_reason': None,
                'blocked_at': None,
                'blocked_until': None
            },
            {
                'daily_request_limit': 350,
                'administrative_safe': 'N'
            }
        ]
        
        with patch('lambda_function.get_mysql_connection', return_value=connection):
            
            event = {
                'action': 'check_status',
                'user_id': 'test_user'
            }
            
            result = lambda_function.check_user_status(event)
            
            assert result['statusCode'] == 200
            body = json.loads(result['body'])
            assert body['is_blocked'] is False
            assert body['block_reason'] is None
            assert body['block_type'] == 'None'
            assert body['performed_by'] is None
    
    def test_check_user_status_no_record(self, mock_mysql_connection, mock_current_time):
        """Test checking status when user has no blocking record"""
        connection, cursor = mock_mysql_connection
        
        cursor.fetchone.side_effect = [
            None,  # No blocking status record
            {
                'daily_request_limit': 350,
                'administrative_safe': 'N'
            }
        ]
        
        with patch('lambda_function.get_mysql_connection', return_value=connection):
            
            event = {
                'action': 'check_status',
                'user_id': 'test_user'
            }
            
            result = lambda_function.check_user_status(event)
            
            assert result['statusCode'] == 200
            body = json.loads(result['body'])
            assert body['is_blocked'] is False
            assert body['block_type'] == 'None'
    
    def test_check_user_status_exception(self, mock_mysql_connection, mock_current_time):
        """Test checking status with database exception"""
        connection, cursor = mock_mysql_connection
        
        cursor.execute.side_effect = Exception('Database query failed')
        
        with patch('lambda_function.get_mysql_connection', return_value=connection):
            
            event = {
                'action': 'check_status',
                'user_id': 'test_user'
            }
            
            result = lambda_function.check_user_status(event)
            
            assert result['statusCode'] == 500
            body = json.loads(result['body'])
            assert 'error' in body
            assert 'Database query failed' in body['error']


# ============================================================================
# TEST CLASS: EXECUTE ADMIN BLOCKING
# ============================================================================

class TestExecuteAdminBlocking:
    """Tests for execute_admin_blocking function"""
    
    def test_execute_admin_blocking_1day_duration(self, mock_mysql_connection, mock_iam_client, 
                                                   mock_lambda_client, sample_usage_info, mock_current_time):
        """Test admin blocking with 1-day duration"""
        connection, cursor = mock_mysql_connection
        
        with patch('lambda_function.implement_iam_blocking', return_value=True):
            with patch('lambda_function.send_enhanced_blocking_email', return_value=True):
                
                result = lambda_function.execute_admin_blocking(
                    connection, 'test_user', 'Test reason', 'admin_user', 
                    sample_usage_info, duration='1day'
                )
                
                assert result is True
                
                # Verify database calls
                assert cursor.execute.call_count >= 2  # Status update + audit log
                
                # Verify the blocked_until calculation (should be +1 day)
                insert_call = cursor.execute.call_args_list[0]
                blocked_until_value = insert_call[0][1][3]  # 4th parameter
                assert blocked_until_value is not None
    
    def test_execute_admin_blocking_30days_duration(self, mock_mysql_connection, mock_iam_client, 
                                                     mock_lambda_client, sample_usage_info, mock_current_time):
        """Test admin blocking with 30-day duration"""
        connection, cursor = mock_mysql_connection
        
        with patch('lambda_function.implement_iam_blocking', return_value=True):
            with patch('lambda_function.send_enhanced_blocking_email', return_value=True):
                
                result = lambda_function.execute_admin_blocking(
                    connection, 'test_user', 'Extended block', 'admin_user', 
                    sample_usage_info, duration='30days'
                )
                
                assert result is True
    
    def test_execute_admin_blocking_indefinite(self, mock_mysql_connection, mock_iam_client, 
                                                mock_lambda_client, sample_usage_info, mock_current_time):
        """Test admin blocking with indefinite duration"""
        connection, cursor = mock_mysql_connection
        
        with patch('lambda_function.implement_iam_blocking', return_value=True):
            with patch('lambda_function.send_enhanced_blocking_email', return_value=True):
                
                result = lambda_function.execute_admin_blocking(
                    connection, 'test_user', 'Permanent block', 'admin_user', 
                    sample_usage_info, duration='indefinite'
                )
                
                assert result is True
                
                # Verify blocked_until is None for indefinite
                insert_call = cursor.execute.call_args_list[0]
                blocked_until_value = insert_call[0][1][3]
                assert blocked_until_value is None
    
    def test_execute_admin_blocking_custom_expiration(self, mock_mysql_connection, mock_iam_client, 
                                                       mock_lambda_client, sample_usage_info, mock_current_time):
        """Test admin blocking with custom expiration date"""
        connection, cursor = mock_mysql_connection
        
        with patch('lambda_function.implement_iam_blocking', return_value=True):
            with patch('lambda_function.send_enhanced_blocking_email', return_value=True):
                
                custom_date = '2025-02-15T10:00:00Z'
                result = lambda_function.execute_admin_blocking(
                    connection, 'test_user', 'Custom block', 'admin_user', 
                    sample_usage_info, duration='custom', expires_at=custom_date
                )
                
                assert result is True
    
    def test_execute_admin_blocking_database_failure(self, mock_mysql_connection, mock_iam_client, 
                                                      mock_lambda_client, sample_usage_info, mock_current_time):
        """Test admin blocking with database failure"""
        connection, cursor = mock_mysql_connection
        cursor.execute.side_effect = Exception('Database error')
        
        result = lambda_function.execute_admin_blocking(
            connection, 'test_user', 'Test reason', 'admin_user', 
            sample_usage_info, duration='1day'
        )
        
        assert result is False


# ============================================================================
# TEST CLASS: EXECUTE ADMIN UNBLOCKING
# ============================================================================

class TestExecuteAdminUnblocking:
    """Tests for execute_admin_unblocking function"""
    
    def test_execute_admin_unblocking_success(self, mock_mysql_connection, mock_iam_client, 
                                               mock_lambda_client, mock_current_time):
        """Test successful admin unblocking"""
        connection, cursor = mock_mysql_connection
        cursor.rowcount = 1  # Simulate successful update
        
        # Mock user_limits check
        cursor.fetchone.return_value = {'user_id': 'test_user'}
        
        with patch('lambda_function.implement_iam_unblocking', return_value=True):
            with patch('lambda_function.send_enhanced_unblocking_email', return_value=True):
                
                result = lambda_function.execute_admin_unblocking(
                    connection, 'test_user', 'Test unblock', 'admin_user'
                )
                
                assert result is True
                
                # Verify database calls (status update + protection + audit)
                assert cursor.execute.call_count >= 3
    
    def test_execute_admin_unblocking_sets_admin_protection(self, mock_mysql_connection, mock_iam_client, 
                                                             mock_lambda_client, mock_current_time):
        """Test that admin unblocking sets administrative_safe flag"""
        connection, cursor = mock_mysql_connection
        cursor.rowcount = 1
        cursor.fetchone.return_value = {'user_id': 'test_user'}
        
        with patch('lambda_function.implement_iam_unblocking', return_value=True):
            with patch('lambda_function.send_enhanced_unblocking_email', return_value=True):
                
                result = lambda_function.execute_admin_unblocking(
                    connection, 'test_user', 'Test unblock', 'admin_user'
                )
                
                assert result is True
                
                # Find the UPDATE user_limits call
                update_calls = [call for call in cursor.execute.call_args_list 
                               if 'UPDATE user_limits' in str(call)]
                assert len(update_calls) > 0
                
                # Verify administrative_safe is set to 'Y'
                update_call = update_calls[0]
                assert 'administrative_safe' in str(update_call)
                assert "'Y'" in str(update_call)
    
    def test_execute_admin_unblocking_creates_user_limits_if_missing(self, mock_mysql_connection, 
                                                                      mock_iam_client, mock_lambda_client, 
                                                                      mock_current_time):
        """Test that admin unblocking creates user_limits entry if missing"""
        connection, cursor = mock_mysql_connection
        cursor.rowcount = 1
        cursor.fetchone.return_value = None  # No existing user_limits record
        
        with patch('lambda_function.implement_iam_unblocking', return_value=True):
            with patch('lambda_function.send_enhanced_unblocking_email', return_value=True):
                
                result = lambda_function.execute_admin_unblocking(
                    connection, 'test_user', 'Test unblock', 'admin_user'
                )
                
                assert result is True
                
                # Find the INSERT user_limits call
                insert_calls = [call for call in cursor.execute.call_args_list 
                               if 'INSERT INTO user_limits' in str(call)]
                assert len(insert_calls) > 0
    
    def test_execute_admin_unblocking_database_failure(self, mock_mysql_connection, mock_iam_client, 
                                                        mock_lambda_client, mock_current_time):
        """Test admin unblocking with database failure"""
        connection, cursor = mock_mysql_connection
        cursor.execute.side_effect = Exception('Database error')
        
        result = lambda_function.execute_admin_unblocking(
            connection, 'test_user', 'Test unblock', 'admin_user'
        )
        
        assert result is False
    
    def test_execute_admin_unblocking_iam_failure(self, mock_mysql_connection, mock_iam_client, 
                                                   mock_lambda_client, mock_current_time):
        """Test admin unblocking with IAM failure (should still succeed)"""
        connection, cursor = mock_mysql_connection
        cursor.rowcount = 1
        cursor.fetchone.return_value = {'user_id': 'test_user'}
        
        with patch('lambda_function.implement_iam_unblocking', return_value=False):
            with patch('lambda_function.send_enhanced_unblocking_email', return_value=True):
                
                result = lambda_function.execute_admin_unblocking(
                    connection, 'test_user', 'Test unblock', 'admin_user'
                )
                
                # Should still succeed even if IAM fails (non-critical)
                assert result is True


# ============================================================================
# TEST CLASS: GET USER CURRENT USAGE
# ============================================================================

class TestGetUserCurrentUsage:
    """Tests for get_user_current_usage function"""
    
    def test_get_user_current_usage_success(self, mock_mysql_connection, mock_current_time):
        """Test successful retrieval of user current usage"""
        connection, cursor = mock_mysql_connection
        
        # Mock database responses
        cursor.fetchone.side_effect = [
            {
                'daily_request_limit': 350,
                'monthly_request_limit': 5000,
                'administrative_safe': 'N'
            },
            {'daily_requests_used': 250},
            {'monthly_requests_used': 3500}
        ]
        
        result = lambda_function.get_user_current_usage(connection, 'test_user')
        
        assert result['daily_requests_used'] == 250
        assert result['monthly_requests_used'] == 3500
        assert result['daily_limit'] == 350
        assert result['monthly_limit'] == 5000
        assert result['daily_percent'] == pytest.approx(71.4, rel=0.1)
        assert result['monthly_percent'] == pytest.approx(70.0, rel=0.1)
        assert result['administrative_safe'] is False
    
    def test_get_user_current_usage_no_limits_record(self, mock_mysql_connection, mock_current_time):
        """Test usage retrieval when user has no limits record"""
        connection, cursor = mock_mysql_connection
        
        # Mock database responses
        cursor.fetchone.side_effect = [
            None,  # No limits record
            {'daily_requests_used': 100},
            {'monthly_requests_used': 1500}
        ]
        
        result = lambda_function.get_user_current_usage(connection, 'test_user')
        
        # Should use default limits
        assert result['daily_limit'] == 350
        assert result['monthly_limit'] == 5000
        assert result['administrative_safe'] is False
    
    def test_get_user_current_usage_with_admin_protection(self, mock_mysql_connection, mock_current_time):
        """Test usage retrieval for user with administrative protection"""
        connection, cursor = mock_mysql_connection
        
        cursor.fetchone.side_effect = [
            {
                'daily_request_limit': 350,
                'monthly_request_limit': 5000,
                'administrative_safe': 'Y'
            },
            {'daily_requests_used': 250},
            {'monthly_requests_used': 3500}
        ]
        
        result = lambda_function.get_user_current_usage(connection, 'test_user')
        
        assert result['administrative_safe'] is True
    
    def test_get_user_current_usage_exception(self, mock_mysql_connection, mock_current_time):
        """Test usage retrieval with database exception"""
        connection, cursor = mock_mysql_connection
        cursor.execute.side_effect = Exception('Database error')
        
        result = lambda_function.get_user_current_usage(connection, 'test_user')
        
        # Should return default values on error
        assert result['daily_requests_used'] == 0
        assert result['monthly_requests_used'] == 0
        assert result['daily_limit'] == 350
        assert result['monthly_limit'] == 5000


# ============================================================================
# MAIN EXECUTION
# ============================================================================

if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
