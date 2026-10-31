from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from legal_ai.config import llm
from legal_ai.retriever import get_retriever


RAG_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """You are SENTINEL X, a contract analysis assistant.

Answer questions using only the supplied contract context.

Rules:
1. Do not invent contract terms or legal facts.
2. If the context does not contain the answer, say so clearly.
3. Mention the relevant page and clause number when available.
4. Distinguish what the contract explicitly states from your interpretation.
5. Do not present your response as professional legal advice.

Contract context:
{context}
""",
        ),
        (
            "human",
            "{question}",
        ),
    ]
)


def answer_contract_question(
    question: str,
    document_id: str,
) -> str:
    """
    Answer a question using only the selected contract's retrieved context.
    """
    if not question or not question.strip():
        raise ValueError("Question cannot be empty.")

    if not document_id or not document_id.strip():
        raise ValueError("document_id cannot be empty.")

    retriever = get_retriever(document_id)

    documents = retriever.invoke(question)

    if not documents:
        return "I could not find relevant information in this contract."

    context_parts = []

    for doc in documents:
        page = doc.metadata.get("page_number", "Unknown")
        clause = doc.metadata.get("clause_number", "Unknown")

        context_parts.append(
            f"Page: {page}\n"
            f"Clause: {clause}\n"
            f"Content: {doc.page_content}"
        )

    context = "\n\n".join(context_parts)

    chain = RAG_PROMPT | llm | StrOutputParser()

    return chain.invoke(
        {
            "context": context,
            "question": question,
        }
    )