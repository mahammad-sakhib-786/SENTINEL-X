from langchain_ollama import OllamaEmbeddings


# Initialize the local Ollama embedding model
embeddings = OllamaEmbeddings(
    model="nomic-embed-text:latest"
)


def generate_embedding(text: str) -> list[float]:
    """
    Generate an embedding vector for the supplied text.

    Args:
        text: Text to convert into an embedding.

    Returns:
        A list of floating-point numbers.
    """
    if not text or not text.strip():
        raise ValueError("Text cannot be empty.")

    return embeddings.embed_query(text)