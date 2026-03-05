from file_extractor import extract_text_from_bytes
import pytest

def test_extract_markdown():
    content = b"# Feature\n\nThis is a test PRD."
    text = extract_text_from_bytes(content, "sample.md")
    assert "Feature" in text
    assert "test PRD" in text

def test_extract_plaintext():
    content = b"Plain text PRD content here."
    text = extract_text_from_bytes(content, "notes.txt")
    assert "Plain text PRD" in text

def test_unsupported_format_raises():
    with pytest.raises(ValueError, match="Unsupported"):
        extract_text_from_bytes(b"data", "file.xlsx")
