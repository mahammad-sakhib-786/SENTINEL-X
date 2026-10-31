
from langchain.agents import create_agent

from legal_ai.config import llm
from legal_ai.tools import (
    retrieve_contract_text,
    run_contract_compliance_check,
)


AGENT_SYSTEM_PROMPT = """
You are SENTINEL X, an agentic contract review assistant.

You help users inspect uploaded contracts using the available tools.

Rules:
1. For questions about contract clauses, use retrieve_contract_text.
2. For requests to run a compliance checklist, use
   run_contract_compliance_check with the exact document ID
   supplied in the user message.
3. Never claim that a contract is legally compliant.
4. Never invent contract clauses or legal requirements.
5. Report supporting page numbers and clause numbers when available.
6. Distinguish detected keyword evidence from missing evidence.
7. A missing keyword match does not prove a clause is absent.
8. Do not present your responses as professional legal advice.

The compliance checklist is preliminary and keyword-based.
Explain this limitation whenever reporting compliance findings.
"""


agent = create_agent(
    model=llm,
    tools=[
        retrieve_contract_text,
        run_contract_compliance_check,
    ],
    system_prompt=AGENT_SYSTEM_PROMPT,
)


def ask_contract_agent(question: str, document_id: str) -> str:
    """
    Send a contract question and document ID to the SENTINEL X agent.
    The agent retrieves the PDF path internally through its tools.
    """

    if not question or not question.strip():
        raise ValueError("Question cannot be empty.")

    if not document_id or not document_id.strip():
        raise ValueError("Document ID cannot be empty.")

    user_message = f"""
Uploaded contract document ID: {document_id}

User question:
{question}

Instructions:
- For clause questions, use retrieve_contract_text.
- Pass the exact document ID to retrieve_contract_text.
- For compliance checklist requests, use run_contract_compliance_check.
- Pass the exact document ID to run_contract_compliance_check.
- Do not request or expose the local PDF path.
- Base your answer on tool results.
- Include page and clause references when available.
"""

    response = agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": user_message,
                }
            ]
        }
    )

    return response["messages"][-1].content
