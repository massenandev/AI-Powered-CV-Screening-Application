import uuid
from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from sqlalchemy import text

from app.api.routes import router
from app.config import get_settings
from app.infrastructure.database import engine

app = FastAPI(title="CV Screening API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().origins,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "X-Request-ID"],
)
app.include_router(router)


@app.middleware("http")
async def request_id_middleware(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    request.state.request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    response = await call_next(request)
    response.headers["X-Request-ID"] = request.state.request_id
    return response


def error_response(
    request: Request, status: int, code: str, message: str, details: object = None
) -> JSONResponse:
    return JSONResponse(
        status_code=status,
        content={
            "error": {
                "code": code,
                "message": message,
                "request_id": getattr(request.state, "request_id", "unknown"),
                "details": details or {},
            }
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
    return error_response(request, 422, "VALIDATION_ERROR", "The request is invalid", exc.errors())


@app.exception_handler(LookupError)
async def not_found(request: Request, exc: LookupError) -> JSONResponse:
    return error_response(request, 404, "NOT_FOUND", str(exc))


@app.exception_handler(RuntimeError)
async def provider_error(request: Request, exc: RuntimeError) -> JSONResponse:
    return error_response(request, 503, "SERVICE_UNAVAILABLE", str(exc))


@app.get("/health/live")
async def live() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/health/ready", response_model=None)
async def ready(request: Request) -> dict[str, str] | JSONResponse:
    try:
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
        return {"status": "ready"}
    except Exception:
        return error_response(request, 503, "NOT_READY", "Database is unavailable")
