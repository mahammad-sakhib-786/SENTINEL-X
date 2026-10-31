
from typing import Literal

from pydantic import BaseModel, Field


class EvidenceReview(BaseModel):
    supported_claims: list[str] = Field(
        description="Claims directly supported by supplied evidence"
    )
    unsupported_claims: list[str] = Field(
        description="Claims not established by supplied evidence"
    )
    confidence: Literal["Low", "Medium", "High"]


class RiskAssessment(BaseModel):
    risk_score: int = Field(ge=0, le=100)
    risk_level: Literal[
        "Low", "Moderate", "High", "Critical"
    ]
    rationale: str
    recommendations: list[str]


class SecurityReport(BaseModel):
    executive_summary: str
    limitations: list[str]
    next_steps: list[str]
