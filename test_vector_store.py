from langchain_core.documents import Document

from legal_ai.vector_store import (
    create_vector_store,
    get_vector_store,
)


def test_vector_store_persistence():
    document_id = "sentinel_test_contract_001"

    chunks = [
        Document(
            page_content=(
                "The agreement may be terminated by either party "
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
                "of all sensitive business information."
            ),
            metadata={
                "page_number": 2,
                "clause_number": "6.1",
            },
        ),
    ]

    # Store the test documents.
    db = create_vector_store(chunks, document_id)

    # Reopen the database to verify persistence.
    reopened_db = get_vector_store()

    results = reopened_db.similarity_search(
        "What is the termination notice period?",
        k=2,
        filter={"document_id": document_id},
    )

    assert len(results) > 0
    assert any("30 days" in doc.page_content for doc in results)

    print("SUCCESS: Documents stored in Chroma")
    print("SUCCESS: Persistent database reopened")
    print("SUCCESS: Relevant contract text retrieved")

    for result in results:
        print("Page:", result.metadata.get("page_number"))
        print("Clause:", result.metadata.get("clause_number"))
        print("Content:", result.page_content)


if __name__ == "__main__":
    test_vector_store_persistence()