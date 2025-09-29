# Database DDL Structure

This directory contains the structured DDL (Data Definition Language) files for the AWS Bedrock Usage Control RDS MySQL database.

**UPDATED**: All DDL files have been synchronized with the production database schema as of 2025-09-23.

## Directory Structure

```
Database/
├── README.md                    # This file
├── Tables/                     # Table creation scripts
│   ├── user_limits.sql         # CORRECTED: Main user limits table (was users.sql)
│   ├── bedrock_requests.sql
│   ├── user_blocking_status.sql
│   └── blocking_audit_log.sql
├── Views/                      # View creation scripts
│   └── v_user_realtime_usage.sql # UPDATED: Production schema
├── Stored_Procedures/          # Stored procedure scripts
│   └── CheckUserLimits.sql     # UPDATED: Production schema
├── Indexes/                    # Additional index scripts (if any)
├── Functions/                  # Function scripts (empty - no custom functions)
└── Triggers/                   # Trigger scripts (empty - no triggers)
```

## Database Objects (Production Schema)

### Tables

1. **user_limits** - Stores user information, quotas, and administrative protection settings
2. **bedrock_requests** - Individual request records table with tokens and cost tracking
3. **user_blocking_status** - Current blocking status for users
4. **blocking_audit_log** - Complete audit trail of blocking/unblocking operations

### Views

1. **v_user_realtime_usage** - Real-time user usage check for blocking decisions
2. **v_hourly_usage** - Hourly usage analysis
3. **v_model_usage_stats** - Model usage statistics
4. **v_team_usage_dashboard** - Team usage dashboard
5. **v_last_10_days_usage** - Last 10 days detailed usage

### Stored Procedures

1. **CheckUserLimits** - Check if user should be blocked (called on each request)
2. **LogBedrockRequest** - Log a new request with cost calculation
3. **ExecuteUserBlocking** - Execute user blocking with CET timestamps
4. **ExecuteUserUnblocking** - Execute user unblocking with CET timestamps

### Indexes

- Additional performance optimization indexes for the bedrock_requests table

## Usage

To deploy the complete database schema:

1. Create the database: `CREATE DATABASE bedrock_usage;`
2. Execute table creation scripts in order (Tables/)
3. Execute view creation scripts (Views/)
4. Execute stored procedure scripts (Stored_Procedures/)
5. Execute additional index scripts (Indexes/)

## Notes

- All timestamps are handled with CET timezone support
- The bedrock_requests table is partitioned by date for better performance
- Foreign key constraints ensure data integrity
- Indexes are optimized for dashboard queries and real-time operations
