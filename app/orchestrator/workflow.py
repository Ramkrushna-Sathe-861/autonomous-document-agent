"""End-to-end autonomous document generation workflow."""

import re
from datetime import datetime, timezone
from uuid import uuid4

from app.agents import ExecutorAgent, PlannerAgent, ReflectionAgent
from app.core.exceptions import ReflectionError
from app.llm import GroqClient
from app.schemas import DocumentResponse, ExecutorResult
from app.tools import DocumentTool


class AgentOrchestrator:
    """Coordinate planning, execution, reflection, recovery, and DOCX output."""

    def __init__(self, llm: GroqClient | None = None) -> None:
        shared_llm = llm or GroqClient()
        self.planner = PlannerAgent(shared_llm)
        self.executor = ExecutorAgent(shared_llm)
        self.reflector = ReflectionAgent(shared_llm)
        self.documents = DocumentTool()

    async def run(self, request: str) -> DocumentResponse:
        plan = await self.planner.create_plan(request)
        sections = await self.executor.execute(request, plan)
        reflection = await self.reflector.review(request, sections)

        if reflection.status == "FAIL":
            try:
                sections = await self.executor.revise(
                    request, plan, sections, reflection.issues + reflection.suggestions
                )
                reflection = await self.reflector.review(request, sections)
                reflection.revised = True
            except Exception as exc:
                raise ReflectionError(f"Document recovery pass failed: {exc}") from exc

        if reflection.status != "PASS":
            raise ReflectionError(
                "Document did not pass quality review after one revision: "
                + "; ".join(reflection.issues)
            )

        filename = self._filename(plan.document_title)
        path = self._render(plan.document_title, plan.assumptions, sections, filename)
        return DocumentResponse(
            status="completed",
            execution_plan=plan,
            summary=(
                f"Generated {plan.document_type} with {len(sections)} sections. "
                f"Quality review passed at {reflection.confidence_score:.0%} confidence."
            ),
            document_path=str(path),
            document_url=f"/documents/{path.name}",
            reflection_result=reflection,
            generated_at=datetime.now(timezone.utc),
        )

    def _render(
        self,
        title: str,
        assumptions: list[str],
        sections: list[ExecutorResult],
        filename: str,
    ):
        document = self.documents.create_document(title)
        if assumptions:
            self.documents.add_heading(document, "Planning Assumptions", level=1)
            self.documents.add_bulleted_list(document, assumptions)
        for section in sections:
            self.documents.add_heading(document, section.section_title, level=1)
            self._add_content(document, section.content)
        return self.documents.save_document(document, filename)

    def _add_content(self, document, content: str) -> None:
        paragraphs: list[str] = []
        bullets: list[str] = []

        def flush() -> None:
            if paragraphs:
                self.documents.add_paragraph(document, "\n".join(paragraphs))
                paragraphs.clear()
            if bullets:
                self.documents.add_bulleted_list(document, bullets.copy())
                bullets.clear()

        for line in content.splitlines():
            stripped = line.strip()
            if stripped.startswith(("- ", "* ")):
                if paragraphs:
                    flush()
                bullets.append(stripped[2:].strip())
            elif not stripped:
                flush()
            else:
                if bullets:
                    flush()
                paragraphs.append(stripped)
        flush()

    @staticmethod
    def _filename(title: str) -> str:
        slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")[:50]
        return f"{slug or 'document'}-{uuid4().hex[:8]}.docx"
