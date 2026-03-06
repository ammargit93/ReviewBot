import asyncio
import hashlib
import time
from pathlib import Path
from uuid import uuid4

from langchain_core.documents import Document
from server.models import File, Session
from .utils import document_splitter

async def process_file(path_str, session, semaphore):
    async with semaphore:
        filepath = Path(path_str)

        if not filepath.exists() or not filepath.is_file():
            return None

        try:
            content = filepath.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            return None
 
        filehash = hashlib.sha1(content.encode("utf-8")).hexdigest()

        existing = await File.filter(
            session=session,
            file_hash=filehash
        ).first()

        if existing:
            return None

        file_id = str(uuid4())

        document = Document(
            page_content=content,
            metadata={"path": str(filepath)},
            id=file_id
        )

        file_data = {
            "file_path": str(filepath),
            "file_hash": filehash,
            "file_embed_id": file_id
        }

        return document, file_data


async def run_indexing(paths, session_name, vector_store):
    start = time.perf_counter()

    session, _ = await Session.get_or_create(session_name=session_name)

    semaphore = asyncio.Semaphore(10)

    tasks = [
        process_file(path, session, semaphore)
        for path in paths
    ]
    results = await asyncio.gather(*tasks)
    documents = []
    files_to_create = []
    for result in results:
        if result:
            doc, file_data = result
            documents.append(doc)
            files_to_create.append(file_data)

    if documents:
        docs, split_ids = document_splitter(documents=documents)
        vector_store.add_documents(documents=docs, ids=split_ids)
        await asyncio.gather(*[
            File.create(session=session, **file_data)
            for file_data in files_to_create
        ])

    end = time.perf_counter()

    return {
        "indexed_files": len(documents),
        "time_taken_seconds": round(end - start, 4),
    }