from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from uuid import uuid4
from typing import List

def document_splitter(documents: List[Document]):
    splitter = RecursiveCharacterTextSplitter(chunk_size=100, chunk_overlap=0)
    chunks = splitter.split_documents(documents)
    uuids = []
    new_docs = []
    for chunk in chunks:
        file_id = str(uuid4())
        new_docs.append(Document(
            page_content=chunk.page_content,
            metadata={"path": chunk.metadata["path"]},
            id=file_id
        ))
        uuids.append(file_id)
    return (new_docs, uuids)