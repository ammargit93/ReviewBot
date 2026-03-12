from typing import List
from uuid import uuid4
from pathlib import Path

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter


splitter = RecursiveCharacterTextSplitter(
    chunk_size=1200,
    chunk_overlap=500,
    separators=[
        "\n\n",     # logical blocks
        "\n",       # lines
        "{",        # block start (C, Go, Java, JS)
        "}",        # block end
        ";",        # statement terminator
        " ",        # words
        ""          # fallback
    ]
)

def document_splitter(documents: List[Document]):
    chunks = splitter.split_documents(documents)

    new_docs = []
    ids = []

    for i, chunk in enumerate(chunks):
        file_path = chunk.metadata.get("path", "unknown")
        session = chunk.metadata.get("session")
        filename = Path(file_path).name
        chunk_id = str(uuid4())

        new_docs.append(
            Document(
                page_content=f"File: {filename}\nPath: {file_path}\n\n{chunk.page_content}",
                metadata={
                    "path": file_path,
                    "filename": filename,
                    "chunk": i,
                    "session": session
                },
                id=chunk_id
            )
        )

        ids.append(chunk_id)

    return new_docs, ids