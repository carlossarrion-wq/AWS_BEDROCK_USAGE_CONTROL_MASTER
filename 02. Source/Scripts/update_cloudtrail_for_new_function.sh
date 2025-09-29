#!/bin/bash

# Update CloudTrail and CloudWatch Events to point to new bedrock-realtime-usage-controller function
# This script updates AWS artifacts to use the new merged function

echo "🔄 Updating AWS artifacts to point to bedrock-realtime-usage-controller..."

# Set variables
NEW_FUNCTION_NAME="bedrock-realtime-usage-controller"
OLD_FUNCTION_NAME="bedrock-realtime-request-logger"
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
REGION=$(aws configure get region)
if [ -z "$REGION" ]; then
    REGION="eu-west-1"
fi

echo "📍 Using Account ID: $ACCOUNT_ID, Region: $REGION"
echo "🔄 Updating from: $OLD_FUNCTION_NAME to: $NEW_FUNCTION_NAME"

# 1. Update CloudWatch Events Rules (EventBridge)
echo ""
echo "1️⃣ Updating CloudWatch Events Rules..."

# List all rules that might be targeting the old function
echo "🔍 Finding EventBridge rules targeting the old function..."
RULES=$(aws events list-rules --query 'Rules[].Name' --output text)

for RULE in $RULES; do
    echo "🔍 Checking rule: $RULE"
    
    # Get targets for this rule
    TARGETS=$(aws events list-targets-by-rule --rule "$RULE" --query 'Targets[?contains(Arn, `'$OLD_FUNCTION_NAME'`)].Id' --output text)
    
    if [ ! -z "$TARGETS" ]; then
        echo "✅ Found rule $RULE with targets pointing to old function"
        
        # Get the target details
        TARGET_DETAILS=$(aws events list-targets-by-rule --rule "$RULE" --query 'Targets[?contains(Arn, `'$OLD_FUNCTION_NAME'`)]' --output json)
        
        # Update each target
        for TARGET_ID in $TARGETS; do
            echo "🔄 Updating target $TARGET_ID in rule $RULE"
            
            # Remove old target
            aws events remove-targets --rule "$RULE" --ids "$TARGET_ID"
            
            # Add new target with updated ARN
            NEW_ARN="arn:aws:lambda:$REGION:$ACCOUNT_ID:function:$NEW_FUNCTION_NAME"
            aws events put-targets --rule "$RULE" --targets "Id=$TARGET_ID,Arn=$NEW_ARN"
            
            # Add permission for EventBridge to invoke the new Lambda function
            aws lambda add-permission \
                --function-name "$NEW_FUNCTION_NAME" \
                --statement-id "allow-eventbridge-$RULE-$TARGET_ID" \
                --action lambda:InvokeFunction \
                --principal events.amazonaws.com \
                --source-arn "arn:aws:events:$REGION:$ACCOUNT_ID:rule/$RULE" \
                2>/dev/null || echo "⚠️ Permission may already exist"
            
            echo "✅ Updated target $TARGET_ID to point to $NEW_FUNCTION_NAME"
        done
    fi
done

# 2. Update CloudWatch Log Groups Subscription Filters
echo ""
echo "2️⃣ Updating CloudWatch Log Groups Subscription Filters..."

# Find log groups with subscription filters pointing to the old function
echo "🔍 Finding CloudWatch Log Groups with subscription filters..."
LOG_GROUPS=$(aws logs describe-log-groups --query 'logGroups[].logGroupName' --output text)

for LOG_GROUP in $LOG_GROUPS; do
    # Check if this log group has subscription filters
    FILTERS=$(aws logs describe-subscription-filters --log-group-name "$LOG_GROUP" --query 'subscriptionFilters[?contains(destinationArn, `'$OLD_FUNCTION_NAME'`)].filterName' --output text 2>/dev/null)
    
    if [ ! -z "$FILTERS" ]; then
        echo "✅ Found log group $LOG_GROUP with subscription filters pointing to old function"
        
        for FILTER_NAME in $FILTERS; do
            echo "🔄 Updating subscription filter $FILTER_NAME in log group $LOG_GROUP"
            
            # Get filter details
            FILTER_DETAILS=$(aws logs describe-subscription-filters --log-group-name "$LOG_GROUP" --filter-name-prefix "$FILTER_NAME" --query 'subscriptionFilters[0]' --output json)
            FILTER_PATTERN=$(echo "$FILTER_DETAILS" | jq -r '.filterPattern // ""')
            
            # Delete old subscription filter
            aws logs delete-subscription-filter --log-group-name "$LOG_GROUP" --filter-name "$FILTER_NAME"
            
            # Create new subscription filter with updated ARN
            NEW_ARN="arn:aws:lambda:$REGION:$ACCOUNT_ID:function:$NEW_FUNCTION_NAME"
            aws logs put-subscription-filter \
                --log-group-name "$LOG_GROUP" \
                --filter-name "$FILTER_NAME" \
                --filter-pattern "$FILTER_PATTERN" \
                --destination-arn "$NEW_ARN"
            
            # Add permission for CloudWatch Logs to invoke the new Lambda function
            aws lambda add-permission \
                --function-name "$NEW_FUNCTION_NAME" \
                --statement-id "allow-cloudwatch-logs-$(echo $LOG_GROUP | tr '/' '-')" \
                --action lambda:InvokeFunction \
                --principal logs.amazonaws.com \
                --source-arn "arn:aws:logs:$REGION:$ACCOUNT_ID:log-group:$LOG_GROUP:*" \
                2>/dev/null || echo "⚠️ Permission may already exist"
            
            echo "✅ Updated subscription filter $FILTER_NAME to point to $NEW_FUNCTION_NAME"
        done
    fi
done

# 3. Update CloudTrail Event Data Store (if using CloudTrail Lake)
echo ""
echo "3️⃣ Checking CloudTrail Event Data Stores..."

# List event data stores
EVENT_DATA_STORES=$(aws cloudtrail list-event-data-stores --query 'EventDataStores[].EventDataStoreArn' --output text 2>/dev/null)

if [ ! -z "$EVENT_DATA_STORES" ]; then
    echo "✅ Found CloudTrail Event Data Stores"
    for EDS_ARN in $EVENT_DATA_STORES; do
        echo "🔍 Checking Event Data Store: $EDS_ARN"
        # Note: Event Data Stores don't directly reference Lambda functions
        # They are queried by Lambda functions, so no update needed here
    done
else
    echo "ℹ️ No CloudTrail Event Data Stores found"
fi

# 4. Update any API Gateway integrations
echo ""
echo "4️⃣ Checking API Gateway integrations..."

# List REST APIs
REST_APIS=$(aws apigateway get-rest-apis --query 'items[].id' --output text 2>/dev/null)

if [ ! -z "$REST_APIS" ]; then
    for API_ID in $REST_APIS; do
        echo "🔍 Checking REST API: $API_ID"
        
        # Get resources for this API
        RESOURCES=$(aws apigateway get-resources --rest-api-id "$API_ID" --query 'items[].id' --output text 2>/dev/null)
        
        for RESOURCE_ID in $RESOURCES; do
            # Check methods for this resource
            METHODS=$(aws apigateway get-resource --rest-api-id "$API_ID" --resource-id "$RESOURCE_ID" --query 'resourceMethods' --output text 2>/dev/null)
            
            if [ "$METHODS" != "None" ] && [ ! -z "$METHODS" ]; then
                for METHOD in $METHODS; do
                    # Get integration details
                    INTEGRATION=$(aws apigateway get-integration --rest-api-id "$API_ID" --resource-id "$RESOURCE_ID" --http-method "$METHOD" --query 'uri' --output text 2>/dev/null)
                    
                    if [[ "$INTEGRATION" == *"$OLD_FUNCTION_NAME"* ]]; then
                        echo "✅ Found API Gateway integration pointing to old function"
                        echo "🔄 Updating integration for API $API_ID, Resource $RESOURCE_ID, Method $METHOD"
                        
                        # Update integration
                        NEW_URI="arn:aws:apigateway:$REGION:lambda:path/2015-03-31/functions/arn:aws:lambda:$REGION:$ACCOUNT_ID:function:$NEW_FUNCTION_NAME/invocations"
                        aws apigateway put-integration \
                            --rest-api-id "$API_ID" \
                            --resource-id "$RESOURCE_ID" \
                            --http-method "$METHOD" \
                            --type AWS_PROXY \
                            --integration-http-method POST \
                            --uri "$NEW_URI"
                        
                        # Add permission for API Gateway to invoke the new Lambda function
                        aws lambda add-permission \
                            --function-name "$NEW_FUNCTION_NAME" \
                            --statement-id "allow-apigateway-$API_ID" \
                            --action lambda:InvokeFunction \
                            --principal apigateway.amazonaws.com \
                            --source-arn "arn:aws:execute-api:$REGION:$ACCOUNT_ID:$API_ID/*/*" \
                            2>/dev/null || echo "⚠️ Permission may already exist"
                        
                        echo "✅ Updated API Gateway integration to point to $NEW_FUNCTION_NAME"
                    fi
                done
            fi
        done
    done
else
    echo "ℹ️ No REST APIs found"
fi

# 5. Clean up temporary files
echo ""
echo "🧹 Cleaning up temporary files..."
rm -f env-vars.json

echo ""
echo "✅ AWS artifacts update completed successfully!"
echo ""
echo "📋 Summary of updates:"
echo "✅ CloudWatch Events Rules updated to point to $NEW_FUNCTION_NAME"
echo "✅ CloudWatch Log Groups subscription filters updated"
echo "✅ API Gateway integrations updated (if any)"
echo "✅ Lambda permissions added for new integrations"
echo ""
echo "📋 Next steps:"
echo "1. Update dashboard to use new function endpoints"
echo "2. Test the complete integration"
echo "3. Monitor CloudWatch logs for the new function"
echo ""
echo "🔍 New Function ARN: arn:aws:lambda:$REGION:$ACCOUNT_ID:function:$NEW_FUNCTION_NAME"
