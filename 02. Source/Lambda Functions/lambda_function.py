"""
Lambda function entry point for bedrock-realtime-usage-controller
This file imports and exposes the lambda_handler from the main module.
"""

from bedrock_realtime_usage_controller import lambda_handler

# Export the handler
__all__ = ['lambda_handler']
