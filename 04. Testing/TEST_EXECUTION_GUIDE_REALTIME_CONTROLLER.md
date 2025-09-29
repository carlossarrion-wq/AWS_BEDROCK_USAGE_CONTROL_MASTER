# Test Execution Guide - Bedrock Realtime Usage Controller

## Overview

This document provides comprehensive guidance for executing unit tests for the merged `bedrock-realtime-usage-controller` Lambda function. The test suite validates all functionality including CloudTrail processing, API operations, database interactions, and email services.

## Test Suite Structure

### Test Classes and Coverage

1. **TestEventRouting** - Event routing between CloudTrail and API events
2. **TestCloudTrailEventProcessing** - CloudTrail event parsing and processing
3. **TestTimezoneHandling** - CET timezone conversion and handling
4. **TestDatabaseOperations** - Database connection and operations
5. **TestUserLimitsAndBlocking** - User limits checking and blocking logic
6. **TestBlockingWorkflow** - Complete blocking workflow
7. **TestUnblockingWorkflow** - Complete unblocking workflow
8. **TestIAMPolicyManagement** - IAM policy creation and modification
9. **TestAPIEventHandling** - API event handling for manual operations
10. **TestManualOperations** - Manual blocking/unblocking operations
11. **TestEmailNotifications** - Email notification functionality
12. **TestUserMetadataRetrieval** - User metadata retrieval from IAM
13. **TestErrorHandling** - Error handling and edge cases
14. **TestIntegrationScenarios** - Complete integration scenarios

## Prerequisites

### Required Dependencies

```bash
pip install unittest
pip install boto3
pip install pymysql
pip install pytz
```

### Environment Setup

The tests use mocked environment variables. No actual AWS resources are required for testing.

## Test Execution Methods

### Method 1: Direct Python Execution

```bash
cd /Users/csarrion/Cline/AWS_BEDROCK_USAGE_CONTROL/04. Testing
python test_bedrock_realtime_usage_controller_comprehensive.py
```

### Method 2: Using unittest Module

```bash
cd /Users/csarrion/Cline/AWS_BEDROCK_USAGE_CONTROL/04. Testing
python -m unittest test_bedrock_realtime_usage_controller_comprehensive -v
```

### Method 3: Running Specific Test Classes

```bash
# Run only event routing tests
python -m unittest test_bedrock_realtime_usage_controller_comprehensive.TestEventRouting -v

# Run only database operation tests
python -m unittest test_bedrock_realtime_usage_controller_comprehensive.TestDatabaseOperations -v

# Run only integration tests
python -m unittest test_bedrock_realtime_usage_controller_comprehensive.TestIntegrationScenarios -v
```

### Method 4: Running Individual Test Methods

```bash
# Test specific functionality
python -m unittest test_bedrock_realtime_usage_controller_comprehensive.TestEventRouting.test_lambda_handler_routes_api_event -v
```

## Test Data and Fixtures

### Sample CloudTrail Event
```json
{
    "eventName": "InvokeModel",
    "eventTime": "2024-01-15T10:30:00Z",
    "userIdentity": {
        "type": "IAMUser",
        "arn": "arn:aws:iam::123456789012:user/test-user",
        "userName": "test-user"
    },
    "requestParameters": {
        "modelId": "anthropic.claude-3-5-sonnet-20240620-v1:0"
    },
    "sourceIPAddress": "192.168.1.100",
    "userAgent": "aws-cli/2.0.0",
    "requestID": "test-request-id-123",
    "awsRegion": "eu-west-1"
}
```

### Sample API Event
```json
{
    "action": "block",
    "user_id": "test-user",
    "reason": "Manual admin block",
    "performed_by": "admin-user"
}
```

### Sample Usage Information
```json
{
    "daily_requests_used": 300,
    "monthly_requests_used": 2500,
    "daily_percent": 85.7,
    "monthly_percent": 50.0,
    "daily_limit": 350,
    "monthly_limit": 5000,
    "administrative_safe": false
}
```

## Expected Test Results

### Success Criteria

- **Total Tests**: ~50+ individual test methods
- **Expected Success Rate**: 100%
- **Test Categories**:
  - Event Processing: 8 tests
  - Database Operations: 6 tests
  - Blocking/Unblocking: 10 tests
  - IAM Management: 6 tests
  - Email Notifications: 4 tests
  - Error Handling: 4 tests
  - Integration: 2 tests
  - Manual Operations: 6 tests
  - Metadata Retrieval: 4 tests

### Sample Output

```
TEST EXECUTION SUMMARY
============================================================
Tests run: 52
Failures: 0
Errors: 0
Success rate: 100.0%
============================================================
```

## Test Scenarios Covered

### 1. Event Routing
- ✅ API events routed to `handle_api_event`
- ✅ CloudTrail events routed to `handle_cloudtrail_event`
- ✅ Event type detection and routing logic

### 2. CloudTrail Processing
- ✅ Successful event parsing
- ✅ ARN-format model ID handling
- ✅ Missing data validation
- ✅ User extraction from ARNs
- ✅ Model name mapping

### 3. Database Operations
- ✅ Connection creation and reuse
- ✅ User creation in limits table
- ✅ Existing user handling
- ✅ Connection failure scenarios

### 4. Blocking/Unblocking Workflows
- ✅ Complete blocking workflow execution
- ✅ Database updates during blocking
- ✅ IAM policy creation
- ✅ Email notification sending
- ✅ Automatic unblocking
- ✅ Administrative protection

### 5. Manual Operations
- ✅ Manual user blocking
- ✅ Manual user unblocking
- ✅ User status checking
- ✅ Admin operation logging

### 6. Email Notifications
- ✅ Gmail SMTP functionality
- ✅ Enhanced email service integration
- ✅ Fallback mechanisms
- ✅ Email content validation

### 7. Error Handling
- ✅ Database connection failures
- ✅ Malformed event handling
- ✅ IAM operation failures
- ✅ SMTP failures

### 8. Integration Scenarios
- ✅ End-to-end CloudTrail processing
- ✅ Complete manual blocking workflow
- ✅ Multi-component interaction

## Troubleshooting

### Common Issues

1. **Import Errors**
   ```
   ModuleNotFoundError: No module named 'lambda_function'
   ```
   **Solution**: Ensure you're running from the correct directory and the path is set properly.

2. **Mock Assertion Failures**
   ```
   AssertionError: Expected call not found
   ```
   **Solution**: Check that the function signatures match the actual implementation.

3. **Environment Variable Issues**
   ```
   KeyError: 'RDS_ENDPOINT'
   ```
   **Solution**: The test suite mocks all environment variables automatically.

### Debug Mode

To run tests with additional debugging:

```bash
python -m unittest test_bedrock_realtime_usage_controller_comprehensive -v --buffer
```

## Test Maintenance

### Adding New Tests

1. Create new test methods following the naming convention: `test_<functionality>_<scenario>`
2. Use appropriate mocking for external dependencies
3. Include both success and failure scenarios
4. Update this documentation

### Updating Existing Tests

1. Modify test methods when function signatures change
2. Update mock expectations when implementation changes
3. Ensure test data remains relevant
4. Validate test coverage remains comprehensive

## Coverage Analysis

### Function Coverage
- ✅ `lambda_handler()` - Event routing
- ✅ `handle_api_event()` - API processing
- ✅ `handle_cloudtrail_event()` - CloudTrail processing
- ✅ `parse_bedrock_event()` - Event parsing
- ✅ `execute_user_blocking()` - Blocking workflow
- ✅ `execute_user_unblocking()` - Unblocking workflow
- ✅ `implement_iam_blocking()` - IAM policy management
- ✅ `send_enhanced_blocking_email()` - Email notifications
- ✅ `check_user_limits_with_protection()` - Limit checking
- ✅ `get_mysql_connection()` - Database connectivity

### Edge Cases Covered
- ✅ Missing required parameters
- ✅ Invalid event formats
- ✅ Database connection failures
- ✅ IAM operation failures
- ✅ Email service failures
- ✅ Timezone conversion errors
- ✅ Administrative protection scenarios

## Continuous Integration

### Automated Testing

For CI/CD integration, use:

```bash
#!/bin/bash
cd 04. Testing
python -m unittest test_bedrock_realtime_usage_controller_comprehensive 2>&1 | tee test_results.log
exit_code=${PIPESTATUS[0]}
if [ $exit_code -eq 0 ]; then
    echo "✅ All tests passed"
else
    echo "❌ Tests failed with exit code $exit_code"
    exit $exit_code
fi
```

### Test Reporting

The test suite generates detailed output including:
- Test execution summary
- Failure details with specific error messages
- Success rate calculation
- Individual test results

## Conclusion

This comprehensive test suite ensures the reliability and correctness of the merged `bedrock-realtime-usage-controller` function. Regular execution of these tests will help maintain code quality and catch regressions early in the development process.

For questions or issues with the test suite, refer to the test implementation in `test_bedrock_realtime_usage_controller_comprehensive.py`.
