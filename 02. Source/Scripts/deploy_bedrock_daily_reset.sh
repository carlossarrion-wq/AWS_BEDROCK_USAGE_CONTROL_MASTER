#!/bin/bash

# Deploy Bedrock Daily Reset Lambda Function
# This script deploys the daily reset Lambda function with the fixed blocked_at clearing

echo "🚀 Deploying Bedrock Daily Reset Lambda Function..."

# Set variables
FUNCTION_NAME="bedrock-daily-reset"
LAMBDA_FILE="../Lambda Functions/bedrock_daily_reset.py"
ZIP_FILE="bedrock-daily-reset.zip"

# Check if the Lambda function file exists
if [ ! -f "$LAMBDA_FILE" ]; then
    echo "❌ Error: Lambda function file $LAMBDA_FILE not found!"
    exit 1
fi

# Create deployment package
echo "📦 Creating deployment package with dependencies..."

# Create a clean directory for the package
rm -rf lambda_package_daily_reset
mkdir lambda_package_daily_reset
cd lambda_package_daily_reset

# Copy the Lambda function
cp "$LAMBDA_FILE" lambda_function.py

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
RDS_PASSWORD="BedrockUsage2024!"  # Update this with actual password
RDS_DATABASE="bedrock_usage"
EMAIL_SERVICE_FUNCTION="bedrock-email-service"
SNS_TOPIC_ARN="arn:aws:sns:$REGION:$ACCOUNT_ID:bedrock-usage-alerts"

# Check if function exists
if aws lambda get-function --function-name "$FUNCTION_NAME" >/dev/null 2>&1; then
    echo "🔄 Updating existing Lambda function..."
    aws lambda update-function-code \
        --function-name "$FUNCTION_NAME" \
        --zip-file "fileb://$ZIP_FILE"
    
    echo "⚙️ Updating function configuration..."
    aws lambda update-function-configuration \
        --function-name "$FUNCTION_NAME" \
        --timeout 300 \
        --memory-size 512 \
        --environment Variables="{\"RDS_ENDPOINT\":\"$RDS_ENDPOINT\",\"RDS_USERNAME\":\"$RDS_USERNAME\",\"RDS_PASSWORD\":\"$RDS_PASSWORD\",\"RDS_DATABASE\":\"$RDS_DATABASE\",\"EMAIL_SERVICE_FUNCTION\":\"$EMAIL_SERVICE_FUNCTION\",\"SNS_TOPIC_ARN\":\"$SNS_TOPIC_ARN\",\"ACCOUNT_ID\":\"$ACCOUNT_ID\"}"
else
    echo "🆕 Creating new Lambda function..."
    
    # Create execution role if it doesn't exist
    ROLE_NAME="bedrock-daily-reset-role"
    ROLE_ARN="arn:aws:iam::$ACCOUNT_ID:role/$ROLE_NAME"
    
    if ! aws iam get-role --role-name "$ROLE_NAME" >/dev/null 2>&1; then
        echo "🔐 Creating IAM role for Lambda function..."
        
        # Create trust policy
        cat > trust-policy-daily-reset.json << EOF
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
            --assume-role-policy-document file://trust-policy-daily-reset.json
        
        # Attach basic Lambda execution policy
        aws iam attach-role-policy \
            --role-name "$ROLE_NAME" \
            --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
        
        # Create custom policy for daily reset function
        cat > daily-reset-policy.json << EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "iam:GetUser",
                "iam:GetUserPolicy",
                "iam:PutUserPolicy",
                "iam:DeleteUserPolicy",
                "iam:ListUserPolicies"
            ],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "lambda:InvokeFunction"
            ],
            "Resource": [
                "arn:aws:lambda:$REGION:$ACCOUNT_ID:function:bedrock-email-service"
            ]
        },
        {
            "Effect": "Allow",
            "Action": [
                "sns:Publish"
            ],
            "Resource": [
                "arn:aws:sns:$REGION:$ACCOUNT_ID:bedrock-usage-alerts"
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
            --policy-name "BedrockDailyResetPolicy" \
            --policy-document file://daily-reset-policy.json
        
        # Clean up policy files
        rm -f trust-policy-daily-reset.json daily-reset-policy.json
        
        echo "⏳ Waiting for role to be available..."
        sleep 10
    fi
    
    aws lambda create-function \
        --function-name "$FUNCTION_NAME" \
        --runtime python3.9 \
        --role "$ROLE_ARN" \
        --handler lambda_function.lambda_handler \
        --zip-file "fileb://$ZIP_FILE" \
        --timeout 300 \
        --memory-size 512 \
        --environment Variables="{\"RDS_ENDPOINT\":\"$RDS_ENDPOINT\",\"RDS_USERNAME\":\"$RDS_USERNAME\",\"RDS_PASSWORD\":\"$RDS_PASSWORD\",\"RDS_DATABASE\":\"$RDS_DATABASE\",\"EMAIL_SERVICE_FUNCTION\":\"$EMAIL_SERVICE_FUNCTION\",\"SNS_TOPIC_ARN\":\"$SNS_TOPIC_ARN\",\"ACCOUNT_ID\":\"$ACCOUNT_ID\"}"
fi

# Set up CloudWatch Events rule for daily execution at 00:00 CET
echo "⏰ Setting up CloudWatch Events rule for daily execution..."

RULE_NAME="bedrock-daily-reset-schedule"
RULE_DESCRIPTION="Trigger bedrock daily reset at 00:00 CET daily"

# Create or update the rule (22:00 UTC = 00:00 CET in winter, 23:00 UTC = 00:00 CET in summer)
# Using 23:00 UTC to account for CET/CEST
aws events put-rule \
    --name "$RULE_NAME" \
    --schedule-expression "cron(0 23 * * ? *)" \
    --description "$RULE_DESCRIPTION" \
    --state ENABLED

# Add permission for CloudWatch Events to invoke the Lambda function
aws lambda add-permission \
    --function-name "$FUNCTION_NAME" \
    --statement-id "allow-cloudwatch-events" \
    --action "lambda:InvokeFunction" \
    --principal "events.amazonaws.com" \
    --source-arn "arn:aws:events:$REGION:$ACCOUNT_ID:rule/$RULE_NAME" \
    2>/dev/null || echo "Permission already exists"

# Add the Lambda function as a target for the rule
aws events put-targets \
    --rule "$RULE_NAME" \
    --targets "Id"="1","Arn"="arn:aws:lambda:$REGION:$ACCOUNT_ID:function:$FUNCTION_NAME"

# Clean up
echo "🧹 Cleaning up temporary files..."
rm -rf lambda_package_daily_reset

echo "✅ Deployment completed successfully!"
echo ""
echo "📋 Key Features Deployed:"
echo "✅ Daily reset functionality with blocked_at field clearing"
echo "✅ Automatic unblocking of expired users"
echo "✅ Administrative safe flag management"
echo "✅ IAM policy cleanup"
echo "✅ Email notifications"
echo "✅ CloudWatch Events scheduled execution at 00:00 CET"
echo ""
echo "📋 Next steps:"
echo "1. Verify the CloudWatch Events rule is working"
echo "2. Test the function manually if needed"
echo "3. Monitor CloudWatch logs for execution"
echo ""
echo "🔍 Function ARN: arn:aws:lambda:$REGION:$ACCOUNT_ID:function:$FUNCTION_NAME"
echo "🔍 CloudWatch Events Rule: $RULE_NAME"

cd ..
