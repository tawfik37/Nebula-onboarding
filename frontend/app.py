import os
import json
import streamlit as st
import requests
import uuid

# --- CONFIGURATION ---
API_BASE = os.getenv("API_URL", "http://127.0.0.1:8000")
STREAM_URL = API_BASE + "/api/v1/chat/stream"
st.set_page_config(page_title="Nebula AI Onboarding", page_icon="🚀", layout="wide")

# --- TOOL DISPLAY NAMES ---
TOOL_ICONS = {
    "search_policies": "🔍 Searching policies",
    "lookup_employee": "👤 Looking up employee",
    "lookup_role_requirements": "📋 Checking role requirements",
}

# --- SESSION STATE ---
if "messages" not in st.session_state:
    st.session_state.messages = []

if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())

# Sidebar
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

# Display existing chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if message.get("reasoning"):
            with st.expander("🧠 Agent Reasoning", expanded=False):
                for step in message["reasoning"]:
                    st.markdown(step)
        st.markdown(message["content"])

# Handle User Input
if prompt := st.chat_input("How can I help you today?"):
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("assistant"):
        reasoning_container = st.expander("🧠 Agent Reasoning", expanded=True)
        answer_placeholder = st.empty()
        answer_placeholder.markdown("⏳ Thinking...")

        reasoning_steps = []
        final_answer = ""

        try:
            payload = {"query": prompt, "thread_id": st.session_state.thread_id}
            response = requests.post(STREAM_URL, json=payload, stream=True, timeout=60)

            if response.status_code == 200:
                for line in response.iter_lines(decode_unicode=True):
                    if not line or not line.startswith("data: "):
                        continue
                    data = json.loads(line[6:])
                    event_type = data.get("type")

                    if event_type == "tool_call":
                        label = TOOL_ICONS.get(data["name"], f"🔧 {data['name']}")
                        step = f"**{label}** — `{json.dumps(data['args'])}`"
                        reasoning_steps.append(step)
                        with reasoning_container:
                            st.markdown(step)

                    elif event_type == "tool_result":
                        step = f"↳ *Result from {data['name']}:* `{data['content'][:100]}...`"
                        reasoning_steps.append(step)
                        with reasoning_container:
                            st.markdown(step)

                    elif event_type == "token":
                        final_answer = data["content"]
                        answer_placeholder.markdown(final_answer)

                    elif event_type == "error":
                        answer_placeholder.error(data["content"])

                if not final_answer:
                    answer_placeholder.markdown("No response received.")

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": final_answer or "No response received.",
                    "reasoning": reasoning_steps,
                })
            else:
                answer_placeholder.error(f"API Error: {response.status_code}")

        except requests.exceptions.ConnectionError:
            answer_placeholder.error("Connection Error: Is the backend running?")
        except Exception as e:
            answer_placeholder.error(f"Error: {e}")
