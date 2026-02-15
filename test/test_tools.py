"""Unit tests for RAG engine tools (no API server or LLM needed)."""
import json
import pytest
from rag_engine.agents.tools import lookup_employee, lookup_role_requirements, _load_json


# --- Employee Lookup Tests ---

class TestLookupEmployee:
    def test_by_exact_id(self):
        result = json.loads(lookup_employee.invoke("ENG-042"))
        assert len(result) == 1
        assert result[0]["name"] == "Jordan Lee"

    def test_by_name(self):
        result = json.loads(lookup_employee.invoke("Sarah Chen"))
        assert len(result) == 1
        assert result[0]["employee_id"] == "ENG-DIR-01"

    def test_by_title_keywords(self):
        result = json.loads(lookup_employee.invoke("Systems Administrator"))
        assert any(e["name"] == "Alex Johnson" for e in result)

    def test_by_partial_name(self):
        result = json.loads(lookup_employee.invoke("Elena"))
        assert any(e["name"] == "Elena Rostova" for e in result)

    def test_not_found(self):
        result = lookup_employee.invoke("Nonexistent Person XYZ")
        assert "No employee found" in result

    def test_case_insensitive(self):
        result = json.loads(lookup_employee.invoke("eng-042"))
        assert result[0]["name"] == "Jordan Lee"


# --- Role Requirements Tests ---

class TestLookupRoleRequirements:
    def test_by_title(self):
        result = json.loads(lookup_role_requirements.invoke("Senior Backend Engineer"))
        assert result["role_id"] == "ENG-SR-BE"
        assert "GitHub_Enterprise" in result["required_tools"]

    def test_by_role_id(self):
        result = json.loads(lookup_role_requirements.invoke("SALES-AE-MID"))
        assert result["title"] == "Mid-Market Account Executive"

    def test_not_found(self):
        result = lookup_role_requirements.invoke("Chief Happiness Officer")
        assert "No role definition found" in result

    def test_includes_first_week_goals(self):
        result = json.loads(lookup_role_requirements.invoke("Systems Administrator"))
        assert "first_week_goals" in result
        assert len(result["first_week_goals"]) > 0


# --- JSON Loader Tests ---

class TestLoadJson:
    def test_valid_file(self):
        data = _load_json("org_chart.json")
        assert len(data) > 0
        assert "employee_id" in data[0]

    def test_missing_file(self):
        data = _load_json("nonexistent.json")
        assert data == []


# --- Schema Validation Tests ---

class TestSchemas:
    def test_chat_request_valid(self):
        from backend.app.models.schemas import ChatRequest
        req = ChatRequest(query="What is the password policy?")
        assert req.query == "What is the password policy?"
        assert req.thread_id == "default_thread"

    def test_chat_request_custom_thread(self):
        from backend.app.models.schemas import ChatRequest
        req = ChatRequest(query="Hello", thread_id="my-thread-123")
        assert req.thread_id == "my-thread-123"

    def test_chat_request_empty_query_rejected(self):
        from backend.app.models.schemas import ChatRequest
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            ChatRequest(query="")

    def test_chat_request_too_long_rejected(self):
        from backend.app.models.schemas import ChatRequest
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            ChatRequest(query="x" * 1001)
