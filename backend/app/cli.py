import argparse
import asyncio

from sqlalchemy import text

from app.application.services import IngestionService
from app.config import get_settings
from app.infrastructure.database import engine, session_factory
from app.infrastructure.gemini import GeminiClient
from app.infrastructure.pdf import PyMuPdfExtractor
from app.infrastructure.repositories import SqlDocumentRepository


async def index(force: bool) -> None:
    settings = get_settings()
    gemini = GeminiClient(
        settings.gemini_api_key,
        settings.gemini_chat_model,
        settings.gemini_embedding_model,
        settings.embedding_dimensions,
    )
    # Session-level advisory locks belong to a physical database connection, so
    # keep one connection checked out until the lock has been released.
    async with engine.connect() as connection:
        await connection.execute(text("SELECT pg_advisory_lock(734921)"))
        await connection.commit()

        async with session_factory(bind=connection) as session:
            try:
                service = IngestionService(
                    SqlDocumentRepository(session),
                    PyMuPdfExtractor(),
                    gemini,
                    settings.gemini_embedding_model,
                )
                indexed, skipped = await service.ingest(
                    list(settings.cv_directory.glob("*.pdf")), force
                )
                print(f"Indexed {indexed}; skipped {skipped}")
            finally:
                # A failed statement leaves PostgreSQL's transaction aborted.
                # Roll it back before issuing the unlock so the original error
                # is not replaced by InFailedSQLTransactionError.
                await session.rollback()
                await connection.execute(text("SELECT pg_advisory_unlock(734921)"))
                await connection.commit()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["index"])
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    asyncio.run(index(args.force))


if __name__ == "__main__":
    main()
