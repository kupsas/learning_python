import requests
import time
from concurrent.futures import ThreadPoolExecutor

BASE_URL = "http://127.0.0.1:10000"

def test_homepage():
    """Test rate limiting on homepage endpoint"""
    print("\nTesting homepage rate limit (30/hour)...")
    responses = []
    
    for i in range(35):  # Try 35 requests (more than the hourly limit)
        response = requests.get(BASE_URL + "/")
        status = response.status_code
        responses.append(status)
        print(f"Request {i+1}: Status {status}")
        if status == 429:  # Rate limit exceeded
            print(f"Rate limit hit after {i+1} requests!")
            break
        time.sleep(0.1)  # Small delay to not overwhelm the server
    
    return responses

def test_chat_endpoint():
    """Test rate limiting on chat endpoint"""
    print("\nTesting chat endpoint rate limit (10/hour)...")
    responses = []
    
    headers = {"Content-Type": "application/json"}
    data = {"message": "Hello"}
    
    for i in range(15):  # Try 15 requests (more than the hourly limit)
        response = requests.post(BASE_URL + "/chat", json=data, headers=headers)
        status = response.status_code
        responses.append(status)
        print(f"Request {i+1}: Status {status}")
        if status == 429:  # Rate limit exceeded
            print(f"Rate limit hit after {i+1} requests!")
            break
        time.sleep(0.1)  # Small delay to not overwhelm the server
    
    return responses

if __name__ == "__main__":
    print("Starting rate limit tests...")
    print("Note: This will test until rate limits are hit")
    print("Make sure the Flask application is running first!")
    
    input("Press Enter to start testing...")
    
    try:
        # Test homepage rate limit
        homepage_responses = test_homepage()
        
        # Wait a bit before testing chat endpoint
        time.sleep(1)
        
        # Test chat endpoint rate limit
        chat_responses = test_chat_endpoint()
        
        # Summary
        print("\nTest Summary:")
        print(f"Homepage: {len(homepage_responses)} requests made")
        print(f"Chat endpoint: {len(chat_responses)} requests made")
        print("\nRate limits are working if you see 429 status codes"
              " and the expected number of successful requests")
        
    except requests.exceptions.ConnectionError:
        print("\nError: Could not connect to the server.")
        print("Make sure the Flask application is running on http://127.0.0.1:10000") 