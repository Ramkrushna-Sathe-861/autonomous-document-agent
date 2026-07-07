"""
Request schemas for API endpoints.

Purpose: Define input contracts for API endpoints.
Responsibility: Validate incoming requests using Pydantic v2.
"""

from pydantic import BaseModel, Field


class DocumentRequest(BaseModel):
    """Request to generate a document."""

    request: str = Field(
        ...,
        min_length=10,
        max_length=2000,
        description="Natural language description of the document to generate",
        examples=["Create a project proposal for a Hospital Management System"],
    )

    class Config:
        """Pydantic configuration."""

        json_schema_extra = {
            "example": {
                "request": "Create a project proposal for a Hospital Management System"
            }
        }
