
import re
from typing import Any

from langchain_core.documents import Document


# ---------------------------------------------------------
# 1. COMPLIANCE CHECKLIST CONFIGURATION
# ---------------------------------------------------------

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
        "recommendation": (
            "Review termination rights, notice periods, termination "
            "events, cure periods, and post-termination obligations."
        ),
        "review_questions": [
            "Are termination rights defined for both parties?",
            "Are notice periods and termination procedures specified?",
            "Are consequences of termination explained?",
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
        "recommendation": (
            "Review the definition of confidential information, "
            "permitted disclosures, protection obligations, and "
            "confidentiality duration."
        ),
        "review_questions": [
            "Is confidential information clearly defined?",
            "Are permitted disclosures addressed?",
            "Are confidentiality obligations and their duration specified?",
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
        "recommendation": (
            "Review personal-data handling, security safeguards, "
            "data-processing responsibilities, and incident reporting."
        ),
        "review_questions": [
            "Are personal-data processing responsibilities described?",
            "Are security safeguards addressed?",
            "Are data incidents and reporting obligations covered?",
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
        "recommendation": (
            "Review liability caps, excluded damages, exceptions, "
            "and whether the allocation of liability is clear."
        ),
        "review_questions": [
            "Is a liability limit specified?",
            "Are excluded damages identified?",
            "Are exceptions to the limitation explained?",
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
        "recommendation": (
            "Review the dispute escalation process, applicable law, "
            "jurisdiction, arbitration arrangements, and relevant procedures."
        ),
        "review_questions": [
            "Is the dispute resolution process described?",
            "Is governing law identified?",
            "Is jurisdiction or an arbitration procedure specified?",
        ],
    },
}


# ---------------------------------------------------------
# 2. TEXT NORMALIZATION AND MATCHING
# ---------------------------------------------------------

def normalize_text(value: str) -> str:
    """Normalize text for consistent keyword matching."""

    if not isinstance(value, str):
        return ""

    value = value.lower()
    value = re.sub(r"\s+", " ", value)

    return value.strip()


def contains_phrase(text: str, phrase: str) -> bool:
    """Match a complete word or phrase rather than a substring."""

    normalized_text = normalize_text(text)
    normalized_phrase = normalize_text(phrase)

    if not normalized_text or not normalized_phrase:
        return False

    pattern = (
        r"(?<!\w)"
        + re.escape(normalized_phrase)
        + r"(?!\w)"
    )

    return bool(re.search(pattern, normalized_text))


# ---------------------------------------------------------
# 3. EVIDENCE EXTRACTION
# ---------------------------------------------------------

def extract_category_evidence(
    chunks: list[Document],
    check: dict,
) -> list[dict]:
    """Extract heading and supporting evidence for one category."""

    evidence_items = []
    seen_evidence = set()

    for chunk in chunks:
        if not isinstance(chunk, Document):
            continue

        content = chunk.page_content

        if not isinstance(content, str) or not content.strip():
            continue

        metadata = chunk.metadata or {}

        matched_keywords = [
            keyword
            for keyword in check["keywords"]
            if contains_phrase(content, keyword)
        ]

        if not matched_keywords:
            continue

        clause_title = metadata.get("clause_title", "")

        matched_heading_keywords = [
            keyword
            for keyword in check["heading_keywords"]
            if contains_phrase(clause_title, keyword)
        ]

        heading_match = bool(matched_heading_keywords)

        evidence_type = (
            "MATCHING_CLAUSE_HEADING"
            if heading_match
            else "SUPPORTING_KEYWORD_MENTION"
        )

        page = metadata.get(
            "page_number",
            metadata.get("page", "Unknown"),
        )

        clause = metadata.get("clause_number", "Unknown")

        # Avoid duplicate evidence entries.
        evidence_key = (
            str(page),
            str(clause),
            evidence_type,
            normalize_text(content),
        )

        if evidence_key in seen_evidence:
            continue

        seen_evidence.add(evidence_key)

        evidence_items.append({
            "page": page,
            "clause": clause,
            "clause_title": clause_title,
            "matched_keywords": matched_keywords,
            "matched_heading_keywords": matched_heading_keywords,
            "text": content,
            "evidence_type": evidence_type,
            "evidence_strength": (
                "HEADING_MATCH"
                if heading_match
                else "SUPPORTING_TEXT_MATCH"
            ),
        })

    # Primary heading evidence appears before supporting mentions.
    evidence_items.sort(
        key=lambda item: (
            item["evidence_type"] != "MATCHING_CLAUSE_HEADING",
            str(item["page"]),
        )
    )

    return evidence_items


# ---------------------------------------------------------
# 4. FINDING CLASSIFICATION
# ---------------------------------------------------------

def classify_finding(evidence: list[dict]) -> dict:
    """
    Classify detected evidence.

    These classifications describe evidence detection only.
    They do not establish legal compliance.
    """

    has_heading = any(
        item["evidence_type"] == "MATCHING_CLAUSE_HEADING"
        for item in evidence
    )

    has_supporting_text = any(
        item["evidence_type"] == "SUPPORTING_KEYWORD_MENTION"
        for item in evidence
    )

    if has_heading and has_supporting_text:
        return {
            "evidence_status": "HEADING_AND_SUPPORTING_TEXT_FOUND",
            "status": "REVIEW_INDICATED",
            "explanation": (
                "A matching clause heading and supporting keyword "
                "mentions were detected. The clause still requires "
                "substantive review."
            ),
        }

    if has_heading:
        return {
            "evidence_status": "HEADING_FOUND",
            "status": "REVIEW_INDICATED",
            "explanation": (
                "A matching clause heading was detected. Its "
                "substantive contents should be reviewed."
            ),
        }

    if has_supporting_text:
        return {
            "evidence_status": "SUPPORTING_TEXT_ONLY",
            "status": "REVIEW_INDICATED",
            "explanation": (
                "Relevant keywords were detected in contract text, "
                "but a matching clause heading was not identified. "
                "The text may be a reference rather than a complete clause."
            ),
        }

    return {
        "evidence_status": "NO_MATCHING_EVIDENCE",
        "status": "NOT_FOUND_IN_REVIEWED_TEXT",
        "explanation": (
            "No matching keywords or clause heading were detected "
            "in the reviewed text. This does not prove that the "
            "provision is absent from the full agreement."
        ),
    }


# ---------------------------------------------------------
# 5. MAIN COMPLIANCE ENGINE
# ---------------------------------------------------------

def check_contract_compliance(
    chunks: list[Document],
) -> dict:
    """
    Perform a preliminary evidence-based contract review.

    Detects:
    - Matching clause headings.
    - Supporting keyword mentions.
    - Evidence classification.
    - Review explanations.
    - Suggested manual review actions.

    This is not a legal compliance determination.
    """

    if not chunks:
        raise ValueError("Contract chunks cannot be empty.")

    if not isinstance(chunks, list):
        raise TypeError("Chunks must be supplied as a list.")

    results = {}

    for check_id, check in COMPLIANCE_CHECKLIST.items():

        evidence = extract_category_evidence(
            chunks,
            check,
        )

        classification = classify_finding(evidence)

        results[check_id] = {
            "description": check["description"],
            "status": classification["status"],
            "evidence_status": classification["evidence_status"],
            "explanation": classification["explanation"],
            "recommendation": check["recommendation"],
            "review_questions": check["review_questions"],
            "evidence_count": len(evidence),
            "heading_evidence_count": sum(
                item["evidence_type"] == "MATCHING_CLAUSE_HEADING"
                for item in evidence
            ),
            "supporting_evidence_count": sum(
                item["evidence_type"] == "SUPPORTING_KEYWORD_MENTION"
                for item in evidence
            ),
            "evidence": evidence,
        }

    return results


# ---------------------------------------------------------
# 6. EVIDENCE COVERAGE SCORING
# ---------------------------------------------------------

def calculate_contract_risk_score(results: dict) -> dict:
    """
    Calculate a preliminary evidence-coverage score.

    IMPORTANT:
    This is NOT a legal risk score and NOT a compliance score.
    It only measures the presence of matching evidence indicators.
    """

    if not isinstance(results, dict) or not results:
        raise ValueError("Compliance results cannot be empty.")

    category_scores = {}
    total_score = 0

    counts = {
        "heading_found": 0,
        "supporting_text_only": 0,
        "no_matching_evidence": 0,
    }

    for check_id, result in results.items():

        evidence = result.get("evidence", [])

        has_heading = any(
            item.get("evidence_type") == "MATCHING_CLAUSE_HEADING"
            for item in evidence
        )

        has_supporting = any(
            item.get("evidence_type") == "SUPPORTING_KEYWORD_MENTION"
            for item in evidence
        )

        if has_heading:
            score = 0
            status = "HEADING_EVIDENCE_FOUND"
            counts["heading_found"] += 1

        elif has_supporting:
            score = 5
            status = "SUPPORTING_EVIDENCE_ONLY"
            counts["supporting_text_only"] += 1

        else:
            score = 20
            status = "NO_MATCHING_EVIDENCE"
            counts["no_matching_evidence"] += 1

        category_scores[check_id] = {
            "description": result.get("description", check_id),
            "score": score,
            "status": status,
            "evidence_count": len(evidence),
        }

        total_score += score

    total_categories = len(results)
    maximum_score = total_categories * 20

    review_score = round(
        100 * (1 - total_score / maximum_score)
    )

    categories_with_evidence = (
        counts["heading_found"]
        + counts["supporting_text_only"]
    )

    evidence_coverage = round(
        100 * categories_with_evidence / total_categories
    )

    return {
        "review_score": review_score,
        "evidence_coverage": evidence_coverage,
        "total_categories": total_categories,
        "categories_with_evidence": categories_with_evidence,
        "categories_without_matching_evidence": (
            counts["no_matching_evidence"]
        ),
        "evidence_counts": counts,
        "category_scores": category_scores,
        "score_description": (
            "Evidence coverage indicator based on matching headings "
            "and supporting keyword mentions."
        ),
        "disclaimer": (
            "This is an automated evidence-coverage indicator, "
            "not a legal risk score or compliance determination. "
            "Keyword matches do not establish legal sufficiency. "
            "Human review is required."
        ),
    }
