#!/bin/bash

# Deploy Real-time Bedrock Request Logger
# This script deploys the Lambda function that processes CloudTrail events in real-time

set -e

echo "🚀 Deploying Real-time Bedrock Request Logger..."

# Configuration
FUNCTION_NAME="bedrock-realtime-request-logger"
REGION="eu-west-1"
ROLE_NAME="BedrockRealtimeLoggerRole"
POLICY_NAME="BedrockRealtimeLoggerPolicy"
CLOUDTRAIL_NAME="bedrock-realtime-trail"
S3_BUCKET_NAME="bedrock-cloudtrail-logs-$(date +%s)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if AWS CLI is configured
if ! aws sts get-caller-identity &> /dev/null; then
    print_error "AWS CLI is not configured. Please run 'aws configure' first."
    exit 1
fi

# Get account ID
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
print_status "Using AWS Account: $ACCOUNT_ID"

# Create S3 bucket for CloudTrail logs
echo "📦 Creating S3 bucket for CloudTrail logs..."
aws s3 mb s3://$S3_BUCKET_NAME --region $REGION || {
    print_warning "S3 bucket might already exist or there was an error"
}

# Create bucket policy for CloudTrail
cat > /tmp/cloudtrail-bucket-policy.json << EOF
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
            "Resource": "arn:aws:s3:::$S3_BUCKET_NAME"
        },
        {
            "Sid": "AWSCloudTrailWrite",
            "Effect": "Allow",
            "Principal": {
                "Service": "cloudtrail.amazonaws.com"
            },
            "Action": "s3:PutObject",
            "Resource": "arn:aws:s3:::$S3_BUCKET_NAME/*",
            "Condition": {
                "StringEquals": {
                    "s3:x-amz-acl": "bucket-owner-full-control"
                }
            }
        }
    ]
}
EOF

aws s3api put-bucket-policy --bucket $S3_BUCKET_NAME --policy file:///tmp/cloudtrail-bucket-policy.json
print_status "S3 bucket policy applied"

# Create IAM role for Lambda function
echo "🔐 Creating IAM role for Lambda function..."
cat > /tmp/lambda-trust-policy.json << EOF
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

# Create the role
aws iam create-role \
    --role-name $ROLE_NAME \
    --assume-role-policy-document file:///tmp/lambda-trust-policy.json \
    --description "Role for Bedrock real-time request logger Lambda function" || {
    print_warning "Role might already exist"
}

# Create IAM policy for Lambda function
cat > /tmp/lambda-policy.json << EOF
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
            "Resource": "arn:aws:logs:*:*:*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "rds:DescribeDBInstances",
                "rds:Connect"
            ],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "iam:GetUser",
                "iam:ListGroupsForUser",
                "iam:GetGroup"
            ],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "bedrock:GetModelInvocationLoggingConfiguration",
                "bedrock:ListFoundationModels"
            ],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "iam:AttachUserPolicy",
                "iam:DetachUserPolicy",
                "iam:PutUserPolicy",
                "iam:DeleteUserPolicy"
            ],
            "Resource": "arn:aws:iam::*:user/*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "secretsmanager:GetSecretValue"
            ],
            "Resource": "arn:aws:secretsmanager:*:*:secret:rds-db-credentials/*"
        }
    ]
}
EOF

aws iam put-role-policy \
    --role-name $ROLE_NAME \
    --policy-name $POLICY_NAME \
    --policy-document file:///tmp/lambda-policy.json

print_status "IAM role and policy created"

# Wait for role to be available
echo "⏳ Waiting for IAM role to be available..."
sleep 10

# Create deployment package
echo "📦 Creating deployment package..."
cp lambda_function_cloudwatch_logs.py lambda_function.py

# Install dependencies
pip3 install pymysql -t .
zip -r realtime-logger-deployment.zip lambda_function.py pymysql/

# Deploy Lambda function
echo "🚀 Deploying Lambda function..."
aws lambda create-function \
    --function-name $FUNCTION_NAME \
    --runtime python3.9 \
    --role arn:aws:iam::$ACCOUNT_ID:role/$ROLE_NAME \
    --handler lambda_function.lambda_handler \
    --zip-file fileb://realtime-logger-deployment.zip \
    --timeout 300 \
    --memory-size 512 \
    --description "Real-time Bedrock request logger and usage monitor" || {
    print_warning "Lambda function might already exist, updating..."
    aws lambda update-function-code \
        --function-name $FUNCTION_NAME \
        --zip-file fileb://realtime-logger-deployment.zip
}

# Set environment variables separately
aws lambda update-function-configuration \
    --function-name $FUNCTION_NAME \
    --environment 'Variables={"RDS_ENDPOINT":"bedrock-usage-mysql.czuimyk2qu10.eu-west-1.rds.amazonaws.com","RDS_DATABASE":"bedrock_usage","RDS_USERNAME":"admin","RDS_PASSWORD":"BedrockUsage2024!"}'

print_status "Lambda function deployed"

# Create CloudTrail
echo "🛤️  Creating CloudTrail for real-time monitoring..."
aws cloudtrail create-trail \
    --name $CLOUDTRAIL_NAME \
    --s3-bucket-name $S3_BUCKET_NAME \
    --include-global-service-events \
    --is-multi-region-trail \
    --enable-log-file-validation || {
    print_warning "CloudTrail might already exist"
}

# Configure event selector for Bedrock API calls
aws cloudtrail put-event-selectors \
    --trail-name $CLOUDTRAIL_NAME \
    --event-selectors '[
        {
            "ReadWriteType": "All",
            "IncludeManagementEvents": false,
            "DataResources": [
                {
                    "Type": "AWS::Bedrock::*",
                    "Values": ["arn:aws:bedrock:*"]
                }
            ]
        }
    ]'

# Start logging
aws cloudtrail start-logging --name $CLOUDTRAIL_NAME
print_status "CloudTrail configured and started"

# Create EventBridge rule for real-time processing
echo "⚡ Creating EventBridge rule for real-time processing..."
aws events put-rule \
    --name "bedrock-realtime-processing" \
    --event-pattern '{
        "source": ["aws.bedrock"],
        "detail-type": ["AWS API Call via CloudTrail"],
        "detail": {
            "eventSource": ["bedrock-runtime.amazonaws.com"],
            "eventName": ["InvokeModel", "InvokeModelWithResponseStream"]
        }
    }' \
    --state ENABLED \
    --description "Route Bedrock API calls to real-time processor"

# Add Lambda as target
aws events put-targets \
    --rule "bedrock-realtime-processing" \
    --targets "Id"="1","Arn"="arn:aws:lambda:$REGION:$ACCOUNT_ID:function:$FUNCTION_NAME"

# Add permission for EventBridge to invoke Lambda
aws lambda add-permission \
    --function-name $FUNCTION_NAME \
    --statement-id "allow-eventbridge" \
    --action "lambda:InvokeFunction" \
    --principal events.amazonaws.com \
    --source-arn "arn:aws:events:$REGION:$ACCOUNT_ID:rule/bedrock-realtime-processing"

print_status "EventBridge rule configured"

# Clean up temporary files
rm -f /tmp/lambda-trust-policy.json /tmp/lambda-policy.json /tmp/cloudtrail-bucket-policy.json
rm -f lambda_function.py realtime-logger-deployment.zip
rm -rf pymysql/

cd ..

echo ""
print_status "🎉 Real-time Bedrock Request Logger deployed successfully!"
echo ""
echo "📋 Deployment Summary:"
echo "  • Lambda Function: $FUNCTION_NAME"
echo "  • CloudTrail: $CLOUDTRAIL_NAME"
echo "  • S3 Bucket: $S3_BUCKET_NAME"
echo "  • EventBridge Rule: bedrock-realtime-processing"
echo ""
echo "🔧 Next Steps:"
echo "  1. Update the DB_HOST environment variable with your actual RDS endpoint"
echo "  2. Create the database secret in AWS Secrets Manager"
echo "  3. Run the database schema creation script"
echo "  4. Test the system with a Bedrock API call"
echo ""
print_warning "Remember to update the Lambda environment variables with your actual RDS endpoint!"
