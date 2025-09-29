#!/bin/bash

# AWS Bedrock Usage Control System - Complete Deployment Script
# This script deploys the entire AWS Bedrock Usage Control System
# 
# Prerequisites:
# - AWS CLI v2.x configured with administrative permissions
# - Python 3.9+
# - MySQL client (optional)
# - jq for JSON processing
#
# Usage: ./04_Complete_Deployment_Script.sh
#
# Author: AWS Bedrock Usage Control System Team
# Version: 2.0.0

set -e  # Exit on any error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
    exit 1
}

info() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] INFO: $1${NC}"
}

# Configuration
export AWS_REGION="${AWS_REGION:-eu-west-1}"
export AWS_ACCOUNT_ID="${AWS_ACCOUNT_ID:-701055077130}"
export PROJECT_NAME="bedrock-usage-control"

# Validate prerequisites
validate_prerequisites() {
    log "Validating prerequisites..."
    
    # Check AWS CLI
    if ! command -v aws &> /dev/null; then
        error "AWS CLI is not installed. Please install AWS CLI v2.x"
    fi
    
    # Check AWS CLI version
    AWS_CLI_VERSION=$(aws --version 2>&1 | cut -d/ -f2 | cut -d' ' -f1)
    if [[ ! $AWS_CLI_VERSION =~ ^2\. ]]; then
        error "AWS CLI v2.x is required. Current version: $AWS_CLI_VERSION"
    fi
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        error "Python 3 is not installed"
    fi
    
    # Check Python version
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    if [[ ! $PYTHON_VERSION =~ ^3\.[9-9]|^3\.[1-9][0-9] ]]; then
        error "Python 3.9+ is required. Current version: $PYTHON_VERSION"
    fi
    
    # Check jq
    if ! command -v jq &> /dev/null; then
        error "jq is not installed. Please install jq for JSON processing"
    fi
    
    # Check AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        error "AWS credentials are not configured or invalid"
    fi
    
    # Get and validate AWS account ID
    CURRENT_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
    if [[ "$CURRENT_ACCOUNT_ID" != "$AWS_ACCOUNT_ID" ]]; then
        warn "Current AWS Account ID ($CURRENT_ACCOUNT_ID) differs from configured ($AWS_ACCOUNT_ID)"
        read -p "Continue with current account? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            error "Deployment cancelled"
        fi
        export AWS_ACCOUNT_ID="$CURRENT_ACCOUNT_ID"
    fi
    
    log "Prerequisites validated successfully"
    info "AWS Account ID: $AWS_ACCOUNT_ID"
    info "AWS Region: $AWS_REGION"
}

# Create IAM roles and policies
create_iam_resources() {
    log "Creating IAM roles and policies..."
    
    # Create temporary policy documents
    mkdir -p temp_policies
    
    # Trust policy for Lambda functions
    cat > temp_policies/lambda-trust-policy.json << 'EOF'
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
EOF

    # Trust policy for dashboard access
    cat > temp_policies/dashboard-trust-policy.json << EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "AWS": "arn:aws:iam::${AWS_ACCOUNT_ID}:root"
            },
            "Action": "sts:AssumeRole"
        }
    ]
}
EOF

    # Usage monitor policy
    cat > temp_policies/usage-monitor-policy.json << EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "DynamoDBAccess",
            "Effect": "Allow",
            "Action": [
                "dynamodb:GetItem",
                "dynamodb:PutItem",
                "dynamodb:UpdateItem",
                "dynamodb:Query",
                "dynamodb:Scan"
            ],
            "Resource": [
                "arn:aws:dynamodb:*:*:table/bedrock_user_daily_usage",
                "arn:aws:dynamodb:*:*:table/bedrock_blocking_operations",
                "arn:aws:dynamodb:*:*:table/bedrock_blocking_operations/index/*"
            ]
        },
        {
            "Sid": "IAMReadAccess",
            "Effect": "Allow",
            "Action": [
                "iam:ListUserTags",
                "iam:GetUser"
            ],
            "Resource": "*"
        },
        {
            "Sid": "SNSPublishAccess",
            "Effect": "Allow",
            "Action": [
                "sns:Publish"
            ],
            "Resource": "arn:aws:sns:*:*:bedrock-usage-alerts"
        },
        {
            "Sid": "SESEmailAccess",
            "Effect": "Allow",
            "Action": [
                "ses:SendEmail",
                "ses:SendRawEmail"
            ],
            "Resource": "*"
        },
        {
            "Sid": "LambdaInvokeAccess",
            "Effect": "Allow",
            "Action": [
                "lambda:InvokeFunction"
            ],
            "Resource": [
                "arn:aws:lambda:*:*:function:bedrock-email-service",
                "arn:aws:lambda:*:*:function:bedrock-mysql-query-executor"
            ]
        },
        {
            "Sid": "SecretsManagerAccess",
            "Effect": "Allow",
            "Action": [
                "secretsmanager:GetSecretValue"
            ],
            "Resource": "arn:aws:secretsmanager:*:*:secret:bedrock-usage-db-credentials-*"
        },
        {
            "Sid": "RDSConnectAccess",
            "Effect": "Allow",
            "Action": [
                "rds-db:connect"
            ],
            "Resource": "arn:aws:rds-db:*:*:dbuser:bedrock-usage-db/admin"
        }
    ]
}
EOF

    # Policy manager policy
    cat > temp_policies/policy-manager-policy.json << 'EOF'
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "DynamoDBAccess",
            "Effect": "Allow",
            "Action": [
                "dynamodb:GetItem",
                "dynamodb:PutItem",
                "dynamodb:UpdateItem",
                "dynamodb:Query"
            ],
            "Resource": [
                "arn:aws:dynamodb:*:*:table/bedrock_user_daily_usage",
                "arn:aws:dynamodb:*:*:table/bedrock_blocking_operations"
            ]
        },
        {
            "Sid": "IAMPolicyManagement",
            "Effect": "Allow",
            "Action": [
                "iam:GetUser",
                "iam:ListAttachedUserPolicies",
                "iam:AttachUserPolicy",
                "iam:DetachUserPolicy",
                "iam:CreatePolicy",
                "iam:GetPolicy",
                "iam:CreatePolicyVersion",
                "iam:DeletePolicyVersion",
                "iam:ListPolicyVersions"
            ],
            "Resource": "*"
        },
        {
            "Sid": "SNSPublishAccess",
            "Effect": "Allow",
            "Action": [
                "sns:Publish"
            ],
            "Resource": "arn:aws:sns:*:*:bedrock-usage-alerts"
        }
    ]
}
EOF

    # Dashboard access policy
    cat > temp_policies/dashboard-access-policy.json << 'EOF'
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "LambdaInvokeAccess",
            "Effect": "Allow",
            "Action": [
                "lambda:InvokeFunction"
            ],
            "Resource": [
                "arn:aws:lambda:*:*:function:bedrock-usage-monitor-enhanced",
                "arn:aws:lambda:*:*:function:bedrock-policy-manager-enhanced",
                "arn:aws:lambda:*:*:function:bedrock-blocking-history"
            ]
        },
        {
            "Sid": "DynamoDBReadAccess",
            "Effect": "Allow",
            "Action": [
                "dynamodb:Query",
                "dynamodb:Scan"
            ],
            "Resource": [
                "arn:aws:dynamodb:*:*:table/bedrock_user_daily_usage",
                "arn:aws:dynamodb:*:*:table/bedrock_blocking_operations"
            ]
        },
        {
            "Sid": "RDSDescribeAccess",
            "Effect": "Allow",
            "Action": [
                "rds:DescribeDBInstances"
            ],
            "Resource": "*"
        }
    ]
}
EOF

    # Create IAM roles
    info "Creating IAM roles..."
    
    aws iam create-role \
        --role-name bedrock-usage-monitor-role \
        --assume-role-policy-document file://temp_policies/lambda-trust-policy.json \
        --description "Execution role for the usage monitoring Lambda function" \
        2>/dev/null || warn "Role bedrock-usage-monitor-role already exists"
    
    aws iam create-role \
        --role-name bedrock-policy-manager-role \
        --assume-role-policy-document file://temp_policies/lambda-trust-policy.json \
        --description "Execution role for the policy management Lambda function" \
        2>/dev/null || warn "Role bedrock-policy-manager-role already exists"
    
    aws iam create-role \
        --role-name bedrock-dashboard-access-role \
        --assume-role-policy-document file://temp_policies/dashboard-trust-policy.json \
        --description "Role for dashboard access to AWS resources" \
        2>/dev/null || warn "Role bedrock-dashboard-access-role already exists"
    
    # Create IAM policies
    info "Creating IAM policies..."
    
    aws iam create-policy \
        --policy-name BedrockUsageMonitorPolicy \
        --policy-document file://temp_policies/usage-monitor-policy.json \
        --description "Permissions for usage monitoring Lambda function" \
        2>/dev/null || warn "Policy BedrockUsageMonitorPolicy already exists"
    
    aws iam create-policy \
        --policy-name BedrockPolicyManagerPolicy \
        --policy-document file://temp_policies/policy-manager-policy.json \
        --description "Permissions for policy management Lambda function" \
        2>/dev/null || warn "Policy BedrockPolicyManagerPolicy already exists"
    
    aws iam create-policy \
        --policy-name BedrockDashboardAccessPolicy \
        --policy-document file://temp_policies/dashboard-access-policy.json \
        --description "Permissions for dashboard access" \
        2>/dev/null || warn "Policy BedrockDashboardAccessPolicy already exists"
    
    # Attach policies to roles
    info "Attaching policies to roles..."
    
    aws iam attach-role-policy \
        --role-name bedrock-usage-monitor-role \
        --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
    
    aws iam attach-role-policy \
        --role-name bedrock-usage-monitor-role \
        --policy-arn arn:aws:iam::${AWS_ACCOUNT_ID}:policy/BedrockUsageMonitorPolicy
    
    aws iam attach-role-policy \
        --role-name bedrock-policy-manager-role \
        --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
    
    aws iam attach-role-policy \
        --role-name bedrock-policy-manager-role \
        --policy-arn arn:aws:iam::${AWS_ACCOUNT_ID}:policy/BedrockPolicyManagerPolicy
    
    aws iam attach-role-policy \
        --role-name bedrock-dashboard-access-role \
        --policy-arn arn:aws:iam::${AWS_ACCOUNT_ID}:policy/BedrockDashboardAccessPolicy
    
    # Clean up temporary files
    rm -rf temp_policies
    
    log "IAM resources created successfully"
}

# Create DynamoDB tables
create_dynamodb_tables() {
    log "Creating DynamoDB tables..."
    
    # Create user daily usage table
    info "Creating bedrock_user_daily_usage table..."
    aws dynamodb create-table \
        --table-name bedrock_user_daily_usage \
        --attribute-definitions \
            AttributeName=user_id,AttributeType=S \
            AttributeName=date,AttributeType=S \
        --key-schema \
            AttributeName=user_id,KeyType=HASH \
            AttributeName=date,KeyType=RANGE \
        --billing-mode PAY_PER_REQUEST \
        --point-in-time-recovery-specification PointInTimeRecoveryEnabled=true \
        2>/dev/null || warn "Table bedrock_user_daily_usage already exists"
    
    # Create blocking operations table
    info "Creating bedrock_blocking_operations table..."
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
            'IndexName=user-date-index,KeySchema=[{AttributeName=user_id,KeyType=HASH},{AttributeName=timestamp,KeyType=RANGE}],Projection={ProjectionType=ALL},ProvisionedThroughput={ReadCapacityUnits=5,WriteCapacityUnits=5}' \
        --billing-mode PAY_PER_REQUEST \
        --point-in-time-recovery-specification PointInTimeRecoveryEnabled=true \
        2>/dev/null || warn "Table bedrock_blocking_operations already exists"
    
    # Wait for tables to be created
    info "Waiting for DynamoDB tables to be active..."
    aws dynamodb wait table-exists --table-name bedrock_user_daily_usage
    aws dynamodb wait table-exists --table-name bedrock_blocking_operations
    
    log "DynamoDB tables created successfully"
}

# Create SNS topic
create_sns_topic() {
    log "Creating SNS topic for notifications..."
    
    # Create SNS topic
    TOPIC_ARN=$(aws sns create-topic --name bedrock-usage-alerts --query 'TopicArn' --output text 2>/dev/null || \
                aws sns list-topics --query 'Topics[?contains(TopicArn, `bedrock-usage-alerts`)].TopicArn' --output text)
    
    if [[ -z "$TOPIC_ARN" ]]; then
        error "Failed to create or find SNS topic"
    fi
    
    info "SNS Topic ARN: $TOPIC_ARN"
    
    # Ask for email subscription
    read -p "Enter email address for notifications (or press Enter to skip): " EMAIL_ADDRESS
    if [[ -n "$EMAIL_ADDRESS" ]]; then
        aws sns subscribe \
            --topic-arn "$TOPIC_ARN" \
            --protocol email \
            --notification-endpoint "$EMAIL_ADDRESS"
        info "Email subscription created. Please check your email and confirm the subscription."
    fi
    
    export SNS_TOPIC_ARN="$TOPIC_ARN"
    log "SNS topic configured successfully"
}

# Create RDS MySQL instance
create_rds_instance() {
    log "Creating RDS MySQL instance..."
    
    # Check if RDS instance already exists
    if aws rds describe-db-instances --db-instance-identifier bedrock-usage-db &>/dev/null; then
        warn "RDS instance bedrock-usage-db already exists"
        RDS_ENDPOINT=$(aws rds describe-db-instances \
            --db-instance-identifier bedrock-usage-db \
            --query 'DBInstances[0].Endpoint.Address' --output text)
        export RDS_ENDPOINT
        return
    fi
    
    # Get VPC information
    VPC_ID=$(aws ec2 describe-vpcs --filters "Name=is-default,Values=true" --query 'Vpcs[0].VpcId' --output text)
    SUBNET_IDS=$(aws ec2 describe-subnets --filters "Name=vpc-id,Values=$VPC_ID" --query 'Subnets[].SubnetId' --output text)
    
    # Create DB subnet group
    info "Creating DB subnet group..."
    aws rds create-db-subnet-group \
        --db-subnet-group-name bedrock-usage-subnet-group \
        --db-subnet-group-description "Subnet group for Bedrock Usage Control RDS" \
        --subnet-ids $SUBNET_IDS \
        2>/dev/null || warn "DB subnet group already exists"
    
    # Create security group
    info "Creating security group for RDS..."
    SECURITY_GROUP_ID=$(aws ec2 create-security-group \
        --group-name bedrock-usage-rds-sg \
        --description "Security group for Bedrock Usage Control RDS" \
        --vpc-id $VPC_ID \
        --query 'GroupId' --output text 2>/dev/null || \
        aws ec2 describe-security-groups \
            --filters "Name=group-name,Values=bedrock-usage-rds-sg" \
            --query 'SecurityGroups[0].GroupId' --output text)
    
    # Allow MySQL access
    aws ec2 authorize-security-group-ingress \
        --group-id $SECURITY_GROUP_ID \
        --protocol tcp \
        --port 3306 \
        --source-group $SECURITY_GROUP_ID \
        2>/dev/null || warn "Security group rule already exists"
    
    # Generate database password
    DB_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
    
    # Create RDS instance
    info "Creating RDS MySQL instance (this will take 10-15 minutes)..."
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
    
    # Wait for RDS instance to be available
    info "Waiting for RDS instance to be available..."
    aws rds wait db-instance-available --db-instance-identifier bedrock-usage-db
    
    # Get RDS endpoint
    RDS_ENDPOINT=$(aws rds describe-db-instances \
        --db-instance-identifier bedrock-usage-db \
        --query 'DBInstances[0].Endpoint.Address' --output text)
    
    # Store credentials in Secrets Manager
    info "Storing database credentials in Secrets Manager..."
    aws secretsmanager create-secret \
        --name bedrock-usage-db-credentials \
        --description "Database credentials for Bedrock Usage Control" \
        --secret-string "{
            \"username\": \"admin\",
            \"password\": \"$DB_PASSWORD\",
            \"engine\": \"mysql\",
            \"host\": \"$RDS_ENDPOINT\",
            \"port\": 3306,
            \"dbname\": \"bedrock_usage\"
        }" \
        2>/dev/null || warn "Secret already exists"
    
    export RDS_ENDPOINT
    export DB_PASSWORD
    
    log "RDS MySQL instance created successfully"
    info "RDS Endpoint: $RDS_ENDPOINT"
}

# Initialize database schema
initialize_database() {
    log "Initializing database schema..."
    
    if [[ -z "$RDS_ENDPOINT" ]]; then
        error "RDS endpoint not available"
    fi
    
    # Check if MySQL client is available
    if command -v mysql &> /dev/null; then
        info "Creating database and schema using MySQL client..."
        
        # Create database
        mysql -h "$RDS_ENDPOINT" -u admin -p"$DB_PASSWORD" -e "CREATE DATABASE IF NOT EXISTS bedrock_usage;" 2>/dev/null || warn "Database creation failed or already exists"
        
        # Run schema creation script if it exists
        if [[ -f "migration/02_create_database_schema_v2.sql" ]]; then
            mysql -h "$RDS_ENDPOINT" -u admin -p"$DB_PASSWORD" bedrock_usage < migration/02_create_database_schema_v2.sql
            info "Database schema created successfully"
        else
            warn "Database schema file not found. Please run the schema creation script manually."
        fi
    else
        warn "MySQL client not available. Please install MySQL client and run the schema creation script manually:"
        info "mysql -h $RDS_ENDPOINT -u admin -p bedrock_usage < migration/02_create_database_schema_v2.sql"
    fi
    
    log "Database initialization completed"
}

# Deploy Lambda functions
deploy_lambda_functions() {
    log "Deploying Lambda functions..."
    
    # Create deployment directory
    mkdir -p lambda_deployments
    
    # Check if Lambda function source files exist
    if [[ ! -d "individual_blocking_system/lambda_functions" ]]; then
        error "Lambda function source directory not found"
    fi
    
    cd individual_blocking_system/lambda_functions
    
    # Package Usage Monitor Lambda
    info "Packaging bedrock-usage-monitor-enhanced..."
    zip -r ../../lambda_deployments/bedrock-usage-monitor.zip \
        bedrock_usage_monitor_enhanced.py \
        bedrock_email_service.py \
        quota_config.json \
        email_credentials.json \
        2>/dev/null || warn "Some files may be missing from the package"
    
    # Package Policy Manager Lambda
    info "Packaging bedrock-policy-manager-enhanced..."
    zip -r ../../lambda_deployments/bedrock-policy-manager.zip \
        bedrock_policy_manager_enhanced.py \
        2>/dev/null
    
    # Package Daily Reset Lambda
    info "Packaging bedrock-daily-reset..."
    zip -r ../../lambda_deployments/bedrock-daily-reset.zip \
        bedrock_daily_reset.py \
        2>/dev/null
    
    # Package Blocking History Lambda
    info "Packaging bedrock-blocking-history..."
    zip -r ../../lambda_deployments/bedrock-blocking-history.zip \
        bedrock_blocking_history.py \
        2>/dev/null
    
    cd ../..
    
    # Deploy Lambda functions
    info "Deploying Lambda functions..."
    
    # Deploy Usage Monitor Lambda
    aws lambda create-function \
        --function-name bedrock-usage-monitor-enhanced \
        --runtime python3.9 \
        --role arn:aws:iam::${AWS_ACCOUNT_ID}:role/bedrock-usage-monitor-role \
        --handler bedrock_usage_monitor_enhanced.lambda_handler \
        --zip-file fileb://lambda_deployments/bedrock-usage-monitor.zip \
        --timeout 60 \
        --memory-size 256 \
        --environment Variables="{
            \"AWS_REGION\":\"$AWS_REGION\",
            \"ACCOUNT_ID\":\"$AWS_ACCOUNT_ID\",
            \"DYNAMODB_TABLE\":\"bedrock_user_daily_usage\",
            \"SNS_TOPIC_ARN\":\"$SNS_TOPIC_ARN\",
            \"EMAIL_NOTIFICATIONS_ENABLED\":\"true\",
            \"RDS_ENDPOINT\":\"$RDS_ENDPOINT\",
            \"DB_SECRET_NAME\":\"bedrock-usage-db-credentials\",
            \"POLICY_MANAGER_FUNCTION\":\"bedrock-policy-manager-enhanced\"
        }" \
        2>/dev/null || warn "Lambda function bedrock-usage-monitor-enhanced already exists"
    
    # Deploy Policy Manager Lambda
    aws lambda create-function \
        --function-name bedrock-policy-manager-enhanced \
        --runtime python3.9 \
        --role arn:aws:iam::${AWS_ACCOUNT_ID}:role/bedrock-policy-manager-role \
        --handler bedrock_policy_manager_enhanced.lambda_handler \
        --zip-file fileb://lambda_deployments/bedrock-policy-manager.zip \
        --timeout 60 \
        --memory-size 256 \
        --environment Variables="{
            \"AWS_REGION\":\"$AWS_REGION\",
            \"ACCOUNT_ID\":\"$AWS_ACCOUNT_ID\",
            \"DYNAMODB_TABLE\":\"bedrock_user_daily_usage\",
            \"BLOCKING_OPERATIONS_TABLE\":\"bedrock_blocking_operations\"
        }" \
        2>/dev/null || warn "Lambda function bedrock-policy-manager-enhanced already exists"
    
    # Deploy Daily Reset Lambda
    aws lambda create-function \
        --function-name bedrock-daily-reset \
        --runtime python3.9 \
        --role arn:aws:iam::${AWS_ACCOUNT_ID}:role/bedrock-usage-monitor-role \
        --handler bedrock_daily_reset.lambda_handler \
        --zip-file fileb://lambda_deployments/bedrock-daily-reset.zip \
        --timeout 300 \
        --memory-size 512 \
        --environment Variables="{
            \"AWS_REGION\":\"$AWS_REGION\",
            \"ACCOUNT_ID\":\"$AWS_ACCOUNT_ID\",
            \"DYNAMODB_TABLE\":\"bedrock_user_daily_usage\",
            \"BLOCKING_OPERATIONS_TABLE\":\"bedrock_blocking_operations\",
            \"POLICY_MANAGER_FUNCTION\":\"bedrock-policy-manager-enhanced\"
        }" \
        2>/dev/null || warn "Lambda function bedrock-daily-reset already exists"
    
    # Deploy Blocking History Lambda
    aws lambda create-function \
        --function-name bedrock-blocking-history \
        --runtime python3.9 \
        --role arn:aws:iam::${AWS_ACCOUNT_ID}:role/bedrock-usage-monitor-role \
        --handler bedrock_blocking_history.lambda_handler \
        --zip-file fileb://lambda_deployments/bedrock-blocking-history.zip \
        --timeout 30 \
        --memory-size 256 \
        --environment Variables="{
            \"AWS_REGION\":\"$AWS_REGION\",
            \"DYNAMODB_TABLE\":\"bedrock_blocking_operations\"
        }" \
        2>/dev/null || warn "Lambda function bedrock-blocking-history already exists"
    
    log "Lambda functions deployed successfully"
}

# Configure EventBridge rules
configure_eventbridge() {
    log "Configuring EventBridge rules..."
    
    # Create rule for Bedrock API calls
    info "Creating EventBridge rule for Bedrock monitoring..."
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
    
    # Create rule for daily reset
    info "Creating EventBridge rule for daily reset..."
    aws events put-rule \
        --name bedrock-individual-daily-reset \
        --schedule-expression "cron(0 0 * * ? *)" \
        --state ENABLED \
        --description "Daily reset for Bedrock usage counters"
    
    # Add Lambda targets to rules
    info "Adding Lambda targets to EventBridge rules..."
    aws events put-targets \
        --rule bedrock-individual-blocking-monitor \
        --targets "Id"="1","Arn"="arn:aws:lambda:$AWS_REGION:$AWS_ACCOUNT_ID:function:bedrock-usage-monitor-enhanced"
    
    aws events put-targets \
        --rule bedrock-individual-daily-reset \
        --targets "Id"="1","Arn"="arn:aws:lambda:$AWS_REGION:$AWS_ACCOUNT_ID:function:bedrock-daily-reset"
    
    # Grant EventBridge permission to invoke Lambda functions
    info "Granting EventBridge permissions..."
    aws lambda add-permission \
        --function-name bedrock-usage-monitor-enhanced \
        --statement-id allow-eventbridge-monitor \
        --action lambda:InvokeFunction \
        --principal events.amazonaws.com \
        --source-arn arn:aws:events:$AWS_REGION:$AWS_ACCOUNT_ID:rule/bedrock-individual-blocking-monitor \
        2>/dev/null || warn "Permission already exists"
    
    aws lambda add-permission \
        --function-name bedrock-daily-reset \
        --statement-id allow-eventbridge-reset \
        --action lambda:InvokeFunction \
        --principal events.amazonaws.com \
        --source-arn arn:aws:events:$AWS_REGION:$AWS_ACCOUNT_ID:rule/bedrock-individual-daily-reset \
        2>/dev/null || warn "Permission already exists"
    
    log "EventBridge rules configured successfully"
}

# Configure CloudTrail
configure_cloudtrail() {
    log "Configuring CloudTrail..."
    
    # Check if CloudTrail already exists
    EXISTING_TRAIL=$(aws cloudtrail describe-trails --query 'trailList[?IsMultiRegionTrail==`true`].Name' --output text)
    
    if [[ -n "$EXISTING_TRAIL" ]]; then
        info "Using existing CloudTrail: $EXISTING_TRAIL"
        return
    fi
    
    # Create S3 bucket for CloudTrail logs
    BUCKET_NAME="bedrock-usage-cloudtrail-${AWS_ACCOUNT_ID}"
    info "Creating S3 bucket for CloudTrail logs..."
    
    aws s3 mb s3://$BUCKET_NAME --region $AWS_REGION 2>/dev/null || warn "S3 bucket already exists"
    
    # Create bucket policy for CloudTrail
    cat > temp_cloudtrail_policy.json << EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "AWSCloudTrailAclCheck",
            "Effect": "Allow",
            "Principal": {
                "Service": "cloudtrail.amazonaws.com"
            },
            "Action": "s3:GetBucketAcl",
            "Resource": "arn:aws:s3:::$BUCKET_NAME"
        },
        {
            "Sid": "AWSCloudTrailWrite",
            "Effect": "Allow",
            "Principal": {
                "Service": "cloudtrail.amazonaws.com"
            },
            "Action": "s3:PutObject",
            "Resource": "arn:aws:s3:::$BUCKET_NAME/*",
            "Condition": {
                "StringEquals": {
                    "s3:x-amz-acl": "bucket-owner-full-control"
                }
            }
        }
    ]
}
EOF
    
    aws s3api put-bucket-policy --bucket $BUCKET_NAME --policy file://temp_cloudtrail_policy.json
    rm temp_cloudtrail_policy.json
    
    # Create CloudTrail
    info "Creating CloudTrail..."
    aws cloudtrail create-trail \
        --name bedrock-usage-trail \
        --s3-bucket-name $BUCKET_NAME \
        --include-global-service-events \
        --is-multi-region-trail \
        --enable-log-file-validation
    
    # Start logging
    aws cloudtrail start-logging --name bedrock-usage-trail
    
    log "CloudTrail configured successfully"
}

# Configure dashboard
configure_dashboard() {
    log "Configuring dashboard..."
    
    # Update dashboard configuration files
    if [[ -f "bedrock_usage_dashboard_modular.html" ]]; then
        info "Updating dashboard configuration..."
        sed -i.bak "s/701055077130/$AWS_ACCOUNT_ID/g" bedrock_usage_dashboard_modular.html
        sed -i.bak "s/eu-west-1/$AWS_REGION/g" bedrock_usage_dashboard_modular.html
        rm -f bedrock_usage_dashboard_modular.html.bak
    fi
    
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
    
    log "Dashboard configured successfully"
    info "Use './launch_dashboard.sh' to start the dashboard server"
}

# Test deployment
test_deployment() {
    log "Testing deployment..."
    
    # Test Lambda functions
    info "Testing Lambda functions..."
    
    # Test Usage Monitor Lambda
    aws lambda invoke \
        --function-name bedrock-usage-monitor-enhanced \
        --payload '{"detail":{"eventSource":"bedrock.amazonaws.com","eventName":"InvokeModel","userIdentity":{"type":"IAMUser","userName":"test_user"}}}' \
        test_response.json &>/dev/null
    
    if [[ $? -eq 0 ]]; then
        info "✓ Usage Monitor Lambda test passed"
    else
        warn "✗ Usage Monitor Lambda test failed"
    fi
    
    # Test Policy Manager Lambda
    aws lambda invoke \
        --function-name bedrock-policy-manager-enhanced \
        --payload '{"action":"check_status","user_id":"test_user"}' \
        test_response.json &>/dev/null
    
    if [[ $? -eq 0 ]]; then
        info "✓ Policy Manager Lambda test passed"
    else
        warn "✗ Policy Manager Lambda test failed"
    fi
    
    # Test DynamoDB tables
    info "Testing DynamoDB tables..."
    
    aws dynamodb describe-table --table-name bedrock_user_daily_usage &>/dev/null
    if [[ $? -eq 0 ]]; then
        info "✓ DynamoDB table bedrock_user_daily_usage is accessible"
    else
        warn "✗ DynamoDB table bedrock_user_daily_usage is not accessible"
    fi
    
    aws dynamodb describe-table --table-name bedrock_blocking_operations &>/dev/null
    if [[ $? -eq 0 ]]; then
        info "✓ DynamoDB table bedrock_blocking_operations is accessible"
    else
        warn "✗ DynamoDB table bedrock_blocking_operations is not accessible"
    fi
    
    # Test RDS connectivity
    if [[ -n "$RDS_ENDPOINT" ]] && command -v mysql &> /dev/null; then
        info "Testing RDS connectivity..."
        if mysql -h "$RDS_ENDPOINT" -u admin -p"$DB_PASSWORD" -e "SELECT 1;" &>/dev/null; then
            info "✓ RDS MySQL connection successful"
        else
            warn "✗ RDS MySQL connection failed"
        fi
    fi
    
    # Clean up test files
    rm -f test_response.json
    
    log "Deployment testing completed"
}

# Generate deployment summary
generate_summary() {
    log "Generating deployment summary..."
    
    cat > deployment_summary.txt << EOF
AWS Bedrock Usage Control System - Deployment Summary

Deployment Date: $(date)
AWS Account ID: $AWS_ACCOUNT_ID
AWS Region: $AWS_REGION

Resources Created:

IAM Roles:
- bedrock-usage-monitor-role
- bedrock-policy-manager-role
- bedrock-dashboard-access-role

IAM Policies:
- BedrockUsageMonitorPolicy
- BedrockPolicyManagerPolicy
- BedrockDashboardAccessPolicy

Lambda Functions:
- bedrock-usage-monitor-enhanced
- bedrock-policy-manager-enhanced
- bedrock-daily-reset
- bedrock-blocking-history

DynamoDB Tables:
- bedrock_user_daily_usage
- bedrock_blocking_operations

RDS Instance:
- bedrock-usage-db (MySQL 8.0.35)
- Endpoint: $RDS_ENDPOINT

SNS Topic:
- bedrock-usage-alerts
- ARN: $SNS_TOPIC_ARN

EventBridge Rules:
- bedrock-individual-blocking-monitor
- bedrock-individual-daily-reset

Secrets Manager:
- bedrock-usage-db-credentials

Next Steps:

1. Start the dashboard:
   ./launch_dashboard.sh

2. Access the dashboard:
   http://localhost:8080/bedrock_usage_dashboard_modular.html

3. Create your first user:
   python3 provision_bedrock_user.py --username <username> --group <team_group>

4. Configure email notifications (if not done during deployment):
   - Verify email addresses in SES
   - Update email_credentials.json in Lambda functions

5. Test the system:
   - Make a Bedrock API call
   - Check the dashboard for usage data
   - Verify blocking functionality

Important Files:
- Dashboard: bedrock_usage_dashboard_modular.html
- User provisioning: provision_bedrock_user.py
- Configuration: quota_config.json
- Launch script: launch_dashboard.sh

For support and documentation, see:
- Project documents/README.md
- Project documents/Installation Manual/

Deployment completed successfully!
EOF

    info "Deployment summary saved to: deployment_summary.txt"
    
    log "Deployment completed successfully!"
    echo
    echo -e "${GREEN}🎉 AWS Bedrock Usage Control System deployed successfully!${NC}"
    echo
    echo -e "${BLUE}Next steps:${NC}"
    echo "1. Start the dashboard: ${GREEN}./launch_dashboard.sh${NC}"
    echo "2. Access: ${GREEN}http://localhost:8080/bedrock_usage_dashboard_modular.html${NC}"
    echo "3. Create users: ${GREEN}python3 provision_bedrock_user.py --username <user> --group <team>${NC}"
    echo
    echo -e "${YELLOW}Important:${NC} Check deployment_summary.txt for complete details"
}

# Main execution
main() {
    echo -e "${GREEN}"
    echo "=========================================="
    echo "AWS Bedrock Usage Control System"
    echo "Complete Deployment Script v2.0.0"
    echo "=========================================="
    echo -e "${NC}"
    
    # Confirm deployment
    echo -e "${YELLOW}This script will deploy the complete AWS Bedrock Usage Control System.${NC}"
    echo -e "${YELLOW}This may incur AWS charges. Continue? (y/N):${NC}"
    read -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        error "Deployment cancelled by user"
    fi
    
    # Execute deployment steps
    validate_prerequisites
    create_iam_resources
    create_dynamodb_tables
    create_sns_topic
    create_rds_instance
    initialize_database
    deploy_lambda_functions
    configure_eventbridge
    configure_cloudtrail
    configure_dashboard
    test_deployment
    generate_summary
}

# Handle script interruption
trap 'error "Deployment interrupted by user"' INT

# Execute main function
main "$@"
