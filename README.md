# AWS Bedrock Usage Control System - Complete Documentation

## 📋 Project Overview

The **AWS Bedrock Usage Control System** is a comprehensive enterprise-grade solution for monitoring, controlling, and managing AWS Bedrock usage across organizations. This system provides real-time usage tracking, automatic blocking capabilities, administrative protection mechanisms, and a modern web dashboard for complete visibility and control.

### 🎯 Core Objectives

- **Real-time Usage Monitoring**: Track every Bedrock API call with detailed metrics and cost analysis
- **Intelligent Blocking System**: Automatic user blocking with administrative protection mechanisms
- **Granular Access Control**: User, team, and tool-specific permissions and quotas
- **Cost Management**: Detailed cost tracking and budget enforcement
- **Audit & Compliance**: Complete audit trail of all operations and user activities
- **Modern Dashboard**: Interactive web interface for monitoring and management

## 🏗️ System Architecture

### High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    AWS BEDROCK USAGE CONTROL SYSTEM                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────────────┐  │
│  │   Web Dashboard │    │   CLI Manager   │    │  Lambda Functions       │  │
│  │   (HTML/JS)     │    │   (Python)      │    │  (RDS MySQL)            │  │
│  │                 │    │                 │    │                         │  │
│  │ • User Mgmt     │    │ • User Creation │    │ • Realtime Controller   │  │
│  │ • Team Analysis │    │ • Policy Mgmt   │    │ • Daily Reset           │  │
│  │ • Cost Tracking │    │ • Group Mgmt    │    │ • Email Service         │  │
│  │ • Blocking Mgmt │    │ • Provisioning  │    │ • MySQL Query Executor  │  │
│  └─────────────────┘    └─────────────────┘    └─────────────────────────┘  │
│           │                       │                           │              │
│           └───────────────────────┼───────────────────────────┘              │
│                                   │                                          │
│  ┌─────────────────────────────────┼─────────────────────────────────────────┐ │
│  │                    AWS CLOUD INFRASTRUCTURE                              │ │
│  │                                 │                                         │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────────────────┐ │ │
│  │  │     IAM     │  │ CloudWatch  │  │            Lambda Functions         │ │ │
│  │  │             │  │             │  │                                     │ │ │
│  │  │ • Users     │  │ • Metrics   │  │ • bedrock-realtime-usage-controller │ │ │
│  │  │ • Groups    │  │ • Logs      │  │ • bedrock-daily-reset               │ │ │
│  │  │ • Roles     │  │ • Alarms    │  │ • bedrock-email-service             │ │ │
│  │  │ • Policies  │  │ • Filters   │  │ • bedrock-mysql-query-executor      │ │ │
│  │  └─────────────┘  └─────────────┘  └─────────────────────────────────────┘ │ │
│  │                                                                            │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────────────────┐ │ │
│  │  │ CloudTrail  │  │ EventBridge │  │              RDS MySQL              │ │ │
│  │  │             │  │             │  │                                     │ │ │
│  │  │ • API Calls │  │ • Rules     │  │ • users                             │ │ │
│  │  │ • Audit Log │  │ • Triggers  │  │ • bedrock_requests                  │ │ │
│  │  │ • Events    │  │ • Schedule  │  │ • blocking_operations               │ │ │
│  │  │             │  │             │  │ • model_pricing                     │ │ │
│  │  └─────────────┘  └─────────────┘  └─────────────────────────────────────┘ │ │
│  │                                                                            │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────────────────┐ │ │
│  │  │     SNS     │  │     SES     │  │            Gmail SMTP               │ │ │
│  │  │             │  │             │  │                                     │ │ │
│  │  │ • Alerts    │  │ • Email     │  │ • Email Notifications               │ │ │
│  │  │ • Topics    │  │ • Templates │  │ • Warning Emails                    │ │ │
│  │  │ • Subs      │  │ • Delivery  │  │ • Blocking Emails                   │ │ │
│  │  └─────────────┘  └─────────────┘  └─────────────────────────────────────┘ │ │
│  └─────────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Data Flow Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   User Makes    │───▶│   CloudTrail    │───▶│   EventBridge   │
│ Bedrock Request │    │   Captures      │    │   Processes     │
│                 │    │     Event       │    │     Event       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                        │
                                                        ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Email & SNS   │◀───│ Realtime Usage  │◀───│   Lambda        │
│  Notifications  │    │   Controller    │    │  Triggered      │
│                 │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │ Automatic       │
                       │ Blocking &      │
                       │ Policy Mgmt     │
                       │ (if needed)     │
                       └─────────────────┘
```

## 📁 Project Structure

```
AWS_BEDROCK_USAGE_CONTROL/
├── 📄 README.md                                    # This complete project documentation
├── 📄 .gitignore                                   # Git ignore configuration
│
├── 🗂️ 01. Project documents/                       # 📋 COMPLETE DOCUMENTATION
│   ├── 📄 00_DOCUMENTATION_SUMMARY.md              # Documentation overview
│   └── 🗂️ Installation Manual/                     # Detailed installation guides
│       ├── 📄 00_Documentation_Overview.md         # Navigation guide
│       ├── 📄 01_Complete_Installation_Guide.md    # Step-by-step installation
│       ├── 📄 02_AWS_Resources_Documentation.md    # AWS resource specifications
│       ├── 📄 03_IAM_Policies_and_Roles.json      # IAM configuration
│       └── 📄 04_Complete_Deployment_Script.sh     # Automated deployment
│
├── 🗂️ 02. Source/                                  # 🔧 COMPLETE SOURCE CODE
│   ├── 📄 README_Source_Code.md                    # Source code documentation
│   │
│   ├── 🗂️ Dashboard/                               # 🌐 Web Dashboard Components
│   │   ├── 📄 bedrock_usage_dashboard_modular.html # Main dashboard interface
│   │   ├── 📄 login.html                           # Authentication page
│   │   ├── 🗂️ css/                                 # Dashboard styling
│   │   │   └── 📄 dashboard.css                    # Main dashboard styles
│   │   └── 🗂️ js/                                  # Dashboard JavaScript
│   │       ├── 📄 dashboard.js                     # Main dashboard logic
│   │       ├── 📄 mysql-data-service.js            # MySQL data service
│   │       ├── 📄 blocking.js                      # Blocking management
│   │       ├── 📄 charts.js                        # Chart visualizations
│   │       ├── 📄 config.js                        # Frontend configuration
│   │       ├── 📄 cost-analysis-v2.js              # Cost analysis features
│   │       └── 📄 hourly-analytics.js              # Hourly usage analytics
│   │
│   ├── 🗂️ Lambda Functions/                        # ⚡ AWS LAMBDA FUNCTIONS
│   │   ├── 📄 bedrock-realtime-usage-controller.py # 🔥 MAIN CONTROLLER (NEW)
│   │   ├── 📄 bedrock_daily_reset.py               # Daily reset operations
│   │   ├── 📄 bedrock_email_service.py             # Email notification service
│   │   ├── 📄 bedrock_mysql_query_executor.py      # Database query executor
│   │   ├── 📄 lambda_function.py                   # Lambda entry point
│   │   ├── 📄 email_credentials.json               # Email service credentials
│   │   ├── 📄 quota_config.json                    # User/team quota configuration
│   │   ├── 📄 test_email_service.py                # Email service testing
│   │   ├── 📄 README.md                            # Lambda functions documentation
│   │   ├── 🗂️ aws-backups/                         # AWS deployment backups
│   │   ├── 🗂️ pymysql/                             # MySQL Python driver
│   │   └── 🗂️ pytz/                                # Timezone handling library
│   │
│   ├── 🗂️ Scripts/                                 # 🔧 CLI Management & Deployment
│   │   ├── 📄 bedrock_manager.py                   # Main CLI interface
│   │   ├── 📄 config.json                          # AWS configuration
│   │   ├── 📄 provision.py                         # Provisioning utilities
│   │   ├── 📄 provision_bedrock_user.py            # User provisioning
│   │   ├── 📄 deploy_bedrock_realtime_usage_controller.sh # Deploy main controller
│   │   ├── 📄 deploy_bedrock_daily_reset.sh        # Deploy daily reset function
│   │   ├── 📄 update_cloudtrail_for_new_function.sh # Update AWS artifacts
│   │   ├── 📄 disable_old_lambda_functions.sh      # Disable old functions
│   │   ├── 📄 cleanup_old_function_artifacts.sh    # Clean up AWS artifacts
│   │   ├── 🗂️ user/                                # User management module
│   │   ├── 🗂️ group/                               # Group management module
│   │   ├── 🗂️ policy/                              # Policy management module
│   │   └── 🗂️ utils/                               # Utility functions
│   │
│   ├── 🗂️ Database/                                # 🗄️ Database Schema & Scripts
│   │   ├── 📄 README.md                            # Database documentation
│   │   ├── 📄 create_database.sql                  # Simple database creation
│   │   ├── 🗂️ Tables/                              # Table creation scripts
│   │   │   ├── 📄 users.sql                        # Users table
│   │   │   ├── 📄 bedrock_requests.sql             # Request logging table
│   │   │   ├── 📄 blocking_operations.sql          # Blocking audit table
│   │   │   ├── 📄 model_pricing.sql                # Model pricing table
│   │   │   └── 📄 user_limits.sql                  # User limits table
│   │   ├── 🗂️ Views/                               # Database view definitions
│   │   │   ├── 📄 v_user_realtime_usage.sql        # Real-time usage view
│   │   │   ├── 📄 v_hourly_usage.sql               # Hourly analytics view
│   │   │   ├── 📄 v_model_usage_stats.sql          # Model usage statistics
│   │   │   ├── 📄 v_team_usage_dashboard.sql       # Team dashboard view
│   │   │   └── 📄 v_last_10_days_usage.sql         # Recent usage view
│   │   ├── 🗂️ Stored_Procedures/                  # Stored procedure definitions
│   │   │   ├── 📄 CheckUserLimits.sql              # User limit checking
│   │   │   ├── 📄 LogBedrockRequest.sql            # Request logging procedure
│   │   │   ├── 📄 ExecuteUserBlocking.sql          # User blocking procedure
│   │   │   └── 📄 ExecuteUserUnblocking.sql        # User unblocking procedure
│   │   ├── 🗂️ Indexes/                             # Additional index scripts
│   │   ├── 🗂️ Functions/                           # Custom function scripts
│   │   └── 🗂️ Triggers/                            # Trigger scripts
│   │
│   └── 🗂️ Configuration/                           # ⚙️ Configuration Files
│       ├── 📄 package.json                         # Node.js dependencies
│       ├── 📄 env_vars.json                        # Environment variables
│       ├── 📄 quota_config.json                    # User/team quotas
│       ├── 📄 email_credentials.json               # Email configuration
│       ├── 📄 test_bedrock_payload.json            # Test payloads
│       └── 📄 test_blocking_payload.json           # Blocking test data
│
├── 🗂️ 03. Build_folder/                            # 🏗️ Build & Deployment Artifacts
│   ├── 📄 bedrock_email_service.py                 # Email service build
│   ├── 📄 bedrock_policy_manager_enhanced.py       # Policy manager build
│   ├── 📄 requirements.txt                         # Python requirements
│   ├── 🗂️ pymysql/                                 # MySQL driver package
│   └── 🗂️ pytz/                                    # Timezone package
│
├── 🗂️ 04. Testing/                                 # 🧪 Testing & Quality Assurance
│   ├── 📄 FINAL_TEST_RESULTS_REPORT.md             # Latest test results (100% pass)
│   ├── 📄 TEST_RESULTS_REPORT.md                   # Previous test results
│   ├── 📄 test_bedrock_daily_reset_comprehensive.py # Comprehensive daily reset tests
│   ├── 📄 test_bedrock_realtime_usage_controller_comprehensive.py # Controller tests
│   ├── 📄 test_enhanced_blocking.py                # Enhanced blocking tests
│   ├── 📄 test_email_service.py                    # Email notification tests
│   ├── 📄 TEST_EXECUTION_GUIDE_REALTIME_CONTROLLER.md # Test execution guide
│   ├── 📄 TEST_EXECUTION_PLAN.md                   # Test planning document
│   └── Various test configuration and fixture files
│
└── 🗂️ Dependencies/                                # 📦 Python Dependencies
    ├── 🗂️ pymysql/                                 # MySQL Python driver
    └── 🗂️ pytz/                                    # Timezone handling
```

## 🔧 Core Components

### 1. Web Dashboard (`02. Source/Dashboard/`)

**Purpose**: Interactive web interface for monitoring and managing Bedrock usage

**Key Features**:
- **Multi-tab Interface**: User Consumption, Team Consumption, Consumption Details, Blocking Management
- **Real-time Data**: Live usage statistics and status updates via MySQL integration
- **Blocking Management**: Manual blocking/unblocking with duration options
- **Export Capabilities**: CSV export for all data tables
- **Cost Analysis**: Detailed cost tracking and budget monitoring
- **Responsive Design**: Works on desktop and mobile devices

**Technical Stack**:
- HTML5 with modern CSS3
- Vanilla JavaScript (no external dependencies)
- AWS SDK for JavaScript (browser)
- Chart.js for visualizations
- Bootstrap for responsive design

### 2. CLI Management System (`02. Source/Scripts/`)

**Purpose**: Command-line interface for administrative operations

**Core Modules**:

#### `bedrock_manager.py` - Main CLI Interface
```python
# Key Commands:
python3 bedrock_manager.py user create <username> <person_name> <team>
python3 bedrock_manager.py user create-key <username> <tool_name>
python3 bedrock_manager.py user info <username>
python3 bedrock_manager.py group create <team_name>
python3 bedrock_manager.py policy create <policy_name>
```

#### User, Group, and Policy Management Modules
- **user_manager.py**: User CRUD operations, API key generation
- **group_manager.py**: Team/group creation and management
- **policy_manager.py**: IAM policy operations and management

### 3. Lambda Functions System (Updated September 2025)

**Purpose**: Real-time monitoring and blocking system using RDS MySQL

#### 🔥 **NEW: `bedrock-realtime-usage-controller.py` - MAIN CONTROLLER**
**Major Architecture Change**: This function combines the functionality of multiple previous functions into a single, more efficient Lambda function.

**Merged Functionality**:
- **Real-time Request Logging** (previously `bedrock-realtime-logger-fixed`)
- **Policy Management & Blocking** (previously `bedrock-policy-manager-enhanced`)
- **Usage Monitoring & Quota Checking**
- **Email Notification Integration**

**Key Features**:
- **Real-time CloudTrail Event Processing**: Processes Bedrock API calls in real-time with CET timezone handling
- **Direct RDS MySQL Integration**: Uses PyMySQL for direct database operations
- **Auto-provisioning**: Automatically provisions new users in the database
- **Usage Limit Checking**: Uses stored procedures for efficient limit evaluation
- **Automatic Blocking**: Implements IAM policy-based blocking when limits are exceeded
- **Email Notifications**: Integrates with bedrock-email-service for user notifications
- **Comprehensive Audit Logging**: All operations logged for compliance and debugging
- **CET Timezone Support**: All timestamps handled in Central European Time

**Performance Benefits**:
- **Reduced Latency**: Single function eliminates inter-function communication delays
- **Lower Costs**: Fewer Lambda invocations and reduced complexity
- **Simplified Architecture**: Easier to maintain and debug
- **Better Resource Utilization**: Optimized memory and execution time

#### `bedrock_daily_reset.py` - Daily Reset
**Functionality**:
- Automatic daily reset at 00:00 CET
- Unblock automatically blocked users
- Generate daily summary statistics
- Send comprehensive email notifications
- Complete audit trail maintenance

**Test Status**: ✅ **100% PASS RATE** (26/26 tests passing)

#### `bedrock_email_service.py` - Email Service
**Features**:
- Gmail SMTP integration
- Professional HTML email templates with CSS styling
- Color-coded notifications (Amber warnings, Red blocking, Green unblocking)
- Multi-language support (Spanish/English)
- Comprehensive notification types
- Error handling and logging

#### `bedrock_mysql_query_executor.py` - Database Query Executor
**Purpose**: Handles database queries for dashboard and analytics
- User usage statistics
- Team usage aggregations
- Cost analysis queries
- Hourly usage patterns

### 4. Database System (RDS MySQL)

**Purpose**: Unified persistent storage for all usage tracking and audit data

#### Core Tables:

**`users`** - User Configuration
```sql
- user_id (PRIMARY KEY)
- team, person_tag
- daily_limit, monthly_limit
- is_blocked, blocked_reason, blocked_until
- admin_protection_by
- created_at, updated_at
```

**`bedrock_requests`** - Individual Request Records
```sql
- id (AUTO_INCREMENT PRIMARY KEY)
- user_id, team, request_timestamp
- model_id, model_name, request_type
- input_tokens, output_tokens, total_tokens
- cost_usd, region, source_ip, user_agent
- created_at
```

**`blocking_operations`** - Complete Audit Trail
```sql
- id (AUTO_INCREMENT PRIMARY KEY)
- user_id, operation, reason
- performed_by, expires_at
- created_at
```

**`model_pricing`** - Cost Calculation
```sql
- model_id (PRIMARY KEY)
- model_name, input_token_price, output_token_price
- region, effective_date
```

#### Optimized Views:
- **`v_user_realtime_usage`**: Real-time usage checking for blocking decisions
- **`v_hourly_usage`**: Hourly analytics for trend analysis
- **`v_team_usage_dashboard`**: Team-level aggregations for dashboard
- **`v_model_usage_stats`**: Model usage statistics and comparisons
- **`v_last_10_days_usage`**: Recent usage patterns

#### Stored Procedures:
- **`CheckUserLimits`**: Efficient limit evaluation for blocking decisions
- **`LogBedrockRequest`**: Optimized request logging
- **`ExecuteUserBlocking`**: Complete user blocking workflow
- **`ExecuteUserUnblocking`**: Complete user unblocking workflow

## 🔄 System Workflows

### User Request Processing Flow (Updated Architecture)

```
1. User makes Bedrock API call
   ↓
2. CloudTrail captures the event
   ↓
3. EventBridge triggers Lambda (bedrock-realtime-usage-controller)
   ↓
4. MAIN Controller processes event:
   - Extracts user information from IAM tags
   - Logs request to RDS MySQL
   - Checks user limits via stored procedures
   - Evaluates blocking conditions
   - Executes blocking if needed (IAM policy updates)
   - Sends notifications (email + SNS)
   ↓
5. All operations completed in single function execution
   ↓
6. User is blocked/warned as appropriate
```

### Daily Reset Workflow

```
Every day at 00:00 CET:
1. Daily Reset Lambda triggered by EventBridge
   ↓
2. Generate daily summary from RDS MySQL data
   ↓
3. Query all currently blocked users
   ↓
4. Execute complete unblocking workflow:
   - Update blocking_operations table
   - Remove IAM deny policies
   - Send unblocking email notifications
   ↓
5. Send comprehensive daily summary notifications
```

## 🚫 Blocking/Unblocking Logic - Functional Overview

The AWS Bedrock Usage Control System implements a comprehensive blocking and unblocking mechanism that operates at both automatic and manual levels. This system ensures users cannot exceed their allocated quotas while providing administrative flexibility and protection mechanisms.

### 🤖 Automatic Blocking Logic

#### Trigger Conditions
The system automatically blocks users when they exceed their configured limits:

1. **Daily Limit Exceeded**: User reaches 100% of their daily token quota
2. **Monthly Limit Exceeded**: User reaches 100% of their monthly token quota
3. **Critical Threshold Breach**: User exceeds critical usage threshold (default: 85%)

#### Automatic Blocking Process

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        AUTOMATIC BLOCKING WORKFLOW                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  1. Real-time Request Processing                                            │
│     ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐      │
│     │ Bedrock API     │───▶│ CloudTrail      │───▶│ EventBridge     │      │
│     │ Call Made       │    │ Captures Event  │    │ Triggers Lambda │      │
│     └─────────────────┘    └─────────────────┘    └─────────────────┘      │
│                                                             │                │
│  2. Usage Evaluation                                        ▼                │
│     ┌─────────────────────────────────────────────────────────────────┐     │
│     │ bedrock-realtime-usage-controller Lambda Function      │     │
│     │                                                         │     │
│     │ • Extract user info from IAM tags                      │     │
│     │ • Log request to RDS MySQL (bedrock_requests table)   │     │
│     │ • Call CheckUserLimits stored procedure               │     │
│     │ • Evaluate: daily_usage >= daily_limit?               │     │
│     │ • Evaluate: monthly_usage >= monthly_limit?           │     │
│     │ • Check administrative protection status              │     │
│     └─────────────────────────────────────────────────────────────────┘     │
│                                                             │                │
│  3. Blocking Decision & Execution                           ▼                │
│     ┌─────────────────────────────────────────────────────────────────┐     │
│     │ IF (usage >= limit AND NOT admin_protected):           │     │
│     │                                                         │     │
│     │ Database Operations:                                    │     │
│     │ • UPDATE users SET is_blocked=TRUE, blocked_reason     │     │
│     │ • INSERT INTO blocking_operations (audit trail)       │     │
│     │                                                         │     │
│     │ IAM Policy Operations:                                  │     │
│     │ • Create deny policy for Bedrock services             │     │
│     │ • Attach policy to user (immediate effect)            │     │
│     │                                                         │     │
│     │ Notification Operations:                                │     │
│     │ • Send blocking email via bedrock-email-service       │     │
│     │ • Publish SNS alert to administrators                 │     │
│     │ • Log all operations for audit compliance             │     │
│     └─────────────────────────────────────────────────────────────────┘     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### Warning System (Pre-Blocking)
Before automatic blocking occurs, the system sends progressive warnings:

- **60% Usage**: First warning email (amber color-coded)
- **80% Usage**: Critical warning email (amber color-coded)
- **100% Usage**: Automatic blocking + blocking email (red color-coded)

### 🔓 Automatic Unblocking Logic

#### Daily Reset Process
The system automatically unblocks users through a scheduled daily reset:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        AUTOMATIC UNBLOCKING WORKFLOW                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Scheduled Execution: Every day at 00:00 CET                               │
│                                                                             │
│  1. Daily Reset Trigger                                                     │
│     ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐      │
│     │ EventBridge     │───▶│ bedrock-daily   │───▶│ RDS MySQL       │      │
│     │ Cron Schedule   │    │ -reset Lambda   │    │ Query Execution │      │
│     └─────────────────┘    └─────────────────┘    └─────────────────┘      │
│                                                                             │
│  2. Identify Users for Unblocking                                          │
│     ┌─────────────────────────────────────────────────────────────────┐     │
│     │ Query Logic:                                            │     │
│     │                                                         │     │
│     │ SELECT user_id FROM users                               │     │
│     │ WHERE is_blocked = TRUE                                 │     │
│     │   AND (blocked_until IS NULL                           │     │
│     │        OR blocked_until <= CURRENT_TIMESTAMP)          │     │
│     │   AND admin_protection_by IS NULL                      │     │
│     │                                                         │     │
│     │ Criteria for Automatic Unblocking:                     │     │
│     │ • User is currently blocked                            │     │
│     │ • No manual block expiration set OR expiration passed │     │
│     │ • No administrative protection in place                │     │
│     └─────────────────────────────────────────────────────────────────┘     │
│                                                                             │
│  3. Execute Unblocking Operations                                           │
│     ┌─────────────────────────────────────────────────────────────────┐     │
│     │ For Each Eligible User:                                 │     │
│     │                                                         │     │
│     │ Database Operations:                                    │     │
│     │ • UPDATE users SET is_blocked=FALSE, blocked_reason=NULL│     │
│     │ • INSERT INTO blocking_operations (unblock audit)      │     │
│     │ • REMOVE administrative_safe flags if present          │     │
│     │                                                         │     │
│     │ IAM Policy Operations:                                  │     │
│     │ • Retrieve user's current IAM policies                 │     │
│     │ • Remove Bedrock deny statements                       │     │
│     │ • Update or delete policy as needed                    │     │
│     │                                                         │     │
│     │ Notification Operations:                                │     │
│     │ • Send unblocking email (green color-coded)           │     │
│     │ • Include usage statistics and guidelines              │     │
│     │ • Log successful unblocking operation                  │     │
│     └─────────────────────────────────────────────────────────────────┘     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 👨‍💼 Manual Blocking Logic

#### Administrative Blocking
Administrators can manually block users through multiple interfaces:

**Via Web Dashboard:**
1. Navigate to "Blocking Management" tab
2. Select user from dropdown
3. Choose blocking duration (1 hour, 1 day, 1 week, permanent)
4. Provide blocking reason
5. Execute blocking operation

**Via CLI Interface:**
```bash
python3 bedrock_manager.py user block <username> --duration <time> --reason "<reason>"
```

#### Manual Blocking Process

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         MANUAL BLOCKING WORKFLOW                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  1. Administrative Decision                                                 │
│     ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐      │
│     │ Admin Reviews   │───▶│ Blocking        │───▶│ System Executes │      │
│     │ User Behavior   │    │ Decision Made   │    │ Block Operation │      │
│     └─────────────────┘    └─────────────────┘    └─────────────────┘      │
│                                                                             │
│  2. Manual Block Execution                                                  │
│     ┌─────────────────────────────────────────────────────────────────┐     │
│     │ Database Operations:                                    │     │
│     │ • UPDATE users SET is_blocked=TRUE                     │     │
│     │ • SET blocked_reason='<admin_reason>'                  │     │
│     │ • SET blocked_until=<expiration_time>                  │     │
│     │ • SET admin_protection_by='<admin_username>'           │     │
│     │ • INSERT INTO blocking_operations (manual audit)      │     │
│     │                                                         │     │
│     │ IAM Policy Operations:                                  │     │
│     │ • Create comprehensive deny policy                     │     │
│     │ • Include all Bedrock services and actions            │     │
│     │ • Attach policy with immediate effect                  │     │
│     │                                                         │     │
│     │ Notification Operations:                                │     │
│     │ • Send admin blocking email (red color-coded)         │     │
│     │ • Include admin contact information                    │     │
│     │ • Notify other administrators via SNS                  │     │
│     └─────────────────────────────────────────────────────────────────┘     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 🔓 Manual Unblocking Logic

#### Administrative Unblocking
Administrators can manually unblock users before their scheduled reset:

**Via Web Dashboard:**
1. Navigate to "Blocking Management" tab
2. View currently blocked users
3. Select user to unblock
4. Provide unblocking reason
5. Execute unblocking operation

**Via CLI Interface:**
```bash
python3 bedrock_manager.py user unblock <username> --reason "<reason>"
```

#### Manual Unblocking Process

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        MANUAL UNBLOCKING WORKFLOW                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  1. Administrative Review                                                   │
│     ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐      │
│     │ Admin Reviews   │───▶│ Unblocking      │───▶│ System Executes │      │
│     │ Block Status    │    │ Decision Made   │    │ Unblock Operation│      │
│     └─────────────────┘    └─────────────────┘    └─────────────────┘      │
│                                                                             │
│  2. Manual Unblock Execution                                               │
│     ┌─────────────────────────────────────────────────────────────────┐     │
│     │ Database Operations:                                    │     │
│     │ • UPDATE users SET is_blocked=FALSE                    │     │
│     │ • SET blocked_reason=NULL                              │     │
│     │ • SET blocked_until=NULL                               │     │
│     │ • SET admin_protection_by=NULL                         │     │
│     │ • INSERT INTO blocking_operations (manual unblock)    │     │
│     │                                                         │     │
│     │ IAM Policy Operations:                                  │     │
│     │ • Retrieve current user policies                       │     │
│     │ • Remove all Bedrock deny statements                   │     │
│     │ • Restore normal Bedrock access permissions           │     │
│     │                                                         │     │
│     │ Notification Operations:                                │     │
│     │ • Send admin unblocking email (green color-coded)     │     │
│     │ • Include usage guidelines and best practices          │     │
│     │ • Notify administrators of manual intervention         │     │
│     └─────────────────────────────────────────────────────────────────┘     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 🛡️ Administrative Protection Mechanism

#### Protection Logic
The system includes a sophisticated administrative protection mechanism to prevent accidental blocking of critical users:

**Protection Criteria:**
- Users with `admin_protection_by` field set are immune to automatic blocking
- Manual administrative review required for any blocking operations
- Protected users receive warnings but are never automatically blocked
- Protection can be set/removed only by administrators

**Protection Workflow:**
```
IF (user_usage >= limit AND admin_protection_by IS NOT NULL):
    - Send critical warning email
    - Log protection event in audit trail
    - Notify administrators of protection activation
    - DO NOT execute blocking operations
    - Continue monitoring and alerting
```

### 📊 Blocking Decision Matrix

| Condition | Daily Limit | Monthly Limit | Admin Protected | Action |
|-----------|-------------|---------------|-----------------|---------|
| < 60% | < 60% | No | ✅ Normal Operation |
| 60-79% | < 80% | No | ⚠️ First Warning Email |
| 80-99% | < 100% | No | ⚠️ Critical Warning Email |
| ≥ 100% | Any | No | 🚫 **Automatic Block** |
| ≥ 100% | Any | Yes | ⚠️ Protection Alert Only |
| Any | ≥ 100% | No | 🚫 **Automatic Block** |
| Any | ≥ 100% | Yes | ⚠️ Protection Alert Only |
| Manual | Manual | Any | 🚫 **Manual Block** (Admin Override) |

### 🔄 State Transitions

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           USER BLOCKING STATES                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────┐    Auto/Manual     ┌─────────────┐    Daily Reset/Manual   │
│  │   ACTIVE    │───────Block────────▶│   BLOCKED   │◀────────Unblock────────┐ │
│  │             │                    │             │                        │ │
│  │ • Can use   │                    │ • Cannot    │                        │ │
│  │   Bedrock   │                    │   use       │                        │ │
│  │ • Receives  │                    │   Bedrock   │                        │ │
│  │   warnings  │                    │ • Receives  │                        │ │
│  │             │                    │   block     │                        │ │
│  │             │                    │   emails    │                        │ │
│  └─────────────┘                    └─────────────┘                        │ │
│         ▲                                   │                               │ │
│         │                                   │                               │ │
│         └───────────────────────────────────┘                               │ │
│                                                                             │ │
│  ┌─────────────┐    Admin Action     ┌─────────────┐                        │ │
│  │ PROTECTED   │◀────Protection─────▶│   ACTIVE    │                        │ │
│  │             │                    │             │                        │ │
│  │ • Can use   │                    │ • Normal    │                        │ │
│  │   Bedrock   │                    │   operation │                        │ │
│  │ • Immune to │                    │             │                        │ │
│  │   auto-block│                    │             │                        │ │
│  │ • Gets      │                    │             │                        │ │
│  │   warnings  │                    │             │                        │ │
│  └─────────────┘                    └─────────────┘                        │ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 📧 Notification System Integration

The blocking/unblocking system is tightly integrated with the email notification service:

**Email Types:**
1. **Warning Emails** (Amber): Sent at 60% and 80% usage thresholds
2. **Blocking Emails** (Red): Sent when user is automatically or manually blocked
3. **Unblocking Emails** (Green): Sent when user is unblocked (daily reset or manual)
4. **Admin Notification Emails**: Sent to administrators for manual operations
5. **Protection Alert Emails**: Sent when protected users exceed limits

**Email Content:**
- Professional HTML templates with CSS styling
- Usage statistics with visual progress bars
- Clear action items and next steps
- Contact information for support
- Responsive design for all devices

This comprehensive blocking/unblocking system ensures robust quota management while providing flexibility for administrative oversight and user protection.

## 🛡️ Security & Permissions

### IAM Roles and Policies

#### Main Controller Role
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "rds:DescribeDBInstances",
        "iam:GetUser",
        "iam:GetUserPolicy",
        "iam:PutUserPolicy",
        "iam:DeleteUserPolicy",
        "lambda:InvokeFunction",
        "sns:Publish"
      ],
      "Resource": "*"
    }
  ]
}
```

#### Lambda Execution Roles
- **bedrock-realtime-usage-controller-role**: RDS, SNS, IAM, Lambda invoke permissions
- **bedrock-daily-reset-role**: RDS, IAM, SNS, SES permissions
- **bedrock-email-service-role**: SES and basic execution permissions
- **bedrock-mysql-query-executor-role**: RDS read permissions

### Data Protection

- **Encryption at Rest**: RDS instances encrypted with AWS KMS
- **Encryption in Transit**: All API calls use HTTPS/TLS
- **Access Logging**: Complete audit trail of all operations
- **Data Retention**: Configurable retention policies
- **Principle of Least Privilege**: Minimal required permissions for all components

## 📊 Monitoring & Alerting

### CloudWatch Metrics

**Custom Metrics**:
- `UserMetrics/BedrockUsage` - Per-user usage tracking
- `TeamMetrics/BedrockUsage` - Team-level aggregations
- `BlockingMetrics/Operations` - Blocking operation counts
- `CostMetrics/DailyCost` - Daily cost tracking

**System Metrics**:
- Lambda function duration and errors
- RDS connection and query performance
- Email delivery success rates

### SNS Notifications

**Alert Types**:
1. **Warning Alerts**: User approaching daily limit
2. **Blocking Alerts**: User automatically blocked
3. **Admin Alerts**: Manual blocking/unblocking operations
4. **System Alerts**: Lambda errors, database issues
5. **Daily Summaries**: Usage and cost reports

## 💰 Cost Management

### Cost Tracking Features

1. **Real-time Cost Calculation**: Based on token usage and model pricing
2. **Daily/Monthly Budgets**: Configurable per user and team
3. **Cost Alerts**: Automatic notifications when budgets exceeded
4. **Historical Analysis**: Cost trends and projections
5. **Model Comparison**: Cost efficiency analysis across models

### Estimated Monthly Costs

| Service | Monthly Cost (Estimate) | Notes |
|---------|------------------------|-------|
| RDS MySQL (db.t3.micro) | $15-25 | Single-AZ, 20GB storage |
| Lambda Functions | $5-15 | Based on 10K invocations/month |
| CloudWatch Logs | $2-5 | 1GB logs/month |
| SNS | $1-2 | Email notifications |
| SES | $1-2 | Email sending |
| **Total** | **$24-49/month** | Varies with usage |

## 🔧 Configuration Management

### Main Configuration Files

#### `02. Source/Scripts/config.json` - AWS Configuration
```json
{
  "account_id": "701055077130",
  "region": "eu-west-1",
  "inference_profiles": {
    "claude": "arn:aws:bedrock:eu-west-1:701055077130:inference-profile/eu.anthropic.claude-sonnet-4-20250514-v1:0",
    "nova_pro": "arn:aws:bedrock:eu-west-1:701055077130:inference-profile/eu.amazon.nova-pro-v1:0"
  },
  "default_quotas": {
    "user": {
      "monthly_limit": 5000,
      "daily_limit": 350,
      "warning_threshold": 150
    }
  }
}
```

#### `02. Source/Configuration/quota_config.json` - User/Team Quotas
```json
{
  "users": {
    "darwin_001": {
      "daily_limit": 350,
      "monthly_limit": 5000,
      "team": "team_darwin_group"
    }
  },
  "teams": {
    "team_darwin_group": {
      "monthly_limit": 25000
    }
  }
}
```

## 🚀 Quick Start Guide

### Option 1: Automated Deployment (Recommended)
```bash
cd "01. Project documents/Installation Manual"
chmod +x 04_Complete_Deployment_Script.sh
./04_Complete_Deployment_Script.sh
```

### Option 2: Manual Step-by-Step
1. Read this README for system understanding
2. Follow `01. Project documents/Installation Manual/01_Complete_Installation_Guide.md`
3. Use source code from `02. Source/` folder as needed

### Option 3: Source Code Development
1. Review `02. Source/README_Source_Code.md` for code organization
2. Modify source files in appropriate folders
3. Deploy using installation guides

## 🧪 Testing & Quality Assurance

### Test Suite Status

**Latest Test Results** (September 2025):
- **bedrock_daily_reset.py**: ✅ **100% PASS RATE** (26/26 tests)
- **bedrock_realtime_usage_controller.py**: ✅ **Comprehensive tests available**
- **Email Service Integration**: ✅ **All tests passing**

**Automated Tests**:
- `04. Testing/test_bedrock_daily_reset_comprehensive.py` - Daily reset function tests
- `04. Testing/test_bedrock_realtime_usage_controller_comprehensive.py` - Main controller tests
- Unit tests for all Lambda functions
- Integration tests for dashboard functionality
- End-to-end blocking workflow tests
- Database connection and query tests

### Quality Checks

**Code Quality**:
- Python code formatting and linting
- JavaScript code quality checks
- Security scanning for vulnerabilities
- Database query optimization

## 📈 Performance & Scalability

### Performance Optimizations

1. **Lambda Function Consolidation**: Merged multiple functions into single efficient controller
2. **Database Optimizations**: Optimized indexes and connection pooling
3. **Caching Strategy**: Lambda function warm-up and connection reuse
4. **Stored Procedures**: Database-level business logic for better performance

### Scalability Considerations

- **Auto-scaling**: RDS auto-scaling enabled
- **Lambda Concurrency**: Reserved concurrency for critical functions
- **Regional Deployment**: EU-West-1 optimized for European operations
- **Data Archiving**: Automated cleanup of old usage data

## 🔄 Maintenance & Operations

### Regular Maintenance Tasks

**Daily**:
- Monitor Lambda function errors
- Check RDS performance metrics
- Review blocking operations and user feedback

**Weekly**:
- Analyze usage patterns and trends
- Review and update user quotas as needed
- Check system capacity and scaling needs

**Monthly**:
- Update model pricing information
- Review and optimize database performance
- Update documentation and runbooks

## 📞 Support & Troubleshooting

### Common Issues

1. **Dashboard not loading data**: Check AWS credentials and Lambda function permissions
2. **Users not being blocked**: Verify Lambda function permissions and EventBridge rules
3. **Email notifications not working**: Check Gmail SMTP configuration and credentials
4. **Database connection issues**: Verify RDS endpoint and security group settings

### Logging & Debugging

**Log Locations**:
- Lambda logs: CloudWatch Logs `/aws/lambda/function-name`
- Application logs: Custom log groups for detailed debugging
- Database logs: RDS slow query logs and error logs
- System metrics: CloudWatch custom metrics

### Getting Help

- Check the `01. Project documents/Installation Manual/` for detailed setup instructions
- Review CloudWatch logs for error messages
- Use the test scripts in `04. Testing/` to verify system functionality
- Contact the development team for complex issues

## 📝 Recent Changes & Version History

### Version 4.0.0 - Lambda Function Consolidation (September 2025)
- **🔥 MAJOR ARCHITECTURE
