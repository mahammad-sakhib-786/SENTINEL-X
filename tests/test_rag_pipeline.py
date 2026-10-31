from legal_ai.rag_pipeline import answer_contract_question


def test_rag_answers_using_contract_context():
    answer = answer_contract_question(
        question="How many days notice is required for termination?",
        document_id="retriever_test_contract_001",
    )

    print("\nRAG RESPONSE:")
    print(answer)

    assert isinstance(answer, str)
    assert len(answer.strip()) > 0


if __name__ == "__main__":
    test_rag_answers_using_contract_context()