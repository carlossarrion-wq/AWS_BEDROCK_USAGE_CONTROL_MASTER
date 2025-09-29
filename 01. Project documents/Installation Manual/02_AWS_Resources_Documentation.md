# AWS Bedrock Usage Control System - AWS Resources Documentation

## 📋 Table of Contents

1. [Overview of AWS Resources](#overview-of-aws-resources)
2. [IAM Resources](#iam-resources)
3. [Lambda Functions](#lambda-functions)
4. [DynamoDB Tables](#dynamodb-tables)
5. [RDS MySQL Database](#rds-mysql-database)
6. [EventBridge Rules](#eventbridge-rules)
7. [CloudWatch Resources](#cloudwatch-resources)
8. [SNS Topics](#sns-topics)
9. [SES Configuration](#ses-configuration)
10. [CloudTrail Configuration](#cloudtrail-configuration)
11. [Secrets Manager](#secrets-manager)
12. [VPC and Security Groups](#vpc-and-security-groups)
13. [Resource Creation Scripts](#resource-creation-scripts)

## Overview of AWS Resources

The AWS Bedrock Usage Control System utilizes multiple AWS services to provide comprehensive monitoring, blocking, and management capabilities. Below is a complete inventory of all AWS resources used in the system.

### Resource Summary

| Service | Resource Count | Purpose |
|---------|----------------|---------|
| IAM | 3 Roles, 3 Policies, Multiple Users/Groups | Access control and permissions |
| Lambda | 6 Functions | Core processing logic |
| RDS | 1 MySQL Instance | Primary data storage and analytics |
| EventBridge | 2 Rules | Event-driven processing |
| CloudWatch | Multiple Log Groups, Metrics | Monitoring and logging |
| SNS | 1 Topic | Notifications |
| SES | Email Configuration | Email notifications |
| CloudTrail | 1 Trail | API call auditing |
| Secrets Manager | 1 Secret | Database credentials |
| VPC | Security Groups, Subnets | Network security |

## IAM Resources

### IAM Roles

#### 1. bedrock-usage-monitor-role
**Purpose**: Execution role for the usage monitoring Lambda function

**Trust Policy**:
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "Service": "lambda.amazonaws.com"
            },
            "Action": "sts:AssumeRole"
        }
    ]
}
```

**Attached Policies**:
- `AWSLambdaBasicExecutionRole` (AWS Managed)
- `BedrockUsageMonitorPolicy` (Custom)

**Source Configuration**: `Project documents/Installation Manual/03_IAM_Policies_and_Roles.json`

#### 2. bedrock-policy-manager-role
**Purpose**: Execution role for the policy management Lambda function

**Trust Policy**:
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "Service": "lambda.amazonaws.com"
            },
            "Action": "sts:AssumeRole"
        }
    ]
}
```

**Attached Policies**:
- `AWSLambdaBasicExecutionRole` (AWS Managed)
- `BedrockPolicyManagerPolicy` (Custom)

**Source Configuration**: `Project documents/Installation Manual/03_IAM_Policies_and_Roles.json`

#### 3. bedrock-dashboard-access-role
**Purpose**: Role for dashboard access to AWS resources

**Trust Policy**:
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "AWS": "arn:aws:iam::701055077130:root"
            },
            "Action": "sts:AssumeRole"
        }
    ]
}
```

**Attached Policies**:
- `BedrockDashboardAccessPolicy` (Custom)

**Source Configuration**: `Project documents/Installation Manual/03_IAM_Policies_and_Roles.json`

### IAM Policies

#### 1. BedrockUsageMonitorPolicy
**Purpose**: Permissions for usage monitoring Lambda function

**Key Permissions**:
- DynamoDB: Read/Write access to usage and blocking tables
- IAM: Read user tags and information
- SNS: Publish notifications
- SES: Send emails
- Lambda: Invoke policy manager function
- Secrets Manager: Access database credentials
- RDS: Database connection

**Source Configuration**: `Project documents/Installation Manual/03_IAM_Policies_and_Roles.json`

#### 2. BedrockPolicyManagerPolicy
**Purpose**: Permissions for policy management Lambda function

**Key Permissions**:
- DynamoDB: Read/Write access to usage and blocking tables
- IAM: Manage user policies and attachments
- SNS: Publish notifications

**Source Configuration**: `Project documents/Installation Manual/03_IAM_Policies_and_Roles.json`

#### 3. BedrockDashboardAccessPolicy
**Purpose**: Permissions for dashboard access

**Key Permissions**:
- Lambda: Invoke monitoring and management functions
- DynamoDB: Read access to tables
- RDS: Describe instances

**Source Configuration**: `Project documents/Installation Manual/03_IAM_Policies_and_Roles.json`

### User and Group Management

#### User Creation Process
Users are created using the provisioning script:
```bash
python3 provision_bedrock_user.py --username <username> --group <team_group>
```

**Standard User Policies**:
- `<username>_BedrockPolicy`: Bedrock access permissions
- `CloudWatchLogsFullAccess`: Logging permissions

**User Tags**:
- `Person`: User's real name
- `Team`: Team assignment
- `Tool`: Associated tools (e.g., "Cline Agent")

#### Team Groups
**Supported Teams**:
- `team_darwin_group`
- `team_sap_group`
- `team_mulesoft_group`
- `team_yo_leo_gas_group`
- `team_lcorp_group`

**Group Policies**:
- `<team_name>_BedrockPolicy`: Team-specific Bedrock access
- `<team_name>_AssumeRolePolicy`: Role assumption permissions

## Lambda Functions

### Current Lambda Functions in Production (Updated September 2025)

**Major Architecture Change**: The system has been consolidated from multiple Lambda functions into a single, more efficient merged function for real-time processing.

### 1. bedrock-realtime-usage-controller

**Purpose**: **MERGED FUNCTION** - Combines real-time logging, quota checking, blocking logic, and email notifications into a single efficient function

**Configuration**:
- **Runtime**: Python 3.9
- **Memory**: 512 MB
- **Timeout**: 300 seconds (5 minutes)
- **Handler**: `lambda_function.lambda_handler`
- **Execution Role**: `bedrock-realtime-usage-controller-role`

**Environment Variables**:
```json
{
    "RDS_ENDPOINT": "bedrock-usage-db.endpoint.eu-west-1.rds.amazonaws.com",
    "RDS_USERNAME": "admin",
    "RDS_PASSWORD": "[secure-password]",
    "RDS_DATABASE": "bedrock_usage",
    "AWS_REGION": "eu-west-1",
    "ACCOUNT_ID": "701055077130",
    "EMAIL_SERVICE_FUNCTION": "bedrock-email-service",
    "SNS_TOPIC_ARN": "arn:aws:sns:eu-west-1:701055077130:bedrock-usage-alerts"
}
```

**Key Features**:
- **Real-time CloudTrail Event Processing**: Processes Bedrock API calls in real-time with CET timezone handling
- **Direct RDS MySQL Integration**: Uses PyMySQL for direct database operations
- **Auto-provisioning**: Automatically provisions new users in the database
- **Usage Limit Checking**: Uses stored procedures for efficient limit evaluation
- **Automatic Blocking**: Implements IAM policy-based blocking when limits are exceeded
- **Email Notifications**: Integrates with bedrock-email-service for user notifications
- **Comprehensive Audit Logging**: All operations logged for compliance and debugging
- **CET Timezone Support**: All timestamps handled in Central European Time

**Merged Functionality**:
This function combines the capabilities of the previously separate functions:
- `bedrock-realtime-logger-fixed` (Real-time request logging)
- `bedrock-policy-manager-enhanced` (Policy management and blocking)

**Critical IAM Permissions Required**:
- `rds:DescribeDBInstances` - RDS instance access
- `iam:GetUserPolicy` - Read user IAM policies
- `iam:PutUserPolicy` - Modify user IAM policies
- `iam:DeleteUserPolicy` - Delete user IAM policies
- `iam:GetUser` - Get user information and tags
- `lambda:InvokeFunction` - Invoke email service function
- `sns:Publish` - Send SNS notifications

**Database Operations**:
- Inserts new requests into `bedrock_requests` table
- Updates user limits and status in `users` table
- Logs blocking operations in `blocking_operations` table
- Uses stored procedures for efficient limit checking

**Triggers**:
- EventBridge Rule: `bedrock-realtime-processing` - Triggered by Bedrock API calls via CloudTrail

**Source Code**: `02. Source/Lambda Functions/bedrock-realtime-usage-controller.py`

**Deployment**: Can be deployed using automated script `deploy_bedrock_realtime_usage_controller.sh`

### 2. bedrock-daily-reset

**Purpose**: Daily reset operations for expired user blocks and administrative flag management with enhanced IAM policy management

**Configuration**:
- **Runtime**: Python 3.9
- **Memory**: 512 MB
- **Timeout**: 300 seconds (5 minutes)
- **Handler**: `bedrock_daily_reset.lambda_handler`
- **Execution Role**: `bedrock-daily-reset-role` (with enhanced IAM permissions)

**Environment Variables**:
```json
{
    "RDS_ENDPOINT": "bedrock-usage-db.endpoint.eu-west-1.rds.amazonaws.com",
    "RDS_USERNAME": "admin",
    "RDS_PASSWORD": "[secure-password]",
    "RDS_DATABASE": "bedrock_usage",
    "AWS_REGION": "eu-west-1",
    "ACCOUNT_ID": "701055077130",
    "SNS_TOPIC_ARN": "arn:aws:sns:eu-west-1:701055077130:bedrock-usage-alerts",
    "EMAIL_SERVICE_FUNCTION": "bedrock-email-service"
}
```

**Key Features**:
- **Selective Unblocking**: Only unblocks users whose `blocked_until` expiration date has passed
- **Administrative Safe Flag Management**: Removes `administrative_safe` flags from active users and newly unblocked users
- **IAM Policy Management**: Removes deny policies to restore Bedrock access (requires enhanced IAM permissions)
- **Email Notifications**: Sends personalized reset notifications to unblocked users via email service
- **CET Timezone Handling**: All operations performed in Central European Time
- **Comprehensive Audit Logging**: All operations logged for compliance

**Critical IAM Permissions Required**:
- `iam:GetUserPolicy` - Read user IAM policies
- `iam:PutUserPolicy` - Modify user IAM policies
- `iam:DeleteUserPolicy` - Delete user IAM policies
- `lambda:InvokeFunction` - Invoke email service function

**Database Operations**:
- Updates `user_blocking_status` table to unblock expired users
- Removes `administrative_safe` flags from `user_limits` table
- Logs all operations to `blocking_audit_log` table

**Triggers**:
- EventBridge Rule: `bedrock-daily-reset-schedule` (cron: 0 23 * * ? *) - Runs at 00:00 CET daily

**Source Code**: `Project documents/Source/Lambda Functions/bedrock_daily_reset.py`

**Deployment**: Can be deployed using automated script `deploy_bedrock_daily_reset.sh`

### 2. bedrock-email-service

**Purpose**: **ENHANCED CENTRALIZED EMAIL SERVICE** - Professional email notification service with sophisticated HTML templates and comprehensive notification support

**Configuration**:
- **Runtime**: Python 3.9
- **Memory**: 256 MB
- **Timeout**: 30 seconds
- **Handler**: `lambda_handler.lambda_handler`
- **Execution Role**: `bedrock-email-service-role`

**Environment Variables**:
```json
{
    "AWS_REGION": "eu-west-1"
}
```

**Key Features**:
- **Professional HTML Email Templates**: Sophisticated responsive design with CSS styling
- **Gmail SMTP Integration**: Direct email delivery via Gmail SMTP with secure authentication
- **Color-Coded Email System**: Visual distinction for different notification types
- **Multi-Language Support**: Spanish language templates with proper formatting
- **User Display Name Resolution**: Intelligent name resolution from IAM tags and user information
- **CET Timezone Support**: All timestamps displayed in Central European Time (Madrid)
- **Template-Based Architecture**: Modular email generation with HTML and plain text fallbacks
- **Enhanced Visual Design**: Professional corporate styling with proper branding

**Email Types Supported**:
- **Warning Emails**: 80% quota reached (amber/orange color scheme)
- **Blocking Emails**: 100% quota exceeded (light red color scheme)
- **Unblocking Emails**: Daily reset notifications (green color scheme)
- **Admin Blocking Emails**: Manual administrative blocks (light red color scheme)
- **Admin Unblocking Emails**: Manual administrative unblocks (green color scheme)

**Enhanced Email Features**:
- **Responsive Design**: Emails display correctly on desktop and mobile devices
- **Professional Styling**: Corporate-grade email templates with consistent branding
- **Rich Content**: HTML formatting with proper typography and spacing
- **Fallback Support**: Plain text versions for email clients that don't support HTML
- **Security Headers**: Proper email headers for spam prevention and deliverability

**Configuration Files**:
- `email_credentials.json`: Gmail SMTP credentials and configuration
- `lambda_handler.py`: Entry point handler for proper Lambda integration

**Source Code**: 
- Main Service: `02. Source/Lambda Functions/bedrock_email_service.py`
- Handler: `lambda_handler.py` (entry point)

**Integration**: 
- Invoked by `bedrock-realtime-usage-controller` for user notifications
- Invoked by `bedrock-daily-reset` for unblocking notifications
- Invoked by `bedrock-policy-manager-enhanced` for admin notifications

**Deployment**: Enhanced deployment with proper handler configuration and dependencies

### 3. bedrock-policy-manager-enhanced

**Purpose**: Enhanced IAM policy management for user blocking/unblocking with comprehensive email integration

**Configuration**:
- **Runtime**: Python 3.9
- **Memory**: 256 MB
- **Timeout**: 60 seconds
- **Handler**: `bedrock_policy_manager_enhanced.lambda_handler`

**Environment Variables**:
```json
{
    "AWS_REGION": "eu-west-1",
    "ACCOUNT_ID": "701055077130",
    "DYNAMODB_TABLE": "bedrock_user_daily_usage",
    "SNS_TOPIC_ARN": "arn:aws:sns:eu-west-1:701055077130:bedrock-usage-alerts",
    "EMAIL_NOTIFICATIONS_ENABLED": "true"
}
```

**Key Features**:
- **Dynamic IAM Policy Management**: Adds/removes Deny statements to user policies
- **User Blocking/Unblocking**: Complete workflow for blocking and unblocking users
- **Administrative Protection**: Sets protection flags for manual admin operations
- **Enhanced Email Notifications**: Integrates with bedrock-email-service for admin scenarios
- **Audit Trail**: Comprehensive logging of all policy modifications
- **Block Status Checking**: Query current user block status

**Supported Operations**:
- `block`: Block user access by adding Deny statement to IAM policy
- `unblock`: Unblock user access by removing Deny statement from IAM policy
- `check_status`: Check if user is currently blocked

**Source Code**: `Project documents/Source/Lambda Functions/bedrock_policy_manager_enhanced.py`

**Integration**: Works with `bedrock-email-service` for admin notifications

### Legacy/Archived Lambda Functions

The following functions are referenced in older documentation but are not currently in the active Lambda Functions directory:

#### bedrock-realtime-request-logger
- **Status**: Legacy - replaced by newer RDS MySQL integration
- **Location**: Available in `migration/` directory
- **Purpose**: Real-time logging of Bedrock API calls

#### bedrock-mysql-query-executor
- **Status**: Legacy - functionality integrated into other functions
- **Location**: Available in `migration/` directory
- **Purpose**: Database query executor for dashboard

#### bedrock-usage-monitor-current
- **Status**: Legacy - replaced by enhanced policy manager
- **Location**: May be in `individual_blocking_system/lambda_functions/`
- **Purpose**: Usage monitoring with RDS MySQL integration

#### bedrock-blocking-history
- **Status**: Legacy - audit functionality integrated into other functions
- **Purpose**: Audit trail and history management

### Deployment Packages

The following deployment packages are available in the Lambda Functions directory:

1. **bedrock-daily-reset-aws.zip**: Production-ready daily reset function
2. **bedrock-mysql-query-executor-aws.zip**: Legacy MySQL query executor
3. **bedrock-realtime-logger-fixed-aws.zip**: Legacy realtime logger

### Function Dependencies

**Current Active Functions**:
- `bedrock-daily-reset` → `bedrock-email-service` (for notifications)
- `bedrock-policy-manager-enhanced` → `bedrock-email-service` (for admin notifications)

**Required IAM Roles**:
- `bedrock-daily-reset-role`: Enhanced role with IAM policy management permissions
- `bedrock-usage-monitor-role`: Standard role for other Lambda functions
- `bedrock-policy-manager-role`: Role for policy management functions

## DynamoDB Tables

### 1. bedrock_user_daily_usage

**Purpose**: Track daily usage counters and user status

**Configuration**:
- **Partition Key**: `user_id` (String)
- **Sort Key**: `date` (String)
- **Billing Mode**: Pay-per-request
- **Point-in-time Recovery**: Enabled

**Attributes**:
```json
{
    "user_id": "String",
    "date": "String (YYYY-MM-DD)",
    "request_count": "Number",
    "daily_limit": "Number",
    "warning_threshold": "Number",
    "status": "String (ACTIVE|WARNING|BLOCKED|ACTIVE_ADMIN)",
    "team": "String",
    "last_request_time": "String (ISO timestamp)",
    "blocked_at": "String (ISO timestamp)",
    "expires_at": "String (ISO timestamp or 'Indefinite')",
    "admin_protection": "Boolean",
    "first_seen": "String (ISO timestamp)",
    "ttl": "Number (Unix timestamp)"
}
```

**TTL**: 7 days for automatic cleanup

**Creation Script**: 
```bash
aws dynamodb create-table \
    --table-name bedrock_user_daily_usage \
    --attribute-definitions \
        AttributeName=user_id,AttributeType=S \
        AttributeName=date,AttributeType=S \
    --key-schema \
        AttributeName=user_id,KeyType=HASH \
        AttributeName=date,KeyType=RANGE \
    --billing-mode PAY_PER_REQUEST \
    --point-in-time-recovery-specification PointInTimeRecoveryEnabled=true
```

### 2. bedrock_blocking_operations

**Purpose**: Audit trail of all blocking/unblocking operations

**Configuration**:
- **Partition Key**: `operation_id` (String)
- **Sort Key**: `timestamp` (String)
- **Billing Mode**: Pay-per-request
- **Point-in-time Recovery**: Enabled

**Global Secondary Index**: `user-date-index`
- **Partition Key**: `user_id` (String)
- **Sort Key**: `timestamp` (String)

**Attributes**:
```json
{
    "operation_id": "String (UUID)",
    "timestamp": "String (ISO timestamp)",
    "user_id": "String",
    "operation": "String (BLOCK|UNBLOCK|ADMIN_PROTECTION_EXPIRED)",
    "reason": "String",
    "performed_by": "String",
    "duration": "String",
    "expires_at": "String (ISO timestamp or 'Indefinite')",
    "status": "String (SUCCESS|FAILED)",
    "ttl": "Number (Unix timestamp - 90 days)"
}
```

**TTL**: 90 days for automatic cleanup

**Creation Script**:
```bash
aws dynamodb create-table \
    --table-name bedrock_blocking_operations \
    --attribute-definitions \
        AttributeName=operation_id,AttributeType=S \
        AttributeName=timestamp,AttributeType=S \
        AttributeName=user_id,AttributeType=S \
    --key-schema \
        AttributeName=operation_id,KeyType=HASH \
        AttributeName=timestamp,KeyType=RANGE \
    --global-secondary-indexes \
        IndexName=user-date-index,KeySchema='[{AttributeName=user_id,KeyType=HASH},{AttributeName=timestamp,KeyType=RANGE}]',Projection='{ProjectionType=ALL}',ProvisionedThroughput='{ReadCapacityUnits=5,WriteCapacityUnits=5}' \
    --billing-mode PAY_PER_REQUEST \
    --point-in-time-recovery-specification PointInTimeRecoveryEnabled=true
```

## RDS MySQL Database

### Instance Configuration

**Instance Details**:
- **Identifier**: `bedrock-usage-db`
- **Engine**: MySQL 8.0.35
- **Instance Class**: db.t3.micro
- **Storage**: 20 GB GP2
- **Multi-AZ**: No (Single-AZ for cost optimization)
- **Backup Retention**: 7 days
- **Encryption**: Enabled
- **Performance Insights**: Enabled (7 days retention)
- **Deletion Protection**: Enabled

**Network Configuration**:
- **VPC**: Default VPC
- **Subnet Group**: `bedrock-usage-subnet-group`
- **Security Group**: `bedrock-usage-rds-sg`
- **Port**: 3306
- **Public Access**: No

**Creation Script**: `migration/01_create_rds_instance.sh`

### Database Schema

**Database Name**: `bedrock_usage`

**Tables**:

#### 1. users
```sql
CREATE TABLE users (
    user_id VARCHAR(255) PRIMARY KEY,
    team VARCHAR(100) NOT NULL,
    person_tag VARCHAR(255),
    daily_limit INT DEFAULT 250,
    monthly_limit INT DEFAULT 5000,
    warning_threshold INT DEFAULT 60,
    critical_threshold INT DEFAULT 85,
    is_blocked BOOLEAN DEFAULT FALSE,
    blocked_reason VARCHAR(500),
    blocked_until TIMESTAMP NULL,
    admin_protection_by VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

#### 2. bedrock_requests
```sql
CREATE TABLE bedrock_requests (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    team VARCHAR(100) NOT NULL,
    request_timestamp TIMESTAMP(3) DEFAULT CURRENT_TIMESTAMP(3),
    date_only DATE GENERATED ALWAYS AS (DATE(request_timestamp)) STORED,
    hour_only INT GENERATED ALWAYS AS (HOUR(request_timestamp)) STORED,
    model_id VARCHAR(255) NOT NULL,
    model_name VARCHAR(255),
    request_type ENUM('invoke', 'invoke-stream', 'converse', 'converse-stream') DEFAULT 'invoke',
    input_tokens INT DEFAULT 0,
    output_tokens INT DEFAULT 0,
    total_tokens INT GENERATED ALWAYS AS (input_tokens + output_tokens) STORED,
    cost_usd DECIMAL(10,6) DEFAULT 0.000000,
    region VARCHAR(50) DEFAULT 'us-east-1',
    source_ip VARCHAR(45),
    user_agent TEXT,
    session_id VARCHAR(255),
    request_id VARCHAR(255),
    response_time_ms INT DEFAULT 0,
    status_code INT DEFAULT 200,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 3. blocking_operations
```sql
CREATE TABLE blocking_operations (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    operation ENUM('block', 'unblock', 'admin_protect', 'admin_unprotect') NOT NULL,
    reason VARCHAR(500),
    performed_by VARCHAR(255) NOT NULL,
    expires_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 4. model_pricing
```sql
CREATE TABLE model_pricing (
    model_id VARCHAR(255) PRIMARY KEY,
    model_name VARCHAR(255) NOT NULL,
    input_token_price DECIMAL(10,8) DEFAULT 0.00000000,
    output_token_price DECIMAL(10,8) DEFAULT 0.00000000,
    region VARCHAR(50) DEFAULT 'us-east-1',
    effective_date DATE DEFAULT (CURDATE()),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

**Schema Creation Script**: `migration/02_create_database_schema_v2.sql`

### Optimized Views

#### 1. v_user_realtime_usage
```sql
CREATE VIEW v_user_realtime_usage AS
SELECT 
    u.user_id,
    u.team,
    u.daily_limit,
    u.monthly_limit,
    u.is_blocked,
    u.blocked_until,
    u.admin_protection_by,
    COALESCE(today.request_count, 0) as today_requests,
    COALESCE(today.total_cost, 0) as today_cost,
    COALESCE(month.request_count, 0) as monthly_requests,
    COALESCE(month.total_cost, 0) as monthly_cost,
    ROUND((COALESCE(today.request_count, 0) / u.daily_limit) * 100, 2) as daily_usage_percent,
    ROUND((COALESCE(month.request_count, 0) / u.monthly_limit) * 100, 2) as monthly_usage_percent,
    COALESCE(today.last_request, '1970-01-01 00:00:00') as last_request_time
FROM users u
LEFT JOIN (
    SELECT 
        user_id,
        COUNT(*) as request_count,
        SUM(cost_usd) as total_cost,
        MAX(request_timestamp) as last_request
    FROM bedrock_requests 
    WHERE date_only = CURDATE()
    GROUP BY user_id
) today ON u.user_id = today.user_id
LEFT JOIN (
    SELECT 
        user_id,
        COUNT(*) as request_count,
        SUM(cost_usd) as total_cost
    FROM bedrock_requests 
    WHERE date_only >= DATE_FORMAT(NOW(), '%Y-%m-01')
    GROUP BY user_id
) month ON u.user_id = month.user_id;
```

### Stored Procedures

#### 1. CheckUserLimits
```sql
CREATE PROCEDURE CheckUserLimits(
    IN p_user_id VARCHAR(255),
    OUT p_should_block BOOLEAN,
    OUT p_block_reason VARCHAR(500),
    OUT p_daily_usage INT,
    OUT p_monthly_usage INT,
    OUT p_daily_percent DECIMAL(5,2),
    OUT p_monthly_percent DECIMAL(5,2)
)
```

#### 2. LogBedrockRequest
```sql
CREATE PROCEDURE LogBedrockRequest(
    IN p_user_id VARCHAR(255),
    IN p_team VARCHAR(100),
    IN p_model_id VARCHAR(255),
    IN p_model_name VARCHAR(255),
    IN p_request_type VARCHAR(50),
    IN p_input_tokens INT,
    IN p_output_tokens INT,
    IN p_region VARCHAR(50),
    IN p_source_ip VARCHAR(45),
    IN p_user_agent TEXT,
    IN p_session_id VARCHAR(255),
    IN p_request_id VARCHAR(255),
    IN p_response_time_ms INT,
    IN p_status_code INT,
    IN p_error_message TEXT
)
```

**Stored Procedures Script**: `migration/13_update_stored_procedures_for_request_limits_pymysql.sql`

## EventBridge Rules

### 1. bedrock-individual-blocking-monitor

**Purpose**: Trigger usage monitoring on Bedrock API calls

**Event Pattern**:
```json
{
    "source": ["aws.bedrock"],
    "detail-type": ["AWS API Call via CloudTrail"],
    "detail": {
        "eventSource": ["bedrock.amazonaws.com"],
        "eventName": ["InvokeModel", "InvokeModelWithResponseStream"]
    }
}
```

**Target**: Lambda function `bedrock-usage-monitor-enhanced`

**State**: ENABLED

**Creation Script**:
```bash
aws events put-rule \
    --name bedrock-individual-blocking-monitor \
    --event-pattern '{
        "source": ["aws.bedrock"],
        "detail-type": ["AWS API Call via CloudTrail"],
        "detail": {
            "eventSource": ["bedrock.amazonaws.com"],
            "eventName": ["InvokeModel", "InvokeModelWithResponseStream"]
        }
    }' \
    --state ENABLED \
    --description "Monitor Bedrock API calls for usage tracking"
```

### 2. bedrock-individual-daily-reset

**Purpose**: Daily reset of usage counters at midnight UTC

**Schedule Expression**: `cron(0 0 * * ? *)`

**Target**: Lambda function `bedrock-daily-reset`

**State**: ENABLED

**Creation Script**:
```bash
aws events put-rule \
    --name bedrock-individual-daily-reset \
    --schedule-expression "cron(0 0 * * ? *)" \
    --state ENABLED \
    --description "Daily reset for Bedrock usage counters"
```

## CloudWatch Resources

### Log Groups

#### 1. /aws/lambda/bedrock-usage-monitor-enhanced
- **Retention**: 7 days
- **Purpose**: Usage monitor Lambda logs

#### 2. /aws/lambda/bedrock-policy-manager-enhanced
- **Retention**: 7 days
- **Purpose**: Policy manager Lambda logs

#### 3. /aws/lambda/bedrock-daily-reset
- **Retention**: 7 days
- **Purpose**: Daily reset Lambda logs

#### 4. /aws/lambda/bedrock-blocking-history
- **Retention**: 7 days
- **Purpose**: Blocking history Lambda logs

#### 5. /aws/bedrock/user_usage
- **Retention**: 30 days
- **Purpose**: User-specific usage logs

#### 6. /aws/bedrock/team_usage
- **Retention**: 30 days
- **Purpose**: Team-specific usage logs

### Custom Metrics

#### 1. UserMetrics/BedrockUsage
- **Dimensions**: UserId, Team
- **Unit**: Count
- **Purpose**: Track individual user usage

#### 2. TeamMetrics/BedrockUsage
- **Dimensions**: Team
- **Unit**: Count
- **Purpose**: Track team-level usage

#### 3. BlockingMetrics/Operations
- **Dimensions**: Operation, UserId
- **Unit**: Count
- **Purpose**: Track blocking operations

#### 4. CostMetrics/DailyCost
- **Dimensions**: UserId, Team, Model
- **Unit**: None (USD)
- **Purpose**: Track daily costs

### Metric Filters

**User Usage Filter**:
```json
{
    "filterName": "BedrockUserUsageFilter",
    "filterPattern": "[timestamp, requestId, level=\"INFO\", message=\"User*usage*\"]",
    "logGroupName": "/aws/lambda/bedrock-usage-monitor-enhanced",
    "metricTransformations": [
        {
            "metricName": "BedrockUsage",
            "metricNamespace": "UserMetrics",
            "metricValue": "1"
        }
    ]
}
```

## SNS Topics

### bedrock-usage-alerts

**Purpose**: Centralized notification system for all alerts

**Configuration**:
- **Type**: Standard
- **Encryption**: Enabled (AWS managed key)
- **Access Policy**: Allow publish from Lambda functions

**Subscriptions**:
- Email: admin@yourcompany.com
- Additional emails can be added as needed

**Message Types**:
1. **Warning Alerts**: User approaching daily limit
2. **Blocking Alerts**: User automatically blocked
3. **Admin Alerts**: Manual blocking/unblocking operations
4. **System Alerts**: Lambda errors, database issues
5. **Cost Alerts**: Budget threshold exceeded

**Creation Script**:
```bash
aws sns create-topic --name bedrock-usage-alerts

# Subscribe email
aws sns subscribe \
    --topic-arn "arn:aws:sns:eu-west-1:701055077130:bedrock-usage-alerts" \
    --protocol email \
    --notification-endpoint admin@yourcompany.com
```

## SES Configuration

### Email Identity Verification

**Verified Identities**:
- Sender Email: admin@yourcompany.com
- Domain: yourcompany.com (optional)

**Configuration Set**: bedrock-usage-notifications
- **Reputation Tracking**: Enabled
- **Delivery Options**: Enabled
- **Event Publishing**: Enabled

### SMTP Credentials

**SMTP Server**: email-smtp.eu-west-1.amazonaws.com
**Port**: 587 (TLS)
**Authentication**: SMTP credentials

**Credentials Storage**: `individual_blocking_system/lambda_functions/email_credentials.json`

### Email Templates

**Template Types**:
1. **Warning Email**: User approaching limit
2. **Blocking Email**: User blocked notification
3. **Unblocking Email**: User unblocked confirmation
4. **Admin Blocking Email**: Manual admin block
5. **Admin Unblocking Email**: Manual admin unblock

**Template Source**: `individual_blocking_system/lambda_functions/bedrock_email_service.py`

## CloudTrail Configuration

### bedrock-usage-trail

**Purpose**: Capture Bedrock API calls for processing

**Configuration**:
- **Multi-region**: Yes
- **Global Service Events**: Yes
- **Log File Validation**: Yes
- **S3 Bucket**: bedrock-usage-cloudtrail-{ACCOUNT_ID}
- **Event Selectors**: All management and data events

**Data Events**:
- Bedrock InvokeModel
- Bedrock InvokeModelWithResponseStream

**Creation Script**:
```bash
# Create S3 bucket for CloudTrail logs
aws s3 mb s3://bedrock-usage-cloudtrail-$AWS_ACCOUNT_ID

# Create CloudTrail
aws cloudtrail create-trail \
    --name bedrock-usage-trail \
    --s3-bucket-name bedrock-usage-cloudtrail-$AWS_ACCOUNT_ID \
    --include-global-service-events \
    --is-multi-region-trail \
    --enable-log-file-validation

# Start logging
aws cloudtrail start-logging --name bedrock-usage-trail
```

## Secrets Manager

### bedrock-usage-db-credentials

**Purpose**: Store RDS MySQL database credentials securely

**Secret Structure**:
```json
{
    "username": "admin",
    "password": "<GENERATED_PASSWORD>",
    "engine": "mysql",
    "host": "<RDS_ENDPOINT>",
    "port": 3306,
    "dbname": "bedrock_usage"
}
```

**Access Policy**: Lambda functions only

**Rotation**: Manual (can be automated)

**Creation Script**:
```bash
aws secretsmanager create-secret \
    --name bedrock-usage-db-credentials \
    --description "Database credentials for Bedrock Usage Control" \
    --secret-string '{
        "username": "admin",
        "password": "'"$DB_PASSWORD"'",
        "engine": "mysql",
        "host": "'"$RDS_ENDPOINT"'",
        "port": 3306,
        "dbname": "bedrock_usage"
    }'
```

## VPC and Security Groups

### VPC Configuration

**VPC**: Default VPC (can be customized)
**Subnets**: All available subnets in the region
**Internet Gateway**: Default

### Security Groups

#### bedrock-usage-rds-sg

**Purpose**: Security group for RDS MySQL instance

**Inbound Rules**:
- Port 3306 (MySQL) from Lambda security group
- Port 3306 from same security group (self-reference)

**Outbound Rules**:
- All traffic (default)

**Creation Script**:
```bash
# Create security group
SECURITY_GROUP_ID=$(aws ec2 create-security-group \
    --group-name bedrock-usage-rds-sg \
    --description "Security group for Bedrock Usage Control RDS" \
    --vpc-id $VPC_ID \
    --query 'GroupId' --output text)

# Allow MySQL access
aws ec2 authorize-security-group-ingress \
    --group-id $SECURITY_GROUP_ID \
    --protocol tcp \
    --port 3306 \
    --source-group $SECURITY_GROUP_ID
```

### RDS Subnet Group

#### bedrock-usage-subnet-group

**Purpose**: Subnet group for RDS instance placement

**Subnets**: All subnets in default VPC
**Availability Zones**: All AZs in the region

**Creation Script**:
```bash
# Get VPC and subnet information
VPC_ID=$(aws ec2 describe-vpcs --filters "Name=is-default,Values=true" --query 'Vpcs[0].VpcId' --output text)
SUBNET_IDS=$(aws ec2 describe-subnets --filters "Name=vpc-id,Values=$VPC_ID" --query 'Subnets[].SubnetId' --output text)

# Create DB subnet group
aws rds create-db-subnet-group \
    --db-subnet-group-name bedrock-usage-subnet-group \
    --db-subnet-group-description "Subnet group for Bedrock Usage Control RDS" \
    --subnet-ids $SUBNET_IDS
```

## Resource Creation Scripts

### Complete Deployment Scripts

#### 1. Infrastructure Setup
**Script**: `Project documents/Installation Manual/04_Infrastructure_Setup.sh`
**Purpose**: Create all AWS infrastructure resources

#### 2. Lambda Deployment
**Script**: `Project documents/Installation Manual/05_Lambda_Deployment.sh`
**Purpose**: Deploy all Lambda functions with dependencies

#### 3. Database Setup
**Script**: `migration/01_create_rds_instance.sh`
**Purpose**: Create and configure RDS MySQL instance

#### 4. Schema Creation
**Script**: `migration/02_create_database_schema_v2.sql`
**Purpose**: Create database schema, tables, views, and procedures

#### 5. EventBridge Configuration
**Script**: `Project documents/Installation Manual/06_EventBridge_Setup.sh`
**Purpose**: Configure EventBridge rules and targets

#### 6. Monitoring Setup
**Script**: `Project documents/Installation Manual/07_Monitoring_Setup.sh`
**Purpose**: Configure CloudWatch logs, metrics, and alarms

### Individual Resource Scripts

#### IAM Resources
```bash
# Create all IAM roles and policies
./create_iam_resources.sh
```

#### DynamoDB Tables
```bash
# Create DynamoDB tables with proper configuration
./create_dynamodb_tables.sh
```

#### Lambda Functions
```bash
# Package and deploy all Lambda functions
