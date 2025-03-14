# Oracle Chatbot

A Flask-based chatbot application that acts as a mythological oracle, providing wisdom and insights using OpenAI's GPT-4 model.

## Features
- Chat interface with GPT-4 integration
- Rate limiting to prevent abuse
- Security headers and HTTPS support
- Session management
- Production-ready configuration

## Requirements
- Python 3.8+
- OpenAI API key
- Required packages listed in requirements.txt

## Environment Setup

### Development
1. Copy `.env.development.example` to `.env.development`:
```bash
cp .env.development.example .env.development
```

2. Edit `.env.development` with your settings:
```env
FLASK_DEBUG=1
FLASK_ENV=development
OPENAI_API_KEY=your_api_key_here
FLASK_SECRET_KEY=dev_only_secret_key
PORT=10000
DISABLE_RATE_LIMITS=1
```

### Production
1. Copy `.env.production.example` to `.env.production`:
```bash
cp .env.production.example .env.production
```

2. Edit `.env.production` with your settings:
```env
FLASK_DEBUG=0
FLASK_ENV=production
OPENAI_API_KEY=your_api_key_here
FLASK_SECRET_KEY=your_secure_key_here  # Generate using generate_secret_key.py
PORT=10000
DISABLE_RATE_LIMITS=0
```

## Installation
1. Install dependencies:
```bash
pip install -r requirements.txt
```

## Running the Application

### Quick Start (Recommended)
Use the provided script that handles port cleanup and directory management:

For development:
```bash
./run_app.sh
```

For production:
```bash
./run_app.sh production
```

The script will:
- Stop any existing process on port 10000
- Change to the correct directory
- Start the application in the specified mode
- Provide helpful logging output

### Manual Start
If you prefer to run commands manually:

#### Development
Run with Flask development server:
```bash
FLASK_ENV=development flask run --port=10000
```

This will:
- Disable security features for local development
- Disable rate limiting
- Enable debug mode
- Allow HTTP connections

#### Production
Run with Gunicorn:
```bash
FLASK_ENV=production gunicorn --bind 0.0.0.0:10000 app:app --workers=4
```

This will enable:
- Full security features
- HTTPS enforcement
- Rate limiting
- Session security
- Content Security Policy

## Security Features
Development mode disables these features for easier local testing:
- Rate limiting
- HTTPS enforcement
- Strict security headers

Production mode enables:
- Rate limiting
- Content Security Policy
- Secure session cookies
- HTTPS enforcement
- XSS protection

## Deployment
This application is configured for deployment on Render.com:
1. Set up environment variables in Render dashboard
2. Use the production configuration
3. Enable HTTPS
4. Set up health checks

## Testing
Run security tests:
```bash
python test_security.py
```

Run production readiness check:
```bash
python test_production_readiness.py
```

## Troubleshooting
- If seeing security-related errors locally, ensure you're running in development mode
- If rate limits are too restrictive locally, set DISABLE_RATE_LIMITS=1
- For production issues, check logs in the logs/ directory
- If the application won't start, try running `run_app.sh` which will handle cleanup automatically 