# AWS Bedrock Usage Control System - Source Code Documentation

## 📁 Source Code Organization

This folder contains all the source code artifacts that comprise the AWS Bedrock Usage Control System. The code is organized into logical categories for easy navigation and maintenance.

### 📂 Folder Structure

```
Source/
├── Dashboard/                    # Web dashboard and frontend components
├── Lambda Functions/             # AWS Lambda function implementations
├── Scripts/                      # Utility scripts and CLI tools
├── Database/                     # Database schemas and stored procedures
├── Configuration/                # Configuration files and templates
└── README_Source_Code.md         # This documentation file
```

## 🌐 Dashboard Components

### Location: `Dashboard/`

| File | Purpose | Technology |
|------|---------|------------|
| `bedrock_usage_dashboard_modular.html` | Main dashboard interface | HTML5, JavaScript, CSS3 |
| `login.html` | Authentication page | HTML5, JavaScript |
| `css/dashboard.css` | Dashboard styling | CSS3 |
| `js/dashboard.js` | Main dashboard logic | Vanilla JavaScript |
| `js/mysql-data-service.js` | MySQL data service | JavaScript |
| `js/blocking.js` | Blocking management | JavaScript |
| `js/charts.js` | Chart visualizations | Chart.js |
| `js/config.js` | Frontend configuration | JavaScript |
| `js/cost-analysis-v2.js` | Cost analysis features | JavaScript |
| `js/hourly-analytics.js` | Hourly usage analytics | JavaScript |

### Dashboard Features

#### Main Dashboard (`bedrock_usage_dashboard_modular.html`)
- **Multi-tab Interface**: User Consumption, Team Consumption, Consumption Details, Blocking Management
- **Real-time Data**: Live usage statistics and status updates
- **Interactive Charts**: Usage trends, cost analysis, team comparisons
- **Export Functionality**: CSV export for all data tables
- **Responsive Design**: Works on desktop and mobile devices

#### Key JavaScript Modules

**`dashboard.js`** - Core Dashboard Logic
```javascript
// Key functions:
- initializeDashboard()
- loadUserData()
- loadTeamData()
- refreshData()
- handleTabSwitching()
```

**`blocking.js`** - Blocking Management
```javascript
// Key functions:
- blockUser(userId, duration, reason)
- unblockUser(userId)
- getBlockingHistory()
- updateUserStatus()
```

**`mysql-data-service.js`** - Database Integration
```javascript
// Key functions:
- executeQuery(query)
- getUserUsage(userId)
- getTeamUsage(teamId)
- getBlockingOperations()
```

## ⚡ Lambda Functions

### Location: `Lambda Functions/`

| File | Purpose | Runtime | Memory | Timeout |
|------|---------|---------|--------|---------|
| `bedrock_daily_reset.py` | Daily reset operations (RDS MySQL) | Python 3.9 | 512 MB | 300s |
| `bedrock_email_service.py` | Email notification service | Python 3.9 | 256 MB | 30s |
| `test_email_service.py` | Email service testing | Python 3.9 | - | - |

### Current Lambda Functions (Deployed)

| Function Name | Source Location | Database | Purpose |
|---------------|----------------|----------|---------|
| `bedrock-realtime-usage-controller` | `bedrock-realtime-usage-controller.py` | RDS MySQL | **MERGED FUNCTION** - Real-time logging, quota checking, blocking, and email notifications |
| `bedrock-daily-reset` | `bedrock_daily_reset.py` | RDS MySQL | Daily reset operations |
| `bedrock-email-service` | `bedrock_email_service.py` | None | Email notifications |

### Recently Merged Functions (September 2025)

**Major Architecture Change**: The system has been consolidated from multiple Lambda functions into a single, more efficient merged function:

**New Merged Function**:
- `bedrock-realtime-usage-controller` - Combines all real-time processing functionality

**Functions Merged Into New Controller**:
- `bedrock-realtime-logger-fixed` (Real-time request logging)
- `bedrock-policy-manager-enhanced` (Policy management and blocking)

### Obsolete Functions (Removed)

The following functions were removed during the Lambda function consolidation (September 2025):
- `bedrock-realtime-logger-fixed` (merged into bedrock-realtime-usage-controller)
- `bedrock-policy-manager-enhanced` (merged into bedrock-realtime-usage-controller)
- `bedrock_usage_monitor_enhanced.py` (DynamoDB-based - legacy)
- `bedrock_usage_monitor.py` (DynamoDB-based - legacy)
- `bedrock_usage_monitor_with_email.py` (DynamoDB-based - legacy)
- `bedrock_policy_manager.py` (DynamoDB-based - legacy)

### Lambda Function Details

#### `bedrock-realtime-request-logger` - Real-time Request Logger
**Purpose**: Real-time logging of Bedrock API calls with CET timezone handling and RDS MySQL integration

**Key Features**:
- Real-time CloudTrail event processing with CET timezone
- Direct RDS MySQL logging with PyMySQL
- Auto-provisioning of new users
- Usage limit checking with stored procedures
- Email notifications via bedrock-email-service
- Comprehensive audit logging

**Key Functions**:
```python
def lambda_handler(event, context)
def extract_user_info(detail)
def log_bedrock_request(connection, user_info, request_details)
def check_user_limits(connection, user_id)
def send_notification_if_needed(user_id, usage_data)
```

**Environment Variables**:
- `RDS_ENDPOINT`: MySQL RDS endpoint
- `RDS_USERNAME`: Database username
- `RDS_PASSWORD`: Database password
- `RDS_DATABASE`: Database name
- `AWS_REGION`: AWS region
- `ACCOUNT_ID`: AWS account ID
- `EMAIL_SERVICE_FUNCTION`: Email service Lambda function name

#### `bedrock-mysql-query-executor` - Database Query Executor
**Purpose**: Database query executor for dashboard and analytics

**Supported Operations**:
- `get_user_usage`: Retrieve user usage statistics
- `get_team_usage`: Retrieve team usage statistics
- `get_cost_analysis`: Cost analysis queries
- `get_hourly_analytics`: Hourly usage patterns

**Key Functions**:
```python
def lambda_handler(event, context)
def execute_user_usage_query(connection, user_id)
def execute_team_usage_query(connection, team_id)
def execute_cost_analysis_query(connection, filters)
def execute_hourly_analytics_query(connection, date_range)
```

#### `bedrock_daily_reset.py` - Daily Reset
**Purpose**: Simplified daily reset operations for expired user blocks and administrative flag management

**Key Features**:
- **Selective Unblocking**: Only unblocks users whose `blocked_until` expiration date has passed
- **Administrative Safe Flag Management**: Removes `administrative_safe` flags from active users and newly unblocked users
- **Email Notifications**: Sends personalized reset notifications to unblocked users via email service
- **IAM Policy Management**: Removes deny policies to restore Bedrock access
- **CET Timezone Handling**: All operations performed in Central European Time
- **Comprehensive Audit Logging**: All operations logged for compliance

**Key Functions**:
```python
def lambda_handler(event, context)
def unblock_all_blocked_users_and_notify(connection)
def execute_user_unblocking(connection, user_id)
def remove_administrative_safe_flag(connection, user_id)
def implement_iam_unblocking(user_id)
def send_reset_email_notification(user_data)
```

**Scheduled Execution**: Runs daily at 00:00 CET via CloudWatch Events

**Database Operations**:
- Updates `user_blocking_status` table to unblock expired users
- Removes `administrative_safe` flags from `user_limits` table
- Logs all operations to `blocking_audit_log` table

**Integration**: Works with `bedrock-email-service` Lambda for user notifications

#### `bedrock_blocking_history.py` - History Tracking
**Purpose**: Audit trail and history management for blocking operations

**Supported Operations**:
- `get_history`: Retrieve paginated operation history
- `get_user_history`: Get operations for specific user
- `log_operation`: Record new operation

#### `bedrock_email_service.py` - Email Service
**Purpose**: Enhanced email notification service

**Email Types**:
- Warning emails (80% quota reached)
- Blocking emails (100% quota exceeded)
- Unblocking emails (daily reset)
- Admin blocking emails (manual admin block)
- Admin unblocking emails (manual admin unblock)

### Configuration Files

| File | Purpose |
|------|---------|
| `quota_config.json` | User and team quota definitions |
| `email_credentials.json` | SMTP credentials for email service |

## 🔧 Scripts and Utilities

### Location: `Scripts/`

| File | Purpose | Language |
|------|---------|----------|
| `provision_bedrock_user.py` | Complete user provisioning | Python |
| `bedrock_manager.py` | Main CLI interface | Python |
| `config.json` | AWS configuration | JSON |
| `provision.py` | Provisioning utilities | Python |
| Various migration scripts | Database and system setup | Shell/Python |

### Script Details

#### `provision_bedrock_user.py` - User Provisioning
**Purpose**: Complete user provisioning with all necessary configurations

**Usage**:
```bash
python3 provision_bedrock_user.py --username <username> --group <team_group>
```

**Features**:
- Creates IAM user with login profile
- Assigns to team group
- Creates user-specific Bedrock policy
- Configures CloudWatch logs and metrics
- Sets up usage limits and monitoring

#### `bedrock_manager.py` - CLI Manager
**Purpose**: Command-line interface for administrative operations

**Commands**:
```bash
python3 bedrock_manager.py user create <username> <person_name> <team>
python3 bedrock_manager.py user create-key <username> <tool_name>
python3 bedrock_manager.py user info <username>
python3 bedrock_manager.py group create <team_name>
```

### Module Structure

#### `user/` - User Management
- `user_manager.py`: User CRUD operations
- Functions: create_user, delete_user, create_api_key, list_users_by_team

#### `group/` - Group Management
- `group_manager.py`: Team/group operations
- Functions: create_group, delete_group, create_role_for_group

#### `policy/` - Policy Management
- `policy_manager.py`: IAM policy operations
- Functions: create_policy, delete_policy, attach_policy_to_user

#### `utils/` - Utilities
- `aws_utils.py`: AWS helper functions
- Common utilities for AWS service interactions

## 🗄️ Database Components

### Location: `Database/`

The database components are now organized in a structured folder hierarchy for better maintainability:

```
Database/
├── create_database.sql          # Simple database creation script
├── README.md                    # Database documentation
├── Tables/                      # Table creation scripts
│   ├── users.sql
│   ├── bedrock_requests.sql
│   ├── blocking_operations.sql
│   └── model_pricing.sql
├── Views/                       # Database view definitions
│   ├── v_user_realtime_usage.sql
│   ├── v_hourly_usage.sql
│   ├── v_model_usage_stats.sql
│   ├── v_team_usage_dashboard.sql
│   └── v_last_10_days_usage.sql
├── Stored_Procedures/           # Stored procedure definitions
│   ├── CheckUserLimits.sql
│   ├── LogBedrockRequest.sql
│   ├── ExecuteUserBlocking.sql
│   └── ExecuteUserUnblocking.sql
├── Indexes/                     # Additional index scripts
│   └── additional_indexes.sql
├── Functions/                   # Custom function scripts (empty)
└── Triggers/                    # Trigger scripts (empty)
```

### Database Structure Benefits

- **Organized by Object Type**: Each database object type has its own folder
- **Individual Files**: Each table, view, procedure has its own dedicated file
- **Easy Maintenance**: Changes to specific objects can be made in isolation
- **Version Control Friendly**: Individual files make it easier to track changes
- **Deployment Flexibility**: Can deploy specific components as needed

### Database Schema

#### Core Tables

**`users`** - User Configuration
```sql
CREATE TABLE users (
    user_id VARCHAR(255) PRIMARY KEY,
    team VARCHAR(100) NOT NULL,
    person_tag VARCHAR(255),
    daily_limit INT DEFAULT 250,
    monthly_limit INT DEFAULT 5000,
    warning_threshold INT DEFAULT 60,
    critical_threshold INT DEFAULT 85,
    is_blocked BOOLEAN DEFAULT FALSE,
    blocked_reason VARCHAR(500),
    blocked_until TIMESTAMP NULL,
    admin_protection_by VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

**`bedrock_requests`** - Individual Request Records
```sql
CREATE TABLE bedrock_requests (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    team VARCHAR(100) NOT NULL,
    request_timestamp TIMESTAMP(3) DEFAULT CURRENT_TIMESTAMP(3),
    date_only DATE GENERATED ALWAYS AS (DATE(request_timestamp)) STORED,
    hour_only INT GENERATED ALWAYS AS (HOUR(request_timestamp)) STORED,
    model_id VARCHAR(255) NOT NULL,
    model_name VARCHAR(255),
    request_type ENUM('invoke', 'invoke-stream', 'converse', 'converse-stream'),
    input_tokens INT DEFAULT 0,
    output_tokens INT DEFAULT 0,
    total_tokens INT GENERATED ALWAYS AS (input_tokens + output_tokens) STORED,
    cost_usd DECIMAL(10,6) DEFAULT 0.000000,
    -- Additional fields...
);
```

**`blocking_operations`** - Audit Trail
```sql
CREATE TABLE blocking_operations (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    operation ENUM('block', 'unblock', 'admin_protect', 'admin_unprotect') NOT NULL,
    reason VARCHAR(500),
    performed_by VARCHAR(255) NOT NULL,
    expires_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**`model_pricing`** - Cost Calculation
```sql
CREATE TABLE model_pricing (
    model_id VARCHAR(255) PRIMARY KEY,
    model_name VARCHAR(255) NOT NULL,
    input_token_price DECIMAL(10,8) DEFAULT 0.00000000,
    output_token_price DECIMAL(10,8) DEFAULT 0.00000000,
    region VARCHAR(50) DEFAULT 'us-east-1',
    effective_date DATE DEFAULT (CURDATE())
);
```

#### Optimized Views

**`v_user_realtime_usage`** - Real-time Usage Check
- Combines user configuration with current usage
- Calculates usage percentages
- Used for blocking decisions

**`v_hourly_usage`** - Hourly Analytics
- Aggregates usage by hour
- Supports trend analysis
- Used by dashboard charts

**`v_team_usage_dashboard`** - Team Dashboard Data
- Team-level usage aggregations
- Active user counts
- Cost summaries

#### Stored Procedures

**`CheckUserLimits`** - Limit Evaluation
```sql
CREATE PROCEDURE CheckUserLimits(
    IN p_user_id VARCHAR(255),
    OUT p_should_block BOOLEAN,
    OUT p_block_reason VARCHAR(500),
    OUT p_daily_usage INT,
    OUT p_monthly_usage INT,
    OUT p_daily_percent DECIMAL(5,2),
    OUT p_monthly_percent DECIMAL(5,2)
)
```

**`LogBedrockRequest`** - Request Logging
```sql
CREATE PROCEDURE LogBedrockRequest(
    IN p_user_id VARCHAR(255),
    IN p_team VARCHAR(100),
    IN p_model_id VARCHAR(255),
    -- Additional parameters...
)
```

## ⚙️ Configuration Files

### Location: `Configuration/`

| File | Purpose | Format |
|------|---------|--------|
| `package.json` | Node.js dependencies | JSON |
| `env_vars.json` | Environment variables | JSON |
| `test_bedrock_payload.json` | Test payloads | JSON |
| `test_blocking_payload.json` | Blocking test data | JSON |
| Various configuration files | System configuration | JSON |

### Key Configuration Files

#### `quota_config.json` - User/Team Quotas
```json
{
  "users": {
    "darwin_001": {
      "daily_limit": 150,
      "monthly_limit": 3500,
      "warning_threshold": 60,
      "critical_threshold": 85,
      "team": "team_darwin_group"
    }
  },
  "teams": {
    "team_darwin_group": {
      "monthly_limit": 25000,
      "warning_threshold": 60,
      "critical_threshold": 85
    }
  }
}
```

#### `email_credentials.json` - Email Configuration
```json
{
    "smtp_server": "email-smtp.eu-west-1.amazonaws.com",
    "smtp_port": 587,
    "smtp_username": "YOUR_SES_SMTP_USERNAME",
    "smtp_password": "YOUR_SES_SMTP_PASSWORD",
    "sender_email": "admin@yourcompany.com",
    "sender_name": "Bedrock Usage Control System"
}
```

## 🚀 Deployment and Usage

### Quick Start

1. **Deploy Infrastructure**: Use the deployment script from Installation Manual
2. **Configure Settings**: Update configuration files with your AWS account details
3. **Deploy Lambda Functions**: Package and deploy all Lambda functions
4. **Initialize Database**: Run database schema creation scripts
5. **Launch Dashboard**: Start the web server and access the dashboard

### Development Workflow

1. **Local Development**: Modify source files in this Source folder
2. **Testing**: Use test scripts and payloads for validation
3. **Deployment**: Copy modified files to appropriate locations
4. **Update Lambda**: Redeploy Lambda functions with changes
5. **Database Updates**: Apply schema changes using migration scripts

### File Dependencies

```
Dashboard ←→ Lambda Functions (via AWS SDK calls)
    ↓              ↓
Configuration Files ←→ Database (MySQL)
    ↓              ↓
Scripts ←→ AWS Resources (IAM, DynamoDB, etc.)
```

## 🔧 Customization Guide

### Adding New Features

1. **Dashboard**: Modify HTML/JS files in Dashboard folder
2. **Backend Logic**: Update Lambda functions
3. **Database**: Add tables/procedures in Database folder
4. **Configuration**: Update config files as needed
5. **Scripts**: Add utility scripts for new functionality

### Configuration Changes

1. **User Quotas**: Modify `quota_config.json`
2. **AWS Settings**: Update `config.json` files
3. **Email Settings**: Modify `email_credentials.json`
4. **Database**: Update schema files and redeploy

### Testing

1. **Unit Tests**: Use test files in Lambda Functions folder
2. **Integration Tests**: Use payload files in Configuration folder
3. **End-to-End**: Use dashboard and verify in AWS console

## 📝 Code Standards

### Python Code
- Follow PEP 8 style guidelines
- Use type hints where appropriate
- Include comprehensive error handling
- Add logging for debugging

### JavaScript Code
- Use ES6+ features
- Follow consistent naming conventions
- Include error handling for API calls
- Comment complex logic

### SQL Code
- Use consistent naming conventions
- Include proper indexing
- Add comments for complex queries
- Follow MySQL best practices

## 🔍 Troubleshooting

### Common Issues

1. **Lambda Timeouts**: Check function memory and timeout settings
2. **Database Connections**: Verify RDS security groups and credentials
3. **Dashboard Errors**: Check browser console and AWS credentials
4. **Email Failures**: Verify SES configuration and credentials

### Debug Information

- **Lambda Logs**: CloudWatch Logs for each function
- **Database Logs**: RDS slow query and error logs
- **Dashboard Logs**: Browser developer console
- **System Metrics**: CloudWatch custom metrics

---

**Last Updated**: January 2025  
**Version**: 2.0.0  
**Maintainer**: AWS Bedrock Usage Control System Team
