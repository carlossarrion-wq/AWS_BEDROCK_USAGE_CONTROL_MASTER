#!/usr/bin/env python3
import boto3
import json
import sys
import time
import os

# Set variables
REGION = "eu-west-1"
LOG_GROUP_NAME = "/aws/bedrock/user_usage"
TEAM_LOG_GROUP_NAME = "/aws/bedrock/team_usage"
QUOTA_CONFIG_FILE = 'quota_config.json'

def load_quota_config():
    """
    Load the quota configuration from the JSON file.
    """
    try:
        with open(QUOTA_CONFIG_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: Quota configuration file '{QUOTA_CONFIG_FILE}' not found.")
        return {"users": {}, "teams": {}}
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in '{QUOTA_CONFIG_FILE}'.")
        return {"users": {}, "teams": {}}

def update_user_metric_filter(user):
    """
    Update the CloudWatch metric filter for a user to include dimensions.
    """
    print(f"Updating metric filter for user {user}...")
    
    # Create CloudWatch Logs client
    logs_client = boto3.client('logs', region_name=REGION)
    
    # First, check if there's an existing filter with the same name
    try:
        print(f"Checking for existing metric filter: {user}_usage_fixed")
        response = logs_client.describe_metric_filters(
            logGroupName=LOG_GROUP_NAME,
            filterNamePrefix=f"{user}_usage_fixed"
        )
        
        if response['metricFilters']:
            print(f"Deleting existing metric filter: {user}_usage_fixed")
            logs_client.delete_metric_filter(
                logGroupName=LOG_GROUP_NAME,
                filterName=f"{user}_usage_fixed"
            )
            print("Existing metric filter deleted successfully.")
    except Exception as e:
        print(f"Warning: Error checking/deleting existing metric filter: {str(e)}")
    
    # Wait a moment for the deletion to propagate
    time.sleep(1)
    
    # Create new metric filter with dimensions using AWS CLI format
    try:
        print(f"Creating new metric filter with dimensions for {user}...")
        response = logs_client.put_metric_filter(
            logGroupName=LOG_GROUP_NAME,
            filterName=f"{user}_usage_fixed",
            filterPattern=f'{{ $.user = "{user}" }}',
            metricTransformations=[
                {
                    'metricName': 'BedrockUsage',
                    'metricNamespace': 'UserMetrics',
                    'metricValue': '1',
                    'dimensions': {
                        'User': '$.user'
                    }
                }
            ]
        )
        print("New metric filter created successfully with dimensions.")
        return True
    except Exception as e:
        print(f"Error creating metric filter for {user}: {str(e)}")
        return False

def update_user_tool_metric_filter(user, tool):
    """
    Update the CloudWatch metric filter for tool usage to include dimensions.
    """
    print(f"Updating tool metric filter for {user} with {tool}...")
    
    # Create CloudWatch Logs client
    logs_client = boto3.client('logs', region_name=REGION)
    
    # First, check if there's an existing filter with the same name
    try:
        print(f"Checking for existing tool metric filter: {user}_{tool}_usage_fixed")
        response = logs_client.describe_metric_filters(
            logGroupName=LOG_GROUP_NAME,
            filterNamePrefix=f"{user}_{tool}_usage_fixed"
        )
        
        if response['metricFilters']:
            print(f"Deleting existing tool metric filter: {user}_{tool}_usage_fixed")
            logs_client.delete_metric_filter(
                logGroupName=LOG_GROUP_NAME,
                filterName=f"{user}_{tool}_usage_fixed"
            )
            print("Existing tool metric filter deleted successfully.")
    except Exception as e:
        print(f"Warning: Error checking/deleting existing tool metric filter: {str(e)}")
    
    # Wait a moment for the deletion to propagate
    time.sleep(1)
    
    # Create new metric filter with dimensions using AWS CLI format
    try:
        print(f"Creating new tool metric filter with dimensions for {user} with {tool}...")
        response = logs_client.put_metric_filter(
            logGroupName=LOG_GROUP_NAME,
            filterName=f"{user}_{tool}_usage_fixed",
            filterPattern=f'{{ $.user = "{user}" && $.tool = "{tool}" }}',
            metricTransformations=[
                {
                    'metricName': 'BedrockToolUsage',
                    'metricNamespace': 'UserMetrics',
                    'metricValue': '1',
                    'dimensions': {
                        'User': '$.user',
                        'Tool': '$.tool'
                    }
                }
            ]
        )
        print("New tool metric filter created successfully with dimensions.")
        return True
    except Exception as e:
        print(f"Error creating tool metric filter for {user} with {tool}: {str(e)}")
        return False

def update_team_metric_filter(team):
    """
    Update the CloudWatch metric filter for a team to include dimensions.
    """
    print(f"Updating metric filter for team {team}...")
    
    # Create CloudWatch Logs client
    logs_client = boto3.client('logs', region_name=REGION)
    
    # First, check if there's an existing filter with the same name
    try:
        print(f"Checking for existing metric filter: {team}_usage_fixed")
        response = logs_client.describe_metric_filters(
            logGroupName=TEAM_LOG_GROUP_NAME,
            filterNamePrefix=f"{team}_usage_fixed"
        )
        
        if response['metricFilters']:
            print(f"Deleting existing metric filter: {team}_usage_fixed")
            logs_client.delete_metric_filter(
                logGroupName=TEAM_LOG_GROUP_NAME,
                filterName=f"{team}_usage_fixed"
            )
            print("Existing metric filter deleted successfully.")
    except Exception as e:
        print(f"Warning: Error checking/deleting existing metric filter: {str(e)}")
    
    # Wait a moment for the deletion to propagate
    time.sleep(1)
    
    # Create new metric filter with dimensions using AWS CLI format
    try:
        print(f"Creating new metric filter with dimensions for {team}...")
        response = logs_client.put_metric_filter(
            logGroupName=TEAM_LOG_GROUP_NAME,
            filterName=f"{team}_usage_fixed",
            filterPattern=f'{{ $.team = "{team}" }}',
            metricTransformations=[
                {
                    'metricName': 'BedrockTeamUsage',
                    'metricNamespace': 'TeamMetrics',
                    'metricValue': '1',
                    'dimensions': {
                        'Team': '$.team'
                    }
                }
            ]
        )
        print("New team metric filter created successfully with dimensions.")
        return True
    except Exception as e:
        print(f"Error creating metric filter for {team}: {str(e)}")
        return False

def list_metric_filters():
    """
    List all metric filters for the log group to verify the update.
    """
    print(f"\nListing metric filters for log group {LOG_GROUP_NAME}:")
    
    # Create CloudWatch Logs client
    logs_client = boto3.client('logs', region_name=REGION)
    
    try:
        response = logs_client.describe_metric_filters(
            logGroupName=LOG_GROUP_NAME
        )
        
        if not response['metricFilters']:
            print("No metric filters found.")
            return
        
        for filter in response['metricFilters']:
            print(f"\nFilter Name: {filter['filterName']}")
            print(f"Filter Pattern: {filter['filterPattern']}")
            print("Metric Transformations:")
            for transform in filter['metricTransformations']:
                print(f"  - Metric Name: {transform['metricName']}")
                print(f"  - Metric Namespace: {transform['metricNamespace']}")
                print(f"  - Metric Value: {transform['metricValue']}")
                if 'dimensions' in transform:
                    print("  - Dimensions:")
                    for key, value in transform['dimensions'].items():
                        print(f"      {key}: {value}")
    except Exception as e:
        print(f"Error listing metric filters: {str(e)}")

def main():
    print("Updating CloudWatch metric filters to include dimensions for all users and teams...")
    
    # Load quota configuration
    quota_config = load_quota_config()
    
    # Track success/failure
    user_successes = 0
    user_failures = 0
    tool_successes = 0
    tool_failures = 0
    team_successes = 0
    team_failures = 0
    
    # Process all users
    for user, user_config in quota_config.get('users', {}).items():
        # Update user metric filter
        if update_user_metric_filter(user):
            user_successes += 1
        else:
            user_failures += 1
        
        # Tool metric filters are no longer needed since tools section has been removed
        # All users now use a single unified tool approach
    
    # Process all teams
    for team in quota_config.get('teams', {}).keys():
        if update_team_metric_filter(team):
            team_successes += 1
        else:
            team_failures += 1
    
    # List the updated metric filters
    list_metric_filters()
    
    # Print summary
    print("\n=== Metric Filter Update Summary ===")
    print(f"User metric filters: {user_successes} succeeded, {user_failures} failed")
    print(f"Tool metric filters: {tool_successes} succeeded, {tool_failures} failed")
    print(f"Team metric filters: {team_successes} succeeded, {team_failures} failed")
    
    if user_failures == 0 and tool_failures == 0 and team_failures == 0:
        print("\nAll metric filters updated successfully!")
        print("\nNext steps:")
        print("1. Wait for new log events to trigger the filters and generate metrics with the proper dimensions.")
        print("2. Refresh the dashboard to see the data.")
    else:
        print("\nThere were errors updating some metric filters. Please check the logs above.")

if __name__ == "__main__":
    main()
