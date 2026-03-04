import hashlib
import time
from pathlib import Path
from uuid import uuid4

from langchain_core.documents import Document

from server.models import File, Session

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


async def run_indexing(paths, session_name, vector_store):
    start = time.perf_counter()

    session, _ = await Session.get_or_create(
        session_name=session_name
    )

    documents = []
    files_to_create = []

    for path_str in paths:
        filepath = Path(path_str)

        if not filepath.exists() or not filepath.is_file():
            continue

        try:
            content = filepath.read_text(
                encoding="utf-8",
                errors="ignore"
            )
        except Exception:
            continue

        filehash = hashlib.sha1(
            content.encode("utf-8")
        ).hexdigest()

        # Dedup check
        existing = await File.filter(
            session=session,
            file_hash=filehash
        ).first()

        if existing:
            continue

        file_id = str(uuid4())

        documents.append(
            Document(
                page_content=content,
                metadata={"path": str(filepath)},
                id=file_id
            )
        )

        files_to_create.append({
            "file_path": str(filepath),
            "file_hash": filehash,
            "file_embed_id": file_id
        })

    if documents:
        docs, split_ids = document_splitter(
            documents=documents
        )

        vector_store.add_documents(
            documents=docs,
            ids=split_ids
        )

        for file_data in files_to_create:
            await File.create(
                session=session,
                **file_data
            )

    end = time.perf_counter()

    return {
        "indexed_files": len(documents),
        "time_taken_seconds": round(end - start, 4),
    }