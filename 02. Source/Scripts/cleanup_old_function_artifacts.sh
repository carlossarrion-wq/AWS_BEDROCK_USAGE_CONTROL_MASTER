#!/bin/bash

# Cleanup AWS Artifacts for Old Lambda Functions
# This script removes AWS artifacts specifically related to the old disabled functions

echo "🧹 Cleaning up AWS artifacts for old Lambda functions..."

# Set variables
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
echo "🗑️ Functions to cleanup: ${OLD_FUNCTIONS[*]}"

# Function to cleanup artifacts for a specific Lambda function
cleanup_function_artifacts() {
    local function_name=$1
    local function_arn="arn:aws:lambda:$REGION:$ACCOUNT_ID:function:$function_name"
    
    echo ""
    echo "🔄 Cleaning up artifacts for: $function_name"
    
    # 1. Remove EventBridge rules and targets
    echo "🔄 Checking EventBridge rules targeting $function_name..."
    RULES=$(aws events list-rules --query 'Rules[].Name' --output text)
    
    for RULE in $RULES; do
        # Get targets for this rule that match our function
        TARGETS=$(aws events list-targets-by-rule --rule "$RULE" --query "Targets[?contains(Arn, '$function_name')].Id" --output text 2>/dev/null)
        
        if [ ! -z "$TARGETS" ]; then
            echo "🗑️ Removing targets from EventBridge rule: $RULE"
            for TARGET_ID in $TARGETS; do
                aws events remove-targets --rule "$RULE" --ids "$TARGET_ID" >/dev/null 2>&1
                if [ $? -eq 0 ]; then
                    echo "  ✅ Removed target $TARGET_ID from rule $RULE"
                else
                    echo "  ❌ Failed to remove target $TARGET_ID from rule $RULE"
                fi
            done
            
            # Check if rule has no more targets, if so delete the rule
            REMAINING_TARGETS=$(aws events list-targets-by-rule --rule "$RULE" --query 'Targets[].Id' --output text 2>/dev/null)
            if [ -z "$REMAINING_TARGETS" ]; then
                echo "🗑️ Deleting empty EventBridge rule: $RULE"
                aws events delete-rule --name "$RULE" >/dev/null 2>&1
                if [ $? -eq 0 ]; then
                    echo "  ✅ Deleted rule $RULE"
                else
                    echo "  ❌ Failed to delete rule $RULE"
                fi
            fi
        fi
    done
    
    # 2. Remove CloudWatch Log subscription filters
    echo "🔄 Checking CloudWatch Log subscription filters for $function_name..."
    LOG_GROUPS=$(aws logs describe-log-groups --query 'logGroups[].logGroupName' --output text)
    
    for LOG_GROUP in $LOG_GROUPS; do
        FILTERS=$(aws logs describe-subscription-filters --log-group-name "$LOG_GROUP" --query "subscriptionFilters[?contains(destinationArn, '$function_name')].filterName" --output text 2>/dev/null)
        
        if [ ! -z "$FILTERS" ]; then
            echo "🗑️ Removing subscription filters from log group: $LOG_GROUP"
            for FILTER in $FILTERS; do
                aws logs delete-subscription-filter --log-group-name "$LOG_GROUP" --filter-name "$FILTER" >/dev/null 2>&1
                if [ $? -eq 0 ]; then
                    echo "  ✅ Removed filter $FILTER from $LOG_GROUP"
                else
                    echo "  ❌ Failed to remove filter $FILTER from $LOG_GROUP"
                fi
            done
        fi
    done
    
    # 3. Remove Lambda permissions (resource-based policies)
    echo "🔄 Checking Lambda permissions for $function_name..."
    POLICY=$(aws lambda get-policy --function-name "$function_name" --query 'Policy' --output text 2>/dev/null)
    
    if [ "$POLICY" != "None" ] && [ ! -z "$POLICY" ]; then
        echo "🗑️ Removing Lambda permissions for $function_name..."
        # Get statement IDs from the policy
        STATEMENT_IDS=$(echo "$POLICY" | python3 -c "
import json, sys
try:
    policy = json.load(sys.stdin)
    statements = policy.get('Statement', [])
    for stmt in statements:
        if 'Sid' in stmt:
            print(stmt['Sid'])
except:
    pass
" 2>/dev/null)
        
        for SID in $STATEMENT_IDS; do
            if [ ! -z "$SID" ]; then
                aws lambda remove-permission --function-name "$function_name" --statement-id "$SID" >/dev/null 2>&1
                if [ $? -eq 0 ]; then
                    echo "  ✅ Removed permission $SID"
                else
                    echo "  ❌ Failed to remove permission $SID"
                fi
            fi
        done
    fi
    
    # 4. Remove CloudWatch Log Group for the function (if it exists and is specific to this function)
    FUNCTION_LOG_GROUP="/aws/lambda/$function_name"
    echo "🔄 Checking CloudWatch Log Group: $FUNCTION_LOG_GROUP"
    
    if aws logs describe-log-groups --log-group-name-prefix "$FUNCTION_LOG_GROUP" --query 'logGroups[0].logGroupName' --output text 2>/dev/null | grep -q "$FUNCTION_LOG_GROUP"; then
        echo "🗑️ Deleting CloudWatch Log Group: $FUNCTION_LOG_GROUP"
        aws logs delete-log-group --log-group-name "$FUNCTION_LOG_GROUP" >/dev/null 2>&1
        if [ $? -eq 0 ]; then
            echo "  ✅ Deleted log group $FUNCTION_LOG_GROUP"
        else
            echo "  ❌ Failed to delete log group $FUNCTION_LOG_GROUP"
        fi
    else
        echo "  ℹ️ Log group $FUNCTION_LOG_GROUP does not exist"
    fi
    
    # 5. Remove any CloudWatch Alarms related to this function
    echo "🔄 Checking CloudWatch Alarms for $function_name..."
    ALARMS=$(aws cloudwatch describe-alarms --query "MetricAlarms[?contains(Dimensions[?Name=='FunctionName'].Value, '$function_name')].AlarmName" --output text 2>/dev/null)
    
    if [ ! -z "$ALARMS" ]; then
        echo "🗑️ Deleting CloudWatch Alarms for $function_name..."
        for ALARM in $ALARMS; do
            aws cloudwatch delete-alarms --alarm-names "$ALARM" >/dev/null 2>&1
            if [ $? -eq 0 ]; then
                echo "  ✅ Deleted alarm $ALARM"
            else
                echo "  ❌ Failed to delete alarm $ALARM"
            fi
        done
    else
        echo "  ℹ️ No CloudWatch Alarms found for $function_name"
    fi
    
    # 6. Finally, delete the Lambda function itself
    echo "🗑️ Deleting Lambda function: $function_name"
    aws lambda delete-function --function-name "$function_name" >/dev/null 2>&1
    if [ $? -eq 0 ]; then
        echo "  ✅ Deleted function $function_name"
    else
        echo "  ❌ Failed to delete function $function_name"
    fi
}

# Cleanup artifacts for each old function
for function_name in "${OLD_FUNCTIONS[@]}"; do
    cleanup_function_artifacts "$function_name"
done

echo ""
echo "✅ Cleanup completed!"
echo ""
echo "📋 Summary of cleanup actions:"
echo "✅ Removed EventBridge rules and targets"
echo "✅ Removed CloudWatch Log subscription filters"
echo "✅ Removed Lambda permissions"
echo "✅ Deleted CloudWatch Log Groups"
echo "✅ Deleted CloudWatch Alarms"
echo "✅ Deleted Lambda functions"
echo ""
echo "📋 Functions cleaned up:"
for function_name in "${OLD_FUNCTIONS[@]}"; do
    echo "  🗑️ $function_name"
done
echo ""
echo "ℹ️ All AWS artifacts related to the old functions have been removed."
echo "ℹ️ The new function 'bedrock-realtime-usage-controller' remains active and unaffected."
