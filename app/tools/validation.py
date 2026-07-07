"""
Validation tool for content quality checks.

Purpose: Validate generated document content against quality standards.
Responsibility: Check for duplicates, empty content, length requirements, section counts.
"""

import logging
import re
from typing import Optional

from app.config import get_settings
from app.core.exceptions import ValidationError

logger = logging.getLogger(__name__)


class ValidationTool:
    """Content validation and quality checking."""

    def __init__(self):
        """Initialize validation tool with settings."""
        self.settings = get_settings()

    def validate_content_length(self, content: str) -> tuple[bool, Optional[str]]:
        """
        Validate content length against configured limits.

        Args:
            content: Content to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        content_length = len(content)

        if content_length < self.settings.min_document_length:
            error = f"Content too short: {content_length} chars (min: {self.settings.min_document_length})"
            logger.warning(error)
            return False, error

        if content_length > self.settings.max_document_length:
            error = f"Content too long: {content_length} chars (max: {self.settings.max_document_length})"
            logger.warning(error)
            return False, error

        logger.debug(f"Content length valid: {content_length} chars")
        return True, None

    def validate_section_count(self, sections: list[dict]) -> tuple[bool, Optional[str]]:
        """
        Validate number of sections.

        Args:
            sections: List of document sections

        Returns:
            Tuple of (is_valid, error_message)
        """
        section_count = len(sections)

        if section_count == 0:
            error = "No sections found in document"
            logger.warning(error)
            return False, error

        if section_count > self.settings.max_document_sections:
            error = f"Too many sections: {section_count} (max: {self.settings.max_document_sections})"
            logger.warning(error)
            return False, error

        logger.debug(f"Section count valid: {section_count} sections")
        return True, None

    def validate_no_empty_sections(self, sections: list[dict]) -> tuple[bool, list[str]]:
        """
        Check for empty sections.

        Args:
            sections: List of document sections

        Returns:
            Tuple of (is_valid, list_of_empty_sections)
        """
        empty_sections = []

        for i, section in enumerate(sections, 1):
            title = section.get("title", f"Section {i}")
            content = section.get("content", "").strip()

            if not content or len(content) < 10:
                empty_sections.append(f"{i}. {title}")

        if empty_sections:
            logger.warning(f"Found {len(empty_sections)} empty sections")
            return False, empty_sections

        logger.debug("No empty sections found")
        return True, []

    def validate_no_duplicates(self, sections: list[dict]) -> tuple[bool, list[tuple[int, int]]]:
        """
        Check for duplicate sections.

        Args:
            sections: List of document sections

        Returns:
            Tuple of (is_valid, list_of_duplicate_indices)
        """
        duplicates = []
        section_hashes = {}

        for i, section in enumerate(sections):
            content = section.get("content", "").strip().lower()

            # Simple hash for comparison
            content_hash = hash(content)

            if content_hash in section_hashes:
                duplicates.append((section_hashes[content_hash], i))
            else:
                section_hashes[content_hash] = i

        if duplicates:
            logger.warning(f"Found {len(duplicates)} duplicate sections")
            return False, duplicates

        logger.debug("No duplicate sections found")
        return True, []

    def validate_section_structure(
        self, section: dict
    ) -> tuple[bool, Optional[str]]:
        """
        Validate individual section structure.

        Args:
            section: Section dictionary

        Returns:
            Tuple of (is_valid, error_message)
        """
        required_keys = {"title", "content"}

        if not isinstance(section, dict):
            return False, "Section must be a dictionary"

        if not all(key in section for key in required_keys):
            missing = required_keys - set(section.keys())
            error = f"Missing required keys: {missing}"
            return False, error

        if not isinstance(section["title"], str) or not section["title"].strip():
            return False, "Section title must be non-empty string"

        if not isinstance(section["content"], str) or not section["content"].strip():
            return False, "Section content must be non-empty string"

        return True, None

    def check_readability(self, content: str) -> tuple[bool, Optional[str]]:
        """
        Check content readability metrics.

        Args:
            content: Content to check

        Returns:
            Tuple of (is_valid, warning_message)
        """
        # Check for excessive paragraph length (> 500 chars)
        paragraphs = content.split("\n\n")
        long_paragraphs = [p for p in paragraphs if len(p) > 500]

        if long_paragraphs:
            warning = f"Found {len(long_paragraphs)} very long paragraphs (>500 chars)"
            logger.debug(warning)
            return True, warning

        # Check for minimum content substance
        words = len(content.split())
        if words < 50:
            warning = f"Content may be too brief: {words} words"
            logger.debug(warning)
            return True, warning

        logger.debug("Readability check passed")
        return True, None

    def validate_all(
        self, document_content: str, sections: list[dict]
    ) -> dict[str, any]:
        """
        Run all validation checks.

        Args:
            document_content: Full document content
            sections: List of document sections

        Returns:
            Validation result dictionary
        """
        results = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "checks": {},
        }

        # Check content length
        valid, error = self.validate_content_length(document_content)
        results["checks"]["content_length"] = valid
        if not valid:
            results["is_valid"] = False
            results["errors"].append(error)

        # Check section count
        valid, error = self.validate_section_count(sections)
        results["checks"]["section_count"] = valid
        if not valid:
            results["is_valid"] = False
            results["errors"].append(error)

        # Check for empty sections
        valid, empty_sections = self.validate_no_empty_sections(sections)
        results["checks"]["no_empty_sections"] = valid
        if not valid:
            results["errors"].extend(
                [f"Empty section: {s}" for s in empty_sections]
            )

        # Check for duplicates
        valid, duplicates = self.validate_no_duplicates(sections)
        results["checks"]["no_duplicates"] = valid
        if not valid:
            results["errors"].extend(
                [f"Duplicate sections: {d}" for d in duplicates]
            )

        # Check section structures
        structure_valid = True
        for section in sections:
            valid, error = self.validate_section_structure(section)
            if not valid:
                structure_valid = False
                results["errors"].append(error)
        results["checks"]["section_structure"] = structure_valid

        # Check readability
        valid, warning = self.check_readability(document_content)
        results["checks"]["readability"] = valid
        if warning:
            results["warnings"].append(warning)

        logger.info(f"Validation complete - Valid: {results['is_valid']}")
        return results
