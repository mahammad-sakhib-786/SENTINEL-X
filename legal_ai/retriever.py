from legal_ai.vector_store import get_vector_store


def get_retriever(document_id: str):
    """
    Create a retriever restricted to one uploaded contract.

    Args:
        document_id: Unique ID of the contract.

    Returns:
        A Chroma retriever configured for similarity search.
    """
    if not document_id or not document_id.strip():
        raise ValueError("document_id cannot be empty.")

    db = get_vector_store()

    return db.as_retriever(
        search_type="similarity",
        search_kwargs={
            "k": 4,
            "filter": {
                "document_id": document_id
            },
        },
    )