#!/usr/bin/env python3
"""
AWS Bedrock Usage Control - User Provisioning Script
"""

import os
import sys
import argparse
import logging
import json
from datetime import datetime

# Add the current directory to the path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from user.user_manager import UserManager
from group.group_manager import GroupManager
from policy.policy_manager import PolicyManager
from utils.aws_utils import load_config

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def provision_user(username, person_name, team_name, create_login=True, attach_policies=True):
    """
    Provision a new user with the specified team and person information
    
    Args:
        username (str): The username for the new user
        person_name (str): The name of the person associated with the user
        team_name (str): The team name the user belongs to
        create_login (bool): Whether to create a login profile for the user
        attach_policies (bool): Whether to attach policies to the user
        
    Returns:
        bool: True if successful, False otherwise
    """
    user_manager = UserManager()
    group_manager = GroupManager()
    policy_manager = PolicyManager()
    
    # Check if team exists, create if it doesn't
    logger.info(f"Checking if team {team_name} exists...")
    group_info = group_manager.get_group_info(team_name)
    if not group_info:
        logger.info(f"Team {team_name} does not exist, creating...")
        team_setup_success = group_manager.setup_team(team_name)
        if not team_setup_success:
            logger.error(f"Failed to set up team {team_name}")
            return False
        logger.info(f"Team {team_name} set up successfully")
    
    # Create user
    logger.info(f"Creating user {username}...")
    user_success = user_manager.create_user(username, person_name, team_name, create_login)
    if not user_success:
        logger.error(f"Failed to create user {username}")
        return False
    logger.info(f"User {username} created successfully")
    
    # Attach policies if requested
    if attach_policies:
        # Create and attach Bedrock policy
        logger.info(f"Creating Bedrock policy for {username}...")
        policy_success, policy_arn = policy_manager.create_bedrock_user_policy(username, team_name)
        if not policy_success:
            logger.warning(f"Failed to create Bedrock policy for {username}")
        else:
            logger.info(f"Attaching Bedrock policy to {username}...")
            attach_success = policy_manager.attach_policy<thinking>
Now I'll create the main script that will be used to provision users, groups, and policies:
</thinking>

<write_to_file>
<path>src/bedrock_manager.py</path>
<content>#!/usr/bin/env python3
"""
AWS Bedrock Usage Control Manager

This script provides a command-line interface for managing AWS Bedrock usage control.
It allows you to create and manage users, groups, roles, and policies for controlling
access to AWS Bedrock services.
"""

import sys
import os
import argparse
import logging
import json
from datetime import datetime

# Add the current directory to the path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import modules
from utils.aws_utils import load_config, get_aws_client
from user.user_manager import UserManager
from group.group_manager import GroupManager
from policy.policy_manager import PolicyManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('bedrock_manager.log')
    ]
)
logger = logging.getLogger(__name__)

class BedrockManager:
    """Main class for managing AWS Bedrock usage control"""
    
    def __init__(self):
        """Initialize the BedrockManager"""
        self.config = load_config()
        self.user_manager = UserManager()
        self.group_manager = GroupManager()
        self.policy_manager = PolicyManager()
    
    def provision_user(self, username, person_name, team_name, create_login=True):
        """
        Provision a new user with the necessary resources
        
        Args:
            username (str): The username for the new user
            person_name (str): The name of the person associated with the user
            team_name (str): The team name the user belongs to
            create_login (bool): Whether to create a login profile for the user
            
        Returns:
            bool: True if successful, False otherwise
        """
        logger.info(f"Provisioning user {username} for {person_name} in team {team_name}")
        
        # Check if group exists, create if it doesn't
        group_name = f"{team_name}_group"
        if not self.group_manager.create_group(team_name):
            logger.info(f"Group {group_name} already exists, continuing...")
        
        # Set up team resources if they don't exist
        self.setup_team_resources(team_name)
        
        # Create user
        if not self.user_manager.create_user(username, person_name, team_name, create_login):
            logger.error(f"Failed to create user {username}")
            return False
        
        # Create and attach user-specific policy
        success, policy_arn = self.policy_manager.create_bedrock_user_policy(username, team_name)
        if success:
            self.policy_manager.attach_policy_to_user(f"{username}_BedrockPolicy", username)
        
        logger.info(f"Successfully provisioned user {username}")
        return True
    
    def setup_team_resources(self, team_name):
        """
        Set up resources for a team
        
        Args:
            team_name (str): The team name to set up resources for
            
        Returns:
            bool: True if successful, False otherwise
        """
        logger.info(f"Setting up resources for team {team_name}")
        
        # Create role for team if it doesn't exist
        role_name = f"{team_name}_BedrockRole"
        if not self.group_manager.create_role_for_group(team_name):
            logger.info(f"Role {role_name} already exists, continuing...")
        
        # Create Bedrock policy if it doesn't exist
        bedrock_policy_name = f"{team_name}_BedrockPolicy"
        bedrock_policy_success, bedrock_policy_arn = self.policy_manager.create_bedrock_policy(team_name)
        if not bedrock_policy_success:
            logger.info(f"Policy {bedrock_policy_name} already exists, continuing...")
            # Get the ARN of the existing policy
            _, bedrock_policy_arn = self.policy_manager.check_if_policy_exists(bedrock_policy_name)
        
        # Create assume role policy if it doesn't exist
        assume_policy_name = f"{team_name}_AssumeRolePolicy"
        assume_policy_success, assume_policy_arn = self.group_manager.create_assume_role_policy(team_name)
        if not assume_policy_success:
            logger.info(f"Policy {assume_policy_name} already exists, continuing...")
            # Get the ARN of the existing policy
            _, assume_policy_arn = self.policy_manager.check_if_policy_exists(assume_policy_name)
        
        # Attach policies
        self.group_manager.attach_policy_to_role(team_name, bedrock_policy_arn)
        self.group_manager.attach_policy_to_group(team_name, assume_policy_arn)
        
        logger.info(f"Successfully set up resources for team {team_name}")
        return True
    
    def create_tool_api_key(self, username, tool_name):
        """
        Create an API key for a user with a tool tag
        
        Args:
            username (str): The username to create the API key for
            tool_name (str): The name of the tool to tag the API key with
            
        Returns:
            tuple: (bool, str) - Success flag and path to credentials file
        """
        logger.info(f"Creating API key for {username} with tool tag {tool_name}")
        
        # Create API key
        success, credentials = self.user_manager.create_api_key(username, tool_name)
        if not success:
            logger.error(f"Failed to create API key for {username}")
            return False, None
        
        # Create tool-specific policy
        policy_success, policy_arn = self.policy_manager.create_tool_specific_policy(username, tool_name)
        if policy_success:
            policy_name = f"{username}_{tool_name}_Policy"
            self.policy_manager.attach_policy_to_user(policy_name, username)
        
        # Save credentials to file
        filename = self.user_manager.save_credentials_to_file(username, tool_name, credentials)
        
        logger.info(f"Successfully created API key for {username} with tool tag {tool_name}")
        return True, filename
    
    def list_users(self, team_name=None):
        """
        List users, optionally filtered by team
        
        Args:
            team_name (str, optional): The team name to filter users by
            
        Returns:
            list: List of user information dictionaries
        """
        logger.info(f"Listing users{' for team ' + team_name if team_name else ''}")
        
        iam_client = get_aws_client('iam')
        users_info = []
        
        if team_name:
            # List users by team
            usernames = self.user_manager.list_users_by_team(team_name)
            for username in usernames:
                user_info = self.user_manager.get_user_info(username)
                if user_info:
                    users_info.append(user_info)
        else:
            # List all users
            paginator = iam_client.get_paginator('list_users')
            for page in paginator.paginate():
                for user in page['Users']:
                    username = user['UserName']
                    user_info = self.user_manager.get_user_info(username)
                    if user_info:
                        users_info.append(user_info)
        
        return users_info
    
    def list_groups(self):
        """
        List all groups
        
        Returns:
            list: List of group information dictionaries
        """
        logger.info("Listing groups")
        
        iam_client = get_aws_client('iam')
        groups_info = []
        
        paginator = iam_client.get_paginator('list_groups')
        for page in paginator.paginate():
            for group in page['Groups']:
                group_name = group['GroupName']
                
                # Extract team name from group name
                if group_name.endswith('_group'):
                    team_name = group_name[:-6]  # Remove '_group' suffix
                    group_info = self.group_manager.get_group_info(team_name)
                    if group_info:
                        groups_info.append(group_info)
        
        return groups_info

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='AWS Bedrock Usage Control Manager')
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # User commands
    user_parser = subparsers.add_parser('user', help='User management commands')
    user_subparsers = user_parser.add_subparsers(dest='user_command', help='User command to execute')
    
    # User create command
    user_create_parser = user_subparsers.add_parser('create', help='Create a new user')
    user_create_parser.add_argument('username', help='Username for the new user')
    user_create_parser.add_argument('person_name', help='Name of the person associated with the user')
    user_create_parser.add_argument('team_name', help='Team name the user belongs to')
    user_create_parser.add_argument('--no-login', action='store_true', help='Do not create a login profile')
    
    # User delete command
    user_delete_parser = user_subparsers.add_parser('delete', help='Delete a user')
    user_delete_parser.add_argument('username', help='Username to delete')
    
    # User info command
    user_info_parser = user_subparsers.add_parser('info', help='Get information about a user')
    user_info_parser.add_argument('username', help='Username to get information for')
    
    # User list command
    user_list_parser = user_subparsers.add_parser('list', help='List users')
    user_list_parser.add_argument('--team', help='Team name to filter users by')
    
    # User create-key command
    user_key_parser = user_subparsers.add_parser('create-key', help='Create an API key for a user')
    user_key_parser.add_argument('username', help='Username to create the API key for')
    user_key_parser.add_argument('tool_name', help='Name of the tool to tag the API key with')
    
    # Group commands
    group_parser = subparsers.add_parser('group', help='Group management commands')
    group_subparsers = group_parser.add_subparsers(dest='group_command', help='Group command to execute')
    
    # Group create command
    group_create_parser = group_subparsers.add_parser('create', help='Create a new group')
    group_create_parser.add_argument('team_name', help='Team name to create a group for')
    
    # Group delete command
    group_delete_parser = group_subparsers.add_parser('delete', help='Delete a group')
    group_delete_parser.add_argument('team_name', help='Team name to delete the group for')
    
    # Group info command
    group_info_parser = group_subparsers.add_parser('info', help='Get information about a group')
    group_info_parser.add_argument('team_name', help='Team name to get information for')
    
    # Group list command
    group_list_parser = group_subparsers.add_parser('list', help='List groups')
    
    # Group setup command
    group_setup_parser = group_subparsers.add_parser('setup', help='Set up a team with group, role, and policies')
    group_setup_parser.add_argument('team_name', help='Team name to set up')
    
    # Policy commands
    policy_parser = subparsers.add_parser('policy', help='Policy management commands')
    policy_subparsers = policy_parser.add_subparsers(dest='policy_command', help='Policy command to execute')
    
    # Policy create command
    policy_create_parser = policy_subparsers.add_parser('create', help='Create a policy')
    policy_create_parser.add_argument('policy_name', help='Name of the policy to create')
    policy_create_parser.add_argument('policy_file', help='Path to a JSON file containing the policy document')
    
    # Policy delete command
    policy_delete_parser = policy_subparsers.add_parser('delete', help='Delete a policy')
    policy_delete_parser.add_argument('policy_name', help='Name of the policy to delete')
    
    # Policy info command
    policy_info_parser = policy_subparsers.add_parser('info', help='Get information about a policy')
    policy_info_parser.add_argument('policy_name', help='Name of the policy to get information for')
    
    # Policy attach command
    policy_attach_parser = policy_subparsers.add_parser('attach', help='Attach a policy to a user or role')
    policy_attach_parser.add_argument('policy_name', help='Name of the policy to attach')
    policy_attach_parser.add_argument('--user', help='Username to attach the policy to')
    policy_attach_parser.add_argument('--role', help='Role name to attach the policy to')
    
    return parser.parse_args()

def main():
    """Main function"""
    args = parse_args()
    bedrock_manager = BedrockManager()
    
    if args.command == 'user':
        if args.user_command == 'create':
            success = bedrock_manager.provision_user(
                args.username,
                args.person_name,
                args.team_name,
                not args.no_login
            )
            if success:
                print(f"User {args.username} created successfully")
            else:
                print(f"Failed to create user {args.username}")
                sys.exit(1)
        
        elif args.user_command == 'delete':
            success = bedrock_manager.user_manager.delete_user(args.username)
            if success:
                print(f"User {args.username} deleted successfully")
            else:
                print(f"Failed to delete user {args.username}")
                sys.exit(1)
        
        elif args.user_command == 'info':
            user_info = bedrock_manager.user_manager.get_user_info(args.username)
            if user_info:
                print(json.dumps(user_info, indent=2))
            else:
                print(f"User {args.username} not found")
                sys.exit(1)
        
        elif args.user_command == 'list':
            users = bedrock_manager.list_users(args.team)
            print(f"Found {len(users)} users")
            for user in users:
                print(f"- {user['username']} ({user['tags'].get('Person', 'Unknown')})")
                print(f"  Team: {user['tags'].get('Team', 'Unknown')}")
                print(f"  Groups: {', '.join(user['groups'])}")
                print(f"  Created: {user['created']}")
                print()
        
        elif args.user_command == 'create-key':
            success, filename = bedrock_manager.create_tool_api_key(args.username, args.tool_name)
            if success:
                print(f"API key created successfully and saved to {filename}")
            else:
                print(f"Failed to create API key for {args.username}")
                sys.exit(1)
    
    elif args.command == 'group':
        if args.group_command == 'create':
            success = bedrock_manager.group_manager.create_group(args.team_name)
            if success:
                print(f"Group for team {args.team_name} created successfully")
            else:
                print(f"Failed to create group for team {args.team_name}")
                sys.exit(1)
        
        elif args.group_command == 'delete':
            success = bedrock_manager.group_manager.delete_group(args.team_name)
            if success:
                print(f"Group for team {args.team_name} deleted successfully")
            else:
                print(f"Failed to delete group for team {args.team_name}")
                sys.exit(1)
        
        elif args.group_command == 'info':
            group_info = bedrock_manager.group_manager.get_group_info(args.team_name)
            if group_info:
                print(json.dumps(group_info, indent=2))
            else:
                print(f"Group for team {args.team_name} not found")
                sys.exit(1)
        
        elif args.group_command == 'list':
            groups = bedrock_manager.list_groups()
            print(f"Found {len(groups)} groups")
            for group in groups:
                print(f"- {group['group_name']}")
                print(f"  Users: {len(group['users'])}")
                print(f"  Policies: {len(group['policies'])}")
                print(f"  Created: {group['created']}")
                print()
        
        elif args.group_command == 'setup':
            success = bedrock_manager.setup_team_resources(args.team_name)
            if success:
                print(f"Team {args.team_name} set up successfully")
            else:
                print(f"Failed to set up team {args.team_name}")
                sys.exit(1)
    
    elif args.command == 'policy':
        if args.policy_command == 'create':
            try:
                with open(args.policy_file, 'r') as f:
                    policy_document = json.load(f)
                
                success, policy_arn = bedrock_manager.policy_manager.create_policy(
                    args.policy_name,
                    policy_document
                )
                
                if success:
                    print(f"Policy {args.policy_name} created successfully")
                    print(f"ARN: {policy_arn}")
                else:
                    print(f"Failed to create policy {args.policy_name}")
                    sys.exit(1)
            except Exception as e:
                print(f"Error creating policy: {str(e)}")
                sys.exit(1)
        
        elif args.policy_command == 'delete':
            success = bedrock_manager.policy_manager.delete_policy(args.policy_name)
            if success:
                print(f"Policy {args.policy_name} deleted successfully")
            else:
                print(f"Failed to delete policy {args.policy_name}")
                sys.exit(1)
        
        elif args.policy_command == 'info':
            policy_info = bedrock_manager.policy_manager.get_policy_info(args.policy_name)
            if policy_info:
                print(json.dumps(policy_info, indent=2))
            else:
                print(f"Policy {args.policy_name} not found")
                sys.exit(1)
        
        elif args.policy_command == 'attach':
            if args.user:
                success = bedrock_manager.policy_manager.attach_policy_to_user(args.policy_name, args.user)
                if success:
                    print(f"Policy {args.policy_name} attached to user {args.user} successfully")
                else:
                    print(f"Failed to attach policy {args.policy_name} to user {args.user}")
                    sys.exit(1)
            elif args.role:
                success = bedrock_manager.policy_manager.attach_policy_to_role(args.policy_name, args.role)
                if success:
                    print(f"Policy {args.policy_name} attached to role {args.role} successfully")
                else:
                    print(f"Failed to attach policy {args.policy_name} to role {args.role}")
                    sys.exit(1)
            else:
                print("Error: You must specify either --user or --role")
                sys.exit(1)
    
    else:
        print("Error: No command specified")
        print("Available commands: user, group, policy")
        sys.exit(1)

if __name__ == "__main__":
    main()
