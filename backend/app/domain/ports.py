from pathlib import Path
from typing import Protocol
from uuid import UUID

from app.domain.models import Chunk, Citation, ExtractedPage, SearchResult


class PdfExtractor(Protocol):
    def extract(self, path: Path) -> list[ExtractedPage]: ...


class Embedder(Protocol):
    async def embed_documents(self, texts: list[str]) -> list[list[float]]: ...
    async def embed_query(self, text: str) -> list[float]: ...


class AnswerGenerator(Protocol):
    async def answer(self, question: str, context: list[SearchResult]) -> str: ...


class DocumentRepository(Protocol):
    async def checksum_is_current(self, path: str, checksum: str, model: str) -> bool: ...
    async def replace_document(
        self, path: str, checksum: str, model: str, chunks: list[Chunk], vectors: list[list[float]]
    ) -> UUID: ...
    async def search(self, vector: list[float], limit: int) -> list[SearchResult]: ...


class ConversationRepository(Protocol):
    async def create(self) -> UUID: ...
    async def exists(self, conversation_id: UUID) -> bool: ...
    async def add_exchange(
        self, conversation_id: UUID, question: str, answer: str, citations: list[Citation]
    ) -> None: ...
    async def messages(
        self, conversation_id: UUID, limit: int = 100
    ) -> list[dict[str, object]]: ...
