from uuid import uuid4

from sqlalchemy.dialects import postgresql

from app.infrastructure.repositories import SqlConversationRepository


class _Result:
    def all(self) -> list[object]:
        return []


class _CapturingSession:
    statement: object | None = None

    async def scalars(self, statement: object) -> _Result:
        self.statement = statement
        return _Result()


async def test_message_history_orders_questions_before_same_timestamp_answers() -> None:
    session = _CapturingSession()

    await SqlConversationRepository(session).messages(uuid4())  # type: ignore[arg-type]

    assert session.statement is not None
    sql = str(session.statement.compile(dialect=postgresql.dialect()))
    assert "ORDER BY messages.created_at, CASE WHEN (messages.role =" in sql
    assert "THEN" in sql and "ELSE" in sql
