from langchain_core.documents import Document

from legal_ai.vector_store import create_vector_store
from legal_ai.retriever import get_retriever


def test_retriever_returns_relevant_contract_clause():
    document_id = "retriever_test_contract_001"

    chunks = [
        Document(
            page_content=(
                "Either party may terminate this agreement "
                "by providing 30 days written notice."
            ),
            metadata={
                "page_number": 1,
                "clause_number": "5.1",
            },
        ),
        Document(
            page_content=(
                "Both parties must protect confidential "
                "business information."
            ),
            metadata={
                "page_number": 2,
                "clause_number": "6.1",
            },
        ),
    ]

    create_vector_store(chunks, document_id)

    retriever = get_retriever(document_id)

    results = retriever.invoke(
        "How many days notice is required for termination?"
    )

    assert len(results) > 0

    assert any(
        "30 days" in doc.page_content
        for doc in results
    )

    assert all(
        doc.metadata.get("document_id") == document_id
        for doc in results
    )

    print("SUCCESS: Relevant clause retrieved")
    print("SUCCESS: Document isolation verified")


if __name__ == "__main__":
    test_retriever_returns_relevant_contract_clause()