"""Planning, execution, reflection, and orchestration in one workflow module."""

import re
from datetime import datetime, timezone
from typing import TypedDict
from uuid import uuid4

from app.core.exceptions import ReflectionError
from app.llm import GroqClient
from app.agents import ExecutorAgent, PlannerAgent, ReflectionAgent
from app.tools import DocumentTool
from app.schemas import DocumentResponse, ExecutionPlan, ExecutorResult, ReflectionResult


class WorkflowState(TypedDict, total=False):
    """Shared state for the LangGraph workflow."""

    request: str
    plan: ExecutionPlan | None
    sections: list[ExecutorResult]
    reflection: ReflectionResult | None
    revision_count: int
    response: DocumentResponse | None


class AgentOrchestrator:
    """Coordinate planning, execution, reflection, recovery, and DOCX output."""

    def __init__(self, llm: GroqClient | None = None) -> None:
        shared_llm = llm or GroqClient()
        self.planner = PlannerAgent(shared_llm)
        self.executor = ExecutorAgent(shared_llm)
        self.reflector = ReflectionAgent(shared_llm)
        self.documents = DocumentTool()
        self.graph = build_graph(self)

    async def run(self, request: str) -> DocumentResponse:
        result = await self.graph.ainvoke({"request": request, "revision_count": 0})
        response = result.get("response")
        if response is None:
            raise ReflectionError("Document workflow did not produce a response")
        return response

    def _render(self, title: str, assumptions: list[str], sections: list[ExecutorResult], filename: str):
        return self.documents.render_document(title, assumptions, sections, filename)

    @staticmethod
    def _filename(title: str) -> str:
        slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")[:50]
        return f"{slug or 'document'}-{uuid4().hex[:8]}.docx"


def build_graph(orchestrator: AgentOrchestrator):
    """Build a LangGraph workflow for planning, execution, reflection, and rendering."""
    try:
        from langgraph.graph import END, StateGraph
    except ImportError as exc:  # pragma: no cover - depends on runtime env
        raise ImportError("langgraph is required to run the graph-based workflow") from exc

    workflow = StateGraph(WorkflowState)

    async def revise_node(state: WorkflowState) -> dict[str, object]:
        plan = state["plan"]
        assert plan is not None
        sections = state.get("sections", [])
        reflection = state.get("reflection")
        if reflection is None:
            raise ReflectionError("Reflection result is missing for revision")
        try:
            revised_sections = await orchestrator.executor.revise(
                state["request"],
                plan,
                sections,
                reflection.issues + reflection.suggestions,
            )
            revised_reflection = await orchestrator.reflector.review(state["request"], revised_sections)
            revised_reflection.revised = True
            return {"sections": revised_sections, "reflection": revised_reflection, "revision_count": 1}
        except Exception as exc:
            raise ReflectionError(f"Document recovery pass failed: {exc}") from exc

    async def validate_node(state: WorkflowState) -> dict[str, object]:
        sections = state.get("sections", [])
        assert isinstance(sections, list)
        validation_results = orchestrator.reflector.validator.validate_all(
            "\n\n".join(section.content for section in sections if hasattr(section, "content")),
            [{"title": section.section_title, "content": section.content} for section in sections if hasattr(section, "section_title") and hasattr(section, "content")],
        )
        return {"validation_results": validation_results}

    async def render_node(state: WorkflowState) -> dict[str, object]:
        plan = state["plan"]
        assert plan is not None
        sections = state.get("sections", [])
        reflection = state.get("reflection")
        assert reflection is not None
        if reflection.status != "PASS":
            raise ReflectionError(
                "Document did not pass quality review after one revision: "
                + "; ".join(reflection.issues)
            )
        filename = orchestrator._filename(plan.document_title)
        path = orchestrator._render(plan.document_title, plan.assumptions, sections, filename)
        response = DocumentResponse(
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
        return {"response": response}

    def should_continue(state: WorkflowState) -> str:
        reflection = state.get("reflection")
        if reflection is None:
            return "render"
        if reflection.status == "FAIL":
            if state.get("revision_count", 0) >= 1:
                return "end"
            return "revise"
        return "render"

    workflow.add_node("template_lookup", orchestrator.planner.templates.build_node())
    workflow.add_node("planner", orchestrator.planner.build_node())
    workflow.add_node("executor", orchestrator.executor.build_node())
    workflow.add_node("validate", validate_node)
    workflow.add_node("reflector", orchestrator.reflector.build_node())
    workflow.add_node("revise", revise_node)
    workflow.add_node("render_document", orchestrator.documents.build_node())
    workflow.add_node("render", render_node)

    workflow.set_entry_point("template_lookup")
    workflow.add_edge("template_lookup", "planner")
    workflow.add_edge("planner", "executor")
    workflow.add_edge("executor", "validate")
    workflow.add_edge("validate", "reflector")
    workflow.add_conditional_edges(
        "reflector",
        should_continue,
        {
            "revise": "revise",
            "render": "render",
            "end": END,
        },
    )
    workflow.add_edge("revise", "validate")
    workflow.add_edge("render_document", "render")
    workflow.add_edge("render", END)
    return workflow.compile()
