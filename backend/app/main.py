import asyncio
import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

from app.api.health import router as health_router
from app.api.v1.router import api_router
from app.config import settings
from app.database import engine
from app.tasks.reaper import reaper_loop

logger = logging.getLogger(__name__)

_STATUS_ERROR_CODES = {
    400: "BAD_REQUEST",
    401: "UNAUTHORIZED",
    403: "FORBIDDEN",
    404: "NOT_FOUND",
    409: "CONFLICT",
    422: "VALIDATION_ERROR",
}

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Schema is managed via Alembic migrations (alembic upgrade head) -- see CLAUDE.md
    reaper_task = asyncio.create_task(reaper_loop())
    yield
    # Cleanup on shutdown
    reaper_task.cancel()
    await engine.dispose()

app = FastAPI(
    title="SentinelIQ API",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    if isinstance(exc.detail, dict) and "error" in exc.detail:
        body = exc.detail
    else:
        code = _STATUS_ERROR_CODES.get(exc.status_code, "HTTP_ERROR")
        body = {"error": {"code": code, "message": str(exc.detail)}}
    return JSONResponse(status_code=exc.status_code, content=body, headers=exc.headers)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    message = "; ".join(
        f"{'.'.join(str(loc) for loc in err['loc'])}: {err['msg']}" for err in exc.errors()
    )
    return JSONResponse(status_code=422, content={"error": {"code": "VALIDATION_ERROR", "message": message}})

@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled exception")
    return JSONResponse(status_code=500, content={"error": {"code": "INTERNAL_ERROR", "message": "An unexpected error occurred."}})

app.include_router(health_router)
app.include_router(api_router, prefix="/api/v1")
