#!/usr/bin/env python3
"""
Lambda Handler for AWS Bedrock Email Service
============================================

This is the entry point for the bedrock-email-service Lambda function.
It imports and uses the EnhancedEmailNotificationService from bedrock_email_service.py

Author: AWS Bedrock Usage Control System
Version: 1.0.0
"""

import json
import logging
from bedrock_email_service import create_email_service

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    """
    Lambda handler for email service requests
    
    Args:
        event: Lambda event containing email action and parameters
        context: Lambda context object
        
    Returns:
        Dict with status code and response
    """
    try:
        logger.info(f"Processing email service request: {json.dumps(event, default=str)}")
        
        # Validate required parameters
        if 'action' not in event:
            logger.error("Missing required parameter: action")
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Missing required parameter: action'})
            }
        
        action = event['action']
        user_id = event.get('user_id')
        
        if not user_id:
            logger.error("Missing required parameter: user_id")
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Missing required parameter: user_id'})
            }
        
        # Create email service instance
        email_service = create_email_service()
        
        # Route to appropriate email function
        if action == 'send_warning_email':
            usage_record = event.get('usage_record', {})
            success = email_service.send_warning_email(user_id, usage_record)
            
        elif action == 'send_blocking_email':
            usage_record = event.get('usage_record', {})
            reason = event.get('reason', 'daily_limit_exceeded')
            success = email_service.send_blocking_email(user_id, usage_record, reason)
            
        elif action == 'send_unblocking_email':
            reason = event.get('reason', 'daily_reset')
            success = email_service.send_unblocking_email(user_id, reason)
            
        elif action == 'send_admin_blocking_email':
            admin_user = event.get('performed_by', 'admin')
            reason = event.get('reason', 'manual_admin_block')
            usage_record = event.get('usage_record')
            success = email_service.send_admin_blocking_email(user_id, admin_user, reason, usage_record)
            
        elif action == 'send_admin_unblocking_email':
            admin_user = event.get('performed_by', 'admin')
            reason = event.get('reason', 'manual_admin_unblock')
            success = email_service.send_admin_unblocking_email(user_id, admin_user, reason)
            
        else:
            logger.error(f"Invalid action: {action}")
            return {
                'statusCode': 400,
                'body': json.dumps({'error': f'Invalid action: {action}'})
            }
        
        # Return response
        if success:
            logger.info(f"Successfully processed {action} for user {user_id}")
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'message': f'Email sent successfully',
                    'action': action,
                    'user_id': user_id,
                    'success': True
                })
            }
        else:
            logger.error(f"Failed to process {action} for user {user_id}")
            return {
                'statusCode': 500,
                'body': json.dumps({
                    'error': f'Failed to send email',
                    'action': action,
                    'user_id': user_id,
                    'success': False
                })
            }
        
    except Exception as e:
        logger.error(f"Error processing email service request: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e),
                'action': event.get('action', 'unknown'),
                'user_id': event.get('user_id', 'unknown')
            })
        }
