import requests
import json
from urllib.parse import urljoin
import time

BASE_URL = "http://127.0.0.1:10000"

def test_security_headers():
    """Test security headers in the response"""
    print("\nTesting Security Headers...")
    response = requests.get(BASE_URL)
    headers = response.headers
    
    # Expected security headers
    expected_headers = [
        'Content-Security-Policy',
        'X-Frame-Options',
        'X-Content-Type-Options',
        'X-XSS-Protection'
    ]
    
    print("\nFound Security Headers:")
    for header in expected_headers:
        if header in headers:
            print(f"✓ {header}: {headers[header]}")
        else:
            print(f"✗ {header} not found")
            
    # Check CSP details if present
    if 'Content-Security-Policy' in headers:
        print("\nContent Security Policy Details:")
        csp = headers['Content-Security-Policy'].split(';')
        for policy in csp:
            print(f"  {policy.strip()}")

def test_session_security():
    """Test session cookie security settings"""
    print("\nTesting Session Security...")
    response = requests.get(BASE_URL)
    
    # Get all cookies from response headers
    all_cookies = response.headers.get('Set-Cookie', '').split(',')
    session_cookies = [c.strip() for c in all_cookies if 'session' in c.lower()]
    
    if session_cookies:
        print("\nSession Cookie Properties:")
        cookie_str = session_cookies[0]
        print(f"✓ HttpOnly: {'httponly' in cookie_str.lower()}")
        print(f"✓ Secure: {'secure' in cookie_str.lower()}")
        print(f"✓ SameSite: {'samesite' in cookie_str.lower()}")
        
        # Print all cookie attributes for inspection
        print("\nAll cookie attributes:")
        attributes = [attr.strip() for attr in cookie_str.split(';')]
        for attr in attributes:
            print(f"  {attr}")
    else:
        print("✗ No session cookie found")

def test_input_validation():
    """Test input validation on the chat endpoint"""
    print("\nTesting Input Validation...")
    headers = {"Content-Type": "application/json"}
    
    # Test cases
    test_cases = [
        {
            "name": "Empty message",
            "data": {"message": ""},
            "expected_status": 400
        },
        {
            "name": "Long message (>500 chars)",
            "data": {"message": "x" * 501},
            "expected_status": 400
        },
        {
            "name": "Missing message field",
            "data": {"wrong_field": "test"},
            "expected_status": 400
        },
        {
            "name": "Invalid Content-Type",
            "data": "raw data",
            "headers": {"Content-Type": "text/plain"},
            "expected_status": 415
        }
    ]
    
    for test in test_cases:
        print(f"\nTesting: {test['name']}")
        test_headers = test.get('headers', headers)
        try:
            if isinstance(test['data'], dict):
                response = requests.post(
                    urljoin(BASE_URL, '/chat'),
                    json=test['data'],
                    headers=test_headers
                )
            else:
                response = requests.post(
                    urljoin(BASE_URL, '/chat'),
                    data=test['data'],
                    headers=test_headers
                )
            
            if response.status_code == test['expected_status']:
                print(f"✓ Got expected status {test['expected_status']}")
                print(f"✓ Error message: {response.json().get('error', 'No error message')}")
            else:
                print(f"✗ Expected status {test['expected_status']}, got {response.status_code}")
        except Exception as e:
            print(f"✗ Test failed: {str(e)}")
        
        time.sleep(0.1)  # Avoid rate limiting

def test_error_handling():
    """Test error handlers"""
    print("\nTesting Error Handling...")
    
    # Test 404 handler
    print("\nTesting 404 Handler:")
    response = requests.get(urljoin(BASE_URL, '/nonexistent'))
    if response.status_code == 404:
        print(f"✓ Got 404 response")
        print(f"✓ Error message: {response.json().get('error', 'No error message')}")
    else:
        print(f"✗ Expected 404, got {response.status_code}")

def main():
    print("Starting security tests...")
    print("Make sure the Flask application is running first!")
    print("Note: Some security features like HTTPS redirect only work in production mode")
    
    input("Press Enter to start testing...")
    
    try:
        # Run all security tests
        test_security_headers()
        test_session_security()
        test_input_validation()
        test_error_handling()
        
        print("\nTests completed!")
        print("\nNote: To test HTTPS redirect and full security headers:")
        print("1. Set FLASK_DEBUG=0 in your environment")
        print("2. Deploy the application to a production server")
        print("3. Access the application via HTTP to verify redirect to HTTPS")
        
    except requests.exceptions.ConnectionError:
        print("\nError: Could not connect to the server.")
        print("Make sure the Flask application is running on http://127.0.0.1:10000")

if __name__ == "__main__":
    main() 