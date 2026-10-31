from langchain_core.documents import Document
from legal_ai.compliance_checker import calculate_contract_risk_score

from legal_ai.compliance_checker import check_contract_compliance


def test_compliance_checker_detects_contract_clauses():
    chunks = [
        Document(
            page_content=(
                "Either party may terminate this agreement "
                "with 30 days written notice."
            ),
            metadata={
                "page_number": 1,
                "clause_number": "5.1",
            },
        ),
        Document(
            page_content=(
                "Both parties must maintain confidentiality "
                "of sensitive business information."
            ),
            metadata={
                "page_number": 2,
                "clause_number": "6.1",
            },
        ),
        Document(
            page_content=(
                "All disputes shall be resolved through arbitration."
            ),
            metadata={
                "page_number": 3,
                "clause_number": "7.1",
            },
        ),
    ]

    results = check_contract_compliance(chunks)

    assert results["termination_clause"]["status"] == "REVIEW_INDICATED"
    assert results["confidentiality_clause"]["status"] == "REVIEW_INDICATED"
    assert results["dispute_resolution_clause"]["status"] == "REVIEW_INDICATED"

    assert results["data_protection_clause"]["status"] == "NOT_FOUND_IN_REVIEWED_TEXT"
    assert results["liability_clause"]["status"] == "NOT_FOUND_IN_REVIEWED_TEXT"

    termination_evidence = results["termination_clause"]["evidence"]

    assert termination_evidence[0]["page"] == 1
    assert termination_evidence[0]["clause"] == "5.1"

    print("SUCCESS: Termination clause detected")
    print("SUCCESS: Confidentiality clause detected")
    print("SUCCESS: Dispute resolution clause detected")
    print("SUCCESS: Evidence metadata verified")


def test_compliance_checker_rejects_empty_chunks():
    try:
        check_contract_compliance([])
    except ValueError as error:
        assert str(error) == "Contract chunks cannot be empty."
    else:
        raise AssertionError("Expected ValueError for empty chunks")



def test_compliance_checker_classifies_primary_and_supporting_evidence():
    chunks = [
        Document(
            page_content=(
                "9. Limitation of Liability. "
                "Neither party is liable for indirect damages."
            ),
            metadata={
                "page_number": 2,
                "clause_number": "9",
                "clause_title": "Limitation of Liability",
            },
        ),
        Document(
            page_content=(
                "The parties agree to perform their obligations."
            ),
            metadata={
                "page_number": 1,
                "clause_number": "Unnumbered",
                "clause_title": "",
            },
        ),
    ]

    results = check_contract_compliance(chunks)
    evidence = results["liability_clause"]["evidence"]

    assert evidence[0]["evidence_type"] == "MATCHING_CLAUSE_HEADING"
    assert evidence[0]["page"] == 2
    assert evidence[0]["clause"] == "9"

    print("SUCCESS: Primary evidence classification verified")

def test_risk_score_rewards_primary_evidence():
    results = {
        "liability_clause": {
            "description": "Limitation of liability provisions",
            "evidence": [
                {"evidence_type": "MATCHING_CLAUSE_HEADING"}
            ],
        },
        "termination_clause": {
            "description": "Termination provisions",
            "evidence": [],
        },
    }

    score = calculate_contract_risk_score(results)

    assert score["review_score"] == 50
    assert score["category_scores"]["liability_clause"]["score"] == 0
    assert score["category_scores"]["termination_clause"]["score"] == 20


def test_risk_score_distinguishes_supporting_evidence():
    results = {
        "liability_clause": {
            "description": "Limitation of liability provisions",
            "evidence": [
                {"evidence_type": "SUPPORTING_KEYWORD_MENTION"}
            ],
        },
    }

    score = calculate_contract_risk_score(results)

    assert score["review_score"] == 75
    assert (
        score["category_scores"]["liability_clause"]["status"]
        == "SUPPORTING_EVIDENCE_ONLY"
    )
if __name__ == "__main__":
    test_compliance_checker_detects_contract_clauses()
    test_compliance_checker_rejects_empty_chunks()
    test_compliance_checker_classifies_primary_and_supporting_evidence()
    test_risk_score_rewards_primary_evidence()
    test_risk_score_distinguishes_supporting_evidence()