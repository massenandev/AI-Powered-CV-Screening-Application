from pathlib import Path
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_chat_service
from app.api.schemas import (
    AnswerResponse,
    ConversationResponse,
    ConversationsResponse,
    MessagesResponse,
    QuestionRequest,
)
from app.application.services import ChatService
from app.infrastructure.database import get_session
from app.infrastructure.repositories import SqlConversationRepository, SqlDocumentRepository

router = APIRouter(prefix="/api/v1")


@router.get("/documents/{document_id}/file", response_class=FileResponse)
async def get_document_file(
    document_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
    download: Annotated[bool, Query()] = False,
) -> FileResponse:
    path = await SqlDocumentRepository(session).path_for(document_id)
    if not path:
        raise LookupError("CV not found")
    file_path = Path(path)
    if not file_path.is_file() or file_path.suffix.lower() != ".pdf":
        raise LookupError("CV file not found")
    return FileResponse(
        file_path,
        media_type="application/pdf",
        filename=file_path.name,
        content_disposition_type="attachment" if download else "inline",
    )


@router.post("/conversations", response_model=ConversationResponse, status_code=201)
async def create_conversation(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ConversationResponse:
    return ConversationResponse(id=await SqlConversationRepository(session).create())


@router.get("/conversations", response_model=ConversationsResponse)
async def get_conversations(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ConversationsResponse:
    return ConversationsResponse(conversations=await SqlConversationRepository(session).conversations())


@router.post("/conversations/{conversation_id}/messages", response_model=AnswerResponse)
async def ask_question(
    conversation_id: UUID,
    payload: QuestionRequest,
    service: Annotated[ChatService, Depends(get_chat_service)],
) -> AnswerResponse:
    answer, sources = await service.ask(conversation_id, payload.question)
    return AnswerResponse(answer=answer, sources=sources)


@router.get("/conversations/{conversation_id}/messages", response_model=MessagesResponse)
async def get_messages(
    conversation_id: UUID, session: Annotated[AsyncSession, Depends(get_session)]
) -> MessagesResponse:
    repository = SqlConversationRepository(session)
    if not await repository.exists(conversation_id):
        raise LookupError("Conversation not found")
    return MessagesResponse(messages=await repository.messages(conversation_id))
