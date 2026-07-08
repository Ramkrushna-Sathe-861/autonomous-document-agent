"""Template management tool for loading JSON document templates."""

import json
import logging
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Any

from app.config import get_settings
from app.core.exceptions import TemplateError

logger = logging.getLogger(__name__)


class Template:
    """Represents a document template."""

    def __init__(self, name: str, data: dict[str, Any]):
        self.name = name
        self.data = data

    def get(self, key: str, default: Any = None) -> Any:
        keys = key.split(".")
        value = self.data
        for part in keys:
            if not isinstance(value, dict):
                return default
            value = value.get(part)
            if value is None:
                return default
        return value

    def get_sections(self) -> list[dict[str, Any]]:
        sections = self.data.get("sections", [])
        return sections if isinstance(sections, list) else []

    def get_metadata(self) -> dict[str, Any]:
        metadata = self.data.get("metadata", {})
        return metadata if isinstance(metadata, dict) else {}


class TemplateTool:
    """Loads and caches JSON templates from the templates directory."""

    def __init__(self):
        self.settings = get_settings()
        self.templates_dir = self.settings.get_templates_path()
        self.templates_dir.mkdir(parents=True, exist_ok=True)
        self._cache: dict[str, Template] = {}

    def build_node(self) -> Callable[[dict[str, object]], Awaitable[dict[str, object]]]:
        """Expose template lookup as a LangGraph node."""

        async def node(state: dict[str, object]) -> dict[str, object]:
            request = state.get("request")
            assert isinstance(request, str)
            return {"template_context": self._template_context()}

        return node

    def _template_context(self) -> str:
        lines: list[str] = []
        for name in self.list_templates():
            template = self.load_template(name)
            titles = [section["title"] for section in template.get_sections()]
            lines.append(f"- {name}: {', '.join(titles)}")
        return "\n".join(lines) or "- No templates available; design an appropriate structure."

    def load_template(self, template_name: str) -> Template:
        if template_name in self._cache:
            logger.debug("Template loaded from cache: %s", template_name)
            return self._cache[template_name]

        template_path = self.templates_dir / f"{template_name}.json"
        if not template_path.exists():
            logger.error("Template not found: %s", template_path)
            raise TemplateError(f"Template '{template_name}' not found")

        try:
            with open(template_path, "r", encoding="utf-8") as file:
                data = json.load(file)
            template = Template(template_name, data)
            self._cache[template_name] = template
            logger.info("Template loaded: %s", template_name)
            return template
        except json.JSONDecodeError as exc:
            logger.error("Invalid JSON in template %s: %s", template_name, exc)
            raise TemplateError(f"Invalid JSON in template: {exc}") from exc
        except Exception as exc:
            logger.error("Failed to load template: %s", exc)
            raise TemplateError(f"Failed to load template: {exc}") from exc

    def list_templates(self) -> list[str]:
        try:
            return sorted(file.stem for file in self.templates_dir.glob("*.json"))
        except Exception as exc:
            logger.error("Failed to list templates: %s", exc)
            return []

    def template_exists(self, template_name: str) -> bool:
        return (self.templates_dir / f"{template_name}.json").exists()

    def create_template(self, template_name: str, data: dict[str, Any]) -> Path:
        template_path = self.templates_dir / f"{template_name}.json"
        try:
            with open(template_path, "w", encoding="utf-8") as file:
                json.dump(data, file, indent=2)
            self._cache.pop(template_name, None)
            logger.info("Template created: %s", template_name)
            return template_path
        except Exception as exc:
            logger.error("Failed to create template: %s", exc)
            raise TemplateError(f"Failed to create template: {exc}") from exc

    def clear_cache(self) -> None:
        self._cache.clear()

    def get_template_content(self, template_name: str) -> dict[str, Any]:
        return self.load_template(template_name).data
