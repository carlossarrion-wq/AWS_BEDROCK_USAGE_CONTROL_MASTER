"""
AWS Bedrock Dashboard Authentication Lambda
Handles dual authentication:
1. First attempt: IAM username/password authentication
2. Second attempt: AWS Access Key + Secret Key authentication
3. Returns temporary credentials via STS AssumeRole if successful
"""

import json
import boto3
import os
from datetime import datetime
from botocore.exceptions import ClientError

# Environment variables
DASHBOARD_ROLE_ARN = os.environ.get('DASHBOARD_ROLE_ARN')
EXTERNAL_ID = os.environ.get('EXTERNAL_ID')
REGION = os.environ.get('AWS_REGION', 'eu-west-1')

def lambda_handler(event, context):
    """
    Main handler for dashboard authentication
    
    Expected input:
    {
        "credential1": "username/email OR access_key",
        "credential2": "password OR secret_key"
    }
    
    Returns:
    {
        "success": true/false,
        "method": "iam_password" or "access_key",
        "credentials": {
            "AccessKeyId": "...",
            "SecretAccessKey": "...",
            "SessionToken": "...",
            "Expiration": "..."
        },
        "userArn": "arn:aws:iam::...",
        "message": "..."
    }
    """
    
    try:
        # Parse input
        body = json.loads(event.get('body', '{}')) if isinstance(event.get('body'), str) else event
        credential1 = body.get('credential1', '').strip()
        credential2 = body.get('credential2', '').strip()
        
        if not credential1 or not credential2:
            return create_response(400, {
                'success': False,
                'message': 'Both credentials are required'
            })
        
        # Attempt 1: Try IAM username/password authentication
        print(f"Attempting IAM username/password authentication for: {credential1}")
        iam_result = try_iam_password_auth(credential1, credential2)
        
        if iam_result['success']:
            print(f"✅ IAM authentication successful for: {credential1}")
            return create_response(200, iam_result)
        
        # Attempt 2: Try Access Key + Secret Key authentication
        print(f"IAM auth failed, attempting Access Key authentication")
        access_key_result = try_access_key_auth(credential1, credential2)
        
        if access_key_result['success']:
            print(f"✅ Access Key authentication successful")
            return create_response(200, access_key_result)
        
        # Both methods failed
        print(f"❌ Both authentication methods failed")
        return create_response(401, {
            'success': False,
            'message': 'Authentication failed. Invalid credentials.',
            'details': {
                'iam_error': iam_result.get('error'),
                'access_key_error': access_key_result.get('error')
            }
        })
        
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        return create_response(500, {
            'success': False,
            'message': f'Internal server error: {str(e)}'
        })


def try_iam_password_auth(username, password):
    """
    Attempt to authenticate using IAM username and password
    Note: AWS IAM doesn't support direct username/password authentication via API
    This would require AWS SSO or a custom identity provider
    
    For now, this returns a controlled failure to fall back to access key method
    """
    try:
        # AWS IAM doesn't provide a direct API for username/password authentication
        # This would require:
        # 1. AWS SSO integration
        # 2. Custom identity provider (IdP)
        # 3. AWS Cognito integration
        
        # For this implementation, we'll check if the username looks like an IAM user
        # and attempt to use it as an access key instead
        
        if '@' in username:
            # Looks like an email, not an IAM username or access key
            return {
                'success': False,
                'error': 'IAM password authentication not available. Use Access Key + Secret Key.'
            }
        
        # If username looks like an access key (starts with AKIA), try it as access key
        if username.startswith('AKIA'):
            return try_access_key_auth(username, password)
        
        return {
            'success': False,
            'error': 'IAM username/password authentication requires AWS SSO or IdP integration'
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': f'IAM authentication error: {str(e)}'
        }


def try_access_key_auth(access_key, secret_key):
    """
    Attempt to authenticate using AWS Access Key and Secret Key
    """
    try:
        # Create STS client with provided credentials
        sts_client = boto3.client(
            'sts',
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=REGION
        )
        
        # Step 1: Validate credentials with GetCallerIdentity
        try:
            caller_identity = sts_client.get_caller_identity()
            user_arn = caller_identity['Arn']
            account_id = caller_identity['Account']
            print(f"✅ Credentials validated for: {user_arn}")
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'InvalidClientTokenId':
                return {
                    'success': False,
                    'error': 'Invalid Access Key ID'
                }
            elif error_code == 'SignatureDoesNotMatch':
                return {
                    'success': False,
                    'error': 'Invalid Secret Access Key'
                }
            else:
                return {
                    'success': False,
                    'error': f'AWS authentication error: {e.response["Error"]["Message"]}'
                }
        
        # Step 2: Assume dashboard role
        if not DASHBOARD_ROLE_ARN:
            return {
                'success': False,
                'error': 'Dashboard role ARN not configured'
            }
        
        try:
            assume_role_params = {
                'RoleArn': DASHBOARD_ROLE_ARN,
                'RoleSessionName': f'dashboard-session-{datetime.now().strftime("%Y%m%d%H%M%S")}',
                'DurationSeconds': 3600  # 1 hour
            }
            
            if EXTERNAL_ID:
                assume_role_params['ExternalId'] = EXTERNAL_ID
            
            assumed_role = sts_client.assume_role(**assume_role_params)
            
            credentials = assumed_role['Credentials']
            
            return {
                'success': True,
                'method': 'access_key',
                'credentials': {
                    'AccessKeyId': credentials['AccessKeyId'],
                    'SecretAccessKey': credentials['SecretAccessKey'],
                    'SessionToken': credentials['SessionToken'],
                    'Expiration': credentials['Expiration'].isoformat()
                },
                'userArn': user_arn,
                'accountId': account_id,
                'message': 'Authentication successful via Access Key'
            }
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'AccessDenied':
                return {
                    'success': False,
                    'error': 'Access denied. User does not have permission to assume dashboard role.'
                }
            else:
                return {
                    'success': False,
                    'error': f'Failed to assume role: {e.response["Error"]["Message"]}'
                }
        
    except Exception as e:
        return {
            'success': False,
            'error': f'Access Key authentication error: {str(e)}'
        }


def create_response(status_code, body):
    """Create HTTP response with CORS headers"""
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
            'Access-Control-Allow-Methods': 'POST,OPTIONS'
        },
        'body': json.dumps(body, default=str)
    }
