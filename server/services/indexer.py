import asyncio
import hashlib
import time
from pathlib import Path
from uuid import uuid4
import shutil

from langchain_core.documents import Document
from server.models import File, Session
from .utils import document_splitter
from reviewbot.config import SNAPSHOT_PATH

MAX_CHUNKS_PER_FILE = 20   # prevents massive contexts


def flush_snapshot():
    snapshot_dir = Path(SNAPSHOT_PATH)
    if snapshot_dir.exists():
        shutil.rmtree(snapshot_dir)

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
            metadata={
                "path": str(filepath),
                "session": session.session_name
            },
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
        await asyncio.gather(*[
            File.create(session=session, **file_data)
            for file_data in files_to_create
        ])
        docs, split_ids = await document_splitter(documents=documents)
        if len(docs) > MAX_CHUNKS_PER_FILE:
            docs = docs[:MAX_CHUNKS_PER_FILE]
            split_ids = split_ids[:MAX_CHUNKS_PER_FILE]

        print("Indexed chunks:", len(docs))
        print("Total characters:", sum(len(d.page_content) for d in docs))

        vector_store.add_documents(
            documents=docs,
            ids=split_ids
        )

    end = time.perf_counter()
    return {
        "indexed_files": len(documents),
        "time_taken_seconds": round(end - start, 4),
    }