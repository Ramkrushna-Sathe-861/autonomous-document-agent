"""
Response schemas for API endpoints.

Purpose: Define output contracts for API endpoints.
Responsibility: Provide type-safe response models with OpenAPI documentation.
"""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class ExecutionStep(BaseModel):
    """A single step in the execution plan."""

    step_number: int = Field(..., description="Sequential step number")
    action: str = Field(..., description="Action to perform")
    description: str = Field(..., description="Detailed description of the step")
    dependencies: list[int] = Field(
        default_factory=list, description="Step numbers this step depends on"
    )


class ExecutionPlan(BaseModel):
    """Structured execution plan for document generation."""

    document_type: str = Field(..., description="Type of document to generate")
    document_title: str = Field(..., description="Title of the final document")
    assumptions: list[str] = Field(
        default_factory=list,
        description="Reasonable assumptions made when the request is incomplete",
    )
    total_steps: int = Field(..., description="Total number of execution steps")
    steps: list[ExecutionStep] = Field(..., description="List of execution steps")
    estimated_sections: int = Field(
        ..., description="Estimated number of sections in final document"
    )


class ExecutorResult(BaseModel):
    """Result of executor agent execution."""

    section_title: str = Field(..., description="Title of the generated section")
    content: str = Field(..., description="Generated content for the section")
    status: str = Field(
        ..., description="Status of generation", pattern="^(success|failed)$"
    )
    error_message: Optional[str] = Field(None, description="Error message if failed")


class ReflectionResult(BaseModel):
    """Result of reflection agent validation."""

    status: str = Field(
        ..., description="Validation status", pattern="^(PASS|FAIL)$"
    )
    issues: list[str] = Field(
        default_factory=list, description="List of identified issues"
    )
    suggestions: list[str] = Field(
        default_factory=list, description="Suggestions for improvement"
    )
    confidence_score: float = Field(
        ..., ge=0.0, le=1.0, description="Confidence in validation (0-1)"
    )
    revised: bool = Field(
        default=False, description="Whether a revision pass was performed"
    )


class DocumentResponse(BaseModel):
    """Successful document generation response."""

    status: str = Field(..., description="Operation status", pattern="^(completed)$")
    execution_plan: ExecutionPlan = Field(..., description="Executed planning")
    summary: str = Field(..., description="Summary of generated document")
    document_path: str = Field(..., description="Path to generated DOCX file")
    document_url: str = Field(..., description="API URL for downloading the DOCX file")
    reflection_result: ReflectionResult = Field(
        ..., description="Reflection agent validation result"
    )
    generated_at: datetime = Field(..., description="Timestamp of generation")


class ErrorResponse(BaseModel):
    """Error response."""

    status: str = Field(..., description="Error status", pattern="^(error)$")
    error_code: str = Field(..., description="Application-specific error code")
    message: str = Field(..., description="Error message")
    details: Optional[dict[str, Any]] = Field(None, description="Additional details")
