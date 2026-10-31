import re

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter


splitter = RecursiveCharacterTextSplitter(
    chunk_size=900,
    chunk_overlap=150,
    separators=[
        "\n\n",
        "\n",
        ". ",
        " ",
        ""
    ],
    add_start_index=True
)


# Match standalone main clause headings such as:
# 1. Definitions
# 6. Confidentiality
# 7. Data Protection and Security
#
# Does not match subsection numbers such as 6.1 or 6.2.
HEADING_PATTERN = re.compile(
    r"(?m)^\s*(\d{1,2})\.\s+([A-Z][^\n]{2,80})\s*$"
)


def split_documents(documents):
    chunks = []

    for document in documents:
        page_text = document.page_content

        if not page_text.strip():
            continue

        headings = list(HEADING_PATTERN.finditer(page_text))

        sections = []

        if not headings:
            sections.append(
                ("Unnumbered", "Unclassified", page_text)
            )
        else:
            # Preserve any text appearing before the first heading.
            intro = page_text[:headings[0].start()]

            if intro.strip():
                sections.append(
                    ("Unnumbered", "Unclassified", intro)
                )

            # Separate the page into main clauses.
            for index, heading in enumerate(headings):
                start = heading.start()

                if index + 1 < len(headings):
                    end = headings[index + 1].start()
                else:
                    end = len(page_text)

                clause_number = heading.group(1)
                clause_title = heading.group(2).strip()
                section_text = page_text[start:end]

                sections.append(
                    (clause_number, clause_title, section_text)
                )

        # Split each clause independently.
        for clause_number, clause_title, section_text in sections:
            section_document = Document(
                page_content=section_text,
                metadata=dict(document.metadata)
            )

            section_chunks = splitter.split_documents(
                [section_document]
            )

            for chunk in section_chunks:
                original_page = document.metadata.get("page", 0)

                chunk.metadata.update({
                    "document_type": "legal",
                    "page": original_page,
                    "page_number": original_page + 1,
                    "clause_number": clause_number,
                    "clause_title": clause_title
                })

                chunks.append(chunk)

    return chunks