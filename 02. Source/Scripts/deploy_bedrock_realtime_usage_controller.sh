#!/bin/bash

# Deploy Bedrock Realtime Usage Controller - Merged Function
# This script deploys the new merged Lambda function that combines realtime logging and usage control

echo "🚀 Deploying Bedrock Realtime Usage Controller (Merged Function)..."

# Set variables
FUNCTION_NAME="bedrock-realtime-usage-controller"
LAMBDA_FILE="../Lambda Functions/bedrock-realtime-usage-controller.py"
QUOTA_CONFIG_FILE="../Configuration/quota_config.json"
EMAIL_CREDENTIALS_FILE="../Configuration/email_credentials.json"
ZIP_FILE="bedrock-realtime-usage-controller.zip"

# Check if the Lambda function file exists
if [ ! -f "$LAMBDA_FILE" ]; then
    echo "❌ Error: Lambda function file $LAMBDA_FILE not found!"
    exit 1
fi

# Check if quota_config.json exists
if [ ! -f "$QUOTA_CONFIG_FILE" ]; then
    echo "❌ Error: Quota config file $QUOTA_CONFIG_FILE not found!"
    exit 1
fi

# Check if email_credentials.json exists
if [ ! -f "$EMAIL_CREDENTIALS_FILE" ]; then
    echo "❌ Error: Email credentials file $EMAIL_CREDENTIALS_FILE not found!"
    exit 1
fi

# Create deployment package
echo "📦 Creating deployment package with dependencies..."

# Create a clean directory for the package
rm -rf lambda_package_usage_controller
mkdir lambda_package_usage_controller
cd lambda_package_usage_controller

# Copy the Lambda function
cp "$LAMBDA_FILE" lambda_function.py

# Copy configuration files
cp "$QUOTA_CONFIG_FILE" quota_config.json
cp "$EMAIL_CREDENTIALS_FILE" email_credentials.json
echo "✅ Added configuration files to Lambda package"

# Install dependencies
echo "📥 Installing dependencies..."
python3 -m pip install pymysql pytz -t .

# Create the ZIP file
echo "🗜️ Creating ZIP package..."
zip -r "../$ZIP_FILE" .

# Go back to scripts directory
cd ..

# Deploy the Lambda function
echo "☁️ Deploying to AWS Lambda..."

# Get current AWS account ID and region
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
REGION=$(aws configure get region)
if [ -z "$REGION" ]; then
    REGION="eu-west-1"
fi

echo "📍 Using Account ID: $ACCOUNT_ID, Region: $REGION"

# Set environment variables (update these with your actual values)
RDS_ENDPOINT="bedrock-usage-mysql.czuimyk2qu10.eu-west-1.rds.amazonaws.com"
RDS_USERNAME="admin"
RDS_PASSWORD="your-secure-password"  # Update this with actual password
RDS_DATABASE="bedrock_usage"
EMAIL_SERVICE_LAMBDA_NAME="bedrock-email-service"

# Check if function exists
if aws lambda get-function --function-name "$FUNCTION_NAME" >/dev/null 2>&1; then
    echo "🔄 Updating existing Lambda function..."
    aws lambda update-function-code \
        --function-name "$FUNCTION_NAME" \
        --zip-file "fileb://$ZIP_FILE"
    
    echo "⚙️ Updating function configuration..."
    aws lambda update-function-configuration \
        --function-name "$FUNCTION_NAME" \
        --timeout 60 \
        --memory-size 512 \
        --environment Variables="{\"RDS_ENDPOINT\":\"$RDS_ENDPOINT\",\"RDS_USERNAME\":\"$RDS_USERNAME\",\"RDS_PASSWORD\":\"$RDS_PASSWORD\",\"RDS_DATABASE\":\"$RDS_DATABASE\",\"EMAIL_SERVICE_LAMBDA_NAME\":\"$EMAIL_SERVICE_LAMBDA_NAME\"}"
else
    echo "🆕 Creating new Lambda function..."
    
    # Create execution role if it doesn't exist
    ROLE_NAME="bedrock-realtime-usage-controller-role"
    ROLE_ARN="arn:aws:iam::$ACCOUNT_ID:role/$ROLE_NAME"
    
    if ! aws iam get-role --role-name "$ROLE_NAME" >/dev/null 2>&1; then
        echo "🔐 Creating IAM role for Lambda function..."
        
        # Create trust policy
        cat > trust-policy.json << EOF
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
            --role-name "$ROLE_NAME" \
            --assume-role-policy-document file://trust-policy.json
        
        # Attach basic Lambda execution policy
        aws iam attach-role-policy \
            --role-name "$ROLE_NAME" \
            --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
        
        # Attach VPC execution policy (if Lambda needs VPC access)
        aws iam attach-role-policy \
            --role-name "$ROLE_NAME" \
            --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole
        
        # Create custom policy for comprehensive access
        cat > comprehensive-policy.json << EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "iam:ListUserTags",
                "iam:GetUser",
                "iam:GetGroupsForUser",
                "iam:AttachUserPolicy",
                "iam:DetachUserPolicy",
                "iam:ListAttachedUserPolicies",
                "iam:CreatePolicy",
                "iam:GetPolicy",
                "iam:DeletePolicy",
                "iam:CreatePolicyVersion",
                "iam:DeletePolicyVersion",
                "iam:ListPolicyVersions"
            ],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "lambda:InvokeFunction"
            ],
            "Resource": [
                "arn:aws:lambda:$REGION:$ACCOUNT_ID:function:bedrock-email-service",
                "arn:aws:lambda:$REGION:$ACCOUNT_ID:function:bedrock-mysql-query-executor"
            ]
        },
        {
            "Effect": "Allow",
            "Action": [
                "logs:CreateLogGroup",
                "logs:CreateLogStream",
                "logs:PutLogEvents"
            ],
            "Resource": "arn:aws:logs:*:*:*"
        }
    ]
}
EOF
        
        aws iam put-role-policy \
            --role-name "$ROLE_NAME" \
            --policy-name "BedrockRealtimeUsageControllerPolicy" \
            --policy-document file://comprehensive-policy.json
        
        # Clean up policy files
        rm -f trust-policy.json comprehensive-policy.json
        
        echo "⏳ Waiting for role to be available..."
        sleep 10
    fi
    
    aws lambda create-function \
        --function-name "$FUNCTION_NAME" \
        --runtime python3.9 \
        --role "$ROLE_ARN" \
        --handler lambda_function.lambda_handler \
        --zip-file "fileb://$ZIP_FILE" \
        --timeout 60 \
        --memory-size 512 \
        --environment Variables="{\"RDS_ENDPOINT\":\"$RDS_ENDPOINT\",\"RDS_USERNAME\":\"$RDS_USERNAME\",\"RDS_PASSWORD\":\"$RDS_PASSWORD\",\"RDS_DATABASE\":\"$RDS_DATABASE\",\"EMAIL_SERVICE_LAMBDA_NAME\":\"$EMAIL_SERVICE_LAMBDA_NAME\"}"
fi

# Clean up
echo "🧹 Cleaning up temporary files..."
rm -rf lambda_package_usage_controller

echo "✅ Deployment completed successfully!"
echo ""
echo "📋 Key Features Deployed:"
echo "✅ Merged realtime logging and usage control functionality"
echo "✅ CloudTrail event processing for automatic blocking"
echo "✅ API event handling for manual operations"
echo "✅ Enhanced email service integration"
echo "✅ Administrative protection workflow"
echo "✅ CET timezone support"
echo "✅ Comprehensive IAM policy management"
echo ""
echo "📋 Next steps:"
echo "1. Update RDS_PASSWORD environment variable with actual password"
echo "2. Update CloudTrail configuration to point to new function"
echo "3. Update CloudWatch Events/EventBridge rules"
echo "4. Update dashboard to use new function endpoints"
echo "5. Test the complete integration"
echo ""
echo "🔍 To update RDS password:"
echo "aws lambda update-function-configuration --function-name $FUNCTION_NAME --environment Variables='{\"RDS_ENDPOINT\":\"$RDS_ENDPOINT\",\"RDS_USERNAME\":\"$RDS_USERNAME\",\"RDS_PASSWORD\":\"YOUR_ACTUAL_PASSWORD\",\"RDS_DATABASE\":\"$RDS_DATABASE\",\"EMAIL_SERVICE_LAMBDA_NAME\":\"$EMAIL_SERVICE_LAMBDA_NAME\"}'"
echo ""
echo "🔍 Function ARN: arn:aws:lambda:$REGION:$ACCOUNT_ID:function:$FUNCTION_NAME"

cd ..
