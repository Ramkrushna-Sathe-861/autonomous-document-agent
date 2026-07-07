"""
Request schemas for API endpoints.

Purpose: Define input contracts for API endpoints.
Responsibility: Validate incoming requests using Pydantic v2.
"""

from pydantic import BaseModel, ConfigDict, Field, field_validator


class DocumentRequest(BaseModel):
    """Request to generate a document."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "request": "Create a project proposal for a Hospital Management System"
            }
        }
    )

    request: str = Field(
        ...,
        min_length=10,
        max_length=2000,
        description="Natural language description of the document to generate",
        examples=["Create a project proposal for a Hospital Management System"],
    )

    @field_validator("request")
    @classmethod
    def normalize_request(cls, value: str) -> str:
        value = " ".join(value.split())
        if not any(character.isalpha() for character in value):
            raise ValueError("request must contain a meaningful natural-language instruction")
        return value
