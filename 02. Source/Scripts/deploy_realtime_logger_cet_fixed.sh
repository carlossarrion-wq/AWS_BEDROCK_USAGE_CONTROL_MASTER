#!/bin/bash

# Deploy Realtime Request Logger with CET Timezone Fix
# This script deploys the Lambda function that stores timestamps in CET format

echo "🚀 Deploying Realtime Request Logger with CET Timezone Fix..."

# Set variables
FUNCTION_NAME="bedrock-realtime-request-logger"
LAMBDA_FILE="05_realtime_request_logger_cet_fixed.py"
ZIP_FILE="bedrock_realtime_logger_cet_fixed.zip"

# Check if the Lambda function file exists
if [ ! -f "$LAMBDA_FILE" ]; then
    echo "❌ Error: Lambda function file $LAMBDA_FILE not found!"
    exit 1
fi

# Create deployment package
echo "📦 Creating deployment package..."

# Create a clean directory for the package
rm -rf lambda_package_cet
mkdir lambda_package_cet
cd lambda_package_cet

# Copy the Lambda function
cp "../$LAMBDA_FILE" lambda_function.py

# Install pymysql dependency
echo "📥 Installing pymysql dependency..."
pip install pymysql -t .

# Create the ZIP file
echo "🗜️ Creating ZIP package..."
zip -r "../$ZIP_FILE" .

# Go back to migration directory
cd ..

# Deploy the Lambda function
echo "☁️ Deploying to AWS Lambda..."

# Check if function exists
if aws lambda get-function --function-name "$FUNCTION_NAME" >/dev/null 2>&1; then
    echo "🔄 Updating existing Lambda function..."
    aws lambda update-function-code \
        --function-name "$FUNCTION_NAME" \
        --zip-file "fileb://$ZIP_FILE"
    
    echo "⚙️ Updating function configuration..."
    aws lambda update-function-configuration \
        --function-name "$FUNCTION_NAME" \
        --timeout 30 \
        --memory-size 256 \
        --environment Variables='{
            "DB_HOST":"bedrock-usage-db.cluster-c123456789.eu-west-1.rds.amazonaws.com",
            "DB_USER":"admin",
            "DB_PASSWORD":"your-secure-password",
            "DB_NAME":"bedrock_usage"
        }'
else
    echo "🆕 Creating new Lambda function..."
    aws lambda create-function \
        --function-name "$FUNCTION_NAME" \
        --runtime python3.9 \
        --role arn:aws:iam::123456789012:role/lambda-execution-role \
        --handler lambda_function.lambda_handler \
        --zip-file "fileb://$ZIP_FILE" \
        --timeout 30 \
        --memory-size 256 \
        --environment Variables='{
            "DB_HOST":"bedrock-usage-db.cluster-c123456789.eu-west-1.rds.amazonaws.com",
            "DB_USER":"admin",
            "DB_PASSWORD":"your-secure-password",
            "DB_NAME":"bedrock_usage"
        }'
fi

# Clean up
echo "🧹 Cleaning up temporary files..."
rm -rf lambda_package_cet
rm -f "$ZIP_FILE"

echo "✅ Deployment completed successfully!"
echo ""
echo "📋 Next steps:"
echo "1. Update the CloudWatch log group trigger to point to this function"
echo "2. Test the function with a sample CloudWatch log event"
echo "3. Verify that timestamps are now stored in CET format"
echo ""
echo "🔍 To test the function:"
echo "aws lambda invoke --function-name $FUNCTION_NAME --payload file://test-lambda-payload.json response.json"

cd ..
