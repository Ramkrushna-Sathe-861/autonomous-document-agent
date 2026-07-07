"""Validation tool for content quality checks."""

import logging
from typing import Any, Optional

from app.config import get_settings

logger = logging.getLogger(__name__)


class ValidationTool:
    """Content validation and quality checking."""

    def __init__(self):
        self.settings = get_settings()

    def validate_content_length(self, content: str) -> tuple[bool, Optional[str]]:
        content_length = len(content)
        if content_length < self.settings.min_document_length:
            return (
                False,
                f"Content too short: {content_length} chars (min: {self.settings.min_document_length})",
            )
        if content_length > self.settings.max_document_length:
            return (
                False,
                f"Content too long: {content_length} chars (max: {self.settings.max_document_length})",
            )
        return True, None

    def validate_section_count(self, sections: list[dict]) -> tuple[bool, Optional[str]]:
        section_count = len(sections)
        if section_count == 0:
            return False, "No sections found in document"
        if section_count > self.settings.max_document_sections:
            return False, f"Too many sections: {section_count} (max: {self.settings.max_document_sections})"
        return True, None

    def validate_no_empty_sections(self, sections: list[dict]) -> tuple[bool, list[str]]:
        empty_sections: list[str] = []
        for index, section in enumerate(sections, 1):
            title = section.get("title", f"Section {index}")
            content = section.get("content", "").strip()
            if not content or len(content) < 10:
                empty_sections.append(f"{index}. {title}")
        return (not empty_sections), empty_sections

    def validate_no_duplicates(
        self, sections: list[dict]
    ) -> tuple[bool, list[tuple[int, int]]]:
        duplicates: list[tuple[int, int]] = []
        section_hashes: dict[str, int] = {}
        for index, section in enumerate(sections):
            content = section.get("content", "").strip().lower()
            content_hash = hash(content)
            if content_hash in section_hashes:
                duplicates.append((section_hashes[content_hash], index))
            else:
                section_hashes[content_hash] = index
        return (not duplicates), duplicates

    def validate_section_structure(self, section: dict) -> tuple[bool, Optional[str]]:
        required_keys = {"title", "content"}
        if not isinstance(section, dict):
            return False, "Section must be a dictionary"
        if not all(key in section for key in required_keys):
            missing = required_keys - set(section.keys())
            return False, f"Missing required keys: {missing}"
        if not isinstance(section["title"], str) or not section["title"].strip():
            return False, "Section title must be non-empty string"
        if not isinstance(section["content"], str) or not section["content"].strip():
            return False, "Section content must be non-empty string"
        return True, None

    def check_readability(self, content: str) -> tuple[bool, Optional[str]]:
        paragraphs = content.split("\n\n")
        long_paragraphs = [paragraph for paragraph in paragraphs if len(paragraph) > 500]
        if long_paragraphs:
            return True, f"Found {len(long_paragraphs)} very long paragraphs (>500 chars)"
        words = len(content.split())
        if words < 50:
            return True, f"Content may be too brief: {words} words"
        return True, None

    def validate_all(self, document_content: str, sections: list[dict]) -> dict[str, Any]:
        results: dict[str, Any] = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "checks": {},
        }

        valid, error = self.validate_content_length(document_content)
        results["checks"]["content_length"] = valid
        if not valid:
            results["is_valid"] = False
            results["errors"].append(error)

        valid, error = self.validate_section_count(sections)
        results["checks"]["section_count"] = valid
        if not valid:
            results["is_valid"] = False
            results["errors"].append(error)

        valid, empty_sections = self.validate_no_empty_sections(sections)
        results["checks"]["no_empty_sections"] = valid
        if not valid:
            results["is_valid"] = False
            results["errors"].extend([f"Empty section: {item}" for item in empty_sections])

        valid, duplicates = self.validate_no_duplicates(sections)
        results["checks"]["no_duplicates"] = valid
        if not valid:
            results["is_valid"] = False
            results["errors"].extend([f"Duplicate sections: {item}" for item in duplicates])

        structure_valid = True
        for section in sections:
            valid, error = self.validate_section_structure(section)
            if not valid:
                structure_valid = False
                results["is_valid"] = False
                results["errors"].append(error)
        results["checks"]["section_structure"] = structure_valid

        valid, warning = self.check_readability(document_content)
        results["checks"]["readability"] = valid
        if warning:
            results["warnings"].append(warning)

        logger.info("Validation complete - Valid: %s", results["is_valid"])
        return results
