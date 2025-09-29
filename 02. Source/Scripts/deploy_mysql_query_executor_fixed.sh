#!/bin/bash

# Deploy MySQL Query Executor Lambda Function
# This Lambda function provides a secure interface for the dashboard to query the MySQL database

set -e

echo "🚀 Starting MySQL Query Executor Lambda deployment..."

# Configuration
FUNCTION_NAME="bedrock-mysql-query-executor"
REGION="eu-west-1"
RUNTIME="python3.9"
HANDLER="lambda_function.lambda_handler"
TIMEOUT=30
MEMORY_SIZE=256

# Get database password from AWS Secrets Manager or environment
if [ -z "$DB_PASSWORD" ]; then
    echo "❌ Error: DB_PASSWORD environment variable is required"
    echo "Please set it with: export DB_PASSWORD='your_database_password'"
    exit 1
fi

echo "📦 Creating deployment package..."

# Create temporary directory for deployment package
TEMP_DIR=$(mktemp -d)
echo "📁 Using temporary directory: $TEMP_DIR"

# Copy Lambda function code
cp migration/mysql_query_executor_lambda.py "$TEMP_DIR/lambda_function.py"

# Create requirements.txt for PyMySQL
cat > "$TEMP_DIR/requirements.txt" << EOF
PyMySQL==1.1.0
EOF

# Install dependencies
echo "📥 Installing Python dependencies..."
cd "$TEMP_DIR"
pip3 install -r requirements.txt -t .

# Create deployment package
echo "📦 Creating deployment ZIP package..."
zip -r lambda-deployment-package.zip . -x "*.pyc" "__pycache__/*"

# Check if Lambda function exists
echo "🔍 Checking if Lambda function exists..."
if aws lambda get-function --function-name "$FUNCTION_NAME" --region "$REGION" >/dev/null 2>&1; then
    echo "🔄 Function exists, updating code..."
    
    # Update function code
    aws lambda update-function-code \
        --function-name "$FUNCTION_NAME" \
        --zip-file fileb://lambda-deployment-package.zip \
        --region "$REGION"
    
    # Update function configuration
    aws lambda update-function-configuration \
        --function-name "$FUNCTION_NAME" \
        --runtime "$RUNTIME" \
        --handler "$HANDLER" \
        --timeout "$TIMEOUT" \
        --memory-size "$MEMORY_SIZE" \
        --environment Variables="{DB_USER=admin,DB_PASSWORD=$DB_PASSWORD}" \
        --region "$REGION"
    
    echo "✅ Lambda function updated successfully"
else
    echo "🆕 Function doesn't exist, creating new function..."
    
    # Get or create IAM role for Lambda
    ROLE_NAME="bedrock-mysql-query-executor-role"
    
    # Check if role exists
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
        
        # Create role
        aws iam create-role \
            --role-name "$ROLE_NAME" \
            --assume-role-policy-document file://trust-policy.json
        
        # Attach basic Lambda execution policy
        aws iam attach-role-policy \
            --role-name "$ROLE_NAME" \
            --policy-arn "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
        
        # Create and attach VPC access policy (if needed for RDS access)
        cat > vpc-policy.json << EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "ec2:CreateNetworkInterface",
                "ec2:DescribeNetworkInterfaces",
                "ec2:DeleteNetworkInterface",
                "ec2:AttachNetworkInterface",
                "ec2:DetachNetworkInterface"
            ],
            "Resource": "*"
        }
    ]
}
EOF
        
        aws iam put-role-policy \
            --role-name "$ROLE_NAME" \
            --policy-name "VPCAccessPolicy" \
            --policy-document file://vpc-policy.json
        
        echo "⏳ Waiting for IAM role to be ready..."
        sleep 10
        
        # Clean up policy files
        rm -f trust-policy.json vpc-policy.json
    fi
    
    # Get role ARN
    ROLE_ARN=$(aws iam get-role --role-name "$ROLE_NAME" --query 'Role.Arn' --output text)
    echo "🔐 Using IAM role: $ROLE_ARN"
    
    # Create Lambda function
    aws lambda create-function \
        --function-name "$FUNCTION_NAME" \
        --runtime "$RUNTIME" \
        --role "$ROLE_ARN" \
        --handler "$HANDLER" \
        --zip-file fileb://lambda-deployment-package.zip \
        --timeout "$TIMEOUT" \
        --memory-size "$MEMORY_SIZE" \
        --environment Variables="{DB_USER=admin,DB_PASSWORD=$DB_PASSWORD}" \
        --region "$REGION"
    
    echo "✅ Lambda function created successfully"
fi

# Test the function
echo "🧪 Testing Lambda function..."
cat > test-event.json << EOF
{
    "action": "query",
    "query": "SELECT 1 as test_value, NOW() as current_time",
    "params": []
}
EOF

echo "📤 Invoking test query..."
aws lambda invoke \
    --function-name "$FUNCTION_NAME" \
    --payload file://test-event.json \
    --region "$REGION" \
    response.json

echo "📥 Test response:"
cat response.json | jq '.'

# Check if test was successful
if grep -q '"statusCode": 200' response.json; then
    echo "✅ Lambda function test passed!"
else
    echo "❌ Lambda function test failed!"
    echo "Check the response above for error details"
fi

# Clean up
cd - > /dev/null
rm -rf "$TEMP_DIR"
rm -f test-event.json response.json

echo ""
echo "🎉 MySQL Query Executor Lambda deployment completed!"
echo ""
echo "📋 Function Details:"
echo "   Name: $FUNCTION_NAME"
echo "   Region: $REGION"
echo "   Runtime: $RUNTIME"
echo "   Handler: $HANDLER"
echo "   Timeout: ${TIMEOUT}s"
echo "   Memory: ${MEMORY_SIZE}MB"
echo ""
echo "🔗 The dashboard can now use this Lambda function to query the MySQL database"
echo "   Function ARN: arn:aws:lambda:$REGION:$(aws sts get-caller-identity --query Account --output text):function:$FUNCTION_NAME"
echo ""
echo "⚠️  Note: Make sure the Lambda function has network access to the RDS instance"
echo "   This may require VPC configuration if RDS is in a private subnet"
