#!/usr/bin/env python3
"""
User Management Module for AWS Bedrock Usage Control
"""

import sys
import os
import logging
import json
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.aws_utils import (
    load_config, get_aws_client, check_if_user_exists, check_if_group_exists
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class UserManager:
    """User Management class for AWS Bedrock Usage Control"""
    
    def __init__(self):
        """Initialize the UserManager"""
        self.config = load_config()
        self.iam_client = get_aws_client('iam')
        self.cloudwatch_client = get_aws_client('cloudwatch')
        self.logs_client = get_aws_client('logs')
        self.sns_client = get_aws_client('sns')
        self.budgets_client = get_aws_client('budgets')
    
    def create_user(self, username, person_name, team_name, create_login=True):
        """
        Create a new IAM user
        
        Args:
            username (str): The username for the new user
            person_name (str): The name of the person associated with the user
            team_name (str): The team name the user belongs to
            create_login (bool): Whether to create a login profile for the user
            
        Returns:
            bool: True if successful, False otherwise
        """
        # Check if user already exists
        if check_if_user_exists(username, self.iam_client):
            logger.warning(f"User {username} already exists")
            return False
        
        # Check if group exists
        if not check_if_group_exists(f"{team_name}_group", self.iam_client):
            logger.warning(f"Group {team_name}_group does not exist")
            return False
        
        try:
            # Create user
            self.iam_client.create_user(UserName=username)
            logger.info(f"Created user: {username}")
            
            # Tag user with team and person information
            self.iam_client.tag_user(
                UserName=username,
                Tags=[
                    {'Key': 'Team', 'Value': team_name},
                    {'Key': 'Person', 'Value': person_name}
                ]
            )
            logger.info(f"Tagged user {username} with Team={team_name} and Person={person_name}")
            
            # Create login profile if requested
            if create_login:
                self.iam_client.create_login_profile(
                    UserName=username,
                    Password=self.config['temp_password'],
                    PasswordResetRequired=True
                )
                logger.info(f"Created login profile for {username}")
            
            # Add user to group
            self.iam_client.add_user_to_group(
                UserName=username,
                GroupName=f"{team_name}_group"
            )
            logger.info(f"Added {username} to group {team_name}_group")
            
            return True
        except Exception as e:
            logger.error(f"Error creating user {username}: {str(e)}")
            return False
    
    def delete_user(self, username):
        """
        Delete an IAM user
        
        Args:
            username (str): The username to delete
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not check_if_user_exists(username, self.iam_client):
            logger.warning(f"User {username} does not exist")
            return False
        
        try:
            # Get user's groups
            groups_response = self.iam_client.list_groups_for_user(UserName=username)
            
            # Remove user from all groups
            for group in groups_response['Groups']:
                self.iam_client.remove_user_from_group(
                    UserName=username,
                    GroupName=group['GroupName']
                )
                logger.info(f"Removed {username} from group {group['GroupName']}")
            
            # Delete login profile if it exists
            try:
                self.iam_client.delete_login_profile(UserName=username)
                logger.info(f"Deleted login profile for {username}")
            except Exception:
                pass
            
            # Delete access keys
            keys_response = self.iam_client.list_access_keys(UserName=username)
            for key in keys_response['AccessKeyMetadata']:
                self.iam_client.delete_access_key(
                    UserName=username,
                    AccessKeyId=key['AccessKeyId']
                )
                logger.info(f"Deleted access key {key['AccessKeyId']} for {username}")
            
            # Detach user policies
            policies_response = self.iam_client.list_attached_user_policies(UserName=username)
            for policy in policies_response['AttachedPolicies']:
                self.iam_client.detach_user_policy(
                    UserName=username,
                    PolicyArn=policy['PolicyArn']
                )
                logger.info(f"Detached policy {policy['PolicyName']} from {username}")
            
            # Delete user
            self.iam_client.delete_user(UserName=username)
            logger.info(f"Deleted user {username}")
            
            return True
        except Exception as e:
            logger.error(f"Error deleting user {username}: {str(e)}")
            return False
    
    def create_api_key(self, username, tool_name):
        """
        Create an API key for a user with a tool tag
        
        Args:
            username (str): The username to create the API key for
            tool_name (str): The name of the tool to tag the API key with
            
        Returns:
            tuple: (bool, dict) - Success flag and credentials dictionary
        """
        if not check_if_user_exists(username, self.iam_client):
            logger.warning(f"User {username} does not exist")
            return False, None
        
        try:
            # Check if user already has 2 access keys (AWS limit)
            keys_response = self.iam_client.list_access_keys(UserName=username)
            if len(keys_response['AccessKeyMetadata']) >= 2:
                # Delete oldest key
                oldest_key = sorted(keys_response['AccessKeyMetadata'], key=lambda k: k['CreateDate'])[0]
                self.iam_client.delete_access_key(
                    UserName=username,
                    AccessKeyId=oldest_key['AccessKeyId']
                )
                logger.info(f"Deleted oldest access key {oldest_key['AccessKeyId']} for {username}")
            
            # Create new access key
            key_response = self.iam_client.create_access_key(UserName=username)
            access_key = key_response['AccessKey']
            
            # Tag the access key
            self.iam_client.tag_user(
                UserName=username,
                Tags=[{'Key': 'Tool', 'Value': tool_name}]
            )
            logger.info(f"Created and tagged access key for {username} with Tool={tool_name}")
            
            # Return credentials
            credentials = {
                'AWS_ACCESS_KEY_ID': access_key['AccessKeyId'],
                'AWS_SECRET_ACCESS_KEY': access_key['SecretAccessKey']
            }
            
            return True, credentials
        except Exception as e:
            logger.error(f"Error creating API key for {username}: {str(e)}")
            return False, None
    
    def get_user_info(self, username):
        """
        Get information about a user
        
        Args:
            username (str): The username to get information for
            
        Returns:
            dict: User information or None if user doesn't exist
        """
        if not check_if_user_exists(username, self.iam_client):
            logger.warning(f"User {username} does not exist")
            return None
        
        try:
            # Get user details
            user_response = self.iam_client.get_user(UserName=username)
            user_info = {
                'username': username,
                'arn': user_response['User']['Arn'],
                'created': user_response['User']['CreateDate'].strftime('%Y-%m-%d %H:%M:%S'),
                'tags': {},
                'groups': [],
                'policies': []
            }
            
            # Get user tags
            tags_response = self.iam_client.list_user_tags(UserName=username)
            for tag in tags_response['Tags']:
                user_info['tags'][tag['Key']] = tag['Value']
            
            # Get user groups
            groups_response = self.iam_client.list_groups_for_user(UserName=username)
            for group in groups_response['Groups']:
                user_info['groups'].append(group['GroupName'])
            
            # Get attached policies
            policies_response = self.iam_client.list_attached_user_policies(UserName=username)
            for policy in policies_response['AttachedPolicies']:
                user_info['policies'].append({
                    'name': policy['PolicyName'],
                    'arn': policy['PolicyArn']
                })
            
            return user_info
        except Exception as e:
            logger.error(f"Error getting user info for {username}: {str(e)}")
            return None
    
    def list_users_by_team(self, team_name):
        """
        List all users in a team
        
        Args:
            team_name (str): The team name to list users for
            
        Returns:
            list: List of usernames in the team
        """
        try:
            # Get all users
            users = []
            paginator = self.iam_client.get_paginator('list_users')
            
            for page in paginator.paginate():
                for user in page['Users']:
                    username = user['UserName']
                    
                    # Get user tags
                    tags_response = self.iam_client.list_user_tags(UserName=username)
                    for tag in tags_response['Tags']:
                        if tag['Key'] == 'Team' and tag['Value'] == team_name:
                            users.append(username)
                            break
            
            return users
        except Exception as e:
            logger.error(f"Error listing users for team {team_name}: {str(e)}")
            return []
    
    def save_credentials_to_file(self, username, tool_name, credentials):
        """
        Save API key credentials to a file
        
        Args:
            username (str): The username the credentials are for
            tool_name (str): The tool name the credentials are for
            credentials (dict): The credentials to save
            
        Returns:
            str: Path to the credentials file
        """
        try:
            # Create filename
            filename = f"{username}_{tool_name}_credentials.txt"
            
            # Write credentials to file
            with open(filename, 'w') as f:
                for key, value in credentials.items():
                    f.write(f"{key}={value}\n")
            
            logger.info(f"Saved credentials to {filename}")
            return filename
        except Exception as e:
            logger.error(f"Error saving credentials to file: {str(e)}")
            return None

# Main function for testing
if __name__ == "__main__":
    user_manager = UserManager()
    
    # Example usage
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "create" and len(sys.argv) >= 5:
            username = sys.argv[2]
            person_name = sys.argv[3]
            team_name = sys.argv[4]
            success = user_manager.create_user(username, person_name, team_name)
            print(f"User creation {'successful' if success else 'failed'}")
        
        elif command == "delete" and len(sys.argv) >= 3:
            username = sys.argv[2]
            success = user_manager.delete_user(username)
            print(f"User deletion {'successful' if success else 'failed'}")
        
        elif command == "info" and len(sys.argv) >= 3:
            username = sys.argv[2]
            user_info = user_manager.get_user_info(username)
            if user_info:
                print(json.dumps(user_info, indent=2))
        
        elif command == "list" and len(sys.argv) >= 3:
            team_name = sys.argv[2]
            users = user_manager.list_users_by_team(team_name)
            print(f"Users in team {team_name}:")
            for user in users:
                print(f"- {user}")
        
        elif command == "create-key" and len(sys.argv) >= 4:
            username = sys.argv[2]
            tool_name = sys.argv[3]
            success, credentials = user_manager.create_api_key(username, tool_name)
            if success:
                filename = user_manager.save_credentials_to_file(username, tool_name, credentials)
                print(f"API key created and saved to {filename}")
        
        else:
            print("Invalid command or arguments")
            print("Usage:")
            print("  python user_manager.py create <username> <person_name> <team_name>")
            print("  python user_manager.py delete <username>")
            print("  python user_manager.py info <username>")
            print("  python user_manager.py list <team_name>")
            print("  python user_manager.py create-key <username> <tool_name>")
    else:
        print("No command provided")
        print("Available commands: create, delete, info, list, create-key")
