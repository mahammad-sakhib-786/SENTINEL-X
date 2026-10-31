from langchain_core.documents import Document
from legal_ai.clause_splitter import split_documents


def test_split_documents():
    docs = [
        Document(
            page_content=(
                "1. Confidentiality\n"
                "The parties must protect confidential information.\n\n"
                "2. Termination\n"
                "Either party may terminate this agreement."
            ),
            metadata={"page": 0}
        )
    ]

    chunks = split_documents(docs)

    assert len(chunks) > 0
    assert chunks[0].metadata["document_type"] == "legal"
    assert chunks[0].metadata["page_number"] == 1