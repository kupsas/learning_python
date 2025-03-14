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

## Environment Variables
Create a `.env` file with:
```env
OPENAI_API_KEY=your_api_key
FLASK_SECRET_KEY=your_secret_key
PORT=10000
FLASK_DEBUG=0
```

## Running Locally
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the application:
   ```bash
   gunicorn app:app
   ```

## Security Features
- Rate limiting
- Content Security Policy
- Secure session cookies
- HTTPS enforcement
- XSS protection

## Deployment

This application is configured for deployment on Render.com. Follow the deployment steps in the main documentation. 