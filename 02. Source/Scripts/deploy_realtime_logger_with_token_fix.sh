#!/bin/bash

# Deploy Real-time Bedrock Request Logger with Token Storage Fix
# This script deploys the updated Lambda function that correctly handles token storage

set -e

echo "🚀 Deploying Real-time Bedrock Request Logger with Token Storage Fix..."

# Configuration
FUNCTION_NAME="bedrock-realtime-request-logger"
REGION="eu-west-1"
ROLE_NAME="BedrockRealtimeLoggerRole"

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

# Create deployment package with the fixed Lambda function
echo "📦 Creating deployment package with token storage fix..."

# Create temporary directory for deployment
mkdir -p /tmp/lambda_deployment
cd /tmp/lambda_deployment

# Copy the fixed Lambda function
cp /Users/csarrion/Cline/AWS_BEDROCK_USAGE_CONTROL/migration/05_realtime_request_logger_fixed.py lambda_function.py

# Install dependencies
echo "📥 Installing dependencies..."
pip3 install pymysql -t . --quiet

# Create deployment package
echo "📦 Creating deployment ZIP..."
zip -r realtime-logger-with-token-fix.zip lambda_function.py pymysql/ -q

print_status "Deployment package created"

# Check if Lambda function exists
if aws lambda get-function --function-name $FUNCTION_NAME &> /dev/null; then
    echo "🔄 Updating existing Lambda function..."
    aws lambda update-function-code \
        --function-name $FUNCTION_NAME \
        --zip-file fileb://realtime-logger-with-token-fix.zip
    
    print_status "Lambda function updated with token storage fix"
else
    print_error "Lambda function $FUNCTION_NAME does not exist. Please run the initial deployment script first."
    exit 1
fi

# Update function configuration to ensure IAM permissions for tag access
echo "🔧 Updating Lambda function configuration..."
aws lambda update-function-configuration \
    --function-name $FUNCTION_NAME \
    --timeout 300 \
    --memory-size 512 \
    --description "Real-time Bedrock request logger with token storage fix and IAM tag support"

print_status "Lambda function configuration updated"

# Update IAM role policy to include IAM tag permissions
echo "🔐 Updating IAM role policy for tag access..."
cat > /tmp/lambda-policy-updated.json << EOF
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
                "iam:GetGroup",
                "iam:ListUserTags"
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
    --policy-name "BedrockRealtimeLoggerPolicy" \
    --policy-document file:///tmp/lambda-policy-updated.json

print_status "IAM role policy updated with tag access permissions"

# Clean up temporary files
cd /Users/csarrion/Cline/AWS_BEDROCK_USAGE_CONTROL
rm -rf /tmp/lambda_deployment
rm -f /tmp/lambda-policy-updated.json

echo ""
print_status "🎉 Real-time Bedrock Request Logger updated successfully with token storage fix!"
echo ""
echo "📋 Update Summary:"
echo "  • Lambda Function: $FUNCTION_NAME"
echo "  • Token Storage: Fixed - input_tokens and output_tokens now correctly set to 0"
echo "  • IAM Tag Support: Added - Team and Person tags can now be extracted"
echo "  • CloudTrail Integration: Maintained - real-time processing continues"
echo ""
echo "🔧 Key Changes:"
echo "  1. ✅ Token fields (input_tokens, output_tokens) now correctly set to 0"
echo "  2. ✅ Team extraction from IAM tags implemented"
echo "  3. ✅ Person extraction from IAM tags implemented"
echo "  4. ✅ Proper logging when token data is not available in CloudTrail"
echo ""
print_status "The Lambda function is now ready to process Bedrock requests with correct token handling!"
