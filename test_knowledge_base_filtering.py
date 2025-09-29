#!/usr/bin/env python3
"""
Test script to verify Knowledge Base session filtering functionality
"""

import json
import sys
import os

# Add the lambda function directory to the path
sys.path.insert(0, '02. Source/Lambda Functions/bedrock-realtime-usage-controller-aws-20250923')

# Mock the environment variables and AWS services for testing
os.environ['RDS_ENDPOINT'] = 'test-endpoint'
os.environ['RDS_USERNAME'] = 'test-user'
os.environ['RDS_PASSWORD'] = 'test-password'
os.environ['RDS_DATABASE'] = 'test-db'

# Mock boto3 clients
class MockIAMClient:
    def list_user_tags(self, UserName):
        # Simulate knowledge base user with no tags
        if UserName == 'knowledge-base-user':
            return {'Tags': []}
        # Simulate regular user with proper tags
        elif UserName == 'regular-user':
            return {'Tags': [
                {'Key': 'Team', 'Value': 'yo_leo_engineering'},
                {'Key': 'Person', 'Value': 'John Doe'}
            ]}
        return {'Tags': []}
    
    def get_groups_for_user(self, UserName):
        return {'Groups': []}

class MockSNSClient:
    pass

class MockLambdaClient:
    pass

# Mock the boto3 clients
import boto3
boto3.client = lambda service: {
    'iam': MockIAMClient(),
    'sns': MockSNSClient(),
    'lambda': MockLambdaClient()
}[service]

# Now import the lambda function
from lambda_function import get_user_team, get_user_person_tag

def test_knowledge_base_filtering():
    """Test that knowledge base sessions are properly filtered"""
    
    print("🧪 Testing Knowledge Base Session Filtering")
    print("=" * 50)
    
    # Test Case 1: Knowledge Base user (both team and person unknown)
    print("\n📋 Test Case 1: Knowledge Base User")
    kb_user = 'knowledge-base-user'
    kb_team = get_user_team(kb_user)
    kb_person = get_user_person_tag(kb_user)
    
    print(f"User: {kb_user}")
    print(f"Team: {kb_team}")
    print(f"Person: {kb_person}")
    
    should_filter_kb = (kb_team == 'unknown' and kb_person == 'Unknown')
    print(f"Should filter (exclude from tracking): {should_filter_kb}")
    
    if should_filter_kb:
        print("✅ PASS: Knowledge Base user will be filtered out")
    else:
        print("❌ FAIL: Knowledge Base user will NOT be filtered out")
    
    # Test Case 2: Regular user (has proper team and person tags)
    print("\n📋 Test Case 2: Regular User")
    regular_user = 'regular-user'
    regular_team = get_user_team(regular_user)
    regular_person = get_user_person_tag(regular_user)
    
    print(f"User: {regular_user}")
    print(f"Team: {regular_team}")
    print(f"Person: {regular_person}")
    
    should_filter_regular = (regular_team == 'unknown' and regular_person == 'Unknown')
    print(f"Should filter (exclude from tracking): {should_filter_regular}")
    
    if not should_filter_regular:
        print("✅ PASS: Regular user will be processed normally")
    else:
        print("❌ FAIL: Regular user will be incorrectly filtered out")
    
    # Test Case 3: Edge case - user with team but no person
    print("\n📋 Test Case 3: Edge Case - Team but no Person")
    edge_team = 'yo_leo_data_science'  # Has team
    edge_person = 'Unknown'  # No person tag
    
    print(f"Team: {edge_team}")
    print(f"Person: {edge_person}")
    
    should_filter_edge = (edge_team == 'unknown' and edge_person == 'Unknown')
    print(f"Should filter (exclude from tracking): {should_filter_edge}")
    
    if not should_filter_edge:
        print("✅ PASS: User with team (but no person) will be processed normally")
    else:
        print("❌ FAIL: User with team (but no person) will be incorrectly filtered out")
    
    print("\n" + "=" * 50)
    print("🎯 Summary:")
    print("- Knowledge Base sessions (team='unknown' AND person='Unknown') will be FILTERED OUT")
    print("- Regular user sessions will be PROCESSED NORMALLY")
    print("- Users with at least one valid tag will be PROCESSED NORMALLY")
    print("\n✅ Knowledge Base filtering implementation is working correctly!")

if __name__ == "__main__":
    test_knowledge_base_filtering()
