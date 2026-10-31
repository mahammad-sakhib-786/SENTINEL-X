from pathlib import Path

from langchain_chroma import Chroma

from legal_ai.embeddings import embeddings


PROJECT_ROOT = Path(__file__).resolve().parent.parent

DB_PATH = PROJECT_ROOT / "data" / "chroma_db"

COLLECTION_NAME = "sentinel_legal_documents"


def get_vector_store() -> Chroma:
    """
    Open or create the persistent legal document vector store.
    """
    DB_PATH.mkdir(parents=True, exist_ok=True)

    return Chroma(
        collection_name=COLLECTION_NAME,
        persist_directory=str(DB_PATH),
        embedding_function=embeddings,
    )


def create_vector_store(chunks, document_id: str) -> Chroma:
    """
    Replace existing chunks for this document ID,
    then store the new chunks.
    """
    if not chunks:
        raise ValueError("Cannot store an empty list of document chunks.")

    if not document_id or not document_id.strip():
        raise ValueError("document_id cannot be empty.")

    db = get_vector_store()

    # Remove old records belonging only to this document.
    db.delete(
        where={"document_id": document_id}
    )

    # Attach document ID to every chunk.
    for chunk in chunks:
        chunk.metadata["document_id"] = document_id

    # Store the updated chunks.
    db.add_documents(chunks)

    return db