#!/usr/bin/env python3
"""
AWS Utility functions for Bedrock Usage Control
"""

import json
import boto3
import logging
import os
import sys
from botocore.exceptions import ClientError

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load configuration
def load_config():
    """Load the configuration from config.json"""
    try:
        config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config.json')
        with open(config_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading configuration: {str(e)}")
        sys.exit(1)

# Initialize AWS clients
def get_aws_client(service_name, config=None):
    """Get an AWS client for the specified service"""
    if config is None:
        config = load_config()
    
    try:
        return boto3.client(service_name, region_name=config['region'])
    except Exception as e:
        logger.error(f"Error creating AWS client for {service_name}: {str(e)}")
        return None

# IAM functions
def check_if_user_exists(username, iam_client=None):
    """Check if an IAM user exists"""
    if iam_client is None:
        iam_client = get_aws_client('iam')
    
    try:
        iam_client.get_user(UserName=username)
        return True
    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchEntity':
            return False
        logger.error(f"Error checking if user exists: {str(e)}")
        raise

def check_if_group_exists(group_name, iam_client=None):
    """Check if an IAM group exists"""
    if iam_client is None:
        iam_client = get_aws_client('iam')
    
    try:
        iam_client.get_group(GroupName=group_name)
        return True
    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchEntity':
            return False
        logger.error(f"Error checking if group exists: {str(e)}")
        raise

def check_if_role_exists(role_name, iam_client=None):
    """Check if an IAM role exists"""
    if iam_client is None:
        iam_client = get_aws_client('iam')
    
    try:
        iam_client.get_role(RoleName=role_name)
        return True
    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchEntity':
            return False
        logger.error(f"Error checking if role exists: {str(e)}")
        raise

def check_if_policy_exists(policy_name, iam_client=None, config=None):
    """Check if an IAM policy exists"""
    if iam_client is None:
        iam_client = get_aws_client('iam')
    
    if config is None:
        config = load_config()
    
    try:
        policies = iam_client.list_policies(Scope='Local')
        for policy in policies['Policies']:
            if policy['PolicyName'] == policy_name:
                return True, policy['Arn']
        return False, None
    except Exception as e:
        logger.error(f"Error checking if policy exists: {str(e)}")
        raise

# CloudWatch functions
def ensure_log_group_exists(log_group_name, logs_client=None):
    """Ensure a CloudWatch log group exists"""
    if logs_client is None:
        logs_client = get_aws_client('logs')
    
    try:
        logs_client.describe_log_groups(logGroupNamePrefix=log_group_name)
        return True
    except Exception:
        try:
            logs_client.create_log_group(logGroupName=log_group_name)
            logger.info(f"Created log group: {log_group_name}")
            return True
        except Exception as e:
            logger.error(f"Error creating log group: {str(e)}")
            return False

def create_metric_filter(log_group_name, filter_name, filter_pattern, metric_name, 
                         metric_namespace, metric_value, dimensions=None, logs_client=None):
    """Create a CloudWatch metric filter"""
    if logs_client is None:
        logs_client = get_aws_client('logs')
    
    try:
        # Check if filter exists and delete it if it does
        try:
            logs_client.delete_metric_filter(
                logGroupName=log_group_name,
                filterName=filter_name
            )
            logger.info(f"Deleted existing metric filter: {filter_name}")
        except Exception:
            pass
        
        # Create metric transformation
        metric_transformation = {
            'metricName': metric_name,
            'metricNamespace': metric_namespace,
            'metricValue': metric_value
        }
        
        # Add dimensions if provided
        if dimensions:
            metric_transformation['dimensions'] = dimensions
        
        # Create the metric filter
        logs_client.put_metric_filter(
            logGroupName=log_group_name,
            filterName=filter_name,
            filterPattern=filter_pattern,
            metricTransformations=[metric_transformation]
        )
        
        logger.info(f"Created metric filter: {filter_name}")
        return True
    except Exception as e:
        logger.error(f"Error creating metric filter: {str(e)}")
        return False

# SNS functions
def ensure_sns_topic_exists(topic_name, sns_client=None):
    """Ensure an SNS topic exists"""
    if sns_client is None:
        sns_client = get_aws_client('sns')
    
    try:
        # Check if topic exists
        topics = sns_client.list_topics()
        for topic in topics['Topics']:
            if topic_name in topic['TopicArn']:
                return topic['TopicArn']
        
        # Create topic if it doesn't exist
        response = sns_client.create_topic(Name=topic_name)
        logger.info(f"Created SNS topic: {topic_name}")
        return response['TopicArn']
    except Exception as e:
        logger.error(f"Error ensuring SNS topic exists: {str(e)}")
        return None

def subscribe_to_sns_topic(topic_arn, protocol, endpoint, sns_client=None):
    """Subscribe to an SNS topic"""
    if sns_client is None:
        sns_client = get_aws_client('sns')
    
    try:
        # Check if subscription already exists
        subscriptions = sns_client.list_subscriptions_by_topic(TopicArn=topic_arn)
        for subscription in subscriptions['Subscriptions']:
            if subscription['Protocol'] == protocol and subscription['Endpoint'] == endpoint:
                return subscription['SubscriptionArn']
        
        # Create subscription if it doesn't exist
        response = sns_client.subscribe(
            TopicArn=topic_arn,
            Protocol=protocol,
            Endpoint=endpoint
        )
        logger.info(f"Subscribed {endpoint} to SNS topic")
        return response['SubscriptionArn']
    except Exception as e:
        logger.error(f"Error subscribing to SNS topic: {str(e)}")
        return None

# CloudWatch Alarms functions
def create_cloudwatch_alarm(alarm_name, metric_name, namespace, dimensions, 
                           threshold, comparison_operator, period, evaluation_periods,
                           statistic, alarm_actions=None, cloudwatch_client=None):
    """Create a CloudWatch alarm"""
    if cloudwatch_client is None:
        cloudwatch_client = get_aws_client('cloudwatch')
    
    try:
        # Delete alarm if it already exists
        try:
            cloudwatch_client.delete_alarms(AlarmNames=[alarm_name])
            logger.info(f"Deleted existing alarm: {alarm_name}")
        except Exception:
            pass
        
        # Create alarm
        alarm_params = {
            'AlarmName': alarm_name,
            'AlarmDescription': f'Alarm for {metric_name}',
            'MetricName': metric_name,
            'Namespace': namespace,
            'Dimensions': dimensions,
            'Threshold': threshold,
            'ComparisonOperator': comparison_operator,
            'Period': period,
            'EvaluationPeriods': evaluation_periods,
            'Statistic': statistic
        }
        
        if alarm_actions:
            alarm_params['AlarmActions'] = alarm_actions
        
        cloudwatch_client.put_metric_alarm(**alarm_params)
        logger.info(f"Created CloudWatch alarm: {alarm_name}")
        return True
    except Exception as e:
        logger.error(f"Error creating CloudWatch alarm: {str(e)}")
        return False

# Budget functions
def create_budget(budget_name, budget_limit, budget_type, time_unit, 
                 start_time, end_time, cost_filters=None, 
                 notifications=None, budgets_client=None, config=None):
    """Create an AWS Budget"""
    if budgets_client is None:
        budgets_client = get_aws_client('budgets')
    
    if config is None:
        config = load_config()
    
    try:
        # Delete budget if it already exists
        try:
            budgets_client.delete_budget(
                AccountId=config['account_id'],
                BudgetName=budget_name
            )
            logger.info(f"Deleted existing budget: {budget_name}")
        except Exception:
            pass
        
        # Create budget
        budget_params = {
            'AccountId': config['account_id'],
            'Budget': {
                'BudgetName': budget_name,
                'BudgetLimit': {
                    'Amount': str(budget_limit),
                    'Unit': 'COUNT'
                },
                'BudgetType': budget_type,
                'TimeUnit': time_unit,
                'TimePeriod': {
                    'Start': start_time,
                    'End': end_time
                }
            }
        }
        
        if cost_filters:
            budget_params['Budget']['CostFilters'] = cost_filters
        
        budgets_client.create_budget(**budget_params)
        logger.info(f"Created budget: {budget_name}")
        
        # Add notifications if provided
        if notifications:
            for notification in notifications:
                budgets_client.create_notification(
                    AccountId=config['account_id'],
                    BudgetName=budget_name,
                    Notification=notification['Notification'],
                    Subscribers=notification['Subscribers']
                )
            logger.info(f"Added notifications to budget: {budget_name}")
        
        return True
    except Exception as e:
        logger.error(f"Error creating budget: {str(e)}")
        return False

# Main function for testing
if __name__ == "__main__":
    config = load_config()
    print(f"Loaded configuration for region: {config['region']}")
    
    # Test AWS client creation
    iam_client = get_aws_client('iam')
    if iam_client:
        print("Successfully created IAM client")
