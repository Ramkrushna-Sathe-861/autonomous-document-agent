"""
Template management tool for loading JSON document templates.

Purpose: Load and manage document templates from JSON files.
Responsibility: Template loading, validation, and retrieval.
"""

import json
import logging
from pathlib import Path
from typing import Any, Optional

from app.config import get_settings
from app.core.exceptions import TemplateError

logger = logging.getLogger(__name__)


class Template:
    """Represents a document template."""

    def __init__(self, name: str, data: dict[str, Any]):
        """Initialize template.

        Args:
            name: Template name
            data: Template data
        """
        self.name = name
        self.data = data

    def get(self, key: str, default: Any = None) -> Any:
        """Get template value by key.

        Args:
            key: Template key (supports dot notation: 'sections.intro')
            default: Default value if key not found

        Returns:
            Template value or default
        """
        keys = key.split(".")
        value = self.data

        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default

        return value

    def get_sections(self) -> list[dict[str, Any]]:
        """Get document sections from template.

        Returns:
            List of section dictionaries
        """
        sections = self.data.get("sections", [])
        return sections if isinstance(sections, list) else []

    def get_metadata(self) -> dict[str, Any]:
        """Get template metadata.

        Returns:
            Metadata dictionary
        """
        return self.data.get("metadata", {})


class TemplateTool:
    """Manages document templates from JSON files."""

    def __init__(self):
        """Initialize template tool with settings."""
        self.settings = get_settings()
        self.templates_dir = self.settings.get_templates_path()
        self.templates_dir.mkdir(parents=True, exist_ok=True)
        self._cache: dict[str, Template] = {}

    def load_template(self, template_name: str) -> Template:
        """
        Load a template from JSON file.

        Args:
            template_name: Template name (without .json extension)

        Returns:
            Template object

        Raises:
            TemplateError: If template not found or invalid
        """
        # Check cache first
        if template_name in self._cache:
            logger.debug(f"Template loaded from cache: {template_name}")
            return self._cache[template_name]

        template_path = self.templates_dir / f"{template_name}.json"

        if not template_path.exists():
            logger.error(f"Template not found: {template_path}")
            raise TemplateError(f"Template '{template_name}' not found")

        try:
            with open(template_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            template = Template(template_name, data)
            self._cache[template_name] = template

            logger.info(f"Template loaded: {template_name}")
            return template

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in template {template_name}: {str(e)}")
            raise TemplateError(f"Invalid JSON in template: {str(e)}")
        except Exception as e:
            logger.error(f"Failed to load template: {str(e)}")
            raise TemplateError(f"Failed to load template: {str(e)}")

    def list_templates(self) -> list[str]:
        """
        List all available templates.

        Returns:
            List of template names
        """
        templates = []
        try:
            for file in self.templates_dir.glob("*.json"):
                templates.append(file.stem)
            logger.debug(f"Found {len(templates)} templates")
            return sorted(templates)

        except Exception as e:
            logger.error(f"Failed to list templates: {str(e)}")
            return []

    def template_exists(self, template_name: str) -> bool:
        """
        Check if template exists.

        Args:
            template_name: Template name

        Returns:
            True if template exists
        """
        template_path = self.templates_dir / f"{template_name}.json"
        return template_path.exists()

    def create_template(
        self, template_name: str, data: dict[str, Any]
    ) -> Path:
        """
        Create a new template file.

        Args:
            template_name: Template name
            data: Template data

        Returns:
            Path to created template

        Raises:
            TemplateError: If template creation fails
        """
        template_path = self.templates_dir / f"{template_name}.json"

        try:
            with open(template_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)

            # Clear cache for this template
            if template_name in self._cache:
                del self._cache[template_name]

            logger.info(f"Template created: {template_name}")
            return template_path

        except Exception as e:
            logger.error(f"Failed to create template: {str(e)}")
            raise TemplateError(f"Failed to create template: {str(e)}")

    def clear_cache(self) -> None:
        """Clear template cache."""
        self._cache.clear()
        logger.debug("Template cache cleared")

    def get_template_content(self, template_name: str) -> dict[str, Any]:
        """
        Get raw template content.

        Args:
            template_name: Template name

        Returns:
            Template data dictionary
        """
        template = self.load_template(template_name)
        return template.data
