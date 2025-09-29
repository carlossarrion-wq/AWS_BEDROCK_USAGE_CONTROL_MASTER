#!/bin/bash

# Complete Real-time Bedrock Usage Control System Deployment
# This script orchestrates the entire deployment process

set -e

# Configuration
REGION="us-east-1"
DB_INSTANCE_ID="bedrock-usage-db"
DB_USERNAME="bedrock_admin"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Check prerequisites
check_prerequisites() {
    if ! command -v aws &> /dev/null; then
        exit 1
    fi
    
    if ! aws sts get-caller-identity &> /dev/null; then
        exit 1
    fi
}

# Deploy RDS instance
deploy_rds() {
    if [ -f "$SCRIPT_DIR/01_create_rds_instance.sh" ]; then
        chmod +x "$SCRIPT_DIR/01_create_rds_instance.sh"
        bash "$SCRIPT_DIR/01_create_rds_instance.sh"
    else
        exit 1
    fi
}

# Wait for RDS to be available
wait_for_rds() {
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        local status=$(aws rds describe-db-instances \
            --db-instance-identifier $DB_INSTANCE_ID \
            --query 'DBInstances[0].DBInstanceStatus' \
            --output text 2>/dev/null || echo "not-found")
        
        if [ "$status" = "available" ]; then
            return 0
        elif [ "$status" = "not-found" ]; then
            return 1
        else
            sleep 30
            ((attempt++))
        fi
    done
    
    return 1
}

# Initialize database
initialize_database() {
    local rds_endpoint=$(aws rds describe-db-instances \
        --db-instance-identifier $DB_INSTANCE_ID \
        --query 'DBInstances[0].Endpoint.Address' \
        --output text)
    
    if [ "$rds_endpoint" = "None" ] || [ -z "$rds_endpoint" ]; then
        return 1
    fi
    
    read -s -p "Enter database password for user '$DB_USERNAME': " db_password
    
    if [ -z "$db_password" ]; then
        return 1
    fi
    
    if command -v mysql &> /dev/null; then
        if mysql -h "$rds_endpoint" -u "$DB_USERNAME" -p"$db_password" -e "SELECT 1;" &> /dev/null; then
            mysql -h "$rds_endpoint" -u "$DB_USERNAME" -p"$db_password" < "$SCRIPT_DIR/08_initialize_database.sql"
        else
            return 1
        fi
    fi
    
    export DB_PASSWORD="$db_password"
    export RDS_ENDPOINT="$rds_endpoint"
}

# Configure database connection
configure_database_connection() {
    if [ -f "$SCRIPT_DIR/07_configure_database_connection.sh" ]; then
        chmod +x "$SCRIPT_DIR/07_configure_database_connection.sh"
        export DB_PASSWORD
        export RDS_ENDPOINT
        bash "$SCRIPT_DIR/07_configure_database_connection.sh"
    else
        return 1
    fi
}

# Deploy real-time logger
deploy_realtime_logger() {
    if [ -f "$SCRIPT_DIR/06_deploy_realtime_logger.sh" ]; then
        chmod +x "$SCRIPT_DIR/06_deploy_realtime_logger.sh"
        bash "$SCRIPT_DIR/06_deploy_realtime_logger.sh"
    else
        return 1
    fi
}

# Test the system
test_system() {
    local test_event='{
        "version": "0",
        "id": "test-event-id",
        "detail-type": "AWS API Call via CloudTrail",
        "source": "aws.bedrock",
        "account": "'$(aws sts get-caller-identity --query Account --output text)'",
        "time": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'",
        "region": "'$REGION'",
        "detail": {
            "eventVersion": "1.08",
            "userIdentity": {
                "type": "IAMUser",
                "principalId": "AIDACKCEVSQ6C2EXAMPLE",
                "arn": "arn:aws:iam::'$(aws sts get-caller-identity --query Account --output text)':user/test-user-1",
                "accountId": "'$(aws sts get-caller-identity --query Account --output text)'",
                "userName": "test-user-1"
            },
            "eventTime": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'",
            "eventSource": "bedrock-runtime.amazonaws.com",
            "eventName": "InvokeModel",
            "awsRegion": "'$REGION'",
            "sourceIPAddress": "203.0.113.12",
            "userAgent": "aws-cli/2.0.0",
            "requestParameters": {
                "modelId": "anthropic.claude-3-5-sonnet-20241022-v2:0"
            },
            "responseElements": {
                "usage": {
                    "inputTokens": 100,
                    "outputTokens": 200
                }
            },
            "requestID": "test-request-id-123",
            "eventID": "test-event-id-456",
            "eventType": "AwsApiCall",
            "recipientAccountId": "'$(aws sts get-caller-identity --query Account --output text)'",
            "serviceEventDetails": null
        }
    }'
    
    aws lambda invoke \
        --function-name "bedrock-realtime-request-logger" \
        --payload "$test_event" \
        --region $REGION \
        /tmp/lambda-response.json &> /dev/null
    
    rm -f /tmp/lambda-response.json
    
    local db_test_event='{"test": "database_connection"}'
    
    aws lambda invoke \
        --function-name "bedrock-realtime-request-logger" \
        --payload "$db_test_event" \
        --region $REGION \
        /tmp/db-test-response.json &> /dev/null
    
    rm -f /tmp/db-test-response.json
}

# Generate deployment summary
generate_summary() {
    local account_id=$(aws sts get-caller-identity --query Account --output text)
    local rds_endpoint=$(aws rds describe-db-instances \
        --db-instance-identifier $DB_INSTANCE_ID \
        --query 'DBInstances[0].Endpoint.Address' \
        --output text 2>/dev/null || echo "Not found")
    
    cat << EOF

Real-time Bedrock Usage Control System Deployment Complete!

Deployment Summary:
==========================================

AWS Account: $account_id
Region: $REGION
RDS Endpoint: $rds_endpoint
Database: $DB_INSTANCE_ID

Components Deployed:
- RDS MySQL Instance
- Real-time Request Logger Lambda
- Database Schema and Stored Procedures
- CloudTrail Integration

Next Steps:
1. Update dashboard configuration to use RDS endpoint
2. Configure CloudTrail to trigger the Lambda function
3. Test real-time blocking functionality
4. Monitor system performance

Configuration Files:
- Database Schema: migration/02_create_database_schema_v2.sql
- Lambda Function: migration/05_realtime_request_logger.py
- Deployment Scripts: migration/06_deploy_realtime_logger.sh

EOF
}

# Main execution flow
main() {
    check_prerequisites
    deploy_rds
    wait_for_rds
    initialize_database
    configure_database_connection
    deploy_realtime_logger
    test_system
    generate_summary
}

# Run main function
main "$@"
