# Comprehensive Unit Test Plan for bedrock_daily_reset.py Lambda Function

## Overview

This document provides a comprehensive testing strategy for the `bedrock_daily_reset.py` Lambda function before AWS deployment. The test suite covers all critical scenarios, edge cases, and integration points to ensure reliable production deployment.

## Test Categories and Coverage

### 1. Database Connection Tests
- **Purpose**: Validate MySQL RDS connection handling
- **Coverage**: Connection establishment, reconnection logic, failure scenarios
- **Critical Scenarios**:
  - Successful connection with connection pooling
  - Connection loss and automatic reconnection
  - Database connection failures and error handling
  - Connection timeout scenarios

### 2. User Unblocking Logic Tests
- **Purpose**: Validate core business logic for user unblocking
- **Coverage**: Expiration date checking, selective unblocking, batch processing
- **Critical Scenarios**:
  - Users with expired `blocked_until` dates
  - Users with NULL `blocked_until` (indefinite blocks)
  - Users with future `blocked_until` dates (should not be unblocked)
  - Mixed scenarios with multiple users
  - Empty result sets (no users to unblock)

### 3. Administrative Safe Flag Management Tests
- **Purpose**: Validate administrative flag removal logic
- **Coverage**: Flag detection, removal, audit logging
- **Critical Scenarios**:
  - Active users with `administrative_safe = 'Y'`
  - Users without the flag (no-op scenarios)
  - Database transaction failures during flag removal
  - Audit log creation for flag removal operations

### 4. IAM Policy Management Tests
- **Purpose**: Validate IAM policy modifications for access restoration
- **Coverage**: Policy retrieval, modification, error handling
- **Critical Scenarios**:
  - Policies with deny statements (removal required)
  - Policies without allow statements (addition required)
  - Non-existent policies (no action needed)
  - IAM service failures and error handling

### 5. Email Notification Tests
- **Purpose**: Validate email service integration
- **Coverage**: Lambda invocation, payload formatting, error handling
- **Critical Scenarios**:
  - Successful email service invocation
  - Default value handling for missing user data
  - Email service failures and error handling
  - Payload structure validation

### 6. Error Handling Tests
- **Purpose**: Validate error notification and recovery mechanisms
- **Coverage**: SNS notifications, error logging, graceful degradation
- **Critical Scenarios**:
  - SNS notification success
  - SNS service failures
  - Error message formatting and content

### 7. Integration Tests
- **Purpose**: Validate end-to-end Lambda function execution
- **Coverage**: Complete workflow, partial failures, success scenarios
- **Critical Scenarios**:
  - Successful complete execution
  - Database connection failures
  - Partial operation failures with error collection
  - Event processing and response formatting

### 8. Performance Tests
- **Purpose**: Validate function performance under load
- **Coverage**: Large user sets, execution time limits
- **Critical Scenarios**:
  - Processing 1000+ users within timeout limits
  - Memory usage optimization
  - Database query efficiency

### 9. Timezone Tests
- **Purpose**: Validate CET timezone handling
- **Coverage**: Time calculations, formatting, comparisons
- **Critical Scenarios**:
  - CET timezone conversion accuracy
  - Timestamp string formatting
  - Date comparison logic for expiration checking

### 10. Edge Cases and Boundary Tests
- **Purpose**: Validate handling of unusual scenarios
- **Coverage**: Boundary conditions, data validation, error recovery
- **Critical Scenarios**:
  - Database transaction failures
  - Malformed user data
  - Network timeouts and retries

## Test Data Requirements

### Database Test Data Setup

```sql
-- Test users for unblocking scenarios
INSERT INTO user_limits (user_id, team, person, daily_request_limit, administrative_safe) VALUES
('expired_user_1', 'team_a', 'John Doe', 350, 'N'),
('expired_user_2', 'team_b', 'Jane Smith', 500, 'Y'),
('future_user_1', 'team_c', 'Bob Wilson', 250, 'N'),
('admin_safe_user_1', 'team_d', 'Alice Brown', 400, 'Y'),
('admin_safe_user_2', 'team_e', 'Charlie Davis', 300, 'Y');

-- Test blocking status data
INSERT INTO user_blocking_status (user_id, is_blocked, blocked_reason, blocked_until) VALUES
('expired_user_1', 'Y', 'Daily limit exceeded', '2025-01-15 23:00:00'),  -- Expired
('expired_user_2', 'Y', 'Daily limit exceeded', NULL),                    -- No expiration
('future_user_1', 'Y', 'Daily limit exceeded', '2025-01-17 00:00:00'),   -- Future expiration
('admin_safe_user_1', 'N', NULL, NULL),                                   -- Active with admin flag
('admin_safe_user_2', 'N', NULL, NULL);                                   -- Active with admin flag
```

### Mock IAM Policy Data

```json
{
  "existing_policy_with_deny": {
    "Statement": [
      {
        "Sid": "BedrockAccess",
        "Effect": "Allow",
        "Action": ["bedrock:InvokeModel", "bedrock:InvokeModelWithResponseStream"],
        "Resource": "*"
      },
      {
        "Sid": "DailyLimitBlock",
        "Effect": "Deny",
        "Action": ["bedrock:InvokeModel", "bedrock:InvokeModelWithResponseStream"],
        "Resource": "*"
      }
    ]
  },
  "policy_only_deny": {
    "Statement": [
      {
        "Sid": "DailyLimitBlock",
        "Effect": "Deny",
        "Action": ["bedrock:InvokeModel"],
        "Resource": "*"
      }
    ]
  }
}
```

## Test Execution Instructions

### Prerequisites

1. **Install Test Dependencies**:
```bash
pip install pytest pytest-mock moto boto3 pymysql pytz
```

2. **Set Environment Variables**:
```bash
export RDS_ENDPOINT="test-rds-endpoint.amazonaws.com"
export RDS_USERNAME="test_user"
export RDS_PASSWORD="test_password"
export RDS_DATABASE="test_bedrock_usage"
export AWS_REGION="eu-west-1"
export ACCOUNT_ID="123456789012"
export SNS_TOPIC_ARN="arn:aws:sns:eu-west-1:123456789012:test-topic"
export EMAIL_SERVICE_FUNCTION="test-email-service"
```

### Running Tests

#### 1. Run All Tests
```bash
cd "Project documents/Source/Lambda Functions"
python -m pytest test_bedrock_daily_reset_comprehensive.py -v
```

#### 2. Run Specific Test Categories
```bash
# Database connection tests
python -m pytest test_bedrock_daily_reset_comprehensive.py::TestBedrockDailyReset::test_get_mysql_connection_success -v

# User unblocking logic tests
python -m pytest test_bedrock_daily_reset_comprehensive.py::TestBedrockDailyReset::test_unblock_expired_users_success -v

# IAM policy tests
python -m pytest test_bedrock_daily_reset_comprehensive.py::TestBedrockDailyReset::test_implement_iam_unblocking_success -v
```

#### 3. Run with Coverage Report
```bash
pip install pytest-cov
python -m pytest test_bedrock_daily_reset_comprehensive.py --cov=bedrock_daily_reset --cov-report=html
```

#### 4. Run Performance Tests
```bash
python -m pytest test_bedrock_daily_reset_comprehensive.py::TestBedrockDailyReset::test_performance_large_user_set -v -s
```

## Expected Test Results

### Success Criteria

1. **All Unit Tests Pass**: 100% test pass rate
2. **Code Coverage**: Minimum 95% code coverage
3. **Performance Requirements**:
   - Process 1000 users within 10 seconds
   - Memory usage under 400MB
   - Database queries complete within 5 seconds each

### Test Result Validation

#### 1. Database Operations
- ✅ Connection establishment and pooling
- ✅ Query execution and result processing
- ✅ Transaction handling and rollback
- ✅ Error handling and recovery

#### 2. Business Logic
- ✅ Correct user selection based on expiration dates
- ✅ Administrative flag management
- ✅ Audit logging for all operations
- ✅ Error collection and reporting

#### 3. AWS Service Integration
- ✅ IAM policy modifications
- ✅ Lambda function invocations
- ✅ SNS notifications
- ✅ Error handling for service failures

#### 4. Data Integrity
- ✅ Consistent database state after operations
- ✅ Proper audit trail creation
- ✅ No data corruption or loss
- ✅ Transactional consistency

## Test Scenarios Matrix

| Scenario | Blocked Users | Admin Safe Users | Expected Unblocked | Expected Notifications | Expected Flag Removals |
|----------|---------------|------------------|-------------------|----------------------|----------------------|
| Normal Operation | 5 expired | 3 active | 5 | 5 | 3 |
| No Expired Users | 0 | 2 active | 0 | 0 | 2 |
| No Admin Safe Users | 3 expired | 0 | 3 | 3 | 0 |
| Mixed Expiration | 2 expired, 2 future | 1 active | 2 | 2 | 1 |
| Partial Failures | 3 expired (1 fails) | 2 active (1 fails) | 2 | 2 | 1 |

## Error Scenarios Testing

### Database Errors
- Connection timeouts
- Query execution failures
- Transaction rollback scenarios
- Connection pool exhaustion

### AWS Service Errors
- IAM policy retrieval failures
- Lambda invocation timeouts
- SNS publishing failures
- Service throttling scenarios

### Data Validation Errors
- Malformed user data
- Missing required fields
- Invalid timestamp formats
- Null value handling

## Monitoring and Logging Validation

### Log Message Verification
- ✅ Successful operation logs
- ✅ Error condition logs
- ✅ Performance metrics logs
- ✅ Audit trail completeness

### Metrics Validation
- ✅ Execution time tracking
- ✅ Success/failure rates
- ✅ User processing counts
- ✅ Error categorization

## Pre-Deployment Checklist

### Code Quality
- [ ] All unit tests pass (100%)
- [ ] Code coverage ≥ 95%
- [ ] No critical security vulnerabilities
- [ ] Performance requirements met

### Integration Readiness
- [ ] Database schema compatibility verified
- [ ] IAM permissions validated
- [ ] Email service integration tested
- [ ] SNS topic configuration confirmed

### Operational Readiness
- [ ] CloudWatch logging configured
- [ ] Error notification setup verified
- [ ] Monitoring dashboards prepared
- [ ] Rollback procedures documented

### Security Validation
- [ ] Environment variable security
- [ ] Database credential protection
- [ ] IAM policy least privilege
- [ ] Audit logging completeness

## Deployment Recommendations

### Staging Environment Testing
1. Deploy to staging environment
2. Run full test suite against staging
3. Perform load testing with production-like data
4. Validate monitoring and alerting

### Production Deployment Strategy
1. **Blue-Green Deployment**: Deploy alongside existing version
2. **Canary Release**: Gradual traffic shifting
3. **Monitoring**: Real-time performance tracking
4. **Rollback Plan**: Immediate rollback capability

### Post-Deployment Validation
1. Monitor first 24 hours closely
2. Validate daily execution at 00:00 CET
3. Confirm email notifications are sent
4. Verify audit logs are created properly

## Troubleshooting Guide

### Common Test Failures

#### Database Connection Issues
```bash
# Check environment variables
echo $RDS_ENDPOINT
echo $RDS_USERNAME

# Verify mock setup
python -c "import unittest.mock; print('Mock available')"
```

#### IAM Policy Test Failures
```bash
# Verify moto installation
pip install moto[iam]
python -c "from moto import mock_iam; print('Moto IAM available')"
```

#### Performance Test Issues
```bash
# Run with profiling
python -m pytest test_bedrock_daily_reset_comprehensive.py::TestBedrockDailyReset::test_performance_large_user_set -v -s --profile
```

### Test Environment Setup Issues

#### Missing Dependencies
```bash
pip install -r requirements-test.txt
```

#### Environment Variable Issues
```bash
# Create test environment file
cat > .env.test << EOF
RDS_ENDPOINT=test-rds-endpoint.amazonaws.com
RDS_USERNAME=test_user
RDS_PASSWORD=test_password
RDS_DATABASE=test_bedrock_usage
AWS_REGION=eu-west-1
ACCOUNT_ID=123456789012
SNS_TOPIC_ARN=arn:aws:sns:eu-west-1:123456789012:test-topic
EMAIL_SERVICE_FUNCTION=test-email-service
EOF

# Load environment
source .env.test
```

## Conclusion

This comprehensive test plan ensures the `bedrock_daily_reset.py` Lambda function is thoroughly validated before AWS deployment. The test suite covers all critical functionality, error scenarios, and performance requirements to guarantee reliable production operation.

Execute all tests and verify 100% pass rate before proceeding with deployment to AWS environment.
