from langchain.tools import tool

from legal_ai.retriever import get_retriever


@tool
def retrieve_contract_text(question: str, document_id: str) -> str:
    """
    Retrieve relevant passages from a specific uploaded contract.

    Use this tool to find contract clauses and supporting text
    related to a user's question.
    """
    if not question or not question.strip():
        return "Error: Question cannot be empty."

    if not document_id or not document_id.strip():
        return "Error: Document ID cannot be empty."

    retriever = get_retriever(document_id)

    documents = retriever.invoke(question)

    if not documents:
        return "No relevant contract text was found."

    results = []

    for doc in documents:
        page = doc.metadata.get("page_number", "Unknown")
        clause = doc.metadata.get("clause_number", "Unknown")

        results.append(
            f"Page: {page}\n"
            f"Clause: {clause}\n"
            f"Text: {doc.page_content}"
        )

    return "\n\n".join(results)

from legal_ai.clause_splitter import split_documents
from legal_ai.compliance_checker import check_contract_compliance
from legal_ai.document_loader import load_document


@tool
def run_contract_compliance_check(pdf_path: str) -> str:
    """
    Run the preliminary compliance checklist on an uploaded contract PDF.

    Checks for termination, confidentiality, data protection,
    liability, and dispute resolution indicators.
    """
    if not pdf_path or not pdf_path.strip():
        return "Error: PDF path cannot be empty."

    try:
        documents = load_document(pdf_path)

        if not documents:
            return "No readable pages were found in the PDF."

        chunks = split_documents(documents)

        if not chunks:
            return "No readable contract text was found."

        results = check_contract_compliance(chunks)

        output = []

        for check_id, result in results.items():
            output.append(
                f"\n{result['description']}: {result['status']}"
            )

            for evidence in result["evidence"]:
                output.append(
                    f"Page: {evidence['page']} | "
                    f"Clause: {evidence['clause']}"
                )
                output.append(
                    f"Matched keywords: "
                    f"{', '.join(evidence['matched_keywords'])}"
                )
                output.append(
                    f"Evidence: {evidence['text']}"
                )

        output.append(
            "\nDisclaimer: This is a preliminary keyword-based "
            "review checklist, not a legal compliance determination."
        )

        return "\n".join(output)

    except Exception as error:
        return f"Compliance check failed: {error}"
