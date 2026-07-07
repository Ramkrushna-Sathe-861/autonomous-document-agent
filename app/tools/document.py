"""
Document generation tool using python-docx.

Purpose: Encapsulate all DOCX file operations with professional formatting.
Responsibility: Create, format, and save Word documents with structured content.
"""

import logging
from pathlib import Path
from typing import Optional

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches, Pt, RGBColor
from docx.enum.dml import MSO_THEME_COLOR

from app.config import get_settings
from app.core.exceptions import DocumentGenerationError

logger = logging.getLogger(__name__)


class DocumentTool:
    """Professional Word document generation and formatting."""

    def __init__(self):
        """Initialize document tool with settings."""
        self.settings = get_settings()
        self.output_dir = self.settings.get_output_path()
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def create_document(
        self, title: str, author: str = "", company: str = ""
    ) -> Document:
        """
        Create a new Word document with professional formatting.

        Args:
            title: Document title
            author: Document author
            company: Company name

        Returns:
            Configured Document object

        Raises:
            DocumentGenerationError: If document creation fails
        """
        try:
            doc = Document()

            # Configure document properties
            core_props = doc.core_properties
            core_props.author = author or self.settings.document_author
            core_props.company = company or self.settings.document_company
            core_props.title = title

            # Add title
            title_paragraph = doc.add_paragraph(title)
            title_run = title_paragraph.runs[0]
            title_run.font.size = Pt(24)
            title_run.font.bold = True
            title_run.font.color.rgb = RGBColor(31, 78, 121)
            title_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER

            # Add spacing after title
            doc.add_paragraph()

            logger.debug(f"Document created with title: {title}")
            return doc

        except Exception as e:
            logger.error(f"Failed to create document: {str(e)}")
            raise DocumentGenerationError(f"Document creation failed: {str(e)}")

    def add_heading(self, doc: Document, text: str, level: int = 1) -> None:
        """
        Add a heading to the document.

        Args:
            doc: Document object
            text: Heading text
            level: Heading level (1-3)

        Raises:
            DocumentGenerationError: If heading addition fails
        """
        try:
            heading = doc.add_heading(text, level=level)
            heading_run = heading.runs[0] if heading.runs else None

            if heading_run:
                if level == 1:
                    heading_run.font.color.rgb = RGBColor(31, 78, 121)
                    heading_run.font.size = Pt(18)
                elif level == 2:
                    heading_run.font.color.rgb = RGBColor(68, 114, 196)
                    heading_run.font.size = Pt(14)
                else:
                    heading_run.font.color.rgb = RGBColor(112, 144, 192)
                    heading_run.font.size = Pt(12)

            logger.debug(f"Added heading level {level}: {text}")

        except Exception as e:
            logger.error(f"Failed to add heading: {str(e)}")
            raise DocumentGenerationError(f"Heading addition failed: {str(e)}")

    def add_paragraph(
        self, doc: Document, text: str, style: Optional[str] = None
    ) -> None:
        """
        Add a paragraph to the document.

        Args:
            doc: Document object
            text: Paragraph text
            style: Optional paragraph style

        Raises:
            DocumentGenerationError: If paragraph addition fails
        """
        try:
            paragraph = doc.add_paragraph(text, style=style)

            for run in paragraph.runs:
                run.font.name = self.settings.document_font_name
                run.font.size = Pt(self.settings.document_font_size)

            logger.debug(f"Added paragraph: {text[:50]}...")

        except Exception as e:
            logger.error(f"Failed to add paragraph: {str(e)}")
            raise DocumentGenerationError(f"Paragraph addition failed: {str(e)}")

    def add_bulleted_list(self, doc: Document, items: list[str]) -> None:
        """
        Add a bulleted list to the document.

        Args:
            doc: Document object
            items: List of bullet points

        Raises:
            DocumentGenerationError: If list addition fails
        """
        try:
            for item in items:
                p = doc.add_paragraph(item, style="List Bullet")
                for run in p.runs:
                    run.font.name = self.settings.document_font_name
                    run.font.size = Pt(self.settings.document_font_size)

            logger.debug(f"Added bulleted list with {len(items)} items")

        except Exception as e:
            logger.error(f"Failed to add bulleted list: {str(e)}")
            raise DocumentGenerationError(f"Bulleted list addition failed: {str(e)}")

    def add_numbered_list(self, doc: Document, items: list[str]) -> None:
        """
        Add a numbered list to the document.

        Args:
            doc: Document object
            items: List of items

        Raises:
            DocumentGenerationError: If list addition fails
        """
        try:
            for item in items:
                p = doc.add_paragraph(item, style="List Number")
                for run in p.runs:
                    run.font.name = self.settings.document_font_name
                    run.font.size = Pt(self.settings.document_font_size)

            logger.debug(f"Added numbered list with {len(items)} items")

        except Exception as e:
            logger.error(f"Failed to add numbered list: {str(e)}")
            raise DocumentGenerationError(f"Numbered list addition failed: {str(e)}")

    def add_table(
        self, doc: Document, rows: int, cols: int, headers: Optional[list[str]] = None
    ) -> None:
        """
        Add a table to the document.

        Args:
            doc: Document object
            rows: Number of rows
            cols: Number of columns
            headers: Optional header row

        Raises:
            DocumentGenerationError: If table addition fails
        """
        try:
            table = doc.add_table(rows=rows, cols=cols)
            table.style = "Table Grid"

            if headers:
                header_cells = table.rows[0].cells
                for i, header in enumerate(headers):
                    if i < len(header_cells):
                        header_cells[i].text = header
                        for paragraph in header_cells[i].paragraphs:
                            for run in paragraph.runs:
                                run.font.bold = True

            logger.debug(f"Added table: {rows}x{cols}")

        except Exception as e:
            logger.error(f"Failed to add table: {str(e)}")
            raise DocumentGenerationError(f"Table addition failed: {str(e)}")

    def add_page_break(self, doc: Document) -> None:
        """
        Add a page break to the document.

        Args:
            doc: Document object

        Raises:
            DocumentGenerationError: If page break addition fails
        """
        try:
            doc.add_page_break()
            logger.debug("Added page break")

        except Exception as e:
            logger.error(f"Failed to add page break: {str(e)}")
            raise DocumentGenerationError(f"Page break addition failed: {str(e)}")

    def save_document(self, doc: Document, filename: str) -> Path:
        """
        Save document to file.

        Args:
            doc: Document object
            filename: Output filename (with .docx extension)

        Returns:
            Path to saved document

        Raises:
            DocumentGenerationError: If document save fails
        """
        try:
            # Ensure .docx extension
            if not filename.endswith(".docx"):
                filename = f"{filename}.docx"

            file_path = self.output_dir / filename

            # Remove existing file if present
            if file_path.exists():
                file_path.unlink()

            doc.save(str(file_path))
            logger.info(f"Document saved: {file_path}")

            return file_path

        except Exception as e:
            logger.error(f"Failed to save document: {str(e)}")
            raise DocumentGenerationError(f"Document save failed: {str(e)}")
