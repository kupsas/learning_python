import os
import sys
import requests
from urllib.parse import urljoin
from dotenv import load_dotenv
from importlib.metadata import version, PackageNotFoundError

# Load production environment variables
load_dotenv('learning_python/.env.production')

def check_production_readiness():
    """Check if the application is ready for production deployment"""
    checks = {
        "Environment": [],
        "Security": [],
        "Configuration": [],
        "Performance": []
    }
    
    # Environment Checks
    print("\n1. Environment Checks:")
    if os.getenv("FLASK_DEBUG") == "1":
        print("✗ Debug mode is ON - should be OFF in production")
    else:
        print("✓ Debug mode is OFF")
    
    if os.getenv("FLASK_SECRET_KEY"):
        print("✓ Secret key is configured")
    else:
        print("✗ Secret key not found")
    
    # Security Checks
    print("\n2. Security Checks:")
    try:
        response = requests.get("http://127.0.0.1:10000")
        
        if response.headers.get('X-Frame-Options'):
            print("✓ X-Frame-Options header is set")
        else:
            print("✗ X-Frame-Options header missing")
            
        if response.headers.get('Content-Security-Policy'):
            print("✓ Content Security Policy is configured")
        else:
            print("✗ Content Security Policy missing")
            
        if 'secure' in response.headers.get('Set-Cookie', '').lower():
            print("✓ Secure cookies are enabled")
        else:
            print("✗ Secure cookies not enabled")
    except:
        print("✗ Could not connect to application")
    
    # Configuration Checks
    print("\n3. Configuration Checks:")
    required_env_vars = [
        "OPENAI_API_KEY",
        "FLASK_SECRET_KEY",
        "PORT"
    ]
    
    for var in required_env_vars:
        if os.getenv(var):
            print(f"✓ {var} is set")
        else:
            print(f"✗ {var} is missing")
    
    # Dependencies Check
    print("\n4. Dependencies Check:")
    required_packages = [
        "gunicorn",
        "flask-limiter",
        "flask-talisman"
    ]
    
    try:
        for package in required_packages:
            try:
                pkg_version = version(package)
                print(f"✓ {package} is installed (version: {pkg_version})")
            except PackageNotFoundError:
                print(f"✗ {package} is missing")
    except Exception as e:
        print(f"✗ Could not check installed packages: {str(e)}")
    
    print("\nRecommendations:")
    print("1. Make sure debug mode is OFF in production")
    print("2. Use HTTPS in production")
    print("3. Set up proper logging")
    print("4. Use a production-grade web server (gunicorn)")
    print("5. Set up monitoring and error tracking")
    print("6. Regular security updates")
    print("7. Database backups (if applicable)")

if __name__ == "__main__":
    print("Production Readiness Check")
    print("=========================")
    check_production_readiness() 