"""Unit tests for the ingestion pipeline (no API keys needed for most tests)."""
from rag_engine.ingestion.ingest import calculate_file_hash, load_state, save_state, process_document


class TestFileHash:
    def test_consistent_hash(self, tmp_path):
        f = tmp_path / "test.md"
        f.write_text("# Hello World\nSome content here.")
        hash1 = calculate_file_hash(str(f))
        hash2 = calculate_file_hash(str(f))
        assert hash1 == hash2

    def test_different_content_different_hash(self, tmp_path):
        f1 = tmp_path / "a.md"
        f2 = tmp_path / "b.md"
        f1.write_text("Content A")
        f2.write_text("Content B")
        assert calculate_file_hash(str(f1)) != calculate_file_hash(str(f2))


class TestState:
    def test_save_and_load(self, tmp_path, monkeypatch):
        state_file = str(tmp_path / "state.json")
        monkeypatch.setattr("rag_engine.ingestion.ingest.STATE_FILE", state_file)

        save_state({"file.md": "abc123"})
        loaded = load_state()
        assert loaded == {"file.md": "abc123"}

    def test_load_missing_state(self, tmp_path, monkeypatch):
        monkeypatch.setattr("rag_engine.ingestion.ingest.STATE_FILE", str(tmp_path / "missing.json"))
        assert load_state() == {}


class TestProcessDocument:
    def test_splits_markdown(self, tmp_path):
        doc = tmp_path / "policy.md"
        doc.write_text(
            "# Section 1\nFirst section content.\n\n"
            "## Section 1.1\nSubsection content.\n\n"
            "# Section 2\nSecond section content."
        )
        chunks = process_document(str(doc))
        assert len(chunks) >= 2
        assert any("First section" in c.page_content for c in chunks)

    def test_empty_file(self, tmp_path):
        doc = tmp_path / "empty.md"
        doc.write_text("")
        chunks = process_document(str(doc))
        assert chunks == []

    def test_invalid_path(self):
        chunks = process_document("/nonexistent/file.md")
        assert chunks == []
