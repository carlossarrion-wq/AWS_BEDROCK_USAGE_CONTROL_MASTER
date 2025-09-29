"""
Pytest configuration and fixtures for AWS Bedrock Usage Control System

This module provides shared fixtures and configuration for all test modules.
It includes database setup, AWS service mocking, and common test utilities.
"""

import pytest
import os
import json
import boto3
import pymysql
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone, timedelta
import pytz
from moto import mock_aws
import tempfile
import shutil

# Test environment variables
TEST_ENV_VARS = {
    'RDS_ENDPOINT': 'test-rds-endpoint.amazonaws.com',
    'RDS_USERNAME': 'test_user',
    'RDS_PASSWORD': 'test_password',
    'RDS_DATABASE': 'test_bedrock_usage',
    'AWS_REGION': 'eu-west-1',
    'ACCOUNT_ID': '123456789012',
    'SNS_TOPIC_ARN': 'arn:aws:sns:eu-west-1:123456789012:test-topic',
    'EMAIL_SERVICE_LAMBDA_NAME': 'test-bedrock-email-service',
    'EMAIL_NOTIFICATIONS_ENABLED': 'true',
    'AWS_ACCESS_KEY_ID': 'testing',
    'AWS_SECRET_ACCESS_KEY': 'testing',
    'AWS_SECURITY_TOKEN': 'testing',
    'AWS_SESSION_TOKEN': 'testing'
}

@pytest.fixture(scope='session', autouse=True)
def setup_test_environment():
    """Set up test environment variables for all tests"""
    original_env = os.environ.copy()
    os.environ.update(TEST_ENV_VARS)
    yield
    os.environ.clear()
    os.environ.update(original_env)

@pytest.fixture
def mock_database_connection():
    """Mock database connection and cursor"""
    connection_mock = Mock()
    cursor_mock = Mock()
    cursor_context_mock = Mock()
    cursor_context_mock.__enter__ = Mock(return_value=cursor_mock)
    cursor_context_mock.__exit__ = Mock(return_value=None)
    connection_mock.cursor.return_value = cursor_context_mock
    connection_mock.ping = Mock()
    connection_mock.commit = Mock()
    connection_mock.rollback = Mock()
    connection_mock.close = Mock()
    
    return {
        'connection': connection_mock,
        'cursor': cursor_mock,
        'cursor_context': cursor_context_mock
    }

@pytest.fixture
def sample_user_data():
    """Sample user data for testing"""
    return {
        'user_id': 'test-user',
        'team': 'yo_leo_engineering',
        'person': 'John Doe',
        'email': 'test@example.com',
        'daily_limit': 350,
        'monthly_limit': 5000,
        'administrative_safe': False
    }

@pytest.fixture
def sample_usage_data():
    """Sample usage data for testing"""
    return {
        'daily_requests_used': 300,
        'monthly_requests_used': 2500,
        'daily_percent': 85.7,
        'monthly_percent': 50.0,
        'daily_limit': 350,
        'monthly_limit': 5000,
        'administrative_safe': False
    }

@pytest.fixture
def sample_cloudtrail_event():
    """Sample CloudTrail event for testing"""
    return {
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

@pytest.fixture
def sample_api_event():
    """Sample API event for testing"""
    return {
        'action': 'block',
        'user_id': 'test-user',
        'reason': 'Manual admin block',
        'performed_by': 'admin-user'
    }

@pytest.fixture
def mock_aws_services():
    """Mock AWS services (IAM, SNS, Lambda)"""
    with mock_aws():
        # Create mock clients
        iam_client = boto3.client('iam', region_name='eu-west-1')
        sns_client = boto3.client('sns', region_name='eu-west-1')
        lambda_client = boto3.client('lambda', region_name='eu-west-1')
        
        # Create test SNS topic
        topic_response = sns_client.create_topic(Name='test-topic')
        
        # Create test Lambda function
        lambda_client.create_function(
            FunctionName='test-bedrock-email-service',
            Runtime='python3.9',
            Role='arn:aws:iam::123456789012:role/test-role',
            Handler='lambda_function.lambda_handler',
            Code={'ZipFile': b'fake code'},
            Description='Test email service function'
        )
        
        yield {
            'iam': iam_client,
            'sns': sns_client,
            'lambda': lambda_client,
            'topic_arn': topic_response['TopicArn']
        }

@pytest.fixture
def test_iam_user(mock_aws_services):
    """Create a test IAM user with tags"""
    iam_client = mock_aws_services['iam']
    
    # Create user
    iam_client.create_user(UserName='test-user')
    
    # Add tags
    iam_client.tag_user(
        UserName='test-user',
        Tags=[
            {'Key': 'Team', 'Value': 'yo_leo_engineering'},
            {'Key': 'Email', 'Value': 'test@example.com'},
            {'Key': 'Person', 'Value': 'John Doe'}
        ]
    )
    
    return 'test-user'

@pytest.fixture
def test_iam_policy():
    """Sample IAM policy for testing"""
    return {
        'Version': '2012-10-17',
        'Statement': [
            {
                'Sid': 'BedrockAccess',
                'Effect': 'Allow',
                'Action': [
                    'bedrock:InvokeModel',
                    'bedrock:InvokeModelWithResponseStream'
                ],
                'Resource': '*'
            }
        ]
    }

@pytest.fixture
def test_database_schema():
    """Test database schema setup"""
    return {
        'user_limits': [
            {
                'user_id': 'test-user',
                'team': 'yo_leo_engineering',
                'person': 'John Doe',
                'daily_request_limit': 350,
                'monthly_request_limit': 5000,
                'administrative_safe': 'N'
            }
        ],
        'user_blocking_status': [
            {
                'user_id': 'test-user',
                'is_blocked': 'N',
                'blocked_reason': None,
                'blocked_at': None,
                'blocked_until': None
            }
        ],
        'bedrock_requests': [],
        'blocking_audit_log': []
    }

@pytest.fixture
def cet_timezone():
    """CET timezone for testing"""
    return pytz.timezone('Europe/Madrid')

@pytest.fixture
def test_timestamps(cet_timezone):
    """Test timestamps in various formats"""
    base_time = datetime(2024, 1, 15, 12, 0, 0, tzinfo=cet_timezone)
    return {
        'current_cet': base_time,
        'current_utc': base_time.astimezone(pytz.UTC),
        'expired_time': base_time - timedelta(hours=1),
        'future_time': base_time + timedelta(hours=12),
        'cet_string': '2024-01-15 12:00:00',
        'utc_string': '2024-01-15T11:00:00Z'
    }

@pytest.fixture
def temp_test_directory():
    """Create temporary directory for test files"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)

@pytest.fixture
def mock_email_service():
    """Mock email service responses"""
    return {
        'success_response': {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Email sent successfully',
                'email_sent': True
            })
        },
        'failure_response': {
            'statusCode': 500,
            'body': json.dumps({
                'error': 'Email service failed',
                'email_sent': False
            })
        }
    }

@pytest.fixture
def performance_test_data():
    """Generate large dataset for performance testing"""
    users = []
    for i in range(1000):
        users.append({
            'user_id': f'test-user-{i:04d}',
            'team': f'team-{i % 10}',
            'person': f'Person {i}',
            'daily_requests_used': 300 + (i % 100),
            'daily_limit': 350,
            'is_blocked': 'Y' if i % 5 == 0 else 'N',
            'blocked_until': '2024-01-15 10:00:00' if i % 5 == 0 else None
        })
    return users

@pytest.fixture
def dashboard_test_data():
    """Test data for dashboard testing"""
    return {
        'users': [
            {'user_id': 'user1', 'team': 'team_a', 'daily_requests': 100, 'daily_limit': 350},
            {'user_id': 'user2', 'team': 'team_b', 'daily_requests': 250, 'daily_limit': 350},
            {'user_id': 'user3', 'team': 'team_a', 'daily_requests': 400, 'daily_limit': 350}
        ],
        'requests': [
            {'timestamp': '2024-01-15 10:00:00', 'user_id': 'user1', 'model_id': 'claude-3'},
            {'timestamp': '2024-01-15 11:00:00', 'user_id': 'user2', 'model_id': 'claude-3'},
            {'timestamp': '2024-01-15 12:00:00', 'user_id': 'user3', 'model_id': 'claude-3'}
        ]
    }

class TestDatabaseHelper:
    """Helper class for database testing operations"""
    
    @staticmethod
    def create_mock_cursor_with_data(data_sets):
        """Create mock cursor that returns specific data sets"""
        cursor_mock = Mock()
        cursor_mock.fetchone.side_effect = data_sets.get('fetchone', [None])
        cursor_mock.fetchall.side_effect = data_sets.get('fetchall', [[]])
        cursor_mock.rowcount = data_sets.get('rowcount', 0)
        return cursor_mock
    
    @staticmethod
    def verify_sql_execution(cursor_mock, expected_queries):
        """Verify that expected SQL queries were executed"""
        actual_calls = [call[0][0] for call in cursor_mock.execute.call_args_list]
        for expected_query in expected_queries:
            assert any(expected_query in actual_call for actual_call in actual_calls), \
                f"Expected query not found: {expected_query}"

@pytest.fixture
def db_helper():
    """Database testing helper"""
    return TestDatabaseHelper()

# Custom pytest markers
def pytest_configure(config):
    """Configure custom pytest markers"""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "e2e: End-to-end tests")
    config.addinivalue_line("markers", "lambda_func: Lambda function tests")
    config.addinivalue_line("markers", "database: Database tests")
    config.addinivalue_line("markers", "dashboard: Dashboard/UI tests")
    config.addinivalue_line("markers", "email: Email notification tests")
    config.addinivalue_line("markers", "iam: IAM policy tests")
    config.addinivalue_line("markers", "performance: Performance tests")
    config.addinivalue_line("markers", "slow: Slow running tests")
    config.addinivalue_line("markers", "aws: Tests requiring AWS services")

# Test collection hooks
def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on test names"""
    for item in items:
        # Add markers based on test file names
        if "lambda" in item.nodeid:
            item.add_marker(pytest.mark.lambda_func)
        if "database" in item.nodeid:
            item.add_marker(pytest.mark.database)
        if "dashboard" in item.nodeid:
            item.add_marker(pytest.mark.dashboard)
        if "email" in item.nodeid:
            item.add_marker(pytest.mark.email)
        if "iam" in item.nodeid:
            item.add_marker(pytest.mark.iam)
        if "performance" in item.nodeid:
            item.add_marker(pytest.mark.performance)
            item.add_marker(pytest.mark.slow)
        if "integration" in item.nodeid:
            item.add_marker(pytest.mark.integration)
        if "e2e" in item.nodeid:
            item.add_marker(pytest.mark.e2e)
            item.add_marker(pytest.mark.slow)
        
        # Add unit marker to tests that don't have other markers
        if not any(marker.name in ['integration', 'e2e', 'performance'] 
                  for marker in item.iter_markers()):
            item.add_marker(pytest.mark.unit)
