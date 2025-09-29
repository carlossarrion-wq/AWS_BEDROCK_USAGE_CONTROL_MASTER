#!/bin/bash

# Deploy Realtime Request Logger with CET Timezone Fix and Quota Config Support
# This script deploys the Lambda function with quota_config.json included for user limit assignment

echo "🚀 Deploying Realtime Request Logger with CET Timezone Fix and Quota Config Support..."

# Set variables
FUNCTION_NAME="bedrock-realtime-request-logger"
LAMBDA_FILE="05_realtime_request_logger_cet_fixed.py"
QUOTA_CONFIG_FILE="../individual_blocking_system/lambda_functions/quota_config.json"
ZIP_FILE="bedrock_realtime_logger_with_quota_config.zip"

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

# Create deployment package
echo "📦 Creating deployment package with quota_config.json..."

# Create a clean directory for the package
rm -rf lambda_package_with_quota
mkdir lambda_package_with_quota
cd lambda_package_with_quota

# Copy the Lambda function
cp "../$LAMBDA_FILE" lambda_function.py

# Copy the quota_config.json file
cp "../$QUOTA_CONFIG_FILE" quota_config.json
echo "✅ Added quota_config.json to Lambda package"

# Install pymysql dependency
echo "📥 Installing pymysql dependency..."
python3 -m pip install pymysql -t .

# Create the ZIP file
echo "🗜️ Creating ZIP package..."
zip -r "../$ZIP_FILE" .

# Go back to migration directory
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
        --environment Variables="{
            \"RDS_ENDPOINT\":\"$RDS_ENDPOINT\",
            \"RDS_USERNAME\":\"$RDS_USERNAME\",
            \"RDS_PASSWORD\":\"$RDS_PASSWORD\",
            \"RDS_DATABASE\":\"$RDS_DATABASE\"
        }"
else
    echo "🆕 Creating new Lambda function..."
    
    # Create execution role if it doesn't exist
    ROLE_NAME="bedrock-realtime-logger-role"
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
        
        # Create custom policy for IAM access
        cat > iam-policy.json << EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "iam:ListUserTags",
                "iam:GetUser",
                "iam:GetGroupsForUser"
            ],
            "Resource": "*"
        }
    ]
}
EOF
        
        aws iam put-role-policy \
            --role-name "$ROLE_NAME" \
            --policy-name "BedrockRealtimeLoggerIAMPolicy" \
            --policy-document file://iam-policy.json
        
        # Clean up policy files
        rm -f trust-policy.json iam-policy.json
        
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
        --environment Variables="{
            \"RDS_ENDPOINT\":\"$RDS_ENDPOINT\",
            \"RDS_USERNAME\":\"$RDS_USERNAME\",
            \"RDS_PASSWORD\":\"$RDS_PASSWORD\",
            \"RDS_DATABASE\":\"$RDS_DATABASE\"
        }"
fi

# Clean up
echo "🧹 Cleaning up temporary files..."
rm -rf lambda_package_with_quota
# Keep the ZIP file for reference
# rm -f "$ZIP_FILE"

echo "✅ Deployment completed successfully!"
echo ""
echo "📋 Key Features Deployed:"
echo "✅ CET timezone support for timestamps"
echo "✅ quota_config.json included for user limit assignment"
echo "✅ Database-driven user limits with JSON fallback"
echo "✅ Automatic user creation with appropriate limits"
echo ""
echo "📋 Next steps:"
echo "1. Run the database migration: mysql < 11_update_user_limits_schema.sql"
echo "2. Update RDS_PASSWORD environment variable with actual password"
echo "3. Test the function with a sample CloudWatch log event"
echo "4. Verify that new users get limits from quota_config.json"
echo "5. Verify that dashboard loads limits from database"
echo ""
echo "🔍 To test the function:"
echo "aws lambda invoke --function-name $FUNCTION_NAME --payload file://test-lambda-payload.json response.json"
echo ""
echo "🔍 To update RDS password:"
echo "aws lambda update-function-configuration --function-name $FUNCTION_NAME --environment Variables='{\"RDS_ENDPOINT\":\"$RDS_ENDPOINT\",\"RDS_USERNAME\":\"$RDS_USERNAME\",\"RDS_PASSWORD\":\"YOUR_ACTUAL_PASSWORD\",\"RDS_DATABASE\":\"$RDS_DATABASE\"}'"

cd ..
