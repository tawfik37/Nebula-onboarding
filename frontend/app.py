import os
import streamlit as st
import requests
import uuid

# --- CONFIGURATION ---
API_URL = os.getenv("API_URL", "http://127.0.0.1:8000") + "/api/v1/chat"
st.set_page_config(page_title="Nebula AI Onboarding", page_icon="🚀", layout="wide")

# --- SESSION STATE ---
# We need to remember the chat history and a unique thread ID for the user
if "messages" not in st.session_state:
    st.session_state.messages = []

if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())

# Sidebar for debugging and session info
with st.sidebar:
    st.header("🛠️ Debugger")
    st.write(f"**Session ID:** `{st.session_state.thread_id}`")
    if st.button("Clear Chat History"):
        st.session_state.messages = []
        st.rerun()
    st.divider()
    st.info("This panel shows internal details. The main chat is on the right.")

# --- MAIN CHAT INTERFACE ---
st.title("🚀 Nebula AI Onboarding Assistant")
st.markdown("Welcome to the team! Ask me about **policies**, **your role**, or **who people are**.")

# 1. Display existing chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 2. Handle User Input
if prompt := st.chat_input("How can I help you today?"):
    # A. Display User Message immediately
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Save to history
    st.session_state.messages.append({"role": "user", "content": prompt})

    # B. Call the Backend API
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        message_placeholder.markdown("Thinking...")
        
        try:
            payload = {"query": prompt, "thread_id": st.session_state.thread_id}
            response = requests.post(API_URL, json=payload)
            
            if response.status_code == 200:
                data = response.json()
                ai_answer = data.get("answer", "Error: No answer received.")
                
                # Update the UI with the final answer
                message_placeholder.markdown(ai_answer)
                
                # Save to history
                st.session_state.messages.append({"role": "assistant", "content": ai_answer})
            else:
                message_placeholder.error(f"API Error: {response.status_code}")
                
        except Exception as e:
            message_placeholder.error(f"Connection Error: Is the backend running? \n\n{e}")