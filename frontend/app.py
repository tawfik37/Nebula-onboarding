"""
Nebula AI - Frontend Application
Premium UI with modular CSS architecture
"""
import os
import json
import streamlit as st
import requests
import uuid

# Import CSS loader
from css_loader import inject_css

# --- CONFIGURATION ---
API_BASE = os.getenv("API_URL", "http://127.0.0.1:8000")
STREAM_URL = API_BASE + "/api/v1/chat/stream"

st.set_page_config(
    page_title="Nebula AI Onboarding",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- INJECT MODULAR CSS ---
inject_css()

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

if "message_count" not in st.session_state:
    st.session_state.message_count = 0

# --- HERO HEADER ---
st.markdown("""
<div class="hero-section">
    <div class="hero-logo">🚀</div>
    <div class="hero-title">Nebula AI</div>
    <div class="hero-subtitle">Your Intelligent Onboarding Assistant</div>
    <div class="hero-badge">
        <span class="status-dot"></span>
        Powered by Gemini 2.5 Flash + LangGraph ReAct Agent
    </div>
    <div class="hero-divider"></div>
</div>
""", unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("### Control Panel")

    # Stats
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-value">{len(st.session_state.messages)}</div>
            <div class="stat-label">Messages</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-value">{st.session_state.message_count}</div>
            <div class="stat-label">Questions</div>
        </div>
        """, unsafe_allow_html=True)

    st.divider()

    st.markdown("**Session ID**")
    st.code(st.session_state.thread_id[:16] + "...", language=None)

    if st.button("🔄 New Conversation", use_container_width=True):
        st.session_state.messages = []
        st.session_state.thread_id = str(uuid.uuid4())
        st.session_state.message_count = 0
        st.rerun()

    st.divider()

    with st.expander("💡 Example Questions"):
        st.markdown("""
        - What's the home office stipend?
        - Who is the Director of Engineering?
        - What tools does a Senior Backend Engineer need?
        - Can I use my stipend for a standing desk?
        - What's the password policy?
        """)

    st.divider()

    st.markdown("""
    <div class="sidebar-footer">
        Built with LangGraph &bull; ChromaDB &bull; FastAPI<br>
        <a href="https://github.com/tawfik37/Nebula-onboarding">View on GitHub →</a>
    </div>
    """, unsafe_allow_html=True)

# --- WELCOME SCREEN (shown when no messages) ---
if not st.session_state.messages:
    st.markdown("""
    <div class="welcome-container">
        <div class="welcome-message">
            <div class="welcome-title">How can I help you today?</div>
            <div class="welcome-text">
                Ask me about company policies, team members, role requirements,
                or anything related to your onboarding journey.
            </div>
        </div>
        <div class="feature-grid">
            <div class="feature-card">
                <span class="feature-icon">📋</span>
                <span class="feature-label">Company Policies</span>
            </div>
            <div class="feature-card">
                <span class="feature-icon">👥</span>
                <span class="feature-label">Team Directory</span>
            </div>
            <div class="feature-card">
                <span class="feature-icon">🛠️</span>
                <span class="feature-label">Role Setup</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# --- HELPER: Stream response from the API ---
def stream_response(query):
    """Send a query to the API and stream the response into the chat."""
    with st.chat_message("assistant", avatar="✨"):
        reasoning_container = st.expander("🧠 Agent Reasoning Chain", expanded=True)
        answer_placeholder = st.empty()
        answer_placeholder.markdown(
            '<div class="thinking-animation">'
            'Thinking <span class="thinking-dots"><span></span><span></span><span></span></span>'
            '</div>',
            unsafe_allow_html=True
        )

        reasoning_steps = []
        final_answer = ""

        try:
            payload = {"query": query, "thread_id": st.session_state.thread_id}
            response = requests.post(STREAM_URL, json=payload, stream=True, timeout=60)

            if response.status_code == 200:
                for line in response.iter_lines(decode_unicode=True):
                    if not line or not line.startswith("data: "):
                        continue
                    data = json.loads(line[6:])
                    event_type = data.get("type")

                    if event_type == "tool_call":
                        label = TOOL_ICONS.get(data["name"], f"🔧 {data['name']}")
                        step = f"{label}"
                        reasoning_steps.append(step)
                        with reasoning_container:
                            st.markdown(f'<div class="tool-badge">{step}</div>', unsafe_allow_html=True)

                    elif event_type == "tool_result":
                        step = "✅ Retrieved data"
                        reasoning_steps.append(step)

                    elif event_type == "token":
                        final_answer = data["content"]
                        answer_placeholder.markdown(final_answer)

                    elif event_type == "error":
                        answer_placeholder.error(data["content"])

                if not final_answer:
                    answer_placeholder.markdown("_No response received._")

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": final_answer or "No response received.",
                    "reasoning": reasoning_steps,
                })
            else:
                answer_placeholder.error(f"⚠️ API Error: {response.status_code}")

        except requests.exceptions.ConnectionError:
            answer_placeholder.error("❌ **Connection Error**: Is the backend running? (`docker-compose up`)")
        except Exception as e:
            answer_placeholder.error(f"❌ **Error**: {e}")


# --- CHAT HISTORY ---
for message in st.session_state.messages:
    with st.chat_message(message["role"], avatar="🧑‍💼" if message["role"] == "user" else "✨"):
        if message.get("reasoning"):
            with st.expander("🧠 Agent Reasoning Chain", expanded=False):
                for step in message["reasoning"]:
                    st.markdown(f'<div class="tool-badge">{step}</div>', unsafe_allow_html=True)
        st.markdown(message["content"])

# --- CHAT INPUT ---
if prompt := st.chat_input("Ask about policies, people, or your role..."):
    st.session_state.message_count += 1

    with st.chat_message("user", avatar="🧑‍💼"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    stream_response(prompt)
