#!/usr/bin/env python3
"""
Policy Management Module for AWS Bedrock Usage Control
"""

import sys
import os
import logging
import json

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.aws_utils import (
    load_config, get_aws_client, check_if_policy_exists, check_if_user_exists, check_if_role_exists
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PolicyManager:
    """Policy Management class for AWS Bedrock Usage Control"""
    
    def __init__(self):
        """Initialize the PolicyManager"""
        self.config = load_config()
        self.iam_client = get_aws_client('iam')
    
    def create_policy(self, policy_name, policy_document):
        """
        Create an IAM policy
        
        Args:
            policy_name (str): The name of the policy to create
            policy_document (dict): The policy document
            
        Returns:
            tuple: (bool, str) - Success flag and policy ARN
        """
        # Check if policy already exists
        exists, policy_arn = check_if_policy_exists(policy_name, self.iam_client)
        if exists:
            logger.warning(f"Policy {policy_name} already exists")
            return False, policy_arn
        
        try:
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
    
    def delete_policy(self, policy_name):
        """
        Delete an IAM policy
        
        Args:
            policy_name (str): The name of the policy to delete
            
        Returns:
            bool: True if successful, False otherwise
        """
        # Check if policy exists
        exists, policy_arn = check_if_policy_exists(policy_name, self.iam_client)
        if not exists:
            logger.warning(f"Policy {policy_name} does not exist")
            return False
        
        try:
            # Detach policy from all entities
            self.detach_policy_from_all_entities(policy_arn)
            
            # Delete all non-default versions of the policy
            versions_response = self.iam_client.list_policy_versions(PolicyArn=policy_arn)
            for version in versions_response['Versions']:
                if not version['IsDefaultVersion']:
                    self.iam_client.delete_policy_version(
                        PolicyArn=policy_arn,
                        VersionId=version['VersionId']
                    )
                    logger.info(f"Deleted policy version {version['VersionId']} for {policy_name}")
            
            # Delete policy
            self.iam_client.delete_policy(PolicyArn=policy_arn)
            logger.info(f"Deleted policy {policy_name}")
            
            return True
        except Exception as e:
            logger.error(f"Error deleting policy {policy_name}: {str(e)}")
            return False
    
    def detach_policy_from_all_entities(self, policy_arn):
        """
        Detach a policy from all entities
        
        Args:
            policy_arn (str): The ARN of the policy to detach
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Get all entities the policy is attached to
            entities = self.iam_client.list_entities_for_policy(PolicyArn=policy_arn)
            
            # Detach from users
            for user in entities.get('PolicyUsers', []):
                self.iam_client.detach_user_policy(
                    UserName=user['UserName'],
                    PolicyArn=policy_arn
                )
                logger.info(f"Detached policy {policy_arn} from user {user['UserName']}")
            
            # Detach from groups
            for group in entities.get('PolicyGroups', []):
                self.iam_client.detach_group_policy(
                    GroupName=group['GroupName'],
                    PolicyArn=policy_arn
                )
                logger.info(f"Detached policy {policy_arn} from group {group['GroupName']}")
            
            # Detach from roles
            for role in entities.get('PolicyRoles', []):
                self.iam_client.detach_role_policy(
                    RoleName=role['RoleName'],
                    PolicyArn=policy_arn
                )
                logger.info(f"Detached policy {policy_arn} from role {role['RoleName']}")
            
            return True
        except Exception as e:
            logger.error(f"Error detaching policy {policy_arn} from entities: {str(e)}")
            return False
    
    def attach_policy_to_user(self, policy_name, username):
        """
        Attach a policy to a user
        
        Args:
            policy_name (str): The name of the policy to attach
            username (str): The username to attach the policy to
            
        Returns:
            bool: True if successful, False otherwise
        """
        # Check if policy exists
        exists, policy_arn = check_if_policy_exists(policy_name, self.iam_client)
        if not exists:
            logger.warning(f"Policy {policy_name} does not exist")
            return False
        
        # Check if user exists
        if not check_if_user_exists(username, self.iam_client):
            logger.warning(f"User {username} does not exist")
            return False
        
        try:
            # Attach policy to user
            self.iam_client.attach_user_policy(
                UserName=username,
                PolicyArn=policy_arn
            )
            logger.info(f"Attached policy {policy_name} to user {username}")
            
            return True
        except Exception as e:
            logger.error(f"Error attaching policy {policy_name} to user {username}: {str(e)}")
            return False
    
    def attach_policy_to_role(self, policy_name, role_name):
        """
        Attach a policy to a role
        
        Args:
            policy_name (str): The name of the policy to attach
            role_name (str): The role name to attach the policy to
            
        Returns:
            bool: True if successful, False otherwise
        """
        # Check if policy exists
        exists, policy_arn = check_if_policy_exists(policy_name, self.iam_client)
        if not exists:
            logger.warning(f"Policy {policy_name} does not exist")
            return False
        
        # Check if role exists
        if not check_if_role_exists(role_name, self.iam_client):
            logger.warning(f"Role {role_name} does not exist")
            return False
        
        try:
            # Attach policy to role
            self.iam_client.attach_role_policy(
                RoleName=role_name,
                PolicyArn=policy_arn
            )
            logger.info(f"Attached policy {policy_name} to role {role_name}")
            
            return True
        except Exception as e:
            logger.error(f"Error attaching policy {policy_name} to role {role_name}: {str(e)}")
            return False
    
    def create_bedrock_user_policy(self, username, team_name):
        """
        Create a Bedrock policy for a specific user
        
        Args:
            username (str): The username to create the policy for
            team_name (str): The team name the user belongs to
            
        Returns:
            tuple: (bool, str) - Success flag and policy ARN
        """
        policy_name = f"{username}_BedrockPolicy"
        
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
                },
                {
                    "Effect": "Allow",
                    "Action": "sts:AssumeRole",
                    "Resource": f"arn:aws:iam::{self.config['account_id']}:role/{team_name}_BedrockRole"
                }
            ]
        }
        
        # Create policy
        return self.create_policy(policy_name, policy_document)
    
    def create_tool_specific_policy(self, username, tool_name):
        """
        Create a policy for a specific tool used by a user
        
        Args:
            username (str): The username to create the policy for
            tool_name (str): The name of the tool
            
        Returns:
            tuple: (bool, str) - Success flag and policy ARN
        """
        policy_name = f"{username}_{tool_name}_Policy"
        
        # Create policy document
        policy_document = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "bedrock:InvokeModel",
                        "bedrock:InvokeModelWithResponseStream"
                    ],
                    "Resource": "*",
                    "Condition": {
                        "StringEquals": {
                            "aws:PrincipalTag/Tool": tool_name
                        }
                    }
                }
            ]
        }
        
        # Create policy
        return self.create_policy(policy_name, policy_document)
    
    def get_policy_info(self, policy_name):
        """
        Get information about a policy
        
        Args:
            policy_name (str): The name of the policy to get information for
            
        Returns:
            dict: Policy information or None if policy doesn't exist
        """
        # Check if policy exists
        exists, policy_arn = check_if_policy_exists(policy_name, self.iam_client)
        if not exists:
            logger.warning(f"Policy {policy_name} does not exist")
            return None
        
        try:
            # Get policy details
            policy_response = self.iam_client.get_policy(PolicyArn=policy_arn)
            policy = policy_response['Policy']
            
            # Get policy version details
            version_response = self.iam_client.get_policy_version(
                PolicyArn=policy_arn,
                VersionId=policy['DefaultVersionId']
            )
            
            policy_info = {
                'policy_name': policy_name,
                'arn': policy_arn,
                'created': policy['CreateDate'].strftime('%Y-%m-%d %H:%M:%S'),
                'updated': policy['UpdateDate'].strftime('%Y-%m-%d %H:%M:%S'),
                'document': version_response['PolicyVersion']['Document'],
                'attached_entities': {}
            }
            
            # Get attached entities
            entities = self.iam_client.list_entities_for_policy(PolicyArn=policy_arn)
            
            policy_info['attached_entities']['users'] = [user['UserName'] for user in entities.get('PolicyUsers', [])]
            policy_info['attached_entities']['groups'] = [group['GroupName'] for group in entities.get('PolicyGroups', [])]
            policy_info['attached_entities']['roles'] = [role['RoleName'] for role in entities.get('PolicyRoles', [])]
            
            return policy_info
        except Exception as e:
            logger.error(f"Error getting policy info for {policy_name}: {str(e)}")
            return None

# Main function for testing
if __name__ == "__main__":
    policy_manager = PolicyManager()
    
    # Example usage
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "create-user-policy" and len(sys.argv) >= 4:
            username = sys.argv[2]
            team_name = sys.argv[3]
            success, policy_arn = policy_manager.create_bedrock_user_policy(username, team_name)
            print(f"Policy creation {'successful' if success else 'failed'}")
            if success:
                print(f"Policy ARN: {policy_arn}")
        
        elif command == "create-tool-policy" and len(sys.argv) >= 4:
            username = sys.argv[2]
            tool_name = sys.argv[3]
            success, policy_arn = policy_manager.create_tool_specific_policy(username, tool_name)
            print(f"Policy creation {'successful' if success else 'failed'}")
            if success:
                print(f"Policy ARN: {policy_arn}")
        
        elif command == "attach-user" and len(sys.argv) >= 4:
            policy_name = sys.argv[2]
            username = sys.argv[3]
            success = policy_manager.attach_policy_to_user(policy_name, username)
            print(f"Policy attachment {'successful' if success else 'failed'}")
        
        elif command == "attach-role" and len(sys.argv) >= 4:
            policy_name = sys.argv[2]
            role_name = sys.argv[3]
            success = policy_manager.attach_policy_to_role(policy_name, role_name)
            print(f"Policy attachment {'successful' if success else 'failed'}")
        
        elif command == "delete" and len(sys.argv) >= 3:
            policy_name = sys.argv[2]
            success = policy_manager.delete_policy(policy_name)
            print(f"Policy deletion {'successful' if success else 'failed'}")
        
        elif command == "info" and len(sys.argv) >= 3:
            policy_name = sys.argv[2]
            policy_info = policy_manager.get_policy_info(policy_name)
            if policy_info:
                print(json.dumps(policy_info, indent=2))
        
        else:
            print("Invalid command or arguments")
            print("Usage:")
            print("  python policy_manager.py create-user-policy <username> <team_name>")
            print("  python policy_manager.py create-tool-policy <username> <tool_name>")
            print("  python policy_manager.py attach-user <policy_name> <username>")
            print("  python policy_manager.py attach-role <policy_name> <role_name>")
            print("  python policy_manager.py delete <policy_name>")
            print("  python policy_manager.py info <policy_name>")
    else:
        print("No command provided")
        print("Available commands: create-user-policy, create-tool-policy, attach-user, attach-role, delete, info")
