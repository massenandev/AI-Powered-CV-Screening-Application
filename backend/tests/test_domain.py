from uuid import uuid4

import pytest

from app.domain.chunking import chunk_pages
from app.domain.models import ExtractedPage, SearchResult, validate_question


def test_question_is_normalized() -> None:
    assert validate_question("  Who   knows Python? ") == "Who knows Python?"


@pytest.mark.parametrize("question", ["", "   ", "x" * 2001])
def test_invalid_question_is_rejected(question: str) -> None:
    with pytest.raises(ValueError):
        validate_question(question)


def test_chunking_preserves_section_and_page() -> None:
    chunks = chunk_pages([ExtractedPage(2, "SKILLS\nPython PostgreSQL\nEXPERIENCE\nBuilt APIs")])
    assert [(chunk.section, chunk.page) for chunk in chunks] == [("SKILLS", 2), ("EXPERIENCE", 2)]


def test_search_result_has_grounding_metadata() -> None:
    result = SearchResult(uuid4(), uuid4(), "Test Candidate", 1, "Python", 0.9)
    assert result.candidate_name == "Test Candidate"
