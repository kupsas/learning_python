#!/usr/bin/env python3
"""
A conversational chatbot implemented using LangGraph and LangChain.
This chatbot maintains a conversation until the user types 'quit'.
"""

from typing import Annotated, List
from typing_extensions import TypedDict
from rich import print as rprint
from dotenv import load_dotenv
import os

from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, AIMessage, SystemMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages

# Load environment variables
load_dotenv()

# Check if API key is available
if not os.getenv("OPENAI_API_KEY"):
    raise ValueError("OPENAI_API_KEY not found in environment variables. Please check your .env file.")

class State(TypedDict):
    """State schema for the conversation graph."""
    messages: Annotated[List[HumanMessage | AIMessage | SystemMessage], add_messages]
    should_continue: bool


def create_chatbot(llm):
    """Create a chatbot function with a specific LLM."""
    def chatbot(state: State) -> State:
        """Generate and display AI response based on conversation state."""
        try:
            # Convert messages to the format LLM expects
            messages = state["messages"]
            if not messages:
                messages = [SystemMessage(content="You are a helpful AI assistant.")]
            
            # Get response from LLM
            response = llm.invoke(messages)
            
            # Add AI response to messages
            state["messages"].append(response)
            return state
            
        except Exception as e:
            print(f"Error in chatbot: {str(e)}")
            return {
                "messages": state["messages"] + [AIMessage(content="I apologize, I encountered an error. Please try again.")],
                "should_continue": state["should_continue"]
            }
    
    return chatbot


def should_continue(state: State) -> str:
    """Determine if conversation should continue or end."""
    return "continue" if state["should_continue"] else END


def setup_conversation_graph(llm=None) -> StateGraph:
    """Create and configure the conversation workflow graph.
    
    Args:
        llm: The language model to use for the chatbot. If None, defaults to ChatOpenAI with 'o1' model.
        
    Returns:
        StateGraph: A compiled conversation workflow graph ready for execution.
    """
    if llm is None:
        llm = ChatOpenAI(model="gpt-4")
        
    # Initialize the graph
    workflow = StateGraph(State)
    
    # Add chatbot node
    workflow.add_node("chatbot", create_chatbot(llm))
    
    # Set entry point
    workflow.set_entry_point("chatbot")
    
    return workflow.compile()


def main():
    """Main execution function for the chatbot."""
    # Initialize the LLM
    llm = ChatOpenAI(model="gpt-4")
    
    # Initialize conversation state
    state = {
        "messages": [SystemMessage(content="You are a helpful AI assistant. You are given a conversation history and a new message. You need to respond to the new message based on the conversation history. Be cheerful and friendly.")],
        "should_continue": True
    }
    
    # Create and run the conversation graph
    graph = setup_conversation_graph(llm)
    
    while state["should_continue"]:
        user_input = input("\nYou: ")
        if user_input.lower() == "quit":
            break
            
        # Add user message and get response
        state["messages"].append(HumanMessage(content=user_input))
        state = graph.invoke(state)
        
        # Print AI response
        if state["messages"]:
            last_message = state["messages"][-1]
            if isinstance(last_message, AIMessage):
                rprint("\nAI:", last_message.content)
    
    print("\nGoodbye!")


if __name__ == '__main__':
    main() 