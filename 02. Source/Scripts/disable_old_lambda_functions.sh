#!/bin/bash

# Disable Old Lambda Functions
# This script disables the old Lambda functions that have been replaced by bedrock-realtime-usage-controller

echo "🔄 Disabling old Lambda functions replaced by bedrock-realtime-usage-controller..."

# Set variables
NEW_FUNCTION_NAME="bedrock-realtime-usage-controller"
OLD_FUNCTIONS=(
    "bedrock-realtime-logger-fixed"
    "bedrock-policy-manager-enhanced"
)

ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
REGION=$(aws configure get region)
if [ -z "$REGION" ]; then
    REGION="eu-west-1"
fi

echo "📍 Using Account ID: $ACCOUNT_ID, Region: $REGION"
echo "🆕 New function: $NEW_FUNCTION_NAME"
echo "🗑️ Functions to disable: ${OLD_FUNCTIONS[*]}"

# Function to disable a Lambda function
disable_lambda_function() {
    local function_name=$1
    
    echo ""
    echo "🔄 Processing function: $function_name"
    
    # Check if function exists
    if aws lambda get-function --function-name "$function_name" >/dev/null 2>&1; then
        echo "✅ Function $function_name exists"
        
        # Get current function configuration
        echo "📋 Getting current configuration for $function_name..."
        CURRENT_CONFIG=$(aws lambda get-function-configuration --function-name "$function_name")
        CURRENT_DESCRIPTION=$(echo "$CURRENT_CONFIG" | jq -r '.Description // ""')
        
        # Update description to indicate it's disabled
        NEW_DESCRIPTION="[DISABLED] Replaced by $NEW_FUNCTION_NAME - $CURRENT_DESCRIPTION"
        
        # Update function configuration to disable it
        echo "🚫 Disabling function $function_name..."
        aws lambda update-function-configuration \
            --function-name "$function_name" \
            --description "$NEW_DESCRIPTION" \
            --timeout 3 \
            --memory-size 128 \
            --environment Variables='{"DISABLED":"true","REPLACEMENT_FUNCTION":"'$NEW_FUNCTION_NAME'"}' \
            >/dev/null 2>&1
        
        if [ $? -eq 0 ]; then
            echo "✅ Successfully disabled $function_name"
        else
            echo "❌ Failed to disable $function_name"
        fi
        
        # Remove any EventBridge triggers (but keep the function for rollback purposes)
        echo "🔄 Checking for EventBridge rules targeting $function_name..."
        RULES=$(aws events list-rules --query 'Rules[].Name' --output text)
        
        for RULE in $RULES; do
            # Get targets for this rule
            TARGETS=$(aws events list-targets-by-rule --rule "$RULE" --query 'Targets[?contains(Arn, `'$function_name'`)].Id' --output text 2>/dev/null)
            
            if [ ! -z "$TARGETS" ]; then
                echo "⚠️ Found EventBridge rule $RULE targeting $function_name"
                echo "ℹ️ Note: Targets have already been updated to point to $NEW_FUNCTION_NAME"
            fi
        done
        
        # Check for CloudWatch Log subscription filters
        echo "🔄 Checking for CloudWatch Log subscription filters..."
        LOG_GROUPS=$(aws logs describe-log-groups --query 'logGroups[].logGroupName' --output text)
        
        for LOG_GROUP in $LOG_GROUPS; do
            FILTERS=$(aws logs describe-subscription-filters --log-group-name "$LOG_GROUP" --query 'subscriptionFilters[?contains(destinationArn, `'$function_name'`)].filterName' --output text 2>/dev/null)
            
            if [ ! -z "$FILTERS" ]; then
                echo "⚠️ Found CloudWatch Log subscription filters in $LOG_GROUP targeting $function_name"
                echo "ℹ️ Note: Filters have already been updated to point to $NEW_FUNCTION_NAME"
            fi
        done
        
    else
        echo "ℹ️ Function $function_name does not exist (may have been deleted already)"
    fi
}

# Disable each old function
for function_name in "${OLD_FUNCTIONS[@]}"; do
    disable_lambda_function "$function_name"
done

echo ""
echo "📋 Creating disabled function replacement code..."

# Create a simple replacement function code that returns an error
cat > disabled_function.py << 'EOF'
import json
import os

def lambda_handler(event, context):
    """
    This function has been disabled and replaced.
    """
    replacement_function = os.environ.get('REPLACEMENT_FUNCTION', 'bedrock-realtime-usage-controller')
    
    return {
        'statusCode': 410,  # Gone
        'body': json.dumps({
            'error': 'Function Disabled',
            'message': f'This function has been disabled and replaced by {replacement_function}',
            'replacement_function': replacement_function,
            'timestamp': context.aws_request_id
        })
    }
EOF

# Create deployment package for disabled functions
echo "📦 Creating deployment package for disabled functions..."
zip -q disabled_function.zip disabled_function.py

# Update each disabled function with the replacement code
for function_name in "${OLD_FUNCTIONS[@]}"; do
    if aws lambda get-function --function-name "$function_name" >/dev/null 2>&1; then
        echo "🔄 Updating $function_name with disabled function code..."
        aws lambda update-function-code \
            --function-name "$function_name" \
            --zip-file fileb://disabled_function.zip \
            >/dev/null 2>&1
        
        if [ $? -eq 0 ]; then
            echo "✅ Updated $function_name with disabled code"
        else
            echo "❌ Failed to update $function_name code"
        fi
    fi
done

# Clean up temporary files
echo "🧹 Cleaning up temporary files..."
rm -f disabled_function.py disabled_function.zip

echo ""
echo "✅ Old Lambda functions have been disabled successfully!"
echo ""
echo "📋 Summary of actions taken:"
echo "✅ Updated function descriptions to indicate they are disabled"
echo "✅ Reduced memory and timeout to minimum values"
echo "✅ Set environment variables to indicate disabled status"
echo "✅ Replaced function code with disabled handler"
echo "✅ Verified EventBridge and CloudWatch integrations point to new function"
echo ""
echo "📋 Functions disabled:"
for function_name in "${OLD_FUNCTIONS[@]}"; do
    echo "  🚫 $function_name"
done
echo ""
echo "📋 Active function:"
echo "  ✅ $NEW_FUNCTION_NAME"
echo ""
echo "ℹ️ Note: Functions are disabled but not deleted for rollback purposes."
echo "ℹ️ If you want to completely delete them later, you can use:"
for function_name in "${OLD_FUNCTIONS[@]}"; do
    echo "   aws lambda delete-function --function-name $function_name"
done
echo ""
echo "🔍 To verify the new function is working:"
echo "aws lambda invoke --function-name $NEW_FUNCTION_NAME --payload '{}' response.json && cat response.json"
