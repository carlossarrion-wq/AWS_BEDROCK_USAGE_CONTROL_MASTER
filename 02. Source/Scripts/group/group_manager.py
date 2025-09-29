#!/usr/bin/env python3
"""
Group Management Module for AWS Bedrock Usage Control
"""

import sys
import os
import logging
import json

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.aws_utils import (
    load_config, get_aws_client, check_if_group_exists, check_if_role_exists, check_if_policy_exists
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GroupManager:
    """Group Management class for AWS Bedrock Usage Control"""
    
    def __init__(self):
        """Initialize the GroupManager"""
        self.config = load_config()
        self.iam_client = get_aws_client('iam')
    
    def create_group(self, team_name):
        """
        Create a new IAM group for a team
        
        Args:
            team_name (str): The team name to create a group for
            
        Returns:
            bool: True if successful, False otherwise
        """
        group_name = f"{team_name}_group"
        
        # Check if group already exists
        if check_if_group_exists(group_name, self.iam_client):
            logger.warning(f"Group {group_name} already exists")
            return False
        
        try:
            # Create group
            self.iam_client.create_group(GroupName=group_name)
            logger.info(f"Created group: {group_name}")
            
            # Tag group with team information
            self.iam_client.tag_resource(
                ResourceArn=f"arn:aws:iam::{self.config['account_id']}:group/{group_name}",
                Tags=[{'Key': 'Team', 'Value': team_name}]
            )
            logger.info(f"Tagged group {group_name} with Team={team_name}")
            
            return True
        except Exception as e:
            logger.error(f"Error creating group {group_name}: {str(e)}")
            return False
    
    def delete_group(self, team_name):
        """
        Delete an IAM group
        
        Args:
            team_name (str): The team name to delete the group for
            
        Returns:
            bool: True if successful, False otherwise
        """
        group_name = f"{team_name}_group"
        
        if not check_if_group_exists(group_name, self.iam_client):
            logger.warning(f"Group {group_name} does not exist")
            return False
        
        try:
            # Get users in group
            users_response = self.iam_client.get_group(GroupName=group_name)
            
            # Remove all users from group
            for user in users_response['Users']:
                self.iam_client.remove_user_from_group(
                    GroupName=group_name,
                    UserName=user['UserName']
                )
                logger.info(f"Removed user {user['UserName']} from group {group_name}")
            
            # Detach all policies from group
            policies_response = self.iam_client.list_attached_group_policies(GroupName=group_name)
            for policy in policies_response['AttachedPolicies']:
                self.iam_client.detach_group_policy(
                    GroupName=group_name,
                    PolicyArn=policy['PolicyArn']
                )
                logger.info(f"Detached policy {policy['PolicyName']} from group {group_name}")
            
            # Delete group
            self.iam_client.delete_group(GroupName=group_name)
            logger.info(f"Deleted group {group_name}")
            
            return True
        except Exception as e:
            logger.error(f"Error deleting group {group_name}: {str(e)}")
            return False
    
    def create_role_for_group(self, team_name):
        """
        Create an IAM role for a team
        
        Args:
            team_name (str): The team name to create a role for
            
        Returns:
            bool: True if successful, False otherwise
        """
        role_name = f"{team_name}_BedrockRole"
        
        # Check if role already exists
        if check_if_role_exists(role_name, self.iam_client):
            logger.warning(f"Role {role_name} already exists")
            return False
        
        try:
            # Create assume role policy document
            assume_role_policy = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": {
                            "AWS": f"arn:aws:iam::{self.config['account_id']}:root"
                        },
                        "Action": "sts:AssumeRole",
                        "Condition": {
                            "StringEquals": {
                                "aws:PrincipalTag/Team": team_name
                            }
                        }
                    }
                ]
            }
            
            # Create role
            self.iam_client.create_role(
                RoleName=role_name,
                AssumeRolePolicyDocument=json.dumps(assume_role_policy)
            )
            logger.info(f"Created role: {role_name}")
            
            # Tag role with team information
            self.iam_client.tag_role(
                RoleName=role_name,
                Tags=[{'Key': 'Team', 'Value': team_name}]
            )
            logger.info(f"Tagged role {role_name} with Team={team_name}")
            
            return True
        except Exception as e:
            logger.error(f"Error creating role {role_name}: {str(e)}")
            return False
    
    def create_bedrock_policy(self, team_name):
        """
        Create a Bedrock access policy for a team
        
        Args:
            team_name (str): The team name to create a policy for
            
        Returns:
            tuple: (bool, str) - Success flag and policy ARN
        """
        policy_name = f"{team_name}_BedrockPolicy"
        
        # Check if policy already exists
        exists, policy_arn = check_if_policy_exists(policy_name, self.iam_client)
        if exists:
            logger.warning(f"Policy {policy_name} already exists")
            return False, policy_arn
        
        try:
            # Create policy document
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
                            f"arn:aws:bedrock:{self.config['region']}:*:inference-profile/eu.anthropic.claude-sonnet-4-20250514-v1:0",
                            f"arn:aws:bedrock:{self.config['region']}:*:inference-profile/eu.amazon.nova-pro-v1:0",
                            f"arn:aws:bedrock:{self.config['region']}:*:inference-profile/eu.anthropic.claude-3-7-sonnet-20250219-v1:0",
                            f"arn:aws:bedrock:{self.config['region']}:{self.config['account_id']}:inference-profile/eu.anthropic.claude-3-7-sonnet-20250219-v1:0"
                        ]
                    },
                    {
                        "Effect": "Allow",
                        "Action": [
                            "bedrock:GetInferenceProfile",
                            "bedrock:ListInferenceProfiles"
                        ],
                        "Resource": "*"
                    }
                ]
            }
            
            # Create policy
            response = self.iam_client.create_policy(
                PolicyName=policy_name,
                PolicyDocument=json.dumps(policy_document)
            )
            policy_arn = response['Policy']['Arn']
            logger.info(f"Created policy: {policy_name} with ARN: {policy_arn}")
            
            return True, policy_arn
        except Exception as e:
            logger.error(f"Error creating policy {policy_name}: {str(e)}")
            return False, None
    
    def create_assume_role_policy(self, team_name):
        """
        Create a policy for assuming the team's Bedrock role
        
        Args:
            team_name (str): The team name to create a policy for
            
        Returns:
            tuple: (bool, str) - Success flag and policy ARN
        """
        policy_name = f"{team_name}_AssumeRolePolicy"
        role_name = f"{team_name}_BedrockRole"
        
        # Check if policy already exists
        exists, policy_arn = check_if_policy_exists(policy_name, self.iam_client)
        if exists:
            logger.warning(f"Policy {policy_name} already exists")
            return False, policy_arn
        
        try:
            # Create policy document
            policy_document = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Action": "sts:AssumeRole",
                        "Resource": f"arn:aws:iam::{self.config['account_id']}:role/{role_name}"
                    }
                ]
            }
            
            # Create policy
            response = self.iam_client.create_policy(
                PolicyName=policy_name,
                PolicyDocument=json.dumps(policy_document)
            )
            policy_arn = response['Policy']['Arn']
            logger.info(f"Created policy: {policy_name} with ARN: {policy_arn}")
            
            return True, policy_arn
        except Exception as e:
            logger.error(f"Error creating policy {policy_name}: {str(e)}")
            return False, None
    
    def attach_policy_to_group(self, team_name, policy_arn):
        """
        Attach a policy to a group
        
        Args:
            team_name (str): The team name
            policy_arn (str): The policy ARN to attach
            
        Returns:
            bool: True if successful, False otherwise
        """
        group_name = f"{team_name}_group"
        
        if not check_if_group_exists(group_name, self.iam_client):
            logger.warning(f"Group {group_name} does not exist")
            return False
        
        try:
            # Attach policy to group
            self.iam_client.attach_group_policy(
                GroupName=group_name,
                PolicyArn=policy_arn
            )
            logger.info(f"Attached policy {policy_arn} to group {group_name}")
            
            return True
        except Exception as e:
            logger.error(f"Error attaching policy to group {group_name}: {str(e)}")
            return False
    
    def attach_policy_to_role(self, team_name, policy_arn):
        """
        Attach a policy to a role
        
        Args:
            team_name (str): The team name
            policy_arn (str): The policy ARN to attach
            
        Returns:
            bool: True if successful, False otherwise
        """
        role_name = f"{team_name}_BedrockRole"
        
        if not check_if_role_exists(role_name, self.iam_client):
            logger.warning(f"Role {role_name} does not exist")
            return False
        
        try:
            # Attach policy to role
            self.iam_client.attach_role_policy(
                RoleName=role_name,
                PolicyArn=policy_arn
            )
            logger.info(f"Attached policy {policy_arn} to role {role_name}")
            
            return True
        except Exception as e:
            logger.error(f"Error attaching policy to role {role_name}: {str(e)}")
            return False
    
    def setup_team(self, team_name):
        """
        Set up a complete team with group, role, and policies
        
        Args:
            team_name (str): The team name to set up
            
        Returns:
            bool: True if successful, False otherwise
        """
        # Create group
        group_success = self.create_group(team_name)
        if not group_success:
            logger.warning(f"Failed to create group for {team_name}")
            return False
        
        # Create role
        role_success = self.create_role_for_group(team_name)
        if not role_success:
            logger.warning(f"Failed to create role for {team_name}")
            return False
        
        # Create Bedrock policy
        bedrock_policy_success, bedrock_policy_arn = self.create_bedrock_policy(team_name)
        if not bedrock_policy_success:
            logger.warning(f"Failed to create Bedrock policy for {team_name}")
            return False
        
        # Create assume role policy
        assume_policy_success, assume_policy_arn = self.create_assume_role_policy(team_name)
        if not assume_policy_success:
            logger.warning(f"Failed to create assume role policy for {team_name}")
            return False
        
        # Attach Bedrock policy to role
        attach_role_success = self.attach_policy_to_role(team_name, bedrock_policy_arn)
        if not attach_role_success:
            logger.warning(f"Failed to attach Bedrock policy to role for {team_name}")
            return False
        
        # Attach assume role policy to group
        attach_group_success = self.attach_policy_to_group(team_name, assume_policy_arn)
        if not attach_group_success:
            logger.warning(f"Failed to attach assume role policy to group for {team_name}")
            return False
        
        logger.info(f"Successfully set up team {team_name}")
        return True
    
    def get_group_info(self, team_name):
        """
        Get information about a group
        
        Args:
            team_name (str): The team name to get information for
            
        Returns:
            dict: Group information or None if group doesn't exist
        """
        group_name = f"{team_name}_group"
        
        if not check_if_group_exists(group_name, self.iam_client):
            logger.warning(f"Group {group_name} does not exist")
            return None
        
        try:
            # Get group details
            group_response = self.iam_client.get_group(GroupName=group_name)
            
            group_info = {
                'group_name': group_name,
                'arn': group_response['Group']['Arn'],
                'created': group_response['Group']['CreateDate'].strftime('%Y-%m-%d %H:%M:%S'),
                'users': [],
                'policies': []
            }
            
            # Get users in group
            for user in group_response['Users']:
                group_info['users'].append(user['UserName'])
            
            # Get attached policies
            policies_response = self.iam_client.list_attached_group_policies(GroupName=group_name)
            for policy in policies_response['AttachedPolicies']:
                group_info['policies'].append({
                    'name': policy['PolicyName'],
                    'arn': policy['PolicyArn']
                })
            
            return group_info
        except Exception as e:
            logger.error(f"Error getting group info for {group_name}: {str(e)}")
            return None

# Main function for testing
if __name__ == "__main__":
    group_manager = GroupManager()
    
    # Example usage
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "create" and len(sys.argv) >= 3:
            team_name = sys.argv[2]
            success = group_manager.create_group(team_name)
            print(f"Group creation {'successful' if success else 'failed'}")
        
        elif command == "delete" and len(sys.argv) >= 3:
            team_name = sys.argv[2]
            success = group_manager.delete_group(team_name)
            print(f"Group deletion {'successful' if success else 'failed'}")
        
        elif command == "setup" and len(sys.argv) >= 3:
            team_name = sys.argv[2]
            success = group_manager.setup_team(team_name)
            print(f"Team setup {'successful' if success else 'failed'}")
        
        elif command == "info" and len(sys.argv) >= 3:
            team_name = sys.argv[2]
            group_info = group_manager.get_group_info(team_name)
            if group_info:
                print(json.dumps(group_info, indent=2))
        
        else:
            print("Invalid command or arguments")
            print("Usage:")
            print("  python group_manager.py create <team_name>")
            print("  python group_manager.py delete <team_name>")
            print("  python group_manager.py setup <team_name>")
            print("  python group_manager.py info <team_name>")
    else:
        print("No command provided")
        print("Available commands: create, delete, setup, info")
