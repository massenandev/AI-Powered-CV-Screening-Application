from pathlib import Path
from uuid import uuid4

import pytest

from app.application.services import ChatService, IngestionService
from app.domain.models import ExtractedPage, SearchResult


class FakeEmbedder:
    async def embed_documents(self, texts):
        return [[0.1] * 768 for _ in texts]

    async def embed_query(self, text):
        return [0.1] * 768


class FakeDocuments:
    current = False
    replaced = 0

    async def checksum_is_current(self, *args):
        return self.current

    async def replace_document(self, *args):
        self.replaced += 1
        return uuid4()

    async def search(self, vector, limit):
        return [SearchResult(uuid4(), uuid4(), "Ada Example", 1, "Python and FastAPI", 0.95)]


class FakeExtractor:
    def extract(self, path):
        return [ExtractedPage(1, "SKILLS\nPython and FastAPI")]


class FakeConversations:
    saved = False

    async def exists(self, conversation_id):
        return True

    async def add_exchange(self, *args):
        self.saved = True


class FakeGenerator:
    async def answer(self, question, context):
        return "Ada has Python experience [SOURCE 1]."


@pytest.mark.asyncio
async def test_ingestion_skips_current_document(tmp_path: Path) -> None:
    pdf = tmp_path / "cv.pdf"
    pdf.write_bytes(b"pdf")
    docs = FakeDocuments()
    docs.current = True
    assert await IngestionService(docs, FakeExtractor(), FakeEmbedder(), "model").ingest([pdf]) == (
        0,
        1,
    )
    assert docs.replaced == 0


@pytest.mark.asyncio
async def test_chat_returns_citations_and_persists() -> None:
    conversations = FakeConversations()
    answer, citations = await ChatService(
        FakeDocuments(), conversations, FakeEmbedder(), FakeGenerator()
    ).ask(uuid4(), "Who knows Python?")
    assert "Ada" in answer and citations[0].candidate_name == "Ada Example" and conversations.saved
