# =============================================================================
# Oracle Chatbot - A Flask web application that creates a chatbot interface 
# using OpenAI's GPT-4 model, styled as a mythological oracle
# =============================================================================

# --- Import Section ---
# Web framework and related extensions
from flask import Flask, render_template, request, jsonify, session  # Core Flask functionality
from flask_limiter import Limiter  # For rate limiting requests
from flask_limiter.util import get_remote_address
from flask_talisman import Talisman  # For security headers

# Chatbot related imports
from LG_basic_chatbot import setup_conversation_graph  # Custom conversation handler
from langchain_openai import ChatOpenAI  # OpenAI integration
from langchain.schema import HumanMessage, AIMessage, SystemMessage  # Message types for chat

# Utility imports
from dotenv import load_dotenv  # For loading environment variables
import os
import secrets  # For generating secure tokens
import logging
from logging.handlers import RotatingFileHandler
import datetime

# --- Environment Setup ---
# Load different environment variables based on development or production mode
if os.environ.get('FLASK_ENV') == 'development':
    load_dotenv('.env.development')
    logger_name = 'oracle_app_dev'
else:
    load_dotenv('.env.production')
    logger_name = 'oracle_app_prod'

# --- Logging Configuration ---
# Set up rotating log files to manage application logs
log_directory = "logs"
if not os.path.exists(log_directory):
    os.makedirs(log_directory, exist_ok=True)

log_file = os.path.join(log_directory, f"app_{datetime.datetime.now().strftime('%Y%m%d')}.log")
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Create a file handler
file_handler = RotatingFileHandler(
    log_file, 
    maxBytes=1024 * 1024,  # 1MB
    backupCount=10  # Keep 10 backup files
)
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
))

# Create a console handler
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter(
    '%(asctime)s - %(levelname)s - %(message)s'
))

# Get the logger
logger = logging.getLogger(logger_name)
logger.addHandler(file_handler)
logger.addHandler(console_handler)

# Check if API key is available
if not os.getenv("OPENAI_API_KEY"):
    logger.error("OPENAI_API_KEY not found in environment variables")
    raise ValueError("OPENAI_API_KEY not found in environment variables. Please check your .env file.")

# --- Flask Application Setup ---
app = Flask(__name__)

# --- Security Configuration ---
# Configure different security settings based on environment
is_development = os.environ.get('FLASK_ENV') == 'development'
if is_development:
    logger.info("Running in development mode - minimal security features")
    # Development configuration - relaxed security for local testing
    app.config.update(
        SESSION_COOKIE_SECURE=False,  # Allow HTTP in development
        SESSION_COOKIE_HTTPONLY=True,  # Prevent JavaScript access to cookies
        SESSION_COOKIE_SAMESITE='Lax',  # Cookie security policy
        PERMANENT_SESSION_LIFETIME=1800  # Session timeout (30 minutes)
    )
    # Talisman security headers for development
    Talisman(app,
             force_https=False,  # Don't require HTTPS in development
             force_https_permanent=False,
             strict_transport_security=False,
             session_cookie_secure=False,
             content_security_policy={
                 'default-src': "'self'",  # Default content security policy
                 'img-src': ['\'self\'', 'data:', 'https:'],  # Allowed image sources
                 'script-src': ['\'self\'', '\'unsafe-inline\''],  # Allowed script sources
                 'style-src': ['\'self\'', '\'unsafe-inline\''],  # Allowed style sources
             }
             )
else:
    logger.info("Running in production mode - full security features")
    # Production configuration - strict security settings
    # Define Content Security Policy (CSP) for production
    csp = {
        'default-src': "'self'",
        'img-src': ['\'self\'', 'https://images.pexels.com', 'data:'],
        'script-src': ['\'self\'', '\'unsafe-inline\''],
        'style-src': ['\'self\'', '\'unsafe-inline\'', 'https://fonts.googleapis.com'],
        'font-src': ['\'self\'', 'https://fonts.gstatic.com'],
        'connect-src': ['\'self\'']
    }
    # Enable comprehensive security headers for production
    Talisman(app,
             content_security_policy=csp,
             force_https=True,  # Require HTTPS
             force_https_permanent=True,
             strict_transport_security=True,
             strict_transport_security_max_age=31536000,
             strict_transport_security_include_subdomains=True,
             strict_transport_security_preload=True,
             session_cookie_secure=True,
             session_cookie_http_only=True,
             frame_options='DENY',  # Prevent clickjacking
             frame_options_allow_from=None,
             feature_policy={'geolocation': '\'none\''},
             referrer_policy='strict-origin-when-cross-origin'
             )

# --- Rate Limiting Configuration ---
# Protect against abuse by limiting request rates
if not (is_development and os.environ.get('DISABLE_RATE_LIMITS') == '1'):
    limiter = Limiter(
        app=app,
        key_func=get_remote_address,  # Identify users by IP address
        default_limits=["200 per day", "50 per hour"],  # Default rate limits
        storage_uri="memory://"  # Store rate limit data in memory
    )
else:
    logger.info("Rate limiting disabled for development")
    limiter = Limiter(
        app=app,
        key_func=get_remote_address,
        default_limits=[],  # No limits in development if disabled
        storage_uri="memory://"
    )

# --- Session Configuration ---
app.secret_key = os.getenv('FLASK_SECRET_KEY', secrets.token_hex(32))

# --- Chatbot Setup ---
# Initialize the Language Model and conversation handler
llm = ChatOpenAI(model="gpt-4")
graph = setup_conversation_graph(llm)

# --- Helper Functions ---
def convert_messages_for_session(messages):
    """
    Convert message objects to dictionaries for session storage.
    This is needed because session storage can only handle basic Python types.
    """
    converted = []
    for msg in messages:
        if isinstance(msg, (HumanMessage, AIMessage, SystemMessage)):
            converted.append({
                'type': msg.__class__.__name__,
                'content': msg.content
            })
    return converted

def convert_messages_from_session(messages):
    """
    Convert message dictionaries back to message objects.
    This restores the proper message objects when reading from the session.
    """
    converted = []
    type_map = {
        'HumanMessage': HumanMessage,
        'AIMessage': AIMessage,
        'SystemMessage': SystemMessage
    }
    for msg in messages:
        msg_type = type_map.get(msg['type'])
        if msg_type:
            converted.append(msg_type(content=msg['content']))
    return converted

# --- Route Handlers ---
@app.route('/health')
def health_check():
    """
    Health check endpoint to verify the application is running.
    Returns basic information about the application's state.
    """
    logger.debug("Health check endpoint accessed")
    debug_mode = os.environ.get('FLASK_DEBUG', '0')
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.datetime.now().isoformat(),
        "port": int(os.environ.get('PORT', 10000)),
        "debug_mode": debug_mode == '1',
        "environment": os.environ.get('FLASK_ENV', 'production')
    })

@app.route('/')
@limiter.limit("100/day;30/hour")  # Rate limit for homepage access
def home():
    """
    Homepage route that serves the chatbot interface.
    Initializes a new chat session if one doesn't exist.
    """
    logger.info("Homepage accessed")
    if 'messages' not in session:
        initial_messages = [
            SystemMessage(content="You are a mythological oracle, speaking with ancient wisdom and mystical knowledge.")
        ]
        session['messages'] = convert_messages_for_session(initial_messages)
        logger.debug("Initialized new session with default messages")
    return render_template('chatbot.html')

@app.route('/chat', methods=['POST'])
@limiter.limit("50/day;10/hour")  # Stricter rate limits for API endpoint
def chat():
    """
    Main chat endpoint that handles:
    1. Receiving user messages
    2. Processing them through the chatbot
    3. Returning the chatbot's response
    4. Managing chat session state
    """
    try:
        # Input validation
        if not request.is_json:
            logger.warning(f"Invalid content type received: {request.content_type}")
            return jsonify({"error": "Content-Type must be application/json"}), 415

        data = request.json
        user_message = data.get('message', '').strip()
        
        if not user_message:
            logger.warning("Empty message received")
            return jsonify({"error": "No message received"}), 400
        
        if len(user_message) > 500:  # Limit message length for security
            logger.warning(f"Message too long: {len(user_message)} characters")
            return jsonify({"error": "Message too long"}), 400
            
        # Handle new chat request
        if user_message == '__new_chat__':
            logger.info("New chat session requested")
            session.clear()
            session['messages'] = convert_messages_for_session([
                SystemMessage(content="You are a mythological oracle, speaking with ancient wisdom and mystical knowledge.")
            ])
            return jsonify({"response": "Chat reset successfully"})
            
        # Process chat message and get response
        messages = convert_messages_from_session(session.get('messages', []))
        if not messages:
            logger.debug("No messages in session, initializing with default")
            messages = [SystemMessage(content="You are a mythological oracle, speaking with ancient wisdom and mystical knowledge.")]
        
        logger.info(f"Processing chat message of length {len(user_message)}")
        
        # Prepare current state and get response
        current_state = {
            "messages": messages + [HumanMessage(content=user_message)],
            "should_continue": True
        }
        
        result = graph.invoke(current_state)
        
        # Update session state
        session['messages'] = convert_messages_for_session(result["messages"])
        session.modified = True
        
        # Extract and return the response
        ai_messages = [msg for msg in result["messages"] if isinstance(msg, AIMessage)]
        if ai_messages:
            response_content = ai_messages[-1].content
            logger.debug(f"Generated response of length {len(response_content)}")
        else:
            response_content = "The oracle remains silent..."
            logger.warning("No AI response generated")
        
        return jsonify({"response": response_content})
        
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}", exc_info=True)
        return jsonify({
            "error": "The oracle's vision is clouded. Please seek wisdom again in a moment."
        }), 500

# --- Error Handlers ---
@app.errorhandler(429)
def ratelimit_handler(e):
    """Handle rate limit exceeded errors"""
    logger.warning(f"Rate limit exceeded: {str(e)}")
    return jsonify({"error": "The Oracle requires rest. Please wait before seeking more wisdom."}), 429

@app.errorhandler(404)
def not_found_handler(e):
    """Handle 404 not found errors"""
    logger.warning(f"404 error: {request.url}")
    return jsonify({"error": "The path you seek does not exist."}), 404

# --- Application Entry Point ---
if __name__ == '__main__':
    # Start the Flask application
    port = int(os.environ.get('PORT', 10000))
    logger.info(f"Starting application on port {port}")
    app.run(host='0.0.0.0', port=port) 