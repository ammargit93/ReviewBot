import hashlib
from uuid import uuid4
from langchain_core.documents import Document
import time

from reviewbot.models import File
from reviewbot.indexing.chunking import document_splitter


async def embed_documents(all_files, vector_store):
    documents, uuids = [], []
    start = time.perf_counter()
    for filepath in all_files:
        try:
            content = filepath.read_text(encoding="utf-8", errors="ignore")
        except Exception as e:
            print(f"Failed reading {filepath}: {e}")
            continue

        filehash = hashlib.sha1(content.encode("utf-8")).hexdigest()
        file_id = str(uuid4())

        documents.append(Document(page_content=content, metadata={"path": str(filepath)}, id=file_id))
        uuids.append(file_id)

        await File.create(file_path=str(filepath), file_hash=filehash, file_embed_id=file_id)
        print(f"Indexed: {filepath}")

    if documents:
        docs, uuids = document_splitter(documents=documents)
        vector_store.add_documents(documents=docs, ids=uuids)
        end = time.perf_counter()
        print(f"\nIndexed {len(documents)} files successfully.")
        print(f"\nIndexing completed in {end - start:.4f} seconds")
