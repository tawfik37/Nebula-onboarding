import os
import sqlite3
from dotenv import load_dotenv

from langgraph.prebuilt import create_react_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.sqlite import SqliteSaver

from rag_engine.agents.tools import search_policies, lookup_employee, lookup_role_requirements

load_dotenv()

# --- 1. Initialize the LLM ---
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0,
    max_tokens=None,
    timeout=None,
    max_retries=2,
)

# --- 2. Register the Tools ---
tools = [search_policies, lookup_employee, lookup_role_requirements]

# --- 3. System Prompt ---
SYSTEM_PROMPT = """You are the Nebula Dynamics Onboarding Assistant.
Your goal is to help employees navigate company policies and roles.

RULES:
1. ALWAYS use the tools. Do not guess.
2. If a user asks for a role (e.g., "Engineering Director"), use 'lookup_employee' to find the person holding that title.
3. If a policy search for a specific term fails, try a shorter keyword (e.g., "stipend" instead of "remote stipend policy").
4. When asked about managers, look up the employee first, find their 'manager_id', then look up that ID.
5. Be concise and professional.
"""

# --- 4. Persistent Memory (FIXED) ---
DB_FILE = os.getenv("MEMORY_DB_PATH", "./conversation_history.db")

# Create a persistent SQLite connection
# check_same_thread=False allows usage across multiple requests
conn = sqlite3.connect(DB_FILE, check_same_thread=False)
memory = SqliteSaver(conn)

# --- 5. Create the Agent ---
agent_executor = create_react_agent(llm, tools, prompt=SYSTEM_PROMPT, checkpointer=memory)