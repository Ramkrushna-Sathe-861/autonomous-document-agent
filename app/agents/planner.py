"""LLM-backed planner that turns a request into an executable task list."""

import json

from pydantic import ValidationError as PydanticValidationError

from app.config import get_settings
from app.core.exceptions import PlanningError
from app.llm import GroqClient
from app.schemas import ExecutionPlan
from app.tools import TemplateTool


class PlannerAgent:
    """Create and validate a dependency-aware document plan."""

    def __init__(self, llm: GroqClient | None = None) -> None:
        self.llm = llm or GroqClient()
        self.settings = get_settings()
        self.templates = TemplateTool()

    async def create_plan(self, request: str) -> ExecutionPlan:
        template_context = self._template_context()
        prompt = self._build_prompt(request, template_context)
        last_error: Exception | None = None
        for _ in range(self.settings.max_planning_retries + 1):
            try:
                data = await self.llm.structured_complete(
                    prompt,
                    system_prompt=(
                        "You are an autonomous business-document planner. Make useful "
                        "decisions instead of asking follow-up questions. Output valid JSON."
                    ),
                    model=self.settings.planner_model,
                )
                plan = ExecutionPlan.model_validate(data)
                self._validate_plan(plan)
                return plan
            except (PydanticValidationError, ValueError, KeyError) as exc:
                last_error = exc
                prompt += f"\nPrevious response was invalid ({exc}). Correct it."
        raise PlanningError(f"Could not create a valid execution plan: {last_error}")

    def _template_context(self) -> str:
        lines: list[str] = []
        for name in self.templates.list_templates():
            template = self.templates.load_template(name)
            titles = [section["title"] for section in template.get_sections()]
            lines.append(f"- {name}: {', '.join(titles)}")
        return "\n".join(lines) or "- No templates available; design an appropriate structure."

    @staticmethod
    def _validate_plan(plan: ExecutionPlan) -> None:
        if not 2 <= len(plan.steps) <= 12:
            raise ValueError("plan must contain between 2 and 12 steps")
        if plan.total_steps != len(plan.steps) or plan.estimated_sections != len(plan.steps):
            raise ValueError("plan counters do not match steps")
        expected = list(range(1, len(plan.steps) + 1))
        if [step.step_number for step in plan.steps] != expected:
            raise ValueError("step numbers must be sequential")
        for step in plan.steps:
            if any(dep >= step.step_number or dep < 1 for dep in step.dependencies):
                raise ValueError("dependencies must reference earlier steps")

    def _build_prompt(self, request: str, template_context: str) -> str:
        schema = json.dumps(ExecutionPlan.model_json_schema(), indent=2)
        focus_points = self._request_focus_points(request)
        focus_block = "\n".join(f"- {point}" for point in focus_points) or "- Use the request itself to infer the important points."
        return f"""Create an execution plan for this document request:

{request}

Request-driven focus points:
{focus_block}

Available document templates:
{template_context}

Return only one JSON object matching this schema:
{schema}

Rules:
- Make one executable content-generation step per final document section.
- Use 4-8 sections and sequential step_number values starting at 1.
- Make the section titles specific to this request, not generic defaults.
- Avoid copying template headings unless they truly fit the request.
- Each action should be a short section title; description should list the concrete points the section must cover.
- Record reasonable decisions about missing or conflicting details in assumptions.
- dependencies may reference earlier steps only.
- total_steps and estimated_sections must equal the number of steps.
"""

    @staticmethod
    def _request_focus_points(request: str) -> list[str]:
        text = request.lower()
        focus_points: list[str] = []

        keyword_map = [
            ("migrate", "migration approach, rollback plan, and transition risks"),
            ("migration", "migration approach, rollback plan, and transition risks"),
            ("move", "migration approach, rollback plan, and transition risks"),
            ("moving", "migration approach, rollback plan, and transition risks"),
            ("transition", "migration approach, rollback plan, and transition risks"),
            ("budget", "budget, cost categories, and resource allocation"),
            ("timeline", "timeline, milestones, and delivery sequence"),
            ("deliverable", "deliverables and acceptance criteria"),
            ("risk", "risks, dependencies, and mitigation actions"),
            ("training", "training, adoption, and change management"),
            ("stakeholder", "stakeholders, owners, and responsibilities"),
            ("resource", "people, tools, and resource needs"),
            ("system", "scope, functional capabilities, and integrations"),
            ("platform", "scope, functional capabilities, and integrations"),
            ("project plan", "phases, milestones, and execution approach"),
            ("proposal", "business case, scope, and expected outcomes"),
            ("technical", "architecture, implementation, and testing approach"),
            ("rollback", "rollback, contingency, and go-live safeguards"),
            ("success", "success criteria and measurement"),
            ("metric", "success criteria and measurement"),
        ]

        for keyword, point in keyword_map:
            if keyword in text and point not in focus_points:
                focus_points.append(point)

        return focus_points[:6]
