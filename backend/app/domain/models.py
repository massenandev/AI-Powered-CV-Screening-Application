from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID, uuid4


class DocumentStatus(StrEnum):
    PENDING = "pending"
    INDEXED = "indexed"
    FAILED = "failed"


class MessageRole(StrEnum):
    USER = "user"
    ASSISTANT = "assistant"


@dataclass(frozen=True)
class ExtractedPage:
    number: int
    text: str


@dataclass(frozen=True)
class Chunk:
    text: str
    page: int
    section: str


@dataclass(frozen=True)
class SearchResult:
    chunk_id: UUID
    document_id: UUID
    candidate_name: str
    page: int
    text: str
    score: float


@dataclass(frozen=True)
class Citation:
    document_id: UUID
    candidate_name: str
    page: int
    excerpt: str


@dataclass
class Conversation:
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


def validate_question(question: str) -> str:
    normalized = " ".join(question.split())
    if not normalized:
        raise ValueError("Question must not be empty")
    if len(normalized) > 2_000:
        raise ValueError("Question must contain at most 2000 characters")
    return normalized
