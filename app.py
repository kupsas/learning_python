from flask import Flask, render_template, request, jsonify, session
from LG_basic_chatbot import setup_conversation_graph
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, AIMessage, SystemMessage
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Check if API key is available
if not os.getenv("OPENAI_API_KEY"):
    raise ValueError("OPENAI_API_KEY not found in environment variables. Please check your .env file.")

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Set a secret key for session management

# Initialize the LLM and conversation graph
llm = ChatOpenAI(model="gpt-4")
graph = setup_conversation_graph(llm)

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
def home():
    # Initialize session state if it doesn't exist
    if 'messages' not in session:
        initial_messages = [
            SystemMessage(content="You are a mythological oracle, speaking with ancient wisdom and mystical knowledge.")
        ]
        session['messages'] = convert_messages_for_session(initial_messages)
    return render_template('chatbot.html')

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        user_message = data.get('message', '').strip()
        
        if not user_message:
            return jsonify({"response": "No message received"}), 400
            
        # Get or initialize conversation state
        messages = convert_messages_from_session(session.get('messages', []))
        if not messages:
            messages = [SystemMessage(content="You are a mythological oracle, speaking with ancient wisdom and mystical knowledge.")]
        
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
        else:
            response_content = "The oracle remains silent..."
        
        return jsonify({"response": response_content})
        
    except Exception as e:
        print(f"Error in chat endpoint: {str(e)}")
        return jsonify({
            "response": "The oracle's vision is clouded. Please seek wisdom again in a moment."
        }), 500

if __name__ == '__main__':
    app.run(debug=True) 