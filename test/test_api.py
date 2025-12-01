import pytest
import requests
from typing import List

# configure API endpoint
API_URL = "http://127.0.0.1:8000/api/v1/chat"

def query_agent(question: str) -> str:
    """Helper to send request to the running API."""
    payload = {"query": question}
    try:
        response = requests.post(API_URL, json=payload, timeout=20)
        assert response.status_code == 200, f"API returned {response.status_code}"
        return response.json().get("answer", "")
    except requests.exceptions.ConnectionError:
        pytest.fail("Could not connect to backend. Is './run_app.sh' running?")

# --- TEST GROUP 1: UNSTRUCTURED DATA (POLICIES) ---
@pytest.mark.parametrize("question, expected_keywords", [
    ("What is the minimum password length?", ["16", "characters"]),
    ("Can I use my stipend for a standing desk?", ["Yes", "desk"]),
])
def test_policy_rag(question: str, expected_keywords: List[str]):
    answer = query_agent(question)
    for keyword in expected_keywords:
        assert keyword.lower() in answer.lower(), \
            f"Expected '{keyword}' in answer for '{question}'. Got: {answer}"

# --- TEST GROUP 2: COMPLEX REASONING (AGENT LOGIC) ---
@pytest.mark.parametrize("question, expected_keywords", [
    ("Who is the manager of Sarah Chen?", ["Elena", "Rostova"]),
    ("Can a Senior Backend Engineer install TikTok?", ["No", "prohibited"]),
    ("Can I buy a monitor for $800 and a desk for $900?", ["exceeds", "1,500"]),
])
def test_agent_reasoning(question: str, expected_keywords: List[str]):
    answer = query_agent(question)
    for keyword in expected_keywords:
        assert keyword.lower() in answer.lower(), \
            f"Reasoning failure for '{question}'. Got: {answer}"