"""REST endpoints for running the agent and downloading its output."""

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse

from app.config import get_settings
from app.orchestrator import AgentOrchestrator
from app.schemas import DocumentRequest, DocumentResponse

router = APIRouter()


def get_orchestrator() -> AgentOrchestrator:
    return AgentOrchestrator()


@router.get("/health", tags=["system"])
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.post(
    "/agent",
    response_model=DocumentResponse,
    tags=["agent"],
    summary="Generate a document with an autonomous agent",
)
async def run_agent(
    payload: DocumentRequest,
    orchestrator: AgentOrchestrator = Depends(get_orchestrator),
) -> DocumentResponse:
    return await orchestrator.run(payload.request)


@router.get("/documents/{filename}", tags=["documents"])
async def download_document(filename: str) -> FileResponse:
    if filename != Path(filename).name or not filename.lower().endswith(".docx"):
        raise HTTPException(status_code=400, detail="Invalid document filename")
    path = get_settings().get_output_path() / filename
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Document not found")
    return FileResponse(
        path=path,
        filename=filename,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )
