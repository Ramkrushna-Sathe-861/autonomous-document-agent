"""Execute a plan by generating every planned document section."""

from app.config import get_settings
from app.core.exceptions import ExecutionError
from app.llm import GroqClient
from app.schemas import ExecutionPlan, ExecutorResult


class ExecutorAgent:
    """Generate grounded, professional content one plan step at a time."""

    def __init__(self, llm: GroqClient | None = None) -> None:
        self.llm = llm or GroqClient()
        self.settings = get_settings()

    async def execute(self, request: str, plan: ExecutionPlan) -> list[ExecutorResult]:
        results: list[ExecutorResult] = []
        for step in plan.steps:
            prior = "\n".join(
                f"{item.section_title}: {item.content[:500]}" for item in results
            )
            prompt = f"""Original request: {request}
Document title: {plan.document_title}
Document type: {plan.document_type}
Assumptions: {plan.assumptions or ['None']}

Write section {step.step_number}: {step.action}
Section goal: {step.description}
Relevant earlier content:
{prior or 'This is the first section.'}

Write polished business prose with concrete, internally consistent details. Use 2-5
bullet points when helpful so the section clearly shows the key points for this
request. Make the bullets specific to the step, not generic filler. Do not repeat the
section heading and do not wrap the answer in Markdown fences.
"""
            try:
                content = await self.llm.complete(
                    prompt,
                    system_prompt="You are a precise senior business and technical writer.",
                    temperature=0.5,
                    model=self.settings.executor_model,
                )
            except Exception as exc:
                raise ExecutionError(
                    f"Failed while executing step {step.step_number} ({step.action}): {exc}"
                ) from exc
            if len(content.strip()) < 20:
                raise ExecutionError(f"Step {step.step_number} returned insufficient content")
            results.append(
                ExecutorResult(
                    section_title=step.action.strip(),
                    content=content.strip(),
                    status="success",
                )
            )
        return results

    async def revise(
        self, request: str, plan: ExecutionPlan, sections: list[ExecutorResult], issues: list[str]
    ) -> list[ExecutorResult]:
        prompt = f"""Improve these sections for the original request: {request}
Issues to fix: {issues}
Return JSON with a `sections` array. Every item must contain exactly `title` and
`content`. Preserve all {len(sections)} section titles and their order.

Current sections:
{[{'title': s.section_title, 'content': s.content} for s in sections]}
"""
        data = await self.llm.structured_complete(
            prompt,
            system_prompt="You are a meticulous document editor. Output valid JSON only.",
            model=self.settings.executor_model,
            max_tokens=4096,
        )
        revised = data.get("sections", [])
        if len(revised) != len(sections):
            raise ExecutionError("Revision response changed the document structure")
        return [
            ExecutorResult(
                section_title=item["title"], content=item["content"], status="success"
            )
            for item in revised
        ]
