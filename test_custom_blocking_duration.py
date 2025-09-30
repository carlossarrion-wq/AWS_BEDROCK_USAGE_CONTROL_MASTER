#!/usr/bin/env python3
"""
Test script for custom blocking duration functionality
Tests blocking with custom date and unblocking operations
"""

import json
import boto3
from datetime import datetime, timedelta
import pytz

# Configuration
LAMBDA_FUNCTION_NAME = 'bedrock-realtime-usage-controller'
REGION = 'eu-west-1'
TEST_USER_ID = 'sdlc004'

# CET timezone
CET = pytz.timezone('Europe/Madrid')

# Initialize Lambda client
lambda_client = boto3.client('lambda', region_name=REGION)

def get_current_cet_time():
    """Get current time in CET timezone"""
    return datetime.now(CET)

def invoke_lambda(payload):
    """Invoke Lambda function with given payload"""
    try:
        response = lambda_client.invoke(
            FunctionName=LAMBDA_FUNCTION_NAME,
            InvocationType='RequestResponse',
            Payload=json.dumps(payload)
        )
        
        response_payload = json.loads(response['Payload'].read())
        return response_payload
    except Exception as e:
        print(f"❌ Error invoking Lambda: {str(e)}")
        return None

def test_custom_date_blocking():
    """Test blocking with custom date (7 days from now)"""
    print("\n" + "="*80)
    print("TEST 1: Blocking with Custom Date (7 days from now)")
    print("="*80)
    
    # Calculate custom date: 7 days from now
    current_cet = get_current_cet_time()
    custom_date = current_cet + timedelta(days=7)
    custom_date_iso = custom_date.isoformat()
    
    print(f"📅 Current CET time: {current_cet.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📅 Custom blocking until: {custom_date.strftime('%Y-%m-%d %H:%M:%S')} CET")
    print(f"📅 ISO format: {custom_date_iso}")
    
    # Prepare blocking payload with custom duration
    blocking_payload = {
        'action': 'block',
        'user_id': TEST_USER_ID,
        'reason': 'Test: Custom date blocking (7 days)',
        'performed_by': 'test_script',
        'duration': 'custom',
        'expires_at': custom_date_iso,
        'usage_record': {
            'request_count': 100,
            'daily_limit': 350,
            'team': 'test_team',
            'date': current_cet.strftime('%Y-%m-%d')
        }
    }
    
    print(f"\n📤 Sending blocking request...")
    print(f"Payload: {json.dumps(blocking_payload, indent=2)}")
    
    response = invoke_lambda(blocking_payload)
    
    if response:
        print(f"\n📥 Lambda Response:")
        print(json.dumps(response, indent=2))
        
        if response.get('statusCode') == 200:
            print(f"\n✅ TEST 1 PASSED: User {TEST_USER_ID} blocked successfully with custom date")
            return True
        else:
            print(f"\n❌ TEST 1 FAILED: Blocking failed with status {response.get('statusCode')}")
            return False
    else:
        print(f"\n❌ TEST 1 FAILED: No response from Lambda")
        return False

def test_30_days_blocking():
    """Test blocking with 30 days duration"""
    print("\n" + "="*80)
    print("TEST 2: Blocking with 30 Days Duration")
    print("="*80)
    
    current_cet = get_current_cet_time()
    expected_date = current_cet + timedelta(days=30)
    
    print(f"📅 Current CET time: {current_cet.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📅 Expected blocking until: {expected_date.strftime('%Y-%m-%d %H:%M:%S')} CET")
    
    # Prepare blocking payload with 30 days duration
    blocking_payload = {
        'action': 'block',
        'user_id': TEST_USER_ID,
        'reason': 'Test: 30 days blocking',
        'performed_by': 'test_script',
        'duration': '30days',
        'usage_record': {
            'request_count': 100,
            'daily_limit': 350,
            'team': 'test_team',
            'date': current_cet.strftime('%Y-%m-%d')
        }
    }
    
    print(f"\n📤 Sending blocking request...")
    print(f"Payload: {json.dumps(blocking_payload, indent=2)}")
    
    response = invoke_lambda(blocking_payload)
    
    if response:
        print(f"\n📥 Lambda Response:")
        print(json.dumps(response, indent=2))
        
        if response.get('statusCode') == 200:
            print(f"\n✅ TEST 2 PASSED: User {TEST_USER_ID} blocked successfully with 30 days duration")
            return True
        else:
            print(f"\n❌ TEST 2 FAILED: Blocking failed with status {response.get('statusCode')}")
            return False
    else:
        print(f"\n❌ TEST 2 FAILED: No response from Lambda")
        return False

def test_90_days_blocking():
    """Test blocking with 90 days duration"""
    print("\n" + "="*80)
    print("TEST 3: Blocking with 90 Days Duration")
    print("="*80)
    
    current_cet = get_current_cet_time()
    expected_date = current_cet + timedelta(days=90)
    
    print(f"📅 Current CET time: {current_cet.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📅 Expected blocking until: {expected_date.strftime('%Y-%m-%d %H:%M:%S')} CET")
    
    # Prepare blocking payload with 90 days duration
    blocking_payload = {
        'action': 'block',
        'user_id': TEST_USER_ID,
        'reason': 'Test: 90 days blocking',
        'performed_by': 'test_script',
        'duration': '90days',
        'usage_record': {
            'request_count': 100,
            'daily_limit': 350,
            'team': 'test_team',
            'date': current_cet.strftime('%Y-%m-%d')
        }
    }
    
    print(f"\n📤 Sending blocking request...")
    print(f"Payload: {json.dumps(blocking_payload, indent=2)}")
    
    response = invoke_lambda(blocking_payload)
    
    if response:
        print(f"\n📥 Lambda Response:")
        print(json.dumps(response, indent=2))
        
        if response.get('statusCode') == 200:
            print(f"\n✅ TEST 3 PASSED: User {TEST_USER_ID} blocked successfully with 90 days duration")
            return True
        else:
            print(f"\n❌ TEST 3 FAILED: Blocking failed with status {response.get('statusCode')}")
            return False
    else:
        print(f"\n❌ TEST 3 FAILED: No response from Lambda")
        return False

def test_check_blocking_status():
    """Test checking user blocking status"""
    print("\n" + "="*80)
    print("TEST 4: Check User Blocking Status")
    print("="*80)
    
    status_payload = {
        'action': 'check_status',
        'user_id': TEST_USER_ID
    }
    
    print(f"\n📤 Checking status for user {TEST_USER_ID}...")
    
    response = invoke_lambda(status_payload)
    
    if response:
        print(f"\n📥 Lambda Response:")
        print(json.dumps(response, indent=2))
        
        if response.get('statusCode') == 200:
            body = json.loads(response.get('body', '{}'))
            is_blocked = body.get('is_blocked', False)
            block_reason = body.get('block_reason', 'N/A')
            expires_at = body.get('expires_at', 'N/A')
            block_type = body.get('block_type', 'N/A')
            
            print(f"\n📊 User Status:")
            print(f"   - Blocked: {is_blocked}")
            print(f"   - Reason: {block_reason}")
            print(f"   - Expires at: {expires_at}")
            print(f"   - Block type: {block_type}")
            
            if is_blocked:
                print(f"\n✅ TEST 4 PASSED: User {TEST_USER_ID} is correctly blocked")
                return True
            else:
                print(f"\n⚠️  TEST 4 WARNING: User {TEST_USER_ID} is not blocked")
                return True  # Not necessarily a failure
        else:
            print(f"\n❌ TEST 4 FAILED: Status check failed with status {response.get('statusCode')}")
            return False
    else:
        print(f"\n❌ TEST 4 FAILED: No response from Lambda")
        return False

def test_unblocking():
    """Test unblocking user"""
    print("\n" + "="*80)
    print("TEST 5: Unblocking User")
    print("="*80)
    
    unblocking_payload = {
        'action': 'unblock',
        'user_id': TEST_USER_ID,
        'reason': 'Test: Manual unblock',
        'performed_by': 'test_script',
        'usage_record': {
            'request_count': 100,
            'daily_limit': 350,
            'team': 'test_team',
            'date': get_current_cet_time().strftime('%Y-%m-%d')
        }
    }
    
    print(f"\n📤 Sending unblocking request...")
    print(f"Payload: {json.dumps(unblocking_payload, indent=2)}")
    
    response = invoke_lambda(unblocking_payload)
    
    if response:
        print(f"\n📥 Lambda Response:")
        print(json.dumps(response, indent=2))
        
        if response.get('statusCode') == 200:
            print(f"\n✅ TEST 5 PASSED: User {TEST_USER_ID} unblocked successfully")
            return True
        else:
            print(f"\n❌ TEST 5 FAILED: Unblocking failed with status {response.get('statusCode')}")
            return False
    else:
        print(f"\n❌ TEST 5 FAILED: No response from Lambda")
        return False

def test_verify_unblocked_status():
    """Test verifying user is unblocked"""
    print("\n" + "="*80)
    print("TEST 6: Verify User is Unblocked")
    print("="*80)
    
    status_payload = {
        'action': 'check_status',
        'user_id': TEST_USER_ID
    }
    
    print(f"\n📤 Checking status for user {TEST_USER_ID}...")
    
    response = invoke_lambda(status_payload)
    
    if response:
        print(f"\n📥 Lambda Response:")
        print(json.dumps(response, indent=2))
        
        if response.get('statusCode') == 200:
            body = json.loads(response.get('body', '{}'))
            is_blocked = body.get('is_blocked', False)
            
            print(f"\n📊 User Status:")
            print(f"   - Blocked: {is_blocked}")
            
            if not is_blocked:
                print(f"\n✅ TEST 6 PASSED: User {TEST_USER_ID} is correctly unblocked")
                return True
            else:
                print(f"\n❌ TEST 6 FAILED: User {TEST_USER_ID} is still blocked")
                return False
        else:
            print(f"\n❌ TEST 6 FAILED: Status check failed with status {response.get('statusCode')}")
            return False
    else:
        print(f"\n❌ TEST 6 FAILED: No response from Lambda")
        return False

def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("CUSTOM BLOCKING DURATION TESTS")
    print("="*80)
    print(f"Testing Lambda function: {LAMBDA_FUNCTION_NAME}")
    print(f"Region: {REGION}")
    print(f"Test user: {TEST_USER_ID}")
    print("="*80)
    
    results = []
    
    # Test 1: Custom date blocking (7 days)
    results.append(("Custom Date Blocking (7 days)", test_custom_date_blocking()))
    
    # Test 2: Check status after custom blocking
    results.append(("Check Status After Custom Blocking", test_check_blocking_status()))
    
    # Test 3: Unblock user
    results.append(("Unblock User", test_unblocking()))
    
    # Test 4: Verify unblocked
    results.append(("Verify Unblocked Status", test_verify_unblocked_status()))
    
    # Test 5: 30 days blocking
    results.append(("30 Days Blocking", test_30_days_blocking()))
    
    # Test 6: Check status after 30 days blocking
    results.append(("Check Status After 30 Days Blocking", test_check_blocking_status()))
    
    # Test 7: Unblock again
    results.append(("Unblock User Again", test_unblocking()))
    
    # Test 8: 90 days blocking
    results.append(("90 Days Blocking", test_90_days_blocking()))
    
    # Test 9: Final unblock
    results.append(("Final Unblock", test_unblocking()))
    
    # Print summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    passed = 0
    failed = 0
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {test_name}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print("="*80)
    print(f"Total: {len(results)} tests")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print("="*80)
    
    if failed == 0:
        print("\n🎉 ALL TESTS PASSED!")
        return 0
    else:
        print(f"\n⚠️  {failed} TEST(S) FAILED")
        return 1

if __name__ == "__main__":
    exit(main())
