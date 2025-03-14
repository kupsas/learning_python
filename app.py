from flask import Flask, render_template, request, jsonify, session
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_talisman import Talisman
from LG_basic_chatbot import setup_conversation_graph
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, AIMessage, SystemMessage
from dotenv import load_dotenv
import os
import secrets
import logging
from logging.handlers import RotatingFileHandler
import datetime

# Set up logging
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
logger = logging.getLogger('oracle_app')
logger.addHandler(file_handler)
logger.addHandler(console_handler)

# Load environment variables from .env file
load_dotenv()

# Check if API key is available
if not os.getenv("OPENAI_API_KEY"):
    logger.error("OPENAI_API_KEY not found in environment variables")
    raise ValueError("OPENAI_API_KEY not found in environment variables. Please check your .env file.")

app = Flask(__name__)

# Security configurations
if not os.environ.get('FLASK_DEBUG'):
    logger.info("Running in production mode - enabling security features")
    # Enable security headers in production
    csp = {
        'default-src': "'self'",
        'img-src': ['\'self\'', 'https://images.pexels.com', 'data:'],
        'script-src': ['\'self\'', '\'unsafe-inline\''],
        'style-src': ['\'self\'', '\'unsafe-inline\'', 'https://fonts.googleapis.com'],
        'font-src': ['\'self\'', 'https://fonts.gstatic.com'],
        'connect-src': ['\'self\'']
    }
    # Enable all security headers for production
    Talisman(app,
             content_security_policy=csp,
             force_https=True,
             force_https_permanent=True,
             strict_transport_security=True,
             strict_transport_security_max_age=31536000,
             strict_transport_security_include_subdomains=True,
             strict_transport_security_preload=True,
             session_cookie_secure=True,
             session_cookie_http_only=True,
             frame_options='DENY',
             frame_options_allow_from=None,
             feature_policy={'geolocation': '\'none\''},
             referrer_policy='strict-origin-when-cross-origin'
             )
else:
    logger.warning("Running in debug mode - some security features are disabled")

# Rate limiting configuration
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

# Use a secure secret key in production
app.secret_key = os.getenv('FLASK_SECRET_KEY', secrets.token_hex(32))

# Session configuration
app.config.update(
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    PERMANENT_SESSION_LIFETIME=1800  # 30 minutes
)

# Initialize the LLM and conversation graph
llm = ChatOpenAI(model="gpt-4")
graph = setup_conversation_graph(llm)

@app.route('/health')
def health_check():
    """Health check endpoint to verify the application is running."""
    logger.debug("Health check endpoint accessed")
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.datetime.now().isoformat(),
        "port": int(os.environ.get('PORT', 10000)),
        "debug_mode": bool(os.environ.get('FLASK_DEBUG')),
        "environment": os.environ.get('FLASK_ENV', 'production')
    })

def convert_messages_for_session(messages):
    """Convert message objects to dictionaries for session storage."""
    converted = []
    for msg in messages:
        if isinstance(msg, (HumanMessage, AIMessage, SystemMessage)):
            converted.append({
                'type': msg.__class__.__name__,
                'content': msg.content
            })
    return converted

def convert_messages_from_session(messages):
    """Convert message dictionaries back to message objects."""
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

@app.route('/')
@limiter.limit("100/day;30/hour")  # Limit homepage access
def home():
    logger.info("Homepage accessed")
    # Initialize session state if it doesn't exist
    if 'messages' not in session:
        initial_messages = [
            SystemMessage(content="You are a mythological oracle, speaking with ancient wisdom and mystical knowledge.")
        ]
        session['messages'] = convert_messages_for_session(initial_messages)
        logger.debug("Initialized new session with default messages")
    return render_template('chatbot.html')

@app.route('/chat', methods=['POST'])
@limiter.limit("50/day;10/hour")  # Stricter limits for API endpoint
def chat():
    try:
        # Validate Content-Type
        if not request.is_json:
            logger.warning(f"Invalid content type received: {request.content_type}")
            return jsonify({"error": "Content-Type must be application/json"}), 415

        data = request.json
        user_message = data.get('message', '').strip()
        
        # Input validation
        if not user_message:
            logger.warning("Empty message received")
            return jsonify({"error": "No message received"}), 400
        
        if len(user_message) > 500:  # Limit message length
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
            
        # Get or initialize conversation state
        messages = convert_messages_from_session(session.get('messages', []))
        if not messages:
            logger.debug("No messages in session, initializing with default")
            messages = [SystemMessage(content="You are a mythological oracle, speaking with ancient wisdom and mystical knowledge.")]
        
        logger.info(f"Processing chat message of length {len(user_message)}")
        
        # Create current state
        current_state = {
            "messages": messages + [HumanMessage(content=user_message)],
            "should_continue": True
        }
        
        # Get response from the chatbot
        result = graph.invoke(current_state)
        
        # Update session with new messages
        session['messages'] = convert_messages_for_session(result["messages"])
        session.modified = True  # Ensure session is saved
        
        # Get the last AI message
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

# Error handlers
@app.errorhandler(429)
def ratelimit_handler(e):
    logger.warning(f"Rate limit exceeded: {str(e)}")
    return jsonify({"error": "The Oracle requires rest. Please wait before seeking more wisdom."}), 429

@app.errorhandler(404)
def not_found_handler(e):
    logger.warning(f"404 error: {request.url}")
    return jsonify({"error": "The path you seek does not exist."}), 404

if __name__ == '__main__':
    # Use production configuration when deployed
    port = int(os.environ.get('PORT', 10000))
    logger.info(f"Starting application on port {port}")
    app.run(host='0.0.0.0', port=port) 