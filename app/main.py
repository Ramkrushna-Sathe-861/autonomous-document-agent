"""FastAPI application entry point."""

from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.routes import router
from app.config import get_settings
from app.core import ApplicationError, setup_logging
from app.schemas import ErrorResponse

settings = get_settings()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(application: FastAPI):
    setup_logging()
    logger.info("Groq model pinned to: %s", settings.groq_model)
    yield


app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    description="Autonomous planning, execution, reflection, and DOCX generation.",
    lifespan=lifespan,
)
app.include_router(router)


@app.exception_handler(ApplicationError)
async def application_error_handler(request: Request, exc: ApplicationError) -> JSONResponse:
    status_code = 503 if exc.error_code == "LLM_ERROR" else 422
    payload = ErrorResponse(
        status="error",
        error_code=exc.error_code,
        message=exc.message,
        details={"path": request.url.path},
    )
    return JSONResponse(status_code=status_code, content=payload.model_dump())
