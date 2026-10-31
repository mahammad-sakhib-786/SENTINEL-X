from legal_ai.document_loader import load_document

docs = load_document("data/legal_documents/sample_contract.pdf")
print(len(docs))