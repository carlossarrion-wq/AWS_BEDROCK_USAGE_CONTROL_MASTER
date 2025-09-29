// AWS Bedrock Usage Dashboard Configuration

// AWS Configuration
const AWS_CONFIG = {
    region: 'eu-west-1',
    account_id: '701055077130',
    dashboard_role_arn: 'arn:aws:iam::701055077130:role/bedrock-dashboard-access-role',
    external_id: 'bedrock-dashboard-access'
};

// All teams for group consumption display
const ALL_TEAMS = [
    'team_darwin_group',
    'team_sap_group',
    'team_mulesoft_group',
    'team_yo_leo_gas_group',
    'team_lcorp_group'
];

// Bedrock Services for cost analysis
const BEDROCK_SERVICES = [
    'Amazon Bedrock',
    'Claude 3.7 Sonnet (Bedrock Edition)',
    'Claude 3 Sonnet (Bedrock Edition)',
    'Claude 3 Haiku (Bedrock Edition)',
    'Claude 3 Opus (Bedrock Edition)',
    'Amazon Titan Text (Bedrock Edition)'
];

// Pagination configuration
const PAGINATION_CONFIG = {
    operationsPageSize: 10
};

// Chart color palettes
const CHART_COLORS = {
    primary: ['#1e4a72', '#3498db', '#e67e22', '#27ae60', '#2d5aa0', '#f8f9fa', '#6c757d'],
    teams: ['#27ae60', '#1e4a72', '#e67e22', '#3498db', '#2d5aa0', '#f8f9fa', '#6c757d'],
    services: ['#1e4a72', '#27ae60', '#e67e22', '#3498db', '#2d5aa0', '#f39c12']
};

// Default quota configuration (fallback)
const DEFAULT_QUOTA_CONFIG = {
    users: {
        "darwin_001": {
            monthly_limit: 5000,
            daily_limit: 250,
            warning_threshold: 60,
            critical_threshold: 85
        },
        "darwin_002": {
            monthly_limit: 5000,
            daily_limit: 250,
            warning_threshold: 60,
            critical_threshold: 85
        },
        "lcorp_001": {
            monthly_limit: 5000,
            daily_limit: 250,
            warning_threshold: 60,
            critical_threshold: 85
        },
        "lcorp_002": {
            monthly_limit: 5000,
            daily_limit: 250,
            warning_threshold: 60,
            critical_threshold: 85
        },
        "lcorp_007": {
            monthly_limit: 5000,
            daily_limit: 80,
            warning_threshold: 60,
            critical_threshold: 85
        },
        "mulesoft_001": {
            monthly_limit: 5000,
            daily_limit: 250,
            warning_threshold: 60,
            critical_threshold: 85
        },
        "mulesoft_002": {
            monthly_limit: 5000,
            daily_limit: 250,
            warning_threshold: 60,
            critical_threshold: 85
        },
        "sap_001": {
            monthly_limit: 5000,
            daily_limit: 250,
            warning_threshold: 60,
            critical_threshold: 85
        },
        "sap_002": {
            monthly_limit: 5000,
            daily_limit: 250,
            warning_threshold: 60,
            critical_threshold: 85
        },
        "sap_003": {
            monthly_limit: 5000,
            daily_limit: 250,
            warning_threshold: 60,
            critical_threshold: 85
        },
        "yo_leo_gas_001": {
            monthly_limit: 5000,
            daily_limit: 9999,
            warning_threshold: 60,
            critical_threshold: 85
        },
        "yo_leo_gas_002": {
            monthly_limit: 5000,
            daily_limit: 250,
            warning_threshold: 60,
            critical_threshold: 85
        }
    },
    teams: {
        "team_darwin_group": {
            monthly_limit: 25000,
            warning_threshold: 60,
            critical_threshold: 85
        },
        "team_sap_group": {
            monthly_limit: 25000,
            warning_threshold: 60,
            critical_threshold: 85
        },
        "team_mulesoft_group": {
            monthly_limit: 25000,
            warning_threshold: 60,
            critical_threshold: 85
        },
        "team_yo_leo_gas_group": {
            monthly_limit: 25000,
            warning_threshold: 60,
            critical_threshold: 85
        },
        "team_lcorp_group": {
            monthly_limit: 25000,
            warning_threshold: 60,
            critical_threshold: 85
        }
    }
};

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        AWS_CONFIG,
        ALL_TEAMS,
        BEDROCK_SERVICES,
        PAGINATION_CONFIG,
        CHART_COLORS,
        DEFAULT_QUOTA_CONFIG
    };
}
