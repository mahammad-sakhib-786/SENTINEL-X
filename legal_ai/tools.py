
import re
from pathlib import Path

from langchain.tools import tool

from database import get_contract_document_path
from legal_ai.clause_splitter import split_documents
from legal_ai.compliance_checker import check_contract_compliance
from legal_ai.document_loader import load_document
from legal_ai.retriever import get_retriever


UPLOAD_DIR = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "legal_documents"
    / "uploads"
).resolve()


def resolve_contract_path(document_id: str):
    """Resolve and validate a registered contract PDF."""

    if not document_id or not document_id.strip():
        raise ValueError("Document ID cannot be empty.")

    if not re.fullmatch(r"[a-fA-F0-9]{64}", document_id):
        raise ValueError("Invalid document ID.")

    stored_path = get_contract_document_path(document_id)

    if not stored_path:
        raise FileNotFoundError("Registered contract was not found.")

    requested_path = Path(stored_path).resolve()

    if not requested_path.is_relative_to(UPLOAD_DIR):
        raise PermissionError("Document access is not permitted.")

    if requested_path.suffix.lower() != ".pdf":
        raise ValueError("Only PDF documents are supported.")

    if not requested_path.is_file():
        raise FileNotFoundError("Uploaded PDF was not found.")

    return requested_path


@tool
def retrieve_contract_text(question: str, document_id: str) -> str:
    """
    Retrieve relevant passages from a specific uploaded contract.
    """

    if not question or not question.strip():
        return "Error: Question cannot be empty."

    if not document_id or not document_id.strip():
        return "Error: Document ID cannot be empty."

    try:
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

    except Exception:
        return "Contract retrieval failed. Verify the document and application logs."


@tool
def run_contract_compliance_check(document_id: str) -> str:
    """
    Run a preliminary compliance checklist on a registered contract.
    The PDF path is retrieved from the application's database.
    """

    try:
        requested_path = resolve_contract_path(document_id)

        documents = load_document(str(requested_path))

        if not documents:
            return "No readable pages were found."

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
                    f"Evidence type: {evidence['evidence_type']}"
                )

                output.append(
                    f"Matched keywords: "
                    f"{', '.join(evidence['matched_keywords'])}"
                )

                output.append(
                    f"Evidence: {evidence['text']}"
                )

        output.append(
            "\nDisclaimer: Preliminary keyword-based review only. "
            "This is not a legal compliance determination."
        )

        return "\n".join(output)

    except Exception:
        return (
            "Compliance check failed. Verify the registered document "
            "and application logs."
        )
