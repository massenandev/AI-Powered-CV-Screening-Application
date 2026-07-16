from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.services import ChatService
from app.config import get_settings
from app.infrastructure.database import get_session
from app.infrastructure.gemini import GeminiClient
from app.infrastructure.repositories import SqlConversationRepository, SqlDocumentRepository


def get_chat_service(session: Annotated[AsyncSession, Depends(get_session)]) -> ChatService:
    settings = get_settings()
    gemini = GeminiClient(
        settings.gemini_api_key,
        settings.gemini_chat_model,
        settings.gemini_embedding_model,
        settings.embedding_dimensions,
    )
    return ChatService(
        SqlDocumentRepository(session), SqlConversationRepository(session), gemini, gemini
    )
