# AWS Bedrock Usage Control System - Complete Installation Manual

## 📋 Table of Contents

1. [Prerequisites & System Requirements](#prerequisites--system-requirements)
2. [AWS Account Setup](#aws-account-setup)
3. [Infrastructure Provisioning](#infrastructure-provisioning)
4. [Database Setup (RDS MySQL)](#database-setup-rds-mysql)
5. [Lambda Functions Deployment](#lambda-functions-deployment)
6. [EventBridge & CloudTrail Configuration](#eventbridge--cloudtrail-configuration)
7. [IAM Roles & Policies Setup](#iam-roles--policies-setup)
8. [Dashboard Configuration](#dashboard-configuration)
9. [Email Notifications Setup](#email-notifications-setup)
10. [Testing & Verification](#testing--verification)
11. [Troubleshooting](#troubleshooting)

## Prerequisites & System Requirements

### Required Tools & Software

```bash
# AWS CLI v2.x
aws --version
# Expected: aws-cli/2.x.x Python/3.x.x

# Python 3.9+
python3 --version
# Expected: Python 3.9.x or higher

# Node.js 16+ (for testing)
node --version
# Expected: v16.x.x or higher

# jq (JSON processor)
jq --version
# Expected: jq-1.6 or higher

# MySQL Client (optional, for database management)
mysql --version
# Expected: mysql Ver 8.0.x or higher
```

### AWS Account Requirements

- **AWS Account ID**: 701055077130 (update in configuration files)
- **Primary Region**: eu-west-1 (Ireland)
- **Administrative Access**: Full IAM permissions required for initial setup
- **Service Limits**: Ensure sufficient limits for Lambda, DynamoDB, RDS

### Estimated Costs

| Service | Monthly Cost (Estimate) | Notes |
|---------|------------------------|-------|
| RDS MySQL (db.t3.micro) | $15-25 | Single-AZ, 20GB storage |
| Lambda Functions | $5-15 | Based on 10K invocations/month |
| DynamoDB | $5-10 | On-demand pricing |
| CloudWatch Logs | $2-5 | 1GB logs/month |
| SNS | $1-2 | Email notifications |
| SES | $1-2 | Email sending |
| **Total** | **$29-59/month** | Varies with usage |

## AWS Account Setup

### 1. Configure AWS CLI

```bash
# Configure AWS CLI with administrative credentials
aws configure
# AWS Access Key ID: [Your Access Key]
# AWS Secret Access Key: [Your Secret Key]
# Default region name: eu-west-1
# Default output format: json

# Verify configuration
aws sts get-caller-identity
```

### 2. Set Environment Variables

```bash
# Create environment configuration
export AWS_REGION="eu-west-1"
export AWS_ACCOUNT_ID="701055077130"
export PROJECT_NAME="bedrock-usage-control"

# Add to your shell profile for persistence
echo 'export AWS_REGION="eu-west-1"' >> ~/.bashrc
echo 'export AWS_ACCOUNT_ID="701055077130"' >> ~/.bashrc
echo 'export PROJECT_NAME="bedrock-usage-control"' >> ~/.bashrc
```

### 3. Enable Required AWS Services

```bash
# Enable Bedrock service (if not already enabled)
aws bedrock list-foundation-models --region eu-west-1

# Verify CloudTrail is enabled
aws cloudtrail describe-trails --region eu-west-1

# Check EventBridge availability
aws events list-rules --region eu-west-1
```

## Infrastructure Provisioning

### 1. Clone and Setup Project

```bash
# Clone the repository
git clone https://github.com/carlossarrion-wq/AWS_BEDROCK_USAGE_CONTROL.git
cd AWS_BEDROCK_USAGE_CONTROL

# Update configuration files with your AWS Account ID
sed -i 's/701055077130/YOUR_ACCOUNT_ID/g' src/config.json
sed -i 's/701055077130/YOUR_ACCOUNT_ID/g' individual_blocking_system/lambda_functions/quota_config.json

# Make scripts executable
chmod +x migration/*.sh
```

### 2. Create Core IAM Roles

```bash
# Create Lambda execution role for usage monitor
aws iam create-role \
    --role-name bedrock-usage-monitor-role \
    --assume-role-policy-document '{
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
    }'

# Create Lambda execution role for policy manager
aws iam create-role \
    --role-name bedrock-policy-manager-role \
    --assume-role-policy-document '{
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
    }'

# Create dashboard access role
aws iam create-role \
    --role-name bedrock-dashboard-access-role \
    --assume-role-policy-document '{
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "AWS": "arn:aws:iam::'"$AWS_ACCOUNT_ID"':root"
                },
                "Action": "sts:AssumeRole"
            }
        ]
    }'
```

### 3. Create CloudWatch Log Groups

```bash
# Create log groups for Lambda functions
aws logs create-log-group --log-group-name /aws/lambda/bedrock-realtime-request-logger
aws logs create-log-group --log-group-name /aws/lambda/bedrock-mysql-query-executor
aws logs create-log-group --log-group-name /aws/lambda/bedrock-usage-monitor-current
aws logs create-log-group --log-group-name /aws/lambda/bedrock-daily-reset
aws logs create-log-group --log-group-name /aws/lambda/bedrock-email-service

# Set retention policy (30 days)
aws logs put-retention-policy --log-group-name /aws/lambda/bedrock-realtime-request-logger --retention-in-days 30
aws logs put-retention-policy --log-group-name /aws/lambda/bedrock-mysql-query-executor --retention-in-days 30
aws logs put-retention-policy --log-group-name /aws/lambda/bedrock-usage-monitor-current --retention-in-days 30
aws logs put-retention-policy --log-group-name /aws/lambda/bedrock-daily-reset --retention-in-days 30
aws logs put-retention-policy --log-group-name /aws/lambda/bedrock-email-service --retention-in-days 30
```

### 4. Create SNS Topic for Notifications

```bash
# Create SNS topic
aws sns create-topic --name bedrock-usage-alerts

# Get topic ARN
TOPIC_ARN=$(aws sns list-topics --query 'Topics[?contains(TopicArn, `bedrock-usage-alerts`)].TopicArn' --output text)
echo "SNS Topic ARN: $TOPIC_ARN"

# Subscribe email for notifications (replace with your email)
aws sns subscribe \
    --topic-arn "$TOPIC_ARN" \
    --protocol email \
    --notification-endpoint admin@yourcompany.com

# Confirm subscription via email
echo "Please check your email and confirm the SNS subscription"
```

## Database Setup (RDS MySQL)

### 1. Create RDS Subnet Group

```bash
# Get VPC ID and subnet IDs
VPC_ID=$(aws ec2 describe-vpcs --filters "Name=is-default,Values=true" --query 'Vpcs[0].VpcId' --output text)
SUBNET_IDS=$(aws ec2 describe-subnets --filters "Name=vpc-id,Values=$VPC_ID" --query 'Subnets[].SubnetId' --output text)

# Create DB subnet group
aws rds create-db-subnet-group \
    --db-subnet-group-name bedrock-usage-subnet-group \
    --db-subnet-group-description "Subnet group for Bedrock Usage Control RDS" \
    --subnet-ids $SUBNET_IDS
```

### 2. Create Security Group for RDS

```bash
# Create security group
SECURITY_GROUP_ID=$(aws ec2 create-security-group \
    --group-name bedrock-usage-rds-sg \
    --description "Security group for Bedrock Usage Control RDS" \
    --vpc-id $VPC_ID \
    --query 'GroupId' --output text)

# Allow MySQL access from Lambda functions (port 3306)
aws ec2 authorize-security-group-ingress \
    --group-id $SECURITY_GROUP_ID \
    --protocol tcp \
    --port 3306 \
    --source-group $SECURITY_GROUP_ID

echo "Security Group ID: $SECURITY_GROUP_ID"
```

### 3. Create RDS MySQL Instance

```bash
# Generate random password
DB_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
echo "Generated DB Password: $DB_PASSWORD"

# Create RDS instance
aws rds create-db-instance \
    --db-instance-identifier bedrock-usage-db \
    --db-instance-class db.t3.micro \
    --engine mysql \
    --engine-version 8.0.35 \
    --master-username admin \
    --master-user-password "$DB_PASSWORD" \
    --allocated-storage 20 \
    --storage-type gp2 \
    --vpc-security-group-ids $SECURITY_GROUP_ID \
    --db-subnet-group-name bedrock-usage-subnet-group \
    --backup-retention-period 7 \
    --storage-encrypted \
    --deletion-protection \
    --enable-performance-insights \
    --performance-insights-retention-period 7

# Wait for RDS instance to be available (this takes 10-15 minutes)
echo "Waiting for RDS instance to be available..."
aws rds wait db-instance-available --db-instance-identifier bedrock-usage-db

# Get RDS endpoint
RDS_ENDPOINT=$(aws rds describe-db-instances \
    --db-instance-identifier bedrock-usage-db \
    --query 'DBInstances[0].Endpoint.Address' --output text)

echo "RDS Endpoint: $RDS_ENDPOINT"
```

### 4. Store Database Credentials in Secrets Manager

```bash
# Create secret for database credentials
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

### 5. Initialize Database Schema

The database schema is now organized in a structured folder hierarchy. You can deploy the complete schema or individual components as needed.

```bash
# Option 1: Create database using the simple creation script
mysql -h $RDS_ENDPOINT -u admin -p"$DB_PASSWORD" < "Project documents/Source/Database/create_database.sql"

# Option 2: Deploy complete schema step by step
# Step 1: Create database
mysql -h $RDS_ENDPOINT -u admin -p"$DB_PASSWORD" < "Project documents/Source/Database/create_database.sql"

# Step 2: Create tables
mysql -h $RDS_ENDPOINT -u admin -p"$DB_PASSWORD" bedrock_usage < "Project documents/Source/Database/Tables/users.sql"
mysql -h $RDS_ENDPOINT -u admin -p"$DB_PASSWORD" bedrock_usage < "Project documents/Source/Database/Tables/bedrock_requests.sql"
mysql -h $RDS_ENDPOINT -u admin -p"$DB_PASSWORD" bedrock_usage < "Project documents/Source/Database/Tables/blocking_operations.sql"
mysql -h $RDS_ENDPOINT -u admin -p"$DB_PASSWORD" bedrock_usage < "Project documents/Source/Database/Tables/model_pricing.sql"

# Step 3: Create views
mysql -h $RDS_ENDPOINT -u admin -p"$DB_PASSWORD" bedrock_usage < "Project documents/Source/Database/Views/v_user_realtime_usage.sql"
mysql -h $RDS_ENDPOINT -u admin -p"$DB_PASSWORD" bedrock_usage < "Project documents/Source/Database/Views/v_hourly_usage.sql"
mysql -h $RDS_ENDPOINT -u admin -p"$DB_PASSWORD" bedrock_usage < "Project documents/Source/Database/Views/v_model_usage_stats.sql"
mysql -h $RDS_ENDPOINT -u admin -p"$DB_PASSWORD" bedrock_usage < "Project documents/Source/Database/Views/v_team_usage_dashboard.sql"
mysql -h $RDS_ENDPOINT -u admin -p"$DB_PASSWORD" bedrock_usage < "Project documents/Source/Database/Views/v_last_10_days_usage.sql"

# Step 4: Create stored procedures
mysql -h $RDS_ENDPOINT -u admin -p"$DB_PASSWORD" bedrock_usage < "Project documents/Source/Database/Stored_Procedures/CheckUserLimits.sql"
mysql -h $RDS_ENDPOINT -u admin -p"$DB_PASSWORD" bedrock_usage < "Project documents/Source/Database/Stored_Procedures/LogBedrockRequest.sql"
mysql -h $RDS_ENDPOINT -u admin -p"$DB_PASSWORD" bedrock_usage < "Project documents/Source/Database/Stored_Procedures/ExecuteUserBlocking.sql"
mysql -h $RDS_ENDPOINT -u admin -p"$DB_PASSWORD" bedrock_usage < "Project documents/Source/Database/Stored_Procedures/ExecuteUserUnblocking.sql"

# Step 5: Create additional indexes
mysql -h $RDS_ENDPOINT -u admin -p"$DB_PASSWORD" bedrock_usage < "Project documents/Source/Database/Indexes/additional_indexes.sql"

# Verify tables were created
mysql -h $RDS_ENDPOINT -u admin -p"$DB_PASSWORD" bedrock_usage -e "SHOW TABLES;"

# Verify views were created
mysql -h $RDS_ENDPOINT -u admin -p"$DB_PASSWORD" bedrock_usage -e "SHOW FULL TABLES WHERE Table_type = 'VIEW';"

# Verify stored procedures were created
mysql -h $RDS_ENDPOINT -u admin -p"$DB_PASSWORD" bedrock_usage -e "SHOW PROCEDURE STATUS WHERE Db = 'bedrock_usage';"
```

### Database Structure

The database components are organized as follows:
- **Tables/**: Core database tables (users, bedrock_requests, blocking_operations, model_pricing)
- **Views/**: Optimized views for dashboard queries and analytics
- **Stored_Procedures/**: Business logic procedures for blocking and logging
- **Indexes/**: Additional performance optimization indexes
- **create_database.sql**: Simple database creation script

For detailed information about each component, see `Project documents/Source/Database/README.md`.

## Lambda Functions Deployment

### 1. Prepare Lambda Deployment Packages

```bash
# Create deployment directory
mkdir -p lambda_deployments

# Package Realtime Request Logger Lambda (with PyMySQL dependencies)
cd migration
zip -r ../lambda_deployments/bedrock-realtime-request-logger.zip \
    lambda_package_cet_fixed/lambda_function.py \
    lambda_package_cet_fixed/pymysql/

# Package MySQL Query Executor Lambda
zip -r ../lambda_deployments/bedrock-mysql-query-executor.zip \
    mysql_query_executor_lambda.py

# Package Usage Monitor Lambda
cd ../individual_blocking_system/lambda_functions
zip -r ../../lambda_deployments/bedrock-usage-monitor-current.zip \
    bedrock_usage_monitor_current.py \
    quota_config.json

# Package Daily Reset Lambda (RDS MySQL version)
zip -r ../../lambda_deployments/bedrock-daily-reset.zip \
    bedrock_daily_reset.py \
    quota_config.json

# Package Email Service Lambda (Enhanced Version)
zip -r ../../lambda_deployments/bedrock-email-service.zip \
    lambda_handler.py \
    bedrock_email_service.py \
    email_credentials.json

cd ../..
```

### 1.1. Automated Daily Reset Lambda Deployment

For the Daily Reset Lambda function, you can use the automated deployment script:

```bash
# Navigate to the Lambda Functions directory
cd "Project documents/Source/Lambda Functions"

# Make the deployment script executable
chmod +x deploy_bedrock_daily_reset.sh

# Run the automated deployment
./deploy_bedrock_daily_reset.sh
```

**What the script does:**
- Creates deployment package automatically
- Deploys or updates the Lambda function
- Configures environment variables
- Sets up CloudWatch Events rule for daily execution at 00:00 CET
- Configures permissions and targets
- Provides deployment verification

**Script Features:**
- **Automatic Detection**: Checks if function exists and updates or creates accordingly
- **Environment Configuration**: Sets all required environment variables
- **Scheduling**: Configures daily execution at 00:00 CET (23:00 UTC)
- **Permissions**: Grants CloudWatch Events permission to invoke the function
- **Verification**: Checks deployment status and provides summary
- **Error Handling**: Includes error checking and cleanup

**Manual Alternative**: If you prefer manual deployment, continue with the steps below.

### 2. Create Lambda Functions

```bash
# Deploy Realtime Request Logger Lambda
aws lambda create-function \
    --function-name bedrock-realtime-request-logger \
    --runtime python3.9 \
    --role arn:aws:iam::$AWS_ACCOUNT_ID:role/bedrock-usage-monitor-role \
    --handler lambda_function.lambda_handler \
    --zip-file fileb://lambda_deployments/bedrock-realtime-request-logger.zip \
    --timeout 60 \
    --memory-size 256 \
    --environment Variables='{
        "RDS_ENDPOINT":"'"$RDS_ENDPOINT"'",
        "RDS_USERNAME":"admin",
        "RDS_PASSWORD":"'"$DB_PASSWORD"'",
        "RDS_DATABASE":"bedrock_usage",
        "AWS_REGION":"'"$AWS_REGION"'",
        "ACCOUNT_ID":"'"$AWS_ACCOUNT_ID"'",
        "EMAIL_SERVICE_FUNCTION":"bedrock-email-service"
    }'

# Deploy MySQL Query Executor Lambda
aws lambda create-function \
    --function-name bedrock-mysql-query-executor \
    --runtime python3.9 \
    --role arn:aws:iam::$AWS_ACCOUNT_ID:role/bedrock-usage-monitor-role \
    --handler mysql_query_executor_lambda.lambda_handler \
    --zip-file fileb://lambda_deployments/bedrock-mysql-query-executor.zip \
    --timeout 30 \
    --memory-size 256 \
    --environment Variables='{
        "RDS_ENDPOINT":"'"$RDS_ENDPOINT"'",
        "RDS_USERNAME":"admin",
        "RDS_PASSWORD":"'"$DB_PASSWORD"'",
        "RDS_DATABASE":"bedrock_usage"
    }'

# Deploy Usage Monitor Lambda (Current Version)
aws lambda create-function \
    --function-name bedrock-usage-monitor-current \
    --runtime python3.9 \
    --role arn:aws:iam::$AWS_ACCOUNT_ID:role/bedrock-usage-monitor-role \
    --handler bedrock_usage_monitor_current.lambda_handler \
    --zip-file fileb://lambda_deployments/bedrock-usage-monitor-current.zip \
    --timeout 60 \
    --memory-size 256 \
    --environment Variables='{
        "AWS_REGION":"'"$AWS_REGION"'",
        "ACCOUNT_ID":"'"$AWS_ACCOUNT_ID"'",
        "RDS_ENDPOINT":"'"$RDS_ENDPOINT"'",
        "RDS_USERNAME":"admin",
        "RDS_PASSWORD":"'"$DB_PASSWORD"'",
        "RDS_DATABASE":"bedrock_usage",
        "EMAIL_SERVICE_FUNCTION":"bedrock-email-service"
    }'

# Deploy Daily Reset Lambda (RDS MySQL Version)
aws lambda create-function \
    --function-name bedrock-daily-reset \
    --runtime python3.9 \
    --role arn:aws:iam::$AWS_ACCOUNT_ID:role/bedrock-usage-monitor-role \
    --handler bedrock_daily_reset.lambda_handler \
    --zip-file fileb://lambda_deployments/bedrock-daily-reset.zip \
    --timeout 300 \
    --memory-size 512 \
    --environment Variables='{
        "AWS_REGION":"'"$AWS_REGION"'",
        "ACCOUNT_ID":"'"$AWS_ACCOUNT_ID"'",
        "RDS_ENDPOINT":"'"$RDS_ENDPOINT"'",
        "RDS_USERNAME":"admin",
        "RDS_PASSWORD":"'"$DB_PASSWORD"'",
        "RDS_DATABASE":"bedrock_usage",
        "EMAIL_SERVICE_FUNCTION":"bedrock-email-service"
    }'

# Deploy Email Service Lambda
aws lambda create-function \
    --function-name bedrock-email-service \
    --runtime python3.9 \
    --role arn:aws:iam::$AWS_ACCOUNT_ID:role/bedrock-usage-monitor-role \
    --handler lambda_handler.lambda_handler \
    --zip-file fileb://lambda_deployments/bedrock-email-service.zip \
    --timeout 30 \
    --memory-size 256 \
    --environment Variables='{
        "AWS_REGION":"'"$AWS_REGION"'"
    }'
```

### 3. Attach IAM Policies to Lambda Roles

```bash
# Attach basic Lambda execution policy
aws iam attach-role-policy \
    --role-name bedrock-usage-monitor-role \
    --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole

aws iam attach-role-policy \
    --role-name bedrock-policy-manager-role \
    --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole

# Create and attach custom policies (see IAM section below)
```

### 4. Create Daily Reset Role with Enhanced Permissions

**CRITICAL**: The bedrock-daily-reset Lambda function requires additional IAM permissions to modify user policies and invoke other Lambda functions. Create a dedicated role with enhanced permissions:

```bash
# Create Daily Reset Lambda execution role
aws iam create-role \
    --role-name bedrock-daily-reset-role \
    --assume-role-policy-document '{
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
    }'

# Create enhanced policy for daily reset function
cat > bedrock-daily-reset-policy.json << 'EOF'
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "logs:CreateLogGroup",
                "logs:CreateLogStream", 
                "logs:PutLogEvents"
            ],
            "Resource": "arn:aws:logs:eu-west-1:701055077130:*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "iam:GetUserPolicy",
                "iam:PutUserPolicy", 
                "iam:DeleteUserPolicy"
            ],
            "Resource": "arn:aws:iam::701055077130:user/*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "lambda:InvokeFunction"
            ],
            "Resource": [
                "arn:aws:lambda:eu-west-1:701055077130:function:bedrock-email-service",
                "arn:aws:lambda:eu-west-1:701055077130:function:bedrock-policy-manager-enhanced"
            ]
        },
        {
            "Effect": "Allow",
            "Action": [
                "sns:Publish"
            ],
            "Resource": "arn:aws:sns:eu-west-1:701055077130:bedrock-usage-alerts"
        }
    ]
}
EOF

# Create the policy
aws iam create-policy \
    --policy-name BedrockDailyResetPolicy \
    --policy-document file://bedrock-daily-reset-policy.json

# Attach policies to daily reset role
aws iam attach-role-policy \
    --role-name bedrock-daily-reset-role \
    --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole

aws iam attach-role-policy \
    --role-name bedrock-daily-reset-role \
    --policy-arn arn:aws:iam::$AWS_ACCOUNT_ID:policy/BedrockDailyResetPolicy

# Update Daily Reset Lambda to use the correct role
aws lambda update-function-configuration \
    --function-name bedrock-daily-reset \
    --role arn:aws:iam::$AWS_ACCOUNT_ID:role/bedrock-daily-reset-role

echo "✅ Daily Reset Lambda role updated with enhanced IAM permissions"
```

**Why This Fix Is Critical:**
- The daily reset function needs to modify IAM user policies to remove blocking deny statements
- Without `iam:GetUserPolicy`, `iam:PutUserPolicy`, and `iam:DeleteUserPolicy` permissions, the function cannot unblock users at the IAM level
- This was the root cause of the SAP_004 issue where the database was updated but the IAM policy remained blocked
- The function also needs `lambda:InvokeFunction` permission to send email notifications

**Troubleshooting IAM Permission Issues:**
If you encounter IAM permission errors in CloudWatch logs like:
```
AccessDenied when calling the GetUserPolicy operation: 
User is not authorized to perform: iam:GetUserPolicy
```

This indicates the Lambda execution role lacks the required IAM permissions. Apply the fix above to resolve the issue.

## EventBridge & CloudTrail Configuration

### 1. Create EventBridge Rules

```bash
# Create rule for Bedrock API calls
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

# Create rule for daily reset (runs at 00:00 UTC)
aws events put-rule \
    --name bedrock-individual-daily-reset \
    --schedule-expression "cron(0 0 * * ? *)" \
    --state ENABLED \
    --description "Daily reset for Bedrock usage counters"

# Add Lambda targets to rules
aws events put-targets \
    --rule bedrock-individual-blocking-monitor \
    --targets "Id"="1","Arn"="arn:aws:lambda:$AWS_REGION:$AWS_ACCOUNT_ID:function:bedrock-realtime-request-logger"

aws events put-targets \
    --rule bedrock-individual-daily-reset \
    --targets "Id"="1","Arn"="arn:aws:lambda:$AWS_REGION:$AWS_ACCOUNT_ID:function:bedrock-daily-reset"
```

### 2. Grant EventBridge Permission to Invoke Lambda

```bash
# Grant permission for EventBridge to invoke realtime request logger
aws lambda add-permission \
    --function-name bedrock-realtime-request-logger \
    --statement-id allow-eventbridge-monitor \
    --action lambda:InvokeFunction \
    --principal events.amazonaws.com \
    --source-arn arn:aws:events:$AWS_REGION:$AWS_ACCOUNT_ID:rule/bedrock-individual-blocking-monitor

# Grant permission for EventBridge to invoke daily reset
aws lambda add-permission \
    --function-name bedrock-daily-reset \
    --statement-id allow-eventbridge-reset \
    --action lambda:InvokeFunction \
    --principal events.amazonaws.com \
    --source-arn arn:aws:events:$AWS_REGION:$AWS_ACCOUNT_ID:rule/bedrock-individual-daily-reset
```

### 3. Verify CloudTrail Configuration

```bash
# Check if CloudTrail is logging Bedrock events
aws cloudtrail describe-trails --query 'trailList[?IsMultiRegionTrail==`true`]'

# If no multi-region trail exists, create one
aws cloudtrail create-trail \
    --name bedrock-usage-trail \
    --s3-bucket-name bedrock-usage-cloudtrail-$AWS_ACCOUNT_ID \
    --include-global-service-events \
    --is-multi-region-trail \
    --enable-log-file-validation

# Start logging
aws cloudtrail start-logging --name bedrock-usage-trail
```

## IAM Roles & Policies Setup

### 1. Create Custom IAM Policies

Create the usage monitor policy:

```bash
# Create policy document for usage monitor
cat > usage-monitor-policy.json << 'EOF'
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "rds-db:connect"
            ],
            "Resource": "arn:aws:rds-db:*:*:dbuser:bedrock-usage-db/admin"
        },
        {
            "Effect": "Allow",
            "Action": [
                "secretsmanager:GetSecretValue"
            ],
            "Resource": "arn:aws:secretsmanager:*:*:secret:bedrock-usage-db-credentials-*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "iam:ListUserTags",
                "iam:GetUser"
            ],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "sns:Publish"
            ],
            "Resource": "arn:aws:sns:*:*:bedrock-usage-alerts"
        },
        {
            "Effect": "Allow",
            "Action": [
                "ses:SendEmail",
                "ses:SendRawEmail"
            ],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "lambda:InvokeFunction"
            ],
            "Resource": [
                "arn:aws:lambda:*:*:function:bedrock-email-service",
                "arn:aws:lambda:*:*:function:bedrock-mysql-query-executor"
            ]
        }
    ]
}
EOF

# Create the policy
aws iam create-policy \
    --policy-name BedrockUsageMonitorPolicy \
    --policy-document file://usage-monitor-policy.json

# Attach to role
aws iam attach-role-policy \
    --role-name bedrock-usage-monitor-role \
    --policy-arn arn:aws:iam::$AWS_ACCOUNT_ID:policy/BedrockUsageMonitorPolicy
```

Create the MySQL query executor policy:

```bash
# Create policy document for MySQL query executor
cat > mysql-query-executor-policy.json << 'EOF'
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "rds-db:connect"
            ],
            "Resource": "arn:aws:rds-db:*:*:dbuser:bedrock-usage-db/admin"
        },
        {
            "Effect": "Allow",
            "Action": [
                "secretsmanager:GetSecretValue"
            ],
            "Resource": "arn:aws:secretsmanager:*:*:secret:bedrock-usage-db-credentials-*"
        }
    ]
}
EOF

# Create the policy
aws iam create-policy \
    --policy-name BedrockMySQLQueryExecutorPolicy \
    --policy-document file://mysql-query-executor-policy.json

# Attach to role
aws iam attach-role-policy \
    --role-name bedrock-usage-monitor-role \
    --policy-arn arn:aws:iam::$AWS_ACCOUNT_ID:policy/BedrockMySQLQueryExecutorPolicy
```

Create the dashboard access policy:

```bash
# Create policy document for dashboard
cat > dashboard-access-policy.json << 'EOF'
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "lambda:InvokeFunction"
            ],
            "Resource": [
                "arn:aws:lambda:*:*:function:bedrock-mysql-query-executor",
                "arn:aws:lambda:*:*:function:bedrock-usage-monitor-current",
                "arn:aws:lambda:*:*:function:bedrock-email-service"
            ]
        },
        {
            "Effect": "Allow",
            "Action": [
                "secretsmanager:GetSecretValue"
            ],
            "Resource": "arn:aws:secretsmanager:*:*:secret:bedrock-usage-db-credentials-*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "rds:DescribeDBInstances"
            ],
            "Resource": "*"
        }
    ]
}
EOF

# Create the policy
aws iam create-policy \
    --policy-name BedrockDashboardAccessPolicy \
    --policy-document file://dashboard-access-policy.json

# Attach to role
aws iam attach-role-policy \
    --role-name bedrock-dashboard-access-role \
    --policy-arn arn:aws:iam::$AWS_ACCOUNT_ID:policy/BedrockDashboardAccessPolicy
```

## Dashboard Configuration

### 1. Update Dashboard Configuration

```bash
# Update dashboard configuration with your AWS Account ID and region
sed -i 's/701055077130/'"$AWS_ACCOUNT_ID"'/g' bedrock_usage_dashboard_modular.html
sed -i 's/eu-west-1/'"$AWS_REGION"'/g' bedrock_usage_dashboard_modular.html

# Update quota configuration
cp individual_blocking_system/lambda_functions/quota_config.json ./quota_config.json
```

### 2. Configure Web Server

```bash
# Install Python HTTP server (if not available)
python3 -m http.server --help

# Create launch script
cat > launch_dashboard.sh << 'EOF'
#!/bin/bash
echo "Starting Bedrock Usage Control Dashboard..."
echo "Dashboard will be available at: http://localhost:8080/bedrock_usage_dashboard_modular.html"
echo "Login page available at: http://localhost:8080/login.html"
echo ""
echo "Press Ctrl+C to stop the server"
python3 -m http.server 8080
EOF

chmod +x launch_dashboard.sh
```

### 3. Test Dashboard Access

```bash
# Start the dashboard server
./launch_dashboard.sh &

# Test dashboard accessibility
curl -s http://localhost:8080/bedrock_usage_dashboard_modular.html | head -n 5

# Stop the server
pkill -f "python3 -m http.server"
```

## Email Notifications Setup

### 1. Enhanced Email Service Configuration

The system now includes a sophisticated email service with professional HTML templates and CSS styling.

#### Email Service Features:
- **Professional Templates**: HTML/CSS with responsive design
- **Color-Coded Notifications**: 
  - 🟡 Amber (#F4B860): Warning emails (80% quota reached)
  - 🔴 Light Red (#EC7266): Blocking emails
  - 🟢 Green (#9CD286): Unblocking emails
- **Visual Elements**: Progress bars, statistics cards, professional typography
- **Multi-Type Support**: Warning, blocking, unblocking, admin notifications

### 2. Configure Email Service

```bash
# Update email credentials for enhanced service
cat > email_credentials_enhanced.json << 'EOF'
{
  "gmail_smtp": {
    "server": "smtp.gmail.com",
    "port": 587,
    "user": "your-email@gmail.com",
    "password": "your-app-password",
    "use_tls": true
  },
  "email_settings": {
    "default_language": "es",
    "timezone": "Europe/Madrid",
    "reply_to": "your-email@gmail.com"
  }
}
EOF

# Copy to Lambda function directory
cp email_credentials_enhanced.json "02. Source/Lambda Functions/email_credentials.json"
```

### 3. Deploy Enhanced Email Service

```bash
# Use the automated deployment script for email service
cd "02. Source/Lambda Functions"
chmod +x deploy_email_service_fix.sh
./deploy_email_service_fix.sh
```

**What the deployment script does:**
- Creates proper `lambda_handler.py` entry point
- Packages `bedrock_email_service.py` with enhanced templates
- Includes email credentials configuration
- Updates Lambda function with correct handler
- Verifies deployment success

### 4. Test Enhanced Email Service

```bash
# Test the enhanced email service integration
python3 test_email_integration.py

# Expected output:
# 📊 TEST SUMMARY
# Direct Email Service: ✅ PASS
# Controller Integration: ✅ PASS
# 🎉 All tests PASSED! Email integration is working correctly.
```

### 5. Email Template Examples

The enhanced email service provides professional templates:

#### Blocking Email Template:
- Professional header with color-coded background
- Usage statistics with visual progress indicators
- Clear action items and next steps
- Responsive design for all devices

#### Unblocking Email Template:
- Success-themed green color scheme
- Clear restoration confirmation
- Usage guidelines and best practices
- Professional footer with system information

### 6. Configure SES (Alternative to Gmail)

```bash
# If using SES instead of Gmail SMTP
aws ses verify-email-identity --email-address admin@yourcompany.com

# Check verification status
aws ses get-identity-verification-attributes --identities admin@yourcompany.com

# Update email credentials for SES
cat > email_credentials_ses.json << 'EOF'
{
  "ses_config": {
    "region": "eu-west-1",
    "sender_email": "admin@yourcompany.com",
    "sender_name": "Bedrock Usage Control System"
  },
  "email_settings": {
    "default_language": "es",
    "timezone": "Europe/Madrid"
  }
}
EOF
```

### 7. Troubleshooting Email Issues

```bash
# Check email service logs
aws logs tail /aws/lambda/bedrock-email-service --follow

# Test email service directly
aws lambda invoke \
    --function-name bedrock-email-service \
    --payload '{"action": "send_blocking_email", "user_id": "test_user", "usage_record": {"request_count": 350, "daily_limit": 350, "team": "test_team"}, "reason": "Daily limit exceeded"}' \
    email_test_response.json

# Check response
cat email_test_response.json
```

## Testing & Verification

### 1. Test Lambda Functions

```bash
# Test Realtime Request Logger Lambda
aws lambda invoke \
    --function-name bedrock-realtime-request-logger \
    --payload file://test_bedrock_payload.json \
    response.json

cat response.json

# Test MySQL Query Executor Lambda
aws lambda invoke \
    --function-name bedrock-mysql-query-executor \
    --payload '{"query_type":"get_user_usage","user_id":"test_user"}' \
    response.json

cat response.json

# Test Usage Monitor Current Lambda
aws lambda invoke \
    --function-name bedrock-usage-monitor-current \
    --payload '{"action":"check_status","user_id":"test_user"}' \
    response.json

cat response.json
```

### 2. Test EventBridge Rules

```bash
# List EventBridge rules
aws events list-rules --name-prefix bedrock-individual

# Test rule by creating a test event
aws events put-events \
    --entries '[{
        "Source": "aws.bedrock",
        "DetailType": "AWS API Call via CloudTrail",
        "Detail": "{\"eventSource\":\"bedrock.amazonaws.com\",\"eventName\":\"InvokeModel\",\"userIdentity\":{\"type\":\"IAMUser\",\"userName\":\"test_user\"}}"
    }]'
```

### 3. Test Database Connectivity

```bash
# Test database connection
mysql -h $RDS_ENDPOINT -u admin -p"$DB_PASSWORD" bedrock_usage -e "SELECT COUNT(*) FROM users;"

# Test stored procedures
mysql -h $RDS_ENDPOINT -u admin -p"$DB_PASSWORD" bedrock_usage -e "CALL CheckUserLimits('test_user', @should_block, @reason, @daily, @monthly, @daily_pct, @monthly_pct); SELECT @should_block, @reason;"
```

### 4. End-to-End Testing

```bash
# Run comprehensive test suite
python3 test_enhanced_blocking.py

# Check CloudWatch logs
aws logs describe-log-groups --log-group-name-prefix /aws/lambda/bedrock

# Monitor metrics
aws cloudwatch get-metric-statistics \
    --namespace AWS/Lambda \
    --metric-name Invocations \
    --dimensions Name=FunctionName,Value=bedrock-usage-monitor-enhanced \
    --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
    --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
    --period 300 \
    --statistics Sum
```

## Troubleshooting

### Common Issues and Solutions

#### 1. Lambda Function Timeout Errors

```bash
# Increase timeout for Lambda functions
aws lambda update-function-configuration \
    --function-name bedrock-realtime-request-logger \
    --timeout 120

# Check CloudWatch logs for detailed error messages
aws logs tail /aws/lambda/bedrock-realtime-request-logger --follow
```

#### 2. Database Connection Issues

```bash
# Check RDS instance status
aws rds
