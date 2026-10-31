
from unittest.mock import patch

from agents.orchestrator import run_investigation
from agents.schemas import (
    EvidenceReview,
    RiskAssessment,
    SecurityReport,
)


def test_invalid_url_stops_before_ai():
    with patch(
        "agents.orchestrator.generate_structured"
    ) as mock_ai:
        result = run_investigation("not-a-url")

    assert result["valid"] is False
    mock_ai.assert_not_called()


def test_agents_work_together():
    review = EvidenceReview(
        supported_claims=["The URL uses HTTP."],
        unsupported_claims=["The site is confirmed malicious."],
        confidence="Medium",
    )

    assessment = RiskAssessment(
        risk_score=20,
        risk_level="Moderate",
        rationale="Limited indicators are present.",
        recommendations=["Check an approved reputation source."],
    )

    report = SecurityReport(
        executive_summary="Limited indicators were found.",
        limitations=["No external reputation check was performed."],
        next_steps=["Verify with a trusted threat intelligence source."],
    )

    with patch(
        "agents.orchestrator.generate_structured",
        side_effect=[review, assessment, report],
    ) as mock_ai:
        result = run_investigation("http://example.com")

    assert result["valid"] is True
    assert result["ai_report"] == report.executive_summary
    assert result["agent_review"]["confidence"] == "Medium"
    assert len(result["ai_recommendations"]) == 1
    assert mock_ai.call_count == 3
