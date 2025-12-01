from dotenv import load_dotenv

# LangGraph & LangChain Imports
from langgraph.prebuilt import create_react_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import MemorySaver

# Import our custom tools
from rag_engine.agents.tools import search_policies, lookup_employee, lookup_role_requirements

load_dotenv()

# --- 1. Initialize the LLM (The Brain) ---
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0,  # Keep it factual, no creativity for policies
    max_tokens=None,
    timeout=None,
    max_retries=2,
)

# --- 2. Register the Tools (The Hands) ---
tools = [search_policies, lookup_employee, lookup_role_requirements]

# --- 3. Create the Agent Graph ---
# "ReAct" stands for "Reasoning and Acting". This agent can loop: 
# Think -> Call Tool -> Check Result -> Think Again -> Answer.
# Define the System Prompt
SYSTEM_PROMPT = """You are the Nebula Dynamics Onboarding Assistant. 
Your goal is to help employees navigate company policies and roles.

RULES:
1. ALWAYS use the tools. Do not guess.
2. If a user asks for a role (e.g., "Engineering Director"), use 'lookup_employee' to find the person holding that title.
3. If a policy search for a specific term fails, try a shorter keyword (e.g., "stipend" instead of "remote stipend policy").
4. When asked about managers, look up the employee first, find their 'manager_id', then look up that ID.
5. Be concise and professional.
"""
# 2. Initialize Memory Checkpointer
memory = MemorySaver()
# Create the Agent with the prompt
agent_executor = create_react_agent(llm, tools, prompt=SYSTEM_PROMPT, checkpointer=memory)

def ask_agent(user_query: str):
    """
    Main entry point to talk to the agent.
    """
    print(f"\nUser: {user_query}")
    print("Agent is thinking...")
    
    # We send the message to the graph
    # stream_mode="values" returns the full state at each step
    response = agent_executor.invoke({"messages": [HumanMessage(content=user_query)]})
    
    # Extract the final AI message
    final_message = response["messages"][-1].content
    print(f"Answer: {final_message}\n")
    return final_message