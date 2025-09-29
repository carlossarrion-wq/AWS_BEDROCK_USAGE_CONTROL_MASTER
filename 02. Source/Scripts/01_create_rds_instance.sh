#!/bin/bash

# AWS Bedrock Usage Dashboard - RDS MySQL Setup Script
# This script creates the RDS MySQL instance for the dashboard

set -e

echo "🚀 Creating RDS MySQL instance for Bedrock Usage Dashboard..."

# Configuration variables
DB_INSTANCE_ID="bedrock-usage-mysql"
DB_NAME="bedrock_usage"
DB_USERNAME="admin"
DB_PASSWORD="BedrockUsage2024!" # Change this to a secure password
DB_INSTANCE_CLASS="db.t3.micro"
ALLOCATED_STORAGE="20"
ENGINE_VERSION="8.0.43"

# Get default VPC and subnet group
DEFAULT_VPC=$(aws ec2 describe-vpcs --filters "Name=is-default,Values=true" --query 'Vpcs[0].VpcId' --output text)
echo "📍 Using default VPC: $DEFAULT_VPC"

# Check if security group already exists
SECURITY_GROUP_ID=$(aws ec2 describe-security-groups \
    --group-names bedrock-usage-rds-sg \
    --query 'SecurityGroups[0].GroupId' \
    --output text 2>/dev/null || echo "")

if [ -z "$SECURITY_GROUP_ID" ]; then
    # Create security group for RDS
    SECURITY_GROUP_ID=$(aws ec2 create-security-group \
        --group-name bedrock-usage-rds-sg \
        --description "Security group for Bedrock Usage RDS MySQL instance" \
        --vpc-id $DEFAULT_VPC \
        --query 'GroupId' --output text)
    
    echo "🔒 Created security group: $SECURITY_GROUP_ID"
    
    # Allow MySQL access from Lambda functions (port 3306)
    aws ec2 authorize-security-group-ingress \
        --group-id $SECURITY_GROUP_ID \
        --protocol tcp \
        --port 3306 \
        --source-group $SECURITY_GROUP_ID
    
    echo "✅ Configured security group rules"
else
    echo "🔒 Using existing security group: $SECURITY_GROUP_ID"
fi

# Create RDS instance
echo "🏗️ Creating RDS MySQL instance (this may take 10-15 minutes)..."

aws rds create-db-instance \
    --db-instance-identifier $DB_INSTANCE_ID \
    --db-instance-class $DB_INSTANCE_CLASS \
    --engine mysql \
    --engine-version $ENGINE_VERSION \
    --master-username $DB_USERNAME \
    --master-user-password $DB_PASSWORD \
    --allocated-storage $ALLOCATED_STORAGE \
    --storage-type gp2 \
    --vpc-security-group-ids $SECURITY_GROUP_ID \
    --db-name $DB_NAME \
    --backup-retention-period 7 \
    --storage-encrypted \
    --deletion-protection \
    --no-multi-az \
    --no-publicly-accessible

echo "⏳ Waiting for RDS instance to be available..."

# Wait for the instance to be available
aws rds wait db-instance-available --db-instance-identifier $DB_INSTANCE_ID

# Get the RDS endpoint
RDS_ENDPOINT=$(aws rds describe-db-instances \
    --db-instance-identifier $DB_INSTANCE_ID \
    --query 'DBInstances[0].Endpoint.Address' \
    --output text)

echo "✅ RDS MySQL instance created successfully!"
echo "📍 RDS Endpoint: $RDS_ENDPOINT"
echo "🔑 Database Name: $DB_NAME"
echo "👤 Username: $DB_USERNAME"
echo "🔒 Password: $DB_PASSWORD"
echo ""
echo "💡 Save these credentials securely!"
echo "💡 Next step: Run 02_create_database_schema.sql"

# Save connection details to file
cat > rds_connection_details.txt << EOF
RDS_ENDPOINT=$RDS_ENDPOINT
DB_NAME=$DB_NAME
DB_USERNAME=$DB_USERNAME
DB_PASSWORD=$DB_PASSWORD
SECURITY_GROUP_ID=$SECURITY_GROUP_ID
EOF

echo "📄 Connection details saved to rds_connection_details.txt"
