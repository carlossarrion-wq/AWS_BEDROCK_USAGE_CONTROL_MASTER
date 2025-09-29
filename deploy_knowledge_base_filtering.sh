#!/bin/bash

# Deploy Knowledge Base Filtering Update to bedrock-realtime-usage-controller
# This script packages and deploys the updated lambda function with KB filtering

set -e

echo "🚀 Deploying Knowledge Base Filtering Update"
echo "=============================================="

# Configuration
LAMBDA_FUNCTION_NAME="bedrock-realtime-usage-controller"
SOURCE_DIR="02. Source/Lambda Functions/bedrock-realtime-usage-controller-aws-20250923"
TEMP_DIR="/tmp/bedrock-kb-filter-deploy"
ZIP_FILE="bedrock-realtime-usage-controller-kb-filter.zip"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}📦 Step 1: Preparing deployment package...${NC}"

# Clean up any existing temp directory
rm -rf "$TEMP_DIR"
mkdir -p "$TEMP_DIR"

# Copy lambda function files
echo "   Copying lambda function files..."
cp -r "$SOURCE_DIR"/* "$TEMP_DIR/"

# Verify the main lambda function file exists
if [ ! -f "$TEMP_DIR/lambda_function.py" ]; then
    echo -e "${RED}❌ Error: lambda_function.py not found in source directory${NC}"
    exit 1
fi

# Check if the filtering logic is present
if grep -q "FILTERING OUT request from user.*both Team.*and Person.*are unknown" "$TEMP_DIR/lambda_function.py"; then
    echo -e "${GREEN}   ✅ Knowledge Base filtering logic found in lambda function${NC}"
else
    echo -e "${RED}   ❌ Error: Knowledge Base filtering logic not found in lambda function${NC}"
    exit 1
fi

echo -e "${YELLOW}📦 Step 2: Creating deployment package...${NC}"

# Create the zip file
cd "$TEMP_DIR"
zip -r "../$ZIP_FILE" . -x "*.pyc" "__pycache__/*" "*.git*"

# Move zip file to current directory
mv "../$ZIP_FILE" "$OLDPWD/"

echo -e "${GREEN}   ✅ Created deployment package: $ZIP_FILE${NC}"

echo -e "${YELLOW}🚀 Step 3: Deploying to AWS Lambda...${NC}"

# Check if AWS CLI is available
if ! command -v aws &> /dev/null; then
    echo -e "${RED}❌ Error: AWS CLI not found. Please install AWS CLI first.${NC}"
    exit 1
fi

# Update the lambda function
echo "   Updating Lambda function: $LAMBDA_FUNCTION_NAME"

if aws lambda update-function-code \
    --function-name "$LAMBDA_FUNCTION_NAME" \
    --zip-file "fileb://$ZIP_FILE" \
    --no-cli-pager > /dev/null 2>&1; then
    
    echo -e "${GREEN}   ✅ Successfully updated Lambda function${NC}"
    
    # Wait for the update to complete
    echo "   Waiting for function update to complete..."
    aws lambda wait function-updated --function-name "$LAMBDA_FUNCTION_NAME"
    
    echo -e "${GREEN}   ✅ Function update completed${NC}"
    
else
    echo -e "${RED}   ❌ Error: Failed to update Lambda function${NC}"
    echo "   Please check your AWS credentials and permissions"
    exit 1
fi

echo -e "${YELLOW}🔍 Step 4: Verifying deployment...${NC}"

# Get function information
FUNCTION_INFO=$(aws lambda get-function --function-name "$LAMBDA_FUNCTION_NAME" --no-cli-pager 2>/dev/null)

if [ $? -eq 0 ]; then
    LAST_MODIFIED=$(echo "$FUNCTION_INFO" | grep -o '"LastModified": "[^"]*"' | cut -d'"' -f4)
    CODE_SIZE=$(echo "$FUNCTION_INFO" | grep -o '"CodeSize": [0-9]*' | cut -d' ' -f2)
    
    echo -e "${GREEN}   ✅ Function verification successful${NC}"
    echo "   Last Modified: $LAST_MODIFIED"
    echo "   Code Size: $CODE_SIZE bytes"
else
    echo -e "${RED}   ❌ Error: Could not verify function deployment${NC}"
fi

echo -e "${YELLOW}🧹 Step 5: Cleaning up...${NC}"

# Clean up temporary files
rm -rf "$TEMP_DIR"
rm -f "$ZIP_FILE"

echo -e "${GREEN}   ✅ Cleanup completed${NC}"

echo ""
echo "=============================================="
echo -e "${GREEN}🎉 Deployment completed successfully!${NC}"
echo ""
echo "📋 Summary of changes:"
echo "   • Added Knowledge Base session filtering"
echo "   • Sessions with team='unknown' AND person='Unknown' will be excluded"
echo "   • Regular user sessions will continue to be processed normally"
echo ""
echo "🔍 To verify the changes are working:"
echo "   1. Monitor CloudWatch logs for the lambda function"
echo "   2. Look for log messages containing 'FILTERING OUT request from user'"
echo "   3. Check that Knowledge Base sessions are no longer recorded in bedrock_requests table"
echo ""
echo -e "${YELLOW}⚠️  Note: The changes will take effect immediately for new requests${NC}"
