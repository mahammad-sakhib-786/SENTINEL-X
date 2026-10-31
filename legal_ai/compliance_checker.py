
from langchain_core.documents import Document


COMPLIANCE_CHECKLIST = {
    "termination_clause": {
        "description": "Termination and exit provisions",
        "keywords": [
            "termination",
            "terminate",
            "notice period",
            "early termination",
            "expiry",
        ],
        "heading_keywords": [
            "termination",
            "term and termination",
        ],
    },
    "confidentiality_clause": {
        "description": "Confidentiality obligations",
        "keywords": [
            "confidential",
            "confidentiality",
            "non-disclosure",
            "proprietary information",
        ],
        "heading_keywords": [
            "confidentiality",
            "non-disclosure",
        ],
    },
    "data_protection_clause": {
        "description": "Data protection and privacy provisions",
        "keywords": [
            "personal data",
            "data protection",
            "privacy",
            "data processing",
            "security of data",
        ],
        "heading_keywords": [
            "data protection",
            "privacy",
            "data security",
        ],
    },
    "liability_clause": {
        "description": "Limitation of liability provisions",
        "keywords": [
            "limitation of liability",
            "liability",
            "indirect damages",
            "consequential damages",
        ],
        "heading_keywords": [
            "limitation of liability",
            "liability",
        ],
    },
    "dispute_resolution_clause": {
        "description": "Dispute resolution provisions",
        "keywords": [
            "dispute resolution",
            "arbitration",
            "jurisdiction",
            "governing law",
            "mediation",
        ],
        "heading_keywords": [
            "dispute resolution",
            "governing law",
            "arbitration",
        ],
    },
}


def check_contract_compliance(chunks: list[Document]) -> dict:
    """
    Check contract chunks for indicators of common legal provisions.

    Prioritizes evidence from matching clause headings.
    Other keyword matches are retained but identified as
    supporting mentions rather than confirmed clause headings.

    This is a preliminary checklist, not a legal determination.
    """

    if not chunks:
        raise ValueError("Contract chunks cannot be empty.")

    results = {}

    for check_id, check in COMPLIANCE_CHECKLIST.items():
        heading_evidence = []
        supporting_evidence = []

        for chunk in chunks:
            text = chunk.page_content.lower()

            matched_keywords = [
                keyword
                for keyword in check["keywords"]
                if keyword in text
            ]

            if not matched_keywords:
                continue

            clause_title = chunk.metadata.get(
                "clause_title", ""
            ).lower()

            heading_match = any(
                keyword in clause_title
                for keyword in check["heading_keywords"]
            )

            evidence_item = {
                "page": chunk.metadata.get(
                    "page_number",
                    chunk.metadata.get("page", "Unknown"),
                ),
                "clause": chunk.metadata.get(
                    "clause_number", "Unknown"
                ),
                "matched_keywords": matched_keywords,
                "text": chunk.page_content,
                "evidence_type": (
                    "MATCHING_CLAUSE_HEADING"
                    if heading_match
                    else "SUPPORTING_KEYWORD_MENTION"
                ),
            }

            if heading_match:
                heading_evidence.append(evidence_item)
            else:
                supporting_evidence.append(evidence_item)

        evidence = heading_evidence + supporting_evidence

        results[check_id] = {
            "description": check["description"],
            "status": (
                "REVIEW_INDICATED"
                if evidence
                else "NOT_FOUND_IN_REVIEWED_TEXT"
            ),
            "evidence": evidence,
        }

    return results

def calculate_contract_risk_score(results: dict) -> dict:
    """
    Calculate a preliminary evidence-based review score.

    This score measures missing evidence indicators.
    It is not a legal compliance or legal risk determination.
    """

    total_categories = len(results)

    if total_categories == 0:
        raise ValueError("Compliance results cannot be empty.")

    category_scores = {}
    total_score = 0

    for check_id, result in results.items():

        evidence = result.get("evidence", [])

        has_primary_evidence = any(
            item.get("evidence_type") == "MATCHING_CLAUSE_HEADING"
            for item in evidence
        )

        has_supporting_evidence = any(
            item.get("evidence_type") == "SUPPORTING_KEYWORD_MENTION"
            for item in evidence
        )

        if has_primary_evidence:
            score = 0
            status = "PRIMARY_EVIDENCE_FOUND"

        elif has_supporting_evidence:
            score = 5
            status = "SUPPORTING_EVIDENCE_ONLY"

        else:
            score = 20
            status = "NO_MATCHING_EVIDENCE"

        category_scores[check_id] = {
            "description": result["description"],
            "score": score,
            "status": status,
        }

        total_score += score

    maximum_score = total_categories * 20

    review_score = round(
        100 * (1 - total_score / maximum_score)
    )

    return {
        "review_score": review_score,
        "total_categories": total_categories,
        "category_scores": category_scores,
        "disclaimer": (
            "This is an automated evidence-coverage indicator, "
            "not a legal risk score or compliance determination. "
            "Human review is required."
        ),
    }
