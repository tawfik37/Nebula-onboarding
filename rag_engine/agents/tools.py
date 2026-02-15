import json
import os
from typing import List, Dict, Any

# LangChain Imports
from langchain_core.tools import tool
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma

# --- CONFIGURATION ---
DATA_PATH = "./data_seed"
DB_PATH = "./chroma_db"

# --- HELPER: Load JSON Data ---
def _load_json(filename: str) -> List[Dict[str, Any]]:
    path = os.path.join(DATA_PATH, "structured", filename)
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

# --- TOOL 1: Policy Retrieval (Unstructured) ---
@tool
def search_policies(query: str) -> str:
    """
    Useful for answering questions about company policies, benefits, security, 
    remote work, holidays, or IT procedures.
    """
    # Initialize connection
    embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
    vector_store = Chroma(persist_directory=DB_PATH, embedding_function=embeddings)
    
    # INCREASED k=5 to get more context
    results = vector_store.similarity_search(query, k=5)
    
    if not results:
        return "No relevant policy documents found. Try searching for a broader term like 'stipend' or 'benefits'."
    
    formatted_results = ""
    for doc in results:
        formatted_results += f"Source: {os.path.basename(doc.metadata.get('source', 'Unknown'))}\n"
        formatted_results += f"Content: {doc.page_content}\n---\n"
        
    return formatted_results

# --- TOOL 2: Employee Lookup (Structured) ---
@tool
def lookup_employee(name_or_id_or_role: str) -> str:
    """
    Useful for finding details about a specific employee, such as their email, 
    title, location, or manager. Can search by Name, ID, or Job Title.
    """
    employees = _load_json("org_chart.json")
    query_parts = name_or_id_or_role.lower().split() # Split "Engineering Director" -> ["engineering", "director"]
    
    matches = []
    for emp in employees:
        # 1. Exact ID match (Strongest signal)
        if name_or_id_or_role.lower() == emp["employee_id"].lower():
            matches.append(emp)
            continue

        # 2. Text Search (Check Name and Title)
        # We count how many words from the query appear in the employee record
        emp_text = f"{emp['name']} {emp['title']} {emp['role_id']}".lower()
        
        # If all words in the query are found in the employee record, it's a match.
        # e.g. "Engineering" AND "Director" are both in "Director of Engineering"
        if all(part in emp_text for part in query_parts):
            matches.append(emp)
            
    if not matches:
        return f"No employee found matching '{name_or_id_or_role}'. Try using just the first name or exact role title."
    
    return json.dumps(matches, indent=2)

# --- TOOL 3: Role Requirements (Structured) ---
@tool
def lookup_role_requirements(role_title_or_id: str) -> str:
    """
    Useful for finding the specific tools, permissions, and first-week goals 
    associated with a job role.
    
    Args:
        role_title_or_id: The job title (e.g., "Senior Backend Engineer") or Role ID.
    """
    roles = _load_json("role_definitions.json")
    query_str = role_title_or_id.lower()
    
    for role in roles:
        if query_str in role["role_id"].lower() or query_str in role["title"].lower():
            return json.dumps(role, indent=2)
            
    return f"No role definition found for '{role_title_or_id}'."