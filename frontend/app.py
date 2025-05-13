import os
import sys
import streamlit as st
import requests
from dotenv import load_dotenv
import time

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

load_dotenv()

FASTAPI_BACKEND_URL = os.getenv("FASTAPI_BACKEND_URL", "http://api:8080")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Initialize session state variables
if "messages" not in st.session_state:
    st.session_state.messages = []

# Prevent duplicate submissions with a unique message key
if "message_key" not in st.session_state:
    st.session_state.message_key = 0

def increment_message_key():
    st.session_state.message_key += 1
    st.session_state.temp_input = ""

# Function to process message with API
def process_message_with_api(user_input):
    if 'api_key' in st.session_state:
        try:
            response = requests.post(
                f"{FASTAPI_BACKEND_URL}/ask",
                json={"query": user_input},
                headers={"Authorization": f"Bearer {st.session_state.api_key}"}
            )
            
            if response.status_code == 200:
                result = response.json()
                answer = result.get("answer", "I couldn't find an answer to your question.")
                
                # Remove sources formatting - sources will not be displayed
                # Add assistant response to chat without sources
                st.session_state.messages.append({"role": "assistant", "content": answer})
            else:
                # Handle error response
                st.session_state.messages.append({"role": "assistant", "content": f"I encountered an error processing your request. Please try again."})
        except Exception as e:
            # Provide a friendly response when the backend is not available
            if "Connection" in str(e):
                st.session_state.messages.append({"role": "assistant", "content": "I'm having trouble connecting to the backend service. This could happen if no documents are uploaded yet or if the service is still starting up. Please try uploading some documents first or try again in a moment."})
            else:
                st.session_state.messages.append({"role": "assistant", "content": f"I encountered an error: {str(e)}"})
    else:
        st.session_state.messages.append({"role": "assistant", "content": "API key not available. Please check your environment configuration."})

def main():
    st.set_page_config(
        page_title="AI Document Assistant", 
        page_icon="🅰️", 
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Custom CSS for a more professional dark theme look
    st.markdown("""
    <style>
    .stApp {
        background-color: #0e1117;
        color: #ffffff;
    }
    .st-bq {
        background-color: #1e2130;
    }
    .chat-message {
        padding: 1.5rem; 
        border-radius: 0.75rem; 
        margin-bottom: 1rem;
        display: flex;
        flex-direction: row;
        align-items: flex-start;
        gap: 1rem;
    }
    .chat-message.user {
        background-color: #2d3748;
        color: #ffffff;
    }
    .chat-message.assistant {
        background-color: #1a202c;
        color: #ffffff;
        border: 1px solid #3182ce;
    }
    .chat-message .avatar {
        width: 2.5rem;
        height: 2.5rem;
        border-radius: 0.5rem;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.5rem;
    }
    .chat-message .avatar.user {
        background-color: #6c63ff;
        color: white;
    }
    .chat-message .avatar.assistant {
        background-color: #0078FF;
        color: white;
    }
    .chat-message .message {
        flex-grow: 1;
    }
    .stTextInput>div>div>input {
        border-radius: 0.5rem;
        padding: 0.75rem;
        font-size: 1rem;
        background-color: #1e2130;
        color: #ffffff;
        border: 1px solid #3182ce;
    }
    div.stButton > button:first-child {
        background-color: #0078FF;
        color: white;
        border-radius: 0.5rem;
        padding: 0.5rem 1rem;
        font-size: 1rem;
        border: none;
        transition: all 0.3s;
    }
    div.stButton > button:hover {
        background-color: #0069e0;
        color: white;
    }
    .upload-btn {
        display: inline-block;
        background-color: #0078FF;
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 0.5rem;
        cursor: pointer;
        text-align: center;
        margin: 1rem 0;
        transition: all 0.3s;
    }
    .upload-btn:hover {
        background-color: #0069e0;
    }
    .sidebar .block-container {
        padding-top: 2rem;
        background-color: #0e1117;
    }
    .css-6qob1r.e1fqkh3o3 {
        background-color: #1e2130;
        color: #ffffff;
    }
    .css-1d391kg.e1fqkh3o1 {
        background-color: #1e2130;
        color: #ffffff;
    }
    .css-12oz5g7.e1txvo1c0 {
        color: #ffffff;
    }
    header {
        background-color: #0e1117 !important;
    }
    [data-testid="stSidebar"] {
        background-color: #0e1117;
    }
    .stMarkdown {
        color: #ffffff;
    }
    .stPlaceholder [data-testid="stFileUploadDropzone"] {
        background-color: #1e2130;
        border-color: #3182ce;
    }
    .stPlaceholder [data-testid="stFileUploadDropzone"]:hover {
        border-color: #0078FF;
    }
    </style>
    """, unsafe_allow_html=True)

    # Sidebar configuration
    with st.sidebar:
        st.title("📑 AI Document Assistant")
        st.markdown("---")
        
        # Use API key from environment variable
        if GOOGLE_API_KEY:
            st.session_state.api_key = GOOGLE_API_KEY
            st.success("Using Gemini API Key from environment variables ✅")
        else:
            st.error("GOOGLE_API_KEY not found in environment variables. Please add it to your .env file.")
        
        st.markdown("---")
        st.header("📤 Document Upload")
        
        uploaded_files = st.file_uploader(
            "Drop your documents here", 
            type=['pdf', 'txt', 'png', 'jpg', 'jpeg'],
            help="Supported formats: PDF, TXT, PNG, JPG, JPEG",
            accept_multiple_files=True,
            label_visibility="collapsed"
        )
        
        if st.button("Upload & Process Documents", use_container_width=True):
            if uploaded_files and 'api_key' in st.session_state:
                with st.spinner("Processing documents..."):
                    for uploaded_file in uploaded_files:
                        try:
                            files = {"files": (uploaded_file.name, uploaded_file.getvalue())}
                            response = requests.post(
                                f"{FASTAPI_BACKEND_URL}/upload/batch",
                                files=files,
                                headers={"Authorization": f"Bearer {st.session_state.api_key}"}
                            )
                            if response.status_code == 200:
                                st.success(f"✅ Processed {uploaded_file.name}")
                            else:
                                st.error(f"❌ Error processing {uploaded_file.name}: {response.text}")
                        except Exception as e:
                            st.error(f"❌ Error processing {uploaded_file.name}: {e}")
            elif not uploaded_files:
                st.warning("Please upload at least one document.")
            else:
                st.warning("API key not available. Please check your environment configuration.")
        
        st.markdown("---")
        st.caption("© 2023 AI Document Assistant")
    
    # Main content area - Chat interface
    st.title("🅰️ AI Document Assistant")
    st.markdown("Ask me anything about your documents or start a conversation!")
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.container():
            if message["role"] == "user":
                st.markdown(f"""
                <div class="chat-message user">
                    <div class="avatar user">👨‍💼</div>
                    <div class="message">{message["content"]}</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="chat-message assistant">
                    <div class="avatar assistant">🧠</div>
                    <div class="message">{message["content"]}</div>
                </div>
                """, unsafe_allow_html=True)
    
    # Input area - using simple input with a unique key to prevent duplication
    st.markdown("---")
    with st.container():
        col1, col2 = st.columns([5, 1])
        
        # Use a temporary storage for the current input
        if "temp_input" not in st.session_state:
            st.session_state.temp_input = ""
            
        with col1:
            user_input = st.text_input(
                "Ask a question about your documents:", 
                value=st.session_state.temp_input,
                key=f"input_{st.session_state.message_key}",
                label_visibility="collapsed", 
                placeholder="Ask me anything about your documents..."
            )
        
        with col2:
            send_pressed = st.button("Send", key=f"send_{st.session_state.message_key}", use_container_width=True)
        
        # Handle the message sending
        if send_pressed and user_input and user_input.strip():
            # Save the user's message
            st.session_state.messages.append({"role": "user", "content": user_input})
            
            # Process with API
            process_message_with_api(user_input)
            
            # Increment the key to reset the input field
            increment_message_key()
            
            # Rerun to update the UI
            st.rerun()

if __name__ == "__main__":
    main()