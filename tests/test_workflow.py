"""Fast, credit-free tests for the autonomous workflow."""

from pathlib import Path

import pytest
from docx import Document
from fastapi.testclient import TestClient

from app.api.routes import get_orchestrator
from app.main import app
from app.orchestrator import AgentOrchestrator


class FakeLLM:
    """Deterministic stand-in; production code still exercises all orchestration."""

    def __init__(self) -> None:
        self.section_number = 0

    async def structured_complete(self, prompt: str, **kwargs):
        if "Create an execution plan" in prompt:
            return {
                "document_type": "project proposal",
                "document_title": "Inventory Management System Proposal",
                "assumptions": ["The first release is a web application."],
                "total_steps": 3,
                "steps": [
                    {
                        "step_number": 1,
                        "action": "Executive Summary",
                        "description": "Explain the business need and outcome.",
                        "dependencies": [],
                    },
                    {
                        "step_number": 2,
                        "action": "Solution and Scope",
                        "description": "Define capabilities and boundaries.",
                        "dependencies": [1],
                    },
                    {
                        "step_number": 3,
                        "action": "Delivery Plan",
                        "description": "Define milestones, risks, and success measures.",
                        "dependencies": [1, 2],
                    },
                ],
                "estimated_sections": 3,
            }
        return {
            "status": "PASS",
            "issues": [],
            "suggestions": [],
            "confidence_score": 0.93,
        }

    async def complete(self, prompt: str, **kwargs):
        self.section_number += 1
        return (
            f"Section {self.section_number} provides a concrete, decision-ready analysis "
            "for stakeholders. It defines ownership, measurable outcomes, delivery controls, "
            "and practical next actions while keeping the proposal internally consistent.\n\n"
            f"- Milestone {self.section_number} has an accountable owner\n"
            f"- Success measure {self.section_number} is reviewed weekly"
        )


class RecoveryFakeLLM(FakeLLM):
    """Force the quality gate through its one allowed recovery pass."""

    def __init__(self) -> None:
        super().__init__()
        self.review_count = 0

    async def structured_complete(self, prompt: str, **kwargs):
        if "Create an execution plan" in prompt:
            return await super().structured_complete(prompt, **kwargs)
        if "Improve these sections" in prompt:
            return {
                "sections": [
                    {
                        "title": title,
                        "content": (
                            f"Revised {title} gives stakeholders concrete scope, ownership, "
                            "measures, risks, and next steps. The details are internally "
                            "consistent and explicitly tied to the requested business outcome."
                        ),
                    }
                    for title in ["Executive Summary", "Solution and Scope", "Delivery Plan"]
                ]
            }
        self.review_count += 1
        if self.review_count == 1:
            return {
                "status": "FAIL",
                "issues": ["Success criteria need clearer ownership."],
                "suggestions": ["Assign accountable owners."],
                "confidence_score": 0.9,
            }
        return {
            "status": "PASS",
            "issues": [],
            "suggestions": [],
            "confidence_score": 0.96,
        }


@pytest.mark.asyncio
async def test_workflow_creates_a_reviewed_docx(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("OUTPUT_DIR", str(tmp_path))
    result = await AgentOrchestrator(FakeLLM()).run(
        "Create a proposal for an inventory management system for a retail company."
    )

    output = Path(result.document_path)
    assert result.status == "completed"
    assert result.execution_plan.total_steps == 3
    assert result.reflection_result.status == "PASS"
    assert output.is_file()
    assert output.stat().st_size > 0
    text = "\n".join(paragraph.text for paragraph in Document(output).paragraphs)
    assert "Inventory Management System Proposal" in text
    assert "Planning Assumptions" in text


@pytest.mark.asyncio
async def test_failed_reflection_triggers_one_recovery_pass(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("OUTPUT_DIR", str(tmp_path))
    llm = RecoveryFakeLLM()
    result = await AgentOrchestrator(llm).run(
        "Create a proposal and make reasonable decisions where details are missing."
    )

    assert llm.review_count == 2
    assert result.reflection_result.status == "PASS"
    assert result.reflection_result.revised is True


def test_api_validates_bad_requests() -> None:
    with TestClient(app) as client:
        response = client.post("/agent", json={"request": "1234567890"})
    assert response.status_code == 422


def test_api_exposes_plan_and_download(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("OUTPUT_DIR", str(tmp_path))
    orchestrator = AgentOrchestrator(FakeLLM())
    app.dependency_overrides[get_orchestrator] = lambda: orchestrator
    try:
        with TestClient(app) as client:
            response = client.post(
                "/agent",
                json={"request": "Create a detailed inventory project proposal."},
            )
            assert response.status_code == 200
            body = response.json()
            assert len(body["execution_plan"]["steps"]) == 3
            download = client.get(body["document_url"])
            assert download.status_code == 200
            assert download.content.startswith(b"PK")
    finally:
        app.dependency_overrides.clear()
