from langchain_core.documents import Document


# Initial contract review checklist.
# These are review indicators, not legal conclusions.
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
    },
    "confidentiality_clause": {
        "description": "Confidentiality obligations",
        "keywords": [
            "confidential",
            "confidentiality",
            "non-disclosure",
            "proprietary information",
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
    },
    "liability_clause": {
        "description": "Limitation of liability provisions",
        "keywords": [
            "limitation of liability",
            "liability",
            "indirect damages",
            "consequential damages",
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
    },
}


def check_contract_compliance(chunks: list[Document]) -> dict:
    """
    Check contract text for indicators of common legal provisions.

    This is a preliminary checklist, not a legal compliance determination.
    """
    if not chunks:
        raise ValueError("Contract chunks cannot be empty.")

    results = {}

    for check_id, check in COMPLIANCE_CHECKLIST.items():
        evidence = []

        for chunk in chunks:
            text = chunk.page_content.lower()

            matched_keywords = [
                keyword
                for keyword in check["keywords"]
                if keyword in text
            ]

            if matched_keywords:
                evidence.append({
                    "page": chunk.metadata.get(
                        "page_number", "Unknown"
                    ),
                    "clause": chunk.metadata.get(
                        "clause_number", "Unknown"
                    ),
                    "matched_keywords": matched_keywords,
                    "text": chunk.page_content,
                })

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