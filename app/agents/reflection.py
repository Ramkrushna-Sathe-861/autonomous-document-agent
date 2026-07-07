"""Deterministic and semantic self-check for generated documents."""

import json

from app.config import get_settings
from app.llm import GroqClient
from app.schemas import ExecutorResult, ReflectionResult
from app.tools import ValidationTool


class ReflectionAgent:
    """Review quality and provide actionable issues before the document is saved."""

    def __init__(self, llm: GroqClient | None = None) -> None:
        self.llm = llm or GroqClient()
        self.settings = get_settings()
        self.validator = ValidationTool()

    async def review(self, request: str, sections: list[ExecutorResult]) -> ReflectionResult:
        raw_sections = [
            {"title": section.section_title, "content": section.content}
            for section in sections
        ]
        full_text = "\n\n".join(item["content"] for item in raw_sections)
        checks = self.validator.validate_all(full_text, raw_sections)
        if not checks["is_valid"]:
            return ReflectionResult(
                status="FAIL",
                issues=checks["errors"],
                suggestions=checks["warnings"],
                confidence_score=1.0,
            )

        schema = json.dumps(ReflectionResult.model_json_schema())
        prompt = f"""Review this generated business document against the request.
Request: {request}
Document: {raw_sections}
Deterministic warnings: {checks['warnings']}

Return JSON matching {schema}. PASS only if it fulfills the request, is consistent,
professional, and contains no unsupported claims presented as verified facts.
"""
        data = await self.llm.structured_complete(
            prompt,
            system_prompt="You are an independent document quality reviewer. Output JSON only.",
            model=self.settings.reflection_model,
        )
        return ReflectionResult.model_validate(data)
