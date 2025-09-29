#!/usr/bin/env python3
"""
Test script for the Enhanced Email Service
==========================================

This script tests all 5 email scenarios to ensure they work correctly:
1. Warning email (80% quota reached)
2. Blocking email (100% quota exceeded)
3. Unblocking email (daily reset)
4. Admin blocking email (manual admin block)
5. Admin unblocking email (manual admin unblock)

Usage: python test_email_service.py
"""

import json
from bedrock_email_service import create_email_service

def test_email_service():
    """Test all email scenarios"""
    print("🧪 Testing Enhanced Email Service")
    print("=" * 50)
    
    try:
        # Initialize email service
        email_service = create_email_service()
        print(f"✅ Email service initialized successfully")
        print(f"   SMTP Server: {email_service.smtp_server}")
        print(f"   SMTP Port: {email_service.smtp_port}")
        print(f"   Gmail User: {email_service.gmail_user}")
        print()
        
        # Test data
        test_user_id = "sap_003"  # Use existing user from quota config
        test_admin_user = "admin_user"
        
        # Test usage record for warning/blocking scenarios
        test_usage_record = {
            'request_count': 200,  # 80% of 250
            'daily_limit': 250,
            'warning_threshold': 150,
            'team': 'team_sap_group',
            'date': '2025-09-17'
        }
        
        # Test usage record for blocking scenario
        test_blocking_usage_record = {
            'request_count': 250,  # 100% of 250
            'daily_limit': 250,
            'warning_threshold': 150,
            'team': 'team_sap_group',
            'date': '2025-09-17'
        }
        
        print("📧 Testing Email Scenarios:")
        print("-" * 30)
        
        # Test 1: Warning Email (Amber)
        print("1. Testing Warning Email (Amber)...")
        try:
            result = email_service.send_warning_email(test_user_id, test_usage_record)
            print(f"   ✅ Warning email test: {'SUCCESS' if result else 'FAILED'}")
        except Exception as e:
            print(f"   ❌ Warning email test failed: {str(e)}")
        
        # Test 2: Blocking Email (Light Red)
        print("2. Testing Blocking Email (Light Red)...")
        try:
            result = email_service.send_blocking_email(test_user_id, test_blocking_usage_record, 'daily_limit_exceeded')
            print(f"   ✅ Blocking email test: {'SUCCESS' if result else 'FAILED'}")
        except Exception as e:
            print(f"   ❌ Blocking email test failed: {str(e)}")
        
        # Test 3: Unblocking Email (Green)
        print("3. Testing Unblocking Email (Green)...")
        try:
            result = email_service.send_unblocking_email(test_user_id, 'daily_reset')
            print(f"   ✅ Unblocking email test: {'SUCCESS' if result else 'FAILED'}")
        except Exception as e:
            print(f"   ❌ Unblocking email test failed: {str(e)}")
        
        # Test 4: Admin Blocking Email (Light Red)
        print("4. Testing Admin Blocking Email (Light Red)...")
        try:
            result = email_service.send_admin_blocking_email(test_user_id, test_admin_user, 'manual_admin_block')
            print(f"   ✅ Admin blocking email test: {'SUCCESS' if result else 'FAILED'}")
        except Exception as e:
            print(f"   ❌ Admin blocking email test failed: {str(e)}")
        
        # Test 5: Admin Unblocking Email (Green)
        print("5. Testing Admin Unblocking Email (Green)...")
        try:
            result = email_service.send_admin_unblocking_email(test_user_id, test_admin_user, 'manual_admin_unblock')
            print(f"   ✅ Admin unblocking email test: {'SUCCESS' if result else 'FAILED'}")
        except Exception as e:
            print(f"   ❌ Admin unblocking email test failed: {str(e)}")
        
        print()
        print("🎯 Email Service Test Summary:")
        print("=" * 50)
        print("✅ All 5 email scenarios have been tested")
        print("📧 Check the recipient's email inbox for the test emails")
        print("🎨 Verify the color coding:")
        print("   - Warning: Amber/Orange background")
        print("   - Blocking: Light red background")
        print("   - Unblocking: Green background")
        print("   - Admin Blocking: Light red background")
        print("   - Admin Unblocking: Green background")
        print()
        print("📝 All emails should be in Spanish as per the templates")
        print("🕐 All emails should show Madrid timezone (CET)")
        
    except Exception as e:
        print(f"❌ Email service initialization failed: {str(e)}")
        print("🔧 Please check:")
        print("   - Email credentials file exists and is valid")
        print("   - Gmail SMTP settings are correct")
        print("   - Network connectivity is available")

if __name__ == "__main__":
    test_email_service()
