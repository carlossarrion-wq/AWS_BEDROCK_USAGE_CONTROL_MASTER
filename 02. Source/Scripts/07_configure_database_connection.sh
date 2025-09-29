#!/bin/bash

# Configure Database Connection for Real-time Architecture
# This script sets up the database credentials and connection configuration

set -e

echo "🔧 Configuring Database Connection for Real-time Architecture..."

# Configuration
SECRET_NAME="rds-db-credentials/bedrock-usage-db"
REGION="us-east-1"
DB_USERNAME="bedrock_admin"
LAMBDA_FUNCTION_NAME="bedrock-realtime-request-logger"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Check if AWS CLI is configured
if ! aws sts get-caller-identity &> /dev/null; then
    print_error "AWS CLI is not configured. Please run 'aws configure' first."
    exit 1
fi

# Get RDS instance endpoint
echo "🔍 Looking for RDS instance..."
RDS_ENDPOINT=$(aws rds describe-db-instances \
    --db-instance-identifier bedrock-usage-db \
    --query 'DBInstances[0].Endpoint.Address' \
    --output text 2>/dev/null || echo "")

if [ "$RDS_ENDPOINT" = "" ] || [ "$RDS_ENDPOINT" = "None" ]; then
    print_warning "RDS instance 'bedrock-usage-db' not found. Please create it first using 01_create_rds_instance.sh"
    echo "Using placeholder endpoint for now..."
    RDS_ENDPOINT="bedrock-usage-db.cluster-xyz.us-east-1.rds.amazonaws.com"
else
    print_status "Found RDS instance: $RDS_ENDPOINT"
fi

# Prompt for database password
echo ""
print_info "Please enter the database password for user '$DB_USERNAME':"
read -s DB_PASSWORD
echo ""

if [ -z "$DB_PASSWORD" ]; then
    print_error "Password cannot be empty"
    exit 1
fi

# Create secret in AWS Secrets Manager
echo "🔐 Creating database credentials secret..."
SECRET_VALUE=$(cat << EOF
{
    "username": "$DB_USERNAME",
    "password": "$DB_PASSWORD",
    "engine": "mysql",
    "host": "$RDS_ENDPOINT",
    "port": 3306,
    "dbname": "bedrock_usage"
}
EOF
)

aws secretsmanager create-secret \
    --name "$SECRET_NAME" \
    --description "Database credentials for Bedrock usage monitoring system" \
    --secret-string "$SECRET_VALUE" \
    --region $REGION || {
    print_warning "Secret might already exist, updating..."
    aws secretsmanager update-secret \
        --secret-id "$SECRET_NAME" \
        --secret-string "$SECRET_VALUE" \
        --region $REGION
}

print_status "Database credentials secret created/updated"

# Update Lambda function environment variables
echo "🔧 Updating Lambda function environment variables..."
aws lambda update-function-configuration \
    --function-name $LAMBDA_FUNCTION_NAME \
    --environment Variables='{
        "DB_HOST":"'$RDS_ENDPOINT'",
        "DB_NAME":"bedrock_usage",
        "DB_SECRET_NAME":"'$SECRET_NAME'",
        "AWS_REGION":"'$REGION'"
    }' \
    --region $REGION

print_status "Lambda environment variables updated"

# Create VPC configuration for Lambda (if RDS is in VPC)
echo "🌐 Checking VPC configuration..."
VPC_ID=$(aws rds describe-db-instances \
    --db-instance-identifier bedrock-usage-db \
    --query 'DBInstances[0].DBSubnetGroup.VpcId' \
    --output text 2>/dev/null || echo "")

if [ "$VPC_ID" != "" ] && [ "$VPC_ID" != "None" ]; then
    print_info "RDS is in VPC: $VPC_ID"
    
    # Get subnet IDs
    SUBNET_IDS=$(aws rds describe-db-instances \
        --db-instance-identifier bedrock-usage-db \
        --query 'DBInstances[0].DBSubnetGroup.Subnets[].SubnetIdentifier' \
        --output text 2>/dev/null || echo "")
    
    # Get security group ID
    SECURITY_GROUP_ID=$(aws rds describe-db-instances \
        --db-instance-identifier bedrock-usage-db \
        --query 'DBInstances[0].VpcSecurityGroups[0].VpcSecurityGroupId' \
        --output text 2>/dev/null || echo "")
    
    if [ "$SUBNET_IDS" != "" ] && [ "$SECURITY_GROUP_ID" != "" ]; then
        # Convert space-separated subnet IDs to comma-separated
        SUBNET_LIST=$(echo $SUBNET_IDS | tr ' ' ',')
        
        print_info "Configuring Lambda VPC access..."
        aws lambda update-function-configuration \
            --function-name $LAMBDA_FUNCTION_NAME \
            --vpc-config SubnetIds=[$SUBNET_LIST],SecurityGroupIds=[$SECURITY_GROUP_ID] \
            --region $REGION
        
        print_status "Lambda VPC configuration updated"
    else
        print_warning "Could not retrieve VPC configuration details"
    fi
else
    print_info "RDS is not in a VPC or VPC info not available"
fi

echo ""
print_status "🎉 Database connection configured successfully!"
echo ""
echo "📋 Configuration Summary:"
echo "  • Secret Name: $SECRET_NAME"
echo "  • Database Host: $RDS_ENDPOINT"
echo "  • Database Name: bedrock_usage"
echo "  • Lambda Function: $LAMBDA_FUNCTION_NAME"
echo ""
echo "🔧 Next Steps:"
echo "  1. Run the database schema creation script (08_initialize_database.sql)"
echo "  2. Test the database connection"
echo "  3. Deploy the complete system"
echo ""
