#!/usr/bin/env python3
"""
Comprehensive Testing Script for User Blocking/Unblocking
Tests all possible duration values for user 'delta_001'
"""

import boto3
import json
import time
from datetime import datetime, timedelta
import pytz

class BlockingDurationTester:
    def __init__(self):
        self.lambda_client = boto3.client('lambda', region_name='eu-west-1')
        self.function_name = 'bedrock-realtime-usage-controller'
        self.test_user = 'delta_001'
        self.madrid_tz = pytz.timezone('Europe/Madrid')
        
    def invoke_lambda(self, payload):
        """Invoke the Lambda function with the given payload"""
        try:
            response = self.lambda_client.invoke(
                FunctionName=self.function_name,
                InvocationType='RequestResponse',
                Payload=json.dumps(payload)
            )
            
            result = json.loads(response['Payload'].read())
            print(f"Lambda Response: {json.dumps(result, indent=2)}")
            return result
            
        except Exception as e:
            print(f"Error invoking Lambda: {str(e)}")
            return None
    
    def block_user(self, duration_type, custom_date=None):
        """Block user with specified duration"""
        print(f"\n{'='*60}")
        print(f"BLOCKING USER '{self.test_user}' - Duration: {duration_type}")
        print(f"{'='*60}")
        
        # Calculate expires_at based on duration type
        expires_at = None
        if duration_type == "1 day":
            expires_at = (datetime.now(self.madrid_tz) + timedelta(days=1)).isoformat()
        elif duration_type == "30 days":
            expires_at = (datetime.now(self.madrid_tz) + timedelta(days=30)).isoformat()
        elif duration_type == "90 days":
            expires_at = (datetime.now(self.madrid_tz) + timedelta(days=90)).isoformat()
        elif duration_type == "custom" and custom_date:
            # Parse custom date (format: 20/10/2025 10:00)
            try:
                custom_dt = datetime.strptime(custom_date, "%d/%m/%Y %H:%M")
                custom_dt = self.madrid_tz.localize(custom_dt)
                expires_at = custom_dt.isoformat()
            except ValueError as e:
                print(f"Error parsing custom date: {e}")
                return False
        elif duration_type == "indefinite":
            expires_at = "Indefinite"
        
        payload = {
            "action": "block",
            "user_id": self.test_user,
            "reason": f"Testing {duration_type} blocking duration",
            "performed_by": "test_script",
            "duration": duration_type,
            "expires_at": expires_at,
            "usage_record": {
                "timestamp": datetime.now(self.madrid_tz).isoformat(),
                "model_id": "anthropic.claude-3-sonnet-20240229-v1:0",
                "input_tokens": 100,
                "output_tokens": 50,
                "total_cost": 0.01
            }
        }
        
        print(f"Payload: {json.dumps(payload, indent=2)}")
        result = self.invoke_lambda(payload)
        
        if result and result.get('statusCode') == 200:
            print(f"✅ Successfully blocked user '{self.test_user}' for {duration_type}")
            if expires_at and expires_at != "Indefinite":
                print(f"   Expires at: {expires_at}")
            elif expires_at == "Indefinite":
                print(f"   Blocked indefinitely")
            return True
        else:
            print(f"❌ Failed to block user '{self.test_user}' for {duration_type}")
            return False
    
    def unblock_user(self):
        """Unblock the user"""
        print(f"\n{'-'*40}")
        print(f"UNBLOCKING USER '{self.test_user}'")
        print(f"{'-'*40}")
        
        payload = {
            "action": "unblock",
            "user_id": self.test_user,
            "reason": "Testing unblock functionality",
            "performed_by": "test_script"
        }
        
        print(f"Payload: {json.dumps(payload, indent=2)}")
        result = self.invoke_lambda(payload)
        
        if result and result.get('statusCode') == 200:
            print(f"✅ Successfully unblocked user '{self.test_user}'")
            return True
        else:
            print(f"❌ Failed to unblock user '{self.test_user}'")
            return False
    
    def wait_between_tests(self, seconds=3):
        """Wait between test operations"""
        print(f"\nWaiting {seconds} seconds before next operation...")
        time.sleep(seconds)
    
    def run_comprehensive_test(self):
        """Run all blocking duration tests"""
        print(f"\n{'#'*80}")
        print(f"COMPREHENSIVE BLOCKING DURATION TEST FOR USER: {self.test_user}")
        print(f"Test Started: {datetime.now(self.madrid_tz).strftime('%Y-%m-%d %H:%M:%S %Z')}")
        print(f"{'#'*80}")
        
        test_cases = [
            ("1 day", None),
            ("30 days", None),
            ("90 days", None),
            ("custom", "20/10/2025 10:00"),
            ("indefinite", None)
        ]
        
        results = []
        
        for i, (duration_type, custom_date) in enumerate(test_cases, 1):
            print(f"\n\n🔄 TEST CASE {i}/{len(test_cases)}")
            
            # Block user
            block_success = self.block_user(duration_type, custom_date)
            self.wait_between_tests()
            
            # Unblock user
            unblock_success = self.unblock_user()
            self.wait_between_tests(5)  # Longer wait between test cases
            
            results.append({
                'test_case': i,
                'duration_type': duration_type,
                'custom_date': custom_date,
                'block_success': block_success,
                'unblock_success': unblock_success,
                'overall_success': block_success and unblock_success
            })
        
        # Print summary
        self.print_test_summary(results)
    
    def print_test_summary(self, results):
        """Print comprehensive test summary"""
        print(f"\n\n{'#'*80}")
        print(f"TEST SUMMARY")
        print(f"{'#'*80}")
        
        total_tests = len(results)
        successful_tests = sum(1 for r in results if r['overall_success'])
        
        print(f"Total Test Cases: {total_tests}")
        print(f"Successful: {successful_tests}")
        print(f"Failed: {total_tests - successful_tests}")
        print(f"Success Rate: {(successful_tests/total_tests)*100:.1f}%")
        
        print(f"\nDetailed Results:")
        print(f"{'='*80}")
        
        for result in results:
            status = "✅ PASS" if result['overall_success'] else "❌ FAIL"
            duration_info = result['duration_type']
            if result['custom_date']:
                duration_info += f" ({result['custom_date']})"
            
            print(f"Test {result['test_case']}: {duration_info:<25} - {status}")
            if not result['overall_success']:
                if not result['block_success']:
                    print(f"         Block operation failed")
                if not result['unblock_success']:
                    print(f"         Unblock operation failed")
        
        print(f"\nTest Completed: {datetime.now(self.madrid_tz).strftime('%Y-%m-%d %H:%M:%S %Z')}")
        print(f"{'#'*80}")

def main():
    """Main execution function"""
    tester = BlockingDurationTester()
    
    try:
        tester.run_comprehensive_test()
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
