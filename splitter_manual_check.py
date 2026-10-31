from legal_ai.document_loader import load_document
from legal_ai.clause_splitter import split_documents

docs = load_document("data/legal_documents/sample_contract.pdf")
chunks = split_documents(docs)

print("Total chunks:", len(chunks))
for i, c in enumerate(chunks):
    m = c.metadata
    print(f"{i:2d} | page {m['page']} | clause {m['clause_number'] or '-':>2} | "
          f"{m['clause_title'][:35]:<35} | {len(c.page_content)} chars")

print()
conf = [c for c in chunks if c.metadata["clause_title"] == "Confidentiality"]
print("Confidentiality chunks found:", len(conf))
print(conf[0].page_content)
text = conf[0].page_content
print()
print("Contains 6.1:", "6.1" in text)
print("Contains 6.2:", "6.2" in text)
print("Contains 6.3:", "6.3" in text)
print("Contains other clause:", "7. Data Protection" in text or "5. Intellectual" in text)