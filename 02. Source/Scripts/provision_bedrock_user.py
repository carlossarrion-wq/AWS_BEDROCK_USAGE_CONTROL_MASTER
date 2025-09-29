#!/usr/bin/env python3
"""
Provision AWS resources for Bedrock usage tracking for a specific user.

This script provisions all necessary resources for tracking AWS Bedrock usage
for a specific user in the dashboard. It validates the user and group naming
conventions, and creates all required resources if they don't already exist.
If the user doesn't exist, it will be created and associated to the indicated group.

Usage:
    python3 provision_bedrock_user.py --username <username> [--group <group_name>]

Examples:
    python3 provision_bedrock_user.py --username yo_leo_gas_001
    python3 provision_bedrock_user.py --username new_user --group team_mulesoft_group
"""

import argparse
import boto3
import json
import sys
import time
import re
from datetime import datetime
from botocore.exceptions import ClientError

# Constants
REGION = 'eu-west-1'
USER_LOG_GROUP = '/aws/bedrock/user_usage'
TEAM_LOG_GROUP = '/aws/bedrock/team_usage'
QUOTA_CONFIG_FILE = 'individual_blocking_system/lambda_functions/quota_config.json'
DEFAULT_TOOL = 'Cline Agent'

# Team naming pattern
TEAM_PATTERN = re.compile(r'^team_[a-z0-9_]+_group$')
USER_PATTERN = re.compile(r'^[a-z0-9_]+$')

# Configure AWS clients
iam_client = boto3.client('iam', region_name=REGION)
logs_client = boto3.client('logs', region_name=REGION)
cloudwatch_client = boto3.client('cloudwatch', region_name=REGION)
lambda_client = boto3.client('lambda', region_name=REGION)

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Provision AWS resources for Bedrock usage tracking.')
    parser.add_argument('--username', required=True, help='The username to provision resources for')
    parser.add_argument('--group', help='The group to associate the user with (required if user does not exist)')
    return parser.parse_args()

def load_quota_config():
    """Load the quota configuration from the JSON file."""
    try:
        with open(QUOTA_CONFIG_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading quota configuration: {str(e)}")
        return {"users": {}, "teams": {}}

def create_user(username, group_name=None):
    """Create a new IAM user and optionally add to a group."""
    try:
        # Check if user already exists
        try:
            iam_client.get_user(UserName=username)
            print(f"User {username} already exists.")
            user_exists = True
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchEntity':
                # Create the user
                print(f"Creating new IAM user: {username}")
                iam_client.create_user(UserName=username)
                
                # Add Person tag with value "Unknown"
                try:
                    iam_client.tag_user(
                        UserName=username,
                        Tags=[
                            {
                                'Key': 'Person',
                                'Value': 'Unknown'
                            }
                        ]
                    )
                    print(f"Added Person tag with value 'Unknown' to user {username}")
                except ClientError as tag_error:
                    print(f"Warning: Could not add Person tag to user: {str(tag_error)}")
                    print("Continuing with user provisioning...")
                
                user_exists = False
            else:
                print(f"Error checking if user exists: {str(e)}")
                return []
        
        # Generate a cryptographically secure random password that meets AWS password policy requirements
        import secrets
        import string
        
        def generate_secure_password(length=16):
            """
            Generate a cryptographically secure password that meets AWS password policy requirements.
            
            AWS Password Policy Requirements:
            - Minimum 8 characters (we use 16 for better security)
            - At least one uppercase letter
            - At least one lowercase letter  
            - At least one number
            - At least one special character
            
            Args:
                length (int): Password length (minimum 8, default 16)
                
            Returns:
                str: Cryptographically secure password
            """
            if length < 8:
                length = 8
                
            # Define character sets
            lowercase_chars = string.ascii_lowercase
            uppercase_chars = string.ascii_uppercase
            digit_chars = string.digits
            special_chars = "!@#$%^&*()"
            all_chars = lowercase_chars + uppercase_chars + digit_chars + special_chars
            
            # Ensure we have at least one character from each required set
            password_chars = [
                secrets.choice(lowercase_chars),
                secrets.choice(uppercase_chars),
                secrets.choice(digit_chars),
                secrets.choice(special_chars)
            ]
            
            # Fill the remaining length with random characters from all sets
            for _ in range(length - 4):
                password_chars.append(secrets.choice(all_chars))
            
            # Shuffle the password characters using cryptographically secure random
            # Convert to list for in-place shuffling
            password_list = list(password_chars)
            for i in range(len(password_list) - 1, 0, -1):
                j = secrets.randbelow(i + 1)
                password_list[i], password_list[j] = password_list[j], password_list[i]
            
            return ''.join(password_list)
        
        # Generate the secure password
        password = generate_secure_password(16)
        
        # Create or update login profile with the password
        if not user_exists:
            try:
                iam_client.create_login_profile(
                    UserName=username,
                    Password=password,
                    PasswordResetRequired=True
                )
                print(f"User {username} created successfully with temporary password: {password}")
                print("User will be required to change password on first login")
            except ClientError as e:
                print(f"Warning: Could not create login profile: {str(e)}")
                print("Continuing with user provisioning...")
        else:
            try:
                # Try to update the login profile
                iam_client.update_login_profile(
                    UserName=username,
                    Password=password,
                    PasswordResetRequired=True
                )
                print(f"Updated login profile for user {username} with new temporary password: {password}")
                print("User will be required to change password on next login")
            except ClientError as e:
                if e.response['Error']['Code'] == 'NoSuchEntity':
                    # Login profile doesn't exist, create it
                    try:
                        iam_client.create_login_profile(
                            UserName=username,
                            Password=password,
                            PasswordResetRequired=True
                        )
                        print(f"Created login profile for existing user {username} with temporary password: {password}")
                        print("User will be required to change password on first login")
                    except ClientError as e2:
                        print(f"Warning: Could not create login profile: {str(e2)}")
                        print("Continuing with user provisioning...")
                else:
                    print(f"Warning: Could not update login profile: {str(e)}")
                    print("Continuing with user provisioning...")
        
        # Add user to group if specified
        if group_name:
            try:
                print(f"Adding user {username} to group {group_name}")
                iam_client.add_user_to_group(
                    UserName=username,
                    GroupName=group_name
                )
                print(f"User {username} added to group {group_name}")
                
                # Add Team tag to the user (CRITICAL for Lambda function team assignment)
                try:
                    iam_client.tag_user(
                        UserName=username,
                        Tags=[
                            {
                                'Key': 'Team',
                                'Value': group_name
                            }
                        ]
                    )
                    print(f"Added Team tag with value '{group_name}' to user {username}")
                except ClientError as tag_error:
                    print(f"Warning: Could not add Team tag to user: {str(tag_error)}")
                    print("This may cause issues with team assignment in the Lambda function!")
                
                return [group_name]
            except ClientError as e:
                print(f"Error adding user to group: {str(e)}")
                return []
        
        return []
    except ClientError as e:
        print(f"Error creating user {username}: {str(e)}")
        return []

def get_user_groups(username):
    """Get the IAM groups that the user belongs to."""
    try:
        response = iam_client.list_groups_for_user(UserName=username)
        return [group['GroupName'] for group in response['Groups']]
    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchEntity':
            print(f"User {username} does not exist in IAM.")
            return []
        else:
            print(f"Error getting groups for user {username}: {str(e)}")
            return []

def validate_user_and_group(username, groups):
    """Validate that the user and group meet the naming conventions."""
    # Check user naming convention
    if not USER_PATTERN.match(username):
        print(f"Error: Username {username} does not match the required pattern.")
        return None
    
    # If groups exist, validate them
    if groups:
        # Find a group that matches the team pattern
        valid_groups = [g for g in groups if TEAM_PATTERN.match(g)]
        if not valid_groups:
            print(f"Error: User {username} does not belong to any valid team group.")
            print(f"Groups found: {groups}")
            print("Team groups must follow the pattern: team_<name>_group")
            return None
        
        # If multiple valid groups, use the first one
        team_group = valid_groups[0]
        print(f"Found valid team group: {team_group}")
        return team_group
    
    return None

def check_user_in_quota_config(username, team_group, quota_config):
    """Check if the user is in the quota configuration and add if needed."""
    users = quota_config.get('users', {})
    teams = quota_config.get('teams', {})
    
    # Check if user exists in quota config
    if username not in users:
        print(f"Warning: User {username} not found in quota configuration.")
        print(f"Adding user {username} to quota configuration with default values.")
        
        # Add user with default values (250 daily, 5000 monthly)
        users[username] = {
            "monthly_limit": 5000,  # 5,000 per user per month
            "daily_limit": 250,     # 250 per user per day
            "warning_threshold": 150,  # 60% of 250 = 150
            "critical_threshold": 200,  # 80% of 250 = 200
            "team": team_group
        }
    elif 'team' not in users[username]:
        print(f"Warning: User {username} does not have a team assigned in quota configuration.")
        print(f"Setting team to {team_group}.")
        users[username]['team'] = team_group
    elif users[username]['team'] != team_group:
        print(f"Warning: User {username} has team {users[username]['team']} in quota config, but belongs to {team_group} in IAM.")
        print(f"Updating team to {team_group}.")
        users[username]['team'] = team_group
    
    # Check if team exists in quota config
    if team_group not in teams:
        print(f"Warning: Team {team_group} not found in quota configuration.")
        print(f"Adding team {team_group} to quota configuration with default values.")
        
        # Add team with default values
        teams[team_group] = {
            "monthly_limit": 25000,  # 25,000 per team per month
            "warning_threshold": 60,
            "critical_threshold": 85
        }
    
    # Update quota config
    quota_config['users'] = users
    quota_config['teams'] = teams
    
    # Save updated quota config
    try:
        with open(QUOTA_CONFIG_FILE, 'w') as f:
            json.dump(quota_config, f, indent=2, sort_keys=True)
        print(f"Updated quota configuration saved to {QUOTA_CONFIG_FILE}")
    except Exception as e:
        print(f"Error saving quota configuration: {str(e)}")
    
    return quota_config

def create_bedrock_policy_for_user(username):
    """Create and attach Bedrock policy for the user."""
    policy_name = f"{username}_BedrockPolicy"
    
    # Extract team name from username for role assumption
    # Assume username format like "mulesoft_003" -> team "mulesoft"
    team_name = username.split('_')[0] if '_' in username else username
    
    policy_document = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "bedrock:InvokeModel",
                    "bedrock:InvokeModelWithResponseStream",
                    "bedrock:CallWithBearerToken",
                    "bedrock:ListFoundationModels",
                    "bedrock:GetFoundationModel",
                    "bedrock:ListCustomModels",
                    "bedrock:GetCustomModel",
                    "bedrock:ListModelCustomizationJobs",
                    "bedrock:GetModelCustomizationJob",
                    "bedrock:ListPrompts",
                    "bedrock:GetPrompt",
                    "bedrock:ListTagsForResource",
                    "bedrock:ListGuardrails",
                    "bedrock:GetGuardrail",
                    "bedrock:ApplyGuardrail",
                    "bedrock:ListEvaluations",
                    "bedrock:GetEvaluation"
                ],
                "Resource": "*"
            },
            {
                "Effect": "Allow",
                "Action": "bedrock:InvokeModelWithResponseStream",
                "Resource": "*"
            },
            {
                "Effect": "Allow",
                "Action": [
                    "bedrock:InvokeModel",
                    "bedrock:InvokeModelWithResponseStream"
                ],
                "Resource": [
                    "arn:aws:bedrock:*:*:foundation-model/*",
                    "arn:aws:bedrock:*:*:inference-profile/*",
                    "arn:aws:bedrock:eu-west-1:*:inference-profile/eu.anthropic.claude-sonnet-4-20250514-v1:0",
                    "arn:aws:bedrock:eu-central-1:*:foundation-model/anthropic.claude-sonnet-4-20250514-v1:0",
                    "arn:aws:bedrock:eu-west-1:*:inference-profile/eu.amazon.nova-pro-v1:0",
                    "arn:aws:bedrock:eu-west-1:*:inference-profile/eu.anthropic.claude-3-7-sonnet-20250219-v1:0",
                    "arn:aws:bedrock:eu-west-1:701055077130:inference-profile/eu.anthropic.claude-3-7-sonnet-20250219-v1:0"
                ]
            },
            {
                "Effect": "Allow",
                "Action": [
                    "bedrock:GetInferenceProfile",
                    "bedrock:ListInferenceProfiles"
                ],
                "Resource": "*"
            },
            {
                "Effect": "Allow",
                "Action": "sts:AssumeRole",
                "Resource": f"arn:aws:iam::701055077130:role/team_{team_name}_BedrockRole"
            }
        ]
    }
    
    try:
        policy_arn = f"arn:aws:iam::701055077130:policy/{policy_name}"
        
        # Check if policy already exists
        try:
            existing_policy = iam_client.get_policy(PolicyArn=policy_arn)
            print(f"Policy {policy_name} already exists. Updating with new version...")
            
            # Create a new version of the existing policy
            try:
                response = iam_client.create_policy_version(
                    PolicyArn=policy_arn,
                    PolicyDocument=json.dumps(policy_document),
                    SetAsDefault=True
                )
                print(f"Policy {policy_name} updated to version {response['PolicyVersion']['VersionId']}.")
                
                # Clean up old versions (keep only the latest 5 as AWS allows max 5 versions)
                versions_response = iam_client.list_policy_versions(PolicyArn=policy_arn)
                versions = versions_response['Versions']
                non_default_versions = [v for v in versions if not v['IsDefaultVersion']]
                
                if len(non_default_versions) > 4:  # Keep 4 non-default + 1 default = 5 total
                    versions_to_delete = sorted(non_default_versions, key=lambda x: x['CreateDate'])[:-4]
                    for version in versions_to_delete:
                        try:
                            iam_client.delete_policy_version(
                                PolicyArn=policy_arn,
                                VersionId=version['VersionId']
                            )
                            print(f"Deleted old policy version: {version['VersionId']}")
                        except ClientError as e:
                            print(f"Warning: Could not delete version {version['VersionId']}: {str(e)}")
                            
            except ClientError as e:
                print(f"Error updating policy version: {str(e)}")
                return False
                
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchEntity':
                # Create the policy
                print(f"Creating Bedrock policy {policy_name}...")
                response = iam_client.create_policy(
                    PolicyName=policy_name,
                    PolicyDocument=json.dumps(policy_document)
                )
                print(f"Policy {policy_name} created successfully.")
            else:
                print(f"Error checking policy: {str(e)}")
                return False
        
        # Attach policy to user (this is idempotent, so safe to call even if already attached)
        print(f"Attaching policy {policy_name} to user {username}...")
        try:
            iam_client.attach_user_policy(
                UserName=username,
                PolicyArn=policy_arn
            )
            print(f"Policy {policy_name} attached to user {username}.")
        except ClientError as e:
            if e.response['Error']['Code'] == 'EntityAlreadyExists':
                print(f"Policy {policy_name} is already attached to user {username}.")
            else:
                print(f"Error attaching policy: {str(e)}")
                return False
        
        return True
    except ClientError as e:
        print(f"Error creating/attaching Bedrock policy for user {username}: {str(e)}")
        return False

def ensure_cloudwatch_logs_access(username):
    """Ensure the user has CloudWatch Logs access."""
    try:
        # Check if CloudWatchLogsFullAccess policy is attached
        response = iam_client.list_attached_user_policies(UserName=username)
        policies = [p['PolicyName'] for p in response['AttachedPolicies']]
        
        if 'CloudWatchLogsFullAccess' in policies:
            print(f"User {username} already has CloudWatchLogsFullAccess policy attached.")
            return True
        
        # Attach CloudWatchLogsFullAccess policy
        print(f"Attaching CloudWatchLogsFullAccess policy to user {username}...")
        iam_client.attach_user_policy(
            UserName=username,
            PolicyArn='arn:aws:iam::aws:policy/CloudWatchLogsFullAccess'
        )
        print(f"CloudWatchLogsFullAccess policy attached to user {username}.")
        return True
    except ClientError as e:
        print(f"Error ensuring CloudWatch Logs access for user {username}: {str(e)}")
        return False

def ensure_log_groups_exist():
    """Ensure the required CloudWatch log groups exist."""
    log_groups = [USER_LOG_GROUP, TEAM_LOG_GROUP]
    results = {}
    
    for log_group in log_groups:
        try:
            # Check if log group exists
            response = logs_client.describe_log_groups(logGroupNamePrefix=log_group)
            if any(g['logGroupName'] == log_group for g in response.get('logGroups', [])):
                print(f"Log group {log_group} already exists.")
                results[log_group] = True
                continue
            
            # Create log group
            print(f"Creating log group {log_group}...")
            logs_client.create_log_group(logGroupName=log_group)
            print(f"Log group {log_group} created.")
            results[log_group] = True
        except ClientError as e:
            print(f"Error ensuring log group {log_group} exists: {str(e)}")
            results[log_group] = False
    
    return all(results.values())

def ensure_log_streams_exist(username, team_group):
    """Ensure the required CloudWatch log streams exist."""
    streams = [
        (USER_LOG_GROUP, username),
        (TEAM_LOG_GROUP, team_group)
    ]
    results = {}
    
    for log_group, stream_name in streams:
        try:
            # Check if log stream exists
            response = logs_client.describe_log_streams(
                logGroupName=log_group,
                logStreamNamePrefix=stream_name
            )
            if any(s['logStreamName'] == stream_name for s in response.get('logStreams', [])):
                print(f"Log stream {stream_name} already exists in {log_group}.")
                results[(log_group, stream_name)] = True
                continue
            
            # Create log stream
            print(f"Creating log stream {stream_name} in {log_group}...")
            logs_client.create_log_stream(
                logGroupName=log_group,
                logStreamName=stream_name
            )
            print(f"Log stream {stream_name} created in {log_group}.")
            results[(log_group, stream_name)] = True
        except ClientError as e:
            print(f"Error ensuring log stream {stream_name} exists in {log_group}: {str(e)}")
            results[(log_group, stream_name)] = False
    
    return all(results.values())

def ensure_metric_filters_exist(username, team_group):
    """Ensure the required CloudWatch metric filters exist."""
    # User metric filter
    user_filter_name = f"{username}_usage_fixed"
    user_filter_pattern = f"{{ $.user = \"{username}\" }}"
    
    # Team metric filter
    team_filter_name = f"{team_group}_usage_fixed"
    team_filter_pattern = f"{{ $.team = \"{team_group}\" }}"
    
    # Tool metric filters are no longer needed since tools section has been removed
    filters = [
        (USER_LOG_GROUP, user_filter_name, user_filter_pattern, "BedrockUsage", "UserMetrics", {"User": "$.user"}),
        (TEAM_LOG_GROUP, team_filter_name, team_filter_pattern, "BedrockTeamUsage", "TeamMetrics", {"Team": "$.team"})
    ]
    
    results = {}
    
    for log_group, filter_name, filter_pattern, metric_name, namespace, dimensions in filters:
        try:
            # Check if metric filter exists
            response = logs_client.describe_metric_filters(
                logGroupName=log_group,
                filterNamePrefix=filter_name
            )
            
            if any(f['filterName'] == filter_name for f in response.get('metricFilters', [])):
                print(f"Metric filter {filter_name} already exists in {log_group}.")
                
                # Delete existing filter to update it
                print(f"Deleting existing metric filter {filter_name} to update it...")
                logs_client.delete_metric_filter(
                    logGroupName=log_group,
                    filterName=filter_name
                )
                print(f"Existing metric filter {filter_name} deleted.")
            
            # Create metric filter
            print(f"Creating metric filter {filter_name} in {log_group}...")
            logs_client.put_metric_filter(
                logGroupName=log_group,
                filterName=filter_name,
                filterPattern=filter_pattern,
                metricTransformations=[
                    {
                        'metricName': metric_name,
                        'metricNamespace': namespace,
                        'metricValue': '1',
                        'dimensions': dimensions
                    }
                ]
            )
            print(f"Metric filter {filter_name} created in {log_group}.")
            results[(log_group, filter_name)] = True
        except ClientError as e:
            print(f"Error ensuring metric filter {filter_name} exists in {log_group}: {str(e)}")
            results[(log_group, filter_name)] = False
    
    return all(results.values())

def create_test_log_entries(username, team_group):
    """Create test log entries to verify logging works."""
    log_event = {
        'user': username,
        'team': team_group,
        'accessMethod': 'APIKey',
        'tool': DEFAULT_TOOL,
        'eventName': 'InvokeModel',
        'eventTime': datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
        'awsRegion': REGION,
        'sourceIPAddress': '192.168.1.1'
    }
    
    log_entries = [
        (USER_LOG_GROUP, username),
        (TEAM_LOG_GROUP, team_group)
    ]
    
    results = {}
    
    for log_group, stream_name in log_entries:
        try:
            # Add log to CloudWatch
            logs_client.put_log_events(
                logGroupName=log_group,
                logStreamName=stream_name,
                logEvents=[{
                    'timestamp': int(time.time() * 1000),
                    'message': json.dumps(log_event)
                }]
            )
            print(f"Test log entry added to {log_group}/{stream_name}")
            results[(log_group, stream_name)] = True
        except ClientError as e:
            print(f"Error adding test log entry to {log_group}/{stream_name}: {str(e)}")
            results[(log_group, stream_name)] = False
    
    return all(results.values())

def create_custom_metric(username, team_group):
    """Create a custom CloudWatch metric for the user."""
    try:
        # Put a custom metric data point
        cloudwatch_client.put_metric_data(
            Namespace='UserMetrics',
            MetricData=[
                {
                    'MetricName': 'BedrockUsage',
                    'Dimensions': [
                        {
                            'Name': 'User',
                            'Value': username
                        },
                        {
                            'Name': 'AccessMethod',
                            'Value': 'APIKey'
                        }
                    ],
                    'Value': 1,
                    'Unit': 'Count',
                    'Timestamp': datetime.utcnow()
                }
            ]
        )
        print(f"Custom metric created for user {username}")
        
        # Put a custom metric data point for the team
        cloudwatch_client.put_metric_data(
            Namespace='TeamMetrics',
            MetricData=[
                {
                    'MetricName': 'BedrockTeamUsage',
                    'Dimensions': [
                        {
                            'Name': 'Team',
                            'Value': team_group
                        }
                    ],
                    'Value': 1,
                    'Unit': 'Count',
                    'Timestamp': datetime.utcnow()
                }
            ]
        )
        print(f"Custom metric created for team {team_group}")
        return True
    except ClientError as e:
        print(f"Error creating custom metrics: {str(e)}")
        return False

def verify_lambda_function():
    """Verify that the Lambda function exists and has the correct code."""
    try:
        # Check if Lambda function exists
        response = lambda_client.get_function(
            FunctionName='process-bedrock-calls-poc'
        )
        print("Lambda function process-bedrock-calls-poc exists.")
        
        # We could also check the code here, but that's more complex
        # For now, just verify it exists
        return True
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            print("Lambda function process-bedrock-calls-poc does not exist.")
            print("Please create the Lambda function with the correct code.")
            return False
        else:
            print(f"Error verifying Lambda function: {str(e)}")
            return False

def main():
    """Main function."""
    args = parse_arguments()
    username = args.username
    specified_group = args.group
    
    print(f"Provisioning resources for user {username}...")
    
    # Step 1: Get user groups or create user if needed
    print("\nStep 1: Getting user groups from IAM...")
    groups = get_user_groups(username)
    
    # If user doesn't exist and group is specified, create the user
    if not groups and specified_group:
        print(f"User {username} does not exist. Creating user and adding to group {specified_group}...")
        
        # Validate the specified group name
        if not TEAM_PATTERN.match(specified_group):
            print(f"Error: Group name {specified_group} does not match the required pattern.")
            print("Team groups must follow the pattern: team_<name>_group")
            return 1
        
        # Check if the group exists
        try:
            iam_client.get_group(GroupName=specified_group)
            print(f"Group {specified_group} exists.")
        except ClientError as e:
            print(f"Error: Group {specified_group} does not exist: {str(e)}")
            return 1
        
        # Create the user and add to group
        groups = create_user(username, specified_group)
        if not groups and specified_group:
            # If user creation returned empty groups but we know the group exists,
            # try to add the user to the group directly
            try:
                print(f"Attempting to add user {username} to group {specified_group} directly...")
                iam_client.add_user_to_group(
                    UserName=username,
                    GroupName=specified_group
                )
                print(f"User {username} added to group {specified_group}")
                groups = [specified_group]
            except ClientError as e:
                print(f"Error adding user to group: {str(e)}")
                return 1
        
        if not groups:
            print("Failed to create user or add to group.")
            return 1
    elif not groups:
        print(f"Error: User {username} does not exist and no group was specified.")
        print("Please provide a group name with --group to create the user.")
        return 1
    
    # Step 2: Validate user and group
    print("\nStep 2: Validating user and group naming conventions...")
    team_group = validate_user_and_group(username, groups)
    if not team_group:
        # If a specific group was provided and it's valid, use it
        if specified_group and TEAM_PATTERN.match(specified_group):
            print(f"Using specified group: {specified_group}")
            team_group = specified_group
            
            # Add user to the specified group if not already in it
            if specified_group not in groups:
                try:
                    print(f"Adding user {username} to group {specified_group}")
                    iam_client.add_user_to_group(
                        UserName=username,
                        GroupName=specified_group
                    )
                    print(f"User {username} added to group {specified_group}")
                except ClientError as e:
                    print(f"Error adding user to group: {str(e)}")
                    return 1
        else:
            return 1
    
    # Step 2.5: Ensure user has correct Team tag (CRITICAL for Lambda function)
    print(f"\nStep 2.5: Ensuring user {username} has correct Team tag...")
    try:
        # Check current tags
        response = iam_client.list_user_tags(UserName=username)
        current_tags = {tag['Key']: tag['Value'] for tag in response['Tags']}
        current_team_tag = current_tags.get('Team')
        
        if current_team_tag != team_group:
            if current_team_tag:
                print(f"User {username} has incorrect Team tag: '{current_team_tag}' (should be '{team_group}')")
                print(f"Updating Team tag to '{team_group}'...")
            else:
                print(f"User {username} is missing Team tag. Adding Team tag: '{team_group}'...")
            
            # Add or update the Team tag
            iam_client.tag_user(
                UserName=username,
                Tags=[
                    {
                        'Key': 'Team',
                        'Value': team_group
                    }
                ]
            )
            print(f"✅ Team tag updated successfully for user {username}")
        else:
            print(f"✅ User {username} already has correct Team tag: '{team_group}'")
            
    except ClientError as e:
        print(f"Warning: Could not check/update Team tag for user {username}: {str(e)}")
        print("This may cause issues with team assignment in the Lambda function!")
    
    # Step 3: Check user in quota config
    print("\nStep 3: Checking user in quota configuration...")
    quota_config = load_quota_config()
    quota_config = check_user_in_quota_config(username, team_group, quota_config)
    
    # Step 4: Ensure CloudWatch Logs access
    print("\nStep 4: Ensuring CloudWatch Logs access...")
    if not ensure_cloudwatch_logs_access(username):
        print("Warning: Failed to ensure CloudWatch Logs access. Continuing anyway...")
    
    # Step 4.5: Create and attach Bedrock policy for user
    print(f"\nStep 4.5: Creating Bedrock policy for user {username}...")
    if not create_bedrock_policy_for_user(username):
        print("Warning: Failed to create Bedrock policy. Continuing anyway...")
    
    # Step 5: Ensure log groups exist
    print("\nStep 5: Ensuring log groups exist...")
    if not ensure_log_groups_exist():
        print("Error: Failed to ensure log groups exist.")
        return 1
    
    # Step 6: Ensure log streams exist
    print("\nStep 6: Ensuring log streams exist...")
    if not ensure_log_streams_exist(username, team_group):
        print("Error: Failed to ensure log streams exist.")
        return 1
    
    # Step 7: Ensure metric filters exist
    print("\nStep 7: Ensuring metric filters exist...")
    if not ensure_metric_filters_exist(username, team_group):
        print("Error: Failed to ensure metric filters exist.")
        return 1
    
    # Step 8: Create test log entries
    print("\nStep 8: Creating test log entries...")
    if not create_test_log_entries(username, team_group):
        print("Warning: Failed to create test log entries. Continuing anyway...")
    
    # Step 9: Create custom metrics
    print("\nStep 9: Creating custom metrics...")
    if not create_custom_metric(username, team_group):
        print("Warning: Failed to create custom metrics. Continuing anyway...")
    
    # Step 10: Verify Lambda function
    print("\nStep 10: Verifying Lambda function...")
    if not verify_lambda_function():
        print("Warning: Lambda function verification failed. Continuing anyway...")
    
    print("\nProvisioning completed successfully!")
    print(f"User {username} is now set up for Bedrock usage tracking.")
    print(f"Team group: {team_group}")
    print("\nNext steps:")
    print("1. Wait for CloudTrail events to be processed by the Lambda function")
    print("2. Launch the dashboard using: ./launch_dashboard.sh")
    print("3. Log in with your AWS credentials")
    print("4. Verify that metrics are displayed correctly")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
