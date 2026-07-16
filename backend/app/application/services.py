import hashlib
from pathlib import Path

from app.domain.chunking import chunk_pages
from app.domain.models import Citation, SearchResult, validate_question
from app.domain.ports import (
    AnswerGenerator,
    ConversationRepository,
    DocumentRepository,
    Embedder,
    PdfExtractor,
)


class IngestionService:
    def __init__(
        self,
        repository: DocumentRepository,
        extractor: PdfExtractor,
        embedder: Embedder,
        model: str,
    ):
        self.repository = repository
        self.extractor = extractor
        self.embedder = embedder
        self.model = model

    async def ingest(self, paths: list[Path], force: bool = False) -> tuple[int, int]:
        indexed = skipped = 0
        for path in sorted(paths):
            checksum = hashlib.sha256(path.read_bytes()).hexdigest()
            if not force and await self.repository.checksum_is_current(
                str(path), checksum, self.model
            ):
                skipped += 1
                continue
            chunks = chunk_pages(self.extractor.extract(path))
            if not chunks:
                raise ValueError(f"No readable text found in {path.name}")
            vectors = await self.embedder.embed_documents([chunk.text for chunk in chunks])
            await self.repository.replace_document(str(path), checksum, self.model, chunks, vectors)
            indexed += 1
        return indexed, skipped


class ChatService:
    def __init__(
        self,
        documents: DocumentRepository,
        conversations: ConversationRepository,
        embedder: Embedder,
        generator: AnswerGenerator,
    ):
        self.documents = documents
        self.conversations = conversations
        self.embedder = embedder
        self.generator = generator

    async def ask(self, conversation_id: object, question: str) -> tuple[str, list[Citation]]:
        from uuid import UUID

        if not isinstance(conversation_id, UUID) or not await self.conversations.exists(
            conversation_id
        ):
            raise LookupError("Conversation not found")
        question = validate_question(question)
        vector = await self.embedder.embed_query(question)
        comparison = any(
            word in question.lower() for word in ("compare", "best", "which candidates", "who ")
        )
        results = await self.documents.search(vector, limit=16 if comparison else 8)
        answer = await self.generator.answer(question, results)
        citations = _citations(results)
        await self.conversations.add_exchange(conversation_id, question, answer, citations)
        return answer, citations


def _citations(results: list[SearchResult]) -> list[Citation]:
    seen: set[tuple[object, int]] = set()
    citations: list[Citation] = []
    for result in results:
        key = (result.document_id, result.page)
        if key in seen:
            continue
        seen.add(key)
        citations.append(
            Citation(result.document_id, result.candidate_name, result.page, result.text[:240])
        )
    return citations[:6]
