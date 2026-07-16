from pathlib import Path
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models import Chunk, Citation, SearchResult
from app.infrastructure.models import ChunkRow, ConversationRow, DocumentRow, MessageRow


class SqlDocumentRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def checksum_is_current(self, path: str, checksum: str, model: str) -> bool:
        query = select(DocumentRow.id).where(
            DocumentRow.path == path,
            DocumentRow.checksum == checksum,
            DocumentRow.embedding_model == model,
        )
        return (await self.session.scalar(query)) is not None

    async def path_for(self, document_id: UUID) -> str | None:
        return await self.session.scalar(
            select(DocumentRow.path).where(DocumentRow.id == document_id)
        )

    async def replace_document(
        self, path: str, checksum: str, model: str, chunks: list[Chunk], vectors: list[list[float]]
    ) -> UUID:
        if len(chunks) != len(vectors):
            raise ValueError("Every chunk must have one embedding")
        try:
            old = await self.session.scalar(select(DocumentRow).where(DocumentRow.path == path))
            if old:
                await self.session.delete(old)
                await self.session.flush()
            row = DocumentRow(
                path=path,
                candidate_name=_candidate_name(path),
                checksum=checksum,
                embedding_model=model,
            )
            self.session.add(row)
            await self.session.flush()
            self.session.add_all(
                ChunkRow(
                    document_id=row.id,
                    position=i,
                    page=c.page,
                    section=c.section,
                    text=c.text,
                    embedding=v,
                )
                for i, (c, v) in enumerate(zip(chunks, vectors, strict=True))
            )
            await self.session.commit()
        except Exception:
            await self.session.rollback()
            raise
        return row.id

    async def search(self, vector: list[float], limit: int) -> list[SearchResult]:
        distance = ChunkRow.embedding.cosine_distance(vector)
        query = (
            select(ChunkRow, DocumentRow, distance.label("distance"))
            .join(DocumentRow, DocumentRow.id == ChunkRow.document_id)
            .order_by(distance)
            .limit(limit)
        )
        rows = (await self.session.execute(query)).all()
        return [
            SearchResult(c.id, d.id, d.candidate_name, c.page, c.text, max(0.0, 1.0 - float(dist)))
            for c, d, dist in rows
        ]


class SqlConversationRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self) -> UUID:
        row = ConversationRow()
        self.session.add(row)
        await self.session.commit()
        return row.id

    async def exists(self, conversation_id: UUID) -> bool:
        return await self.session.get(ConversationRow, conversation_id) is not None

    async def conversations(self, limit: int = 50) -> list[dict[str, object]]:
        first_question = (
            select(MessageRow.content)
            .where(MessageRow.conversation_id == ConversationRow.id, MessageRow.role == "user")
            .order_by(MessageRow.created_at, MessageRow.id)
            .limit(1)
            .scalar_subquery()
        )
        last_message_at = (
            select(func.max(MessageRow.created_at))
            .where(MessageRow.conversation_id == ConversationRow.id)
            .correlate(ConversationRow)
            .scalar_subquery()
        )
        updated_at = func.coalesce(last_message_at, ConversationRow.created_at)
        query = (
            select(ConversationRow, first_question.label("title"), updated_at.label("updated_at"))
            .where(first_question.is_not(None))
            .order_by(updated_at.desc(), ConversationRow.id.desc())
            .limit(limit)
        )
        rows = (await self.session.execute(query)).all()
        return [
            {"id": conversation.id, "title": title or "New chat", "created_at": conversation.created_at, "updated_at": modified}
            for conversation, title, modified in rows
        ]

    async def add_exchange(
        self, conversation_id: UUID, question: str, answer: str, citations: list[Citation]
    ) -> None:
        data = [
            {
                "document_id": str(c.document_id),
                "candidate_name": c.candidate_name,
                "page": c.page,
                "excerpt": c.excerpt,
            }
            for c in citations
        ]
        self.session.add_all(
            [
                MessageRow(
                    conversation_id=conversation_id, role="user", content=question, citations=[]
                ),
                MessageRow(
                    conversation_id=conversation_id,
                    role="assistant",
                    content=answer,
                    citations=data,
                ),
            ]
        )
        await self.session.commit()

    async def messages(self, conversation_id: UUID, limit: int = 100) -> list[dict[str, object]]:
        query = (
            select(MessageRow)
            .where(MessageRow.conversation_id == conversation_id)
            .order_by(MessageRow.created_at, MessageRow.id)
            .limit(limit)
        )
        rows = (await self.session.scalars(query)).all()
        return [
            {
                "id": row.id,
                "role": row.role,
                "content": row.content,
                "sources": row.citations,
                "created_at": row.created_at,
            }
            for row in rows
        ]


def _candidate_name(path: str) -> str:
    return Path(path).stem.split("_", 1)[-1].replace("_", " ").title()
