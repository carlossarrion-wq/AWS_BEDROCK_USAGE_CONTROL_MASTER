# AWS Bedrock Usage Control System - Documentation Overview

## 📋 Documentation Structure

This documentation package provides comprehensive information for deploying, configuring, and maintaining the AWS Bedrock Usage Control System. The documentation is organized into several key sections:

### 📁 Documentation Files

| File | Purpose | Target Audience |
|------|---------|----------------|
| `README.md` | Complete project overview and architecture | All users |
| `01_Complete_Installation_Guide.md` | Step-by-step installation instructions | System administrators |
| `02_AWS_Resources_Documentation.md` | Detailed AWS resource specifications | DevOps engineers |
| `03_IAM_Policies_and_Roles.json` | IAM configuration definitions | Security engineers |
| `04_Complete_Deployment_Script.sh` | Automated deployment script | System administrators |
| `00_Documentation_Overview.md` | This overview document | All users |

## 🚀 Quick Start Guide

### For First-Time Users

1. **Start Here**: Read `README.md` for project overview and architecture
2. **Installation**: Follow `01_Complete_Installation_Guide.md` for manual setup
3. **Quick Deploy**: Use `04_Complete_Deployment_Script.sh` for automated deployment
4. **Resources**: Reference `02_AWS_Resources_Documentation.md` for detailed specifications

### For Experienced Users

1. **Quick Deploy**: Run `./04_Complete_Deployment_Script.sh`
2. **Customize**: Modify configurations in `03_IAM_Policies_and_Roles.json`
3. **Reference**: Use `02_AWS_Resources_Documentation.md` for troubleshooting

## 📖 Document Descriptions

### README.md - Project Overview
**Purpose**: Comprehensive project documentation covering architecture, components, and workflows.

**Key Sections**:
- System architecture diagrams
- Component descriptions
- Configuration management
- Security considerations
- Performance optimization
- Future roadmap

**Best For**: Understanding the overall system design and capabilities.

### 01_Complete_Installation_Guide.md - Installation Manual
**Purpose**: Step-by-step instructions for manual system deployment.

**Key Sections**:
- Prerequisites validation
- AWS account setup
- Infrastructure provisioning
- Database configuration
- Lambda deployment
- Testing procedures

**Best For**: Manual deployment with full control over each step.

### 02_AWS_Resources_Documentation.md - Resource Specifications
**Purpose**: Detailed documentation of all AWS resources and their configurations.

**Key Sections**:
- IAM roles and policies
- Lambda function specifications
- RDS MySQL database configuration
- EventBridge rules
- CloudWatch resources

**Best For**: Understanding resource requirements and troubleshooting issues.

### 03_IAM_Policies_and_Roles.json - Security Configuration
**Purpose**: Complete IAM policy and role definitions in JSON format.

**Key Sections**:
- Role definitions with trust policies
- Custom policy documents
- User and group management
- Security considerations
- Policy versioning strategy

**Best For**: Security review and custom policy modifications.

### 04_Complete_Deployment_Script.sh - Automated Deployment
**Purpose**: Fully automated deployment script with error handling and validation.

**Key Features**:
- Prerequisites validation
- Resource creation with error handling
- Configuration management
- Testing and verification
- Deployment summary generation

**Best For**: Quick deployment with minimal manual intervention.

## 🎯 Usage Scenarios

### Scenario 1: New Deployment
**Goal**: Deploy the system from scratch in a new AWS account.

**Steps**:
1. Review `README.md` for system understanding
2. Run `./04_Complete_Deployment_Script.sh` for automated deployment
3. Follow post-deployment steps in the generated summary
4. Reference `02_AWS_Resources_Documentation.md` for troubleshooting

### Scenario 2: Manual Deployment
**Goal**: Deploy with full control over each component.

**Steps**:
1. Read `README.md` for architecture overview
2. Follow `01_Complete_Installation_Guide.md` step by step
3. Use `03_IAM_Policies_and_Roles.json` for security configuration
4. Reference `02_AWS_Resources_Documentation.md` for specifications

### Scenario 3: Existing System Modification
**Goal**: Modify or extend an existing deployment.

**Steps**:
1. Review `02_AWS_Resources_Documentation.md` for current state
2. Modify policies in `03_IAM_Policies_and_Roles.json` as needed
3. Use relevant sections of `01_Complete_Installation_Guide.md`
4. Test changes using procedures in the installation guide

### Scenario 4: Troubleshooting
**Goal**: Diagnose and fix system issues.

**Steps**:
1. Check `02_AWS_Resources_Documentation.md` for resource specifications
2. Review logs and metrics as described in `README.md`
3. Use troubleshooting section in `01_Complete_Installation_Guide.md`
4. Verify configurations against `03_IAM_Policies_and_Roles.json`

## 🔧 Configuration Management

### Key Configuration Files

| File | Location | Purpose |
|------|----------|---------|
| `src/config.json` | Project root | AWS account and region settings |
| `quota_config.json` | Project root | User and team quota definitions |
| `email_credentials.json` | Lambda functions | Email service configuration |
| Various `.sql` files | `migration/` | Database schema definitions |

### Environment Variables

The system uses several environment variables for configuration:

```bash
export AWS_REGION="eu-west-1"
export AWS_ACCOUNT_ID="701055077130"
export PROJECT_NAME="bedrock-usage-control"
```

### Customization Points

1. **Account ID**: Update in all configuration files
2. **Region**: Modify region settings across all components
3. **Quotas**: Adjust user and team limits in `quota_config.json`
4. **Email**: Configure SMTP settings in `email_credentials.json`
5. **Database**: Modify schema in SQL files as needed

## 🛡️ Security Considerations

### IAM Best Practices
- All policies follow principle of least privilege
- Roles are service-specific with minimal permissions
- Cross-account access considerations documented

### Data Protection
- Encryption at rest for all data stores
- Encryption in transit for all communications
- Secure credential storage in AWS Secrets Manager

### Access Control
- Role-based access for different system components
- Dashboard access through dedicated IAM role
- User blocking through dynamic policy management

## 📊 Monitoring and Maintenance

### Key Metrics to Monitor
- Lambda function execution metrics
- RDS MySQL connection and query performance
- User blocking/unblocking operations
- Email notification delivery rates

### Regular Maintenance Tasks
- Review and update user quotas
- Monitor system costs and usage patterns
- Update model pricing information
- Review audit logs for compliance
- Monitor RDS MySQL performance and storage

### Backup and Recovery
- RDS MySQL automated backups configured
- Point-in-time recovery available for RDS
- Lambda function versioning for rollback capability
- Database schema versioning in migration scripts

## 🚨 Troubleshooting Quick Reference

### Common Issues

| Issue | Likely Cause | Solution Reference |
|-------|--------------|-------------------|
| Lambda timeout errors | Insufficient timeout/memory | `01_Complete_Installation_Guide.md` |
| Database connection failures | Security group/credentials | `02_AWS_Resources_Documentation.md` |
| Dashboard not loading data | IAM permissions/CORS | `README.md` troubleshooting section |
| Users not being blocked | EventBridge/Lambda issues | `01_Complete_Installation_Guide.md` |
| Email notifications failing | SES configuration | `02_AWS_Resources_Documentation.md` |

### Log Locations
- Lambda logs: CloudWatch Logs `/aws/lambda/function-name`
- Application logs: Custom log groups
- Database logs: RDS slow query and error logs
- System metrics: CloudWatch custom metrics

## 📞 Support and Resources

### Documentation Hierarchy
1. **This Overview** - Start here for navigation
2. **README.md** - System architecture and design
3. **Installation Guide** - Step-by-step procedures
4. **Resource Documentation** - Technical specifications
5. **Configuration Files** - Security and policy definitions

### Getting Help
1. Check the troubleshooting sections in relevant documents
2. Review CloudWatch logs for error messages
3. Verify configurations against the documentation
4. Use the test scripts to validate system functionality

### Contributing to Documentation
When updating the system:
1. Update relevant configuration files
2. Modify documentation to reflect changes
3. Test deployment scripts with new configurations
4. Update this overview if new documents are added

## 📈 Version Information

- **Documentation Version**: 2.1.0
- **System Version**: 2.1.0
- **Last Updated**: September 2025
- **Compatibility**: AWS CLI v2.x, Python 3.9+

### Recent Updates (v2.1.0)
- **Enhanced Email Service**: Professional HTML email templates with sophisticated styling
- **Improved Lambda Integration**: Fixed bedrock-email-service handler configuration
- **Color-Coded Notifications**: Visual distinction for different notification types
- **Responsive Email Design**: Mobile-friendly email templates
- **CET Timezone Support**: All timestamps in Central European Time

## 🔄 Document Maintenance

### Update Schedule
- **Monthly**: Review for accuracy and completeness
- **After Changes**: Update immediately when system changes
- **Quarterly**: Comprehensive review and optimization

### Change Log
- **v2.1.0**: Enhanced email service with professional HTML templates and improved Lambda integration
- **v2.0.0**: Complete documentation rewrite with enhanced deployment automation
- **v1.x**: Initial documentation versions (legacy)

---

**Note**: This documentation is maintained alongside the AWS Bedrock Usage Control System. For the most current version, always refer to the project repository.
