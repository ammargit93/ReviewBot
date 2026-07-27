import asyncio
import hashlib
import time
from pathlib import Path
from uuid import uuid4
import shutil

from langchain_core.documents import Document
from server.models import File, Session, Chunks
from reviewbot.config import SNAPSHOT_PATH

MAX_CHUNKS_PER_FILE = 20   


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

        new_file_hash = hashlib.sha1(content.encode("utf-8")).hexdigest()

        # Find if the file already exists in this session
        existing_file = await File.filter(
            session=session,
            file_path=str(filepath)
        ).first()

        filename = filepath.name

        # If file exists and hash matches, it hasn't changed.
        if existing_file and existing_file.file_hash == new_file_hash:
            return {
                "status": "skipped",
                "file_path": str(filepath)
            }

        # Otherwise, we need to split the file and process chunks.
        # Create a langchain Document representing the whole file
        file_doc = Document(
            page_content=content,
            metadata={
                "path": str(filepath),
                "session": session.session_name
            }
        )

        from server.services.utils import splitter
        chunks = splitter.split_documents([file_doc])
        if len(chunks) > MAX_CHUNKS_PER_FILE:
            chunks = chunks[:MAX_CHUNKS_PER_FILE]

        snapshot_root = Path(SNAPSHOT_PATH)
        snapshot_root.mkdir(parents=True, exist_ok=True)
        safe_name = filename.replace(".", "_")
        file_snapshot_dir = snapshot_root / safe_name
        file_snapshot_dir.mkdir(parents=True, exist_ok=True)

        new_docs_to_add = []
        new_ids_to_add = []
        new_chunks_data = [] # Data to create in SQLite

        new_chunk_hashes = set()
        new_chunks_by_hash = {}

        # First pass: calculate hashes of new chunks
        for i, chunk in enumerate(chunks):
            chunk_hash = hashlib.sha1(chunk.page_content.encode()).hexdigest()
            new_chunk_hashes.add(chunk_hash)
            new_chunks_by_hash[chunk_hash] = (i, chunk)

        delete_chunk_embed_ids = []
        delete_db_chunk_ids = []
        retained_chunks_to_update = []

        if existing_file:
            # File exists but hash changed. Perform incremental chunking.
            old_chunks = await Chunks.filter(file=existing_file).all()
            old_chunks_map = {c.chunk_hash: c for c in old_chunks}

            # Chunks to delete: old chunks whose hash is not in new_chunk_hashes
            for old_hash, old_chunk in old_chunks_map.items():
                if old_hash not in new_chunk_hashes:
                    delete_chunk_embed_ids.append(old_chunk.chunk_embed_id)
                    delete_db_chunk_ids.append(old_chunk.id)

            # Chunks to add / update
            for chunk_hash, (i, chunk) in new_chunks_by_hash.items():
                if chunk_hash in old_chunks_map:
                    # Unchanged chunk, potentially update index if changed
                    old_chunk = old_chunks_map[chunk_hash]
                    if old_chunk.chunk_index != i:
                        old_chunk.chunk_index = i
                        retained_chunks_to_update.append(old_chunk)
                else:
                    # New chunk to add
                    chunk_id = str(uuid4())
                    chunk_file = file_snapshot_dir / f"{safe_name}_{chunk_hash}.txt"
                    if not chunk_file.exists():
                        try:
                            chunk_file.write_text(chunk.page_content, encoding="utf-8")
                        except Exception as e:
                            print(f"❌ Snapshot write failed: {e}")

                    new_docs_to_add.append(
                        Document(
                            page_content=f"File: {filename}\nPath: {str(filepath)}\n\n{chunk.page_content}",
                            metadata={
                                "path": str(filepath),
                                "filename": filename,
                                "chunk": i,
                                "session": session.session_name,
                                "chunk_hash": chunk_hash
                            },
                            id=chunk_id
                        )
                    )
                    new_ids_to_add.append(chunk_id)
                    new_chunks_data.append({
                        "chunk_content": chunk.page_content,
                        "chunk_index": i,
                        "chunk_embed_id": chunk_id,
                        "chunk_hash": chunk_hash
                    })

            return {
                "status": "updated",
                "file_path": str(filepath),
                "new_hash": new_file_hash,
                "existing_file": existing_file,
                "delete_chunk_embed_ids": delete_chunk_embed_ids,
                "delete_db_chunk_ids": delete_db_chunk_ids,
                "new_docs_to_add": new_docs_to_add,
                "new_ids_to_add": new_ids_to_add,
                "new_chunks_data": new_chunks_data,
                "retained_chunks_to_update": retained_chunks_to_update
            }

        else:
            # Completely new file
            for i, chunk in enumerate(chunks):
                chunk_hash = hashlib.sha1(chunk.page_content.encode()).hexdigest()
                chunk_id = str(uuid4())
                chunk_file = file_snapshot_dir / f"{safe_name}_{chunk_hash}.txt"
                if not chunk_file.exists():
                    try:
                        chunk_file.write_text(chunk.page_content, encoding="utf-8")
                    except Exception as e:
                        print(f"❌ Snapshot write failed: {e}")

                new_docs_to_add.append(
                    Document(
                        page_content=f"File: {filename}\nPath: {str(filepath)}\n\n{chunk.page_content}",
                        metadata={
                            "path": str(filepath),
                            "filename": filename,
                            "chunk": i,
                            "session": session.session_name,
                            "chunk_hash": chunk_hash
                        },
                        id=chunk_id
                    )
                )
                new_ids_to_add.append(chunk_id)
                new_chunks_data.append({
                    "chunk_content": chunk.page_content,
                    "chunk_index": i,
                    "chunk_embed_id": chunk_id,
                    "chunk_hash": chunk_hash
                })

            return {
                "status": "created",
                "file_path": str(filepath),
                "new_hash": new_file_hash,
                "new_docs_to_add": new_docs_to_add,
                "new_ids_to_add": new_ids_to_add,
                "new_chunks_data": new_chunks_data
            }


async def run_indexing(paths, session_name, vector_store):
    start = time.perf_counter()

    session, _ = await Session.get_or_create(session_name=session_name)

    semaphore = asyncio.Semaphore(10)
    tasks = [
        process_file(path, session, semaphore)
        for path in paths
    ]

    results = await asyncio.gather(*tasks)

    all_delete_embed_ids = []
    all_new_docs = []
    all_new_ids = []

    files_indexed_count = 0

    for res in results:
        if not res or res["status"] == "skipped":
            continue

        files_indexed_count += 1

        if res["status"] == "updated":
            # 1. Delete old embeddings from Chroma
            if res["delete_chunk_embed_ids"]:
                all_delete_embed_ids.extend(res["delete_chunk_embed_ids"])

            # 2. Delete old chunks from DB
            if res["delete_db_chunk_ids"]:
                await Chunks.filter(id__in=res["delete_db_chunk_ids"]).delete()

            # 3. Create new chunks in DB for this existing file
            for chunk_data in res["new_chunks_data"]:
                await Chunks.create(file=res["existing_file"], **chunk_data)

            # 4. Update index positions for retained chunks
            for old_chunk in res["retained_chunks_to_update"]:
                await old_chunk.save()

            # 5. Update file hash
            res["existing_file"].file_hash = res["new_hash"]
            await res["existing_file"].save()

            # 6. Add new docs to list for batch embedding
            all_new_docs.extend(res["new_docs_to_add"])
            all_new_ids.extend(res["new_ids_to_add"])

        elif res["status"] == "created":
            # 1. Create File record
            file_id = str(uuid4())
            new_file = await File.create(
                session=session,
                file_path=res["file_path"],
                file_hash=res["new_hash"],
                file_embed_id=file_id
            )

            # 2. Create Chunk records in DB
            for chunk_data in res["new_chunks_data"]:
                await Chunks.create(file=new_file, **chunk_data)

            # 3. Add new docs to list for batch embedding
            all_new_docs.extend(res["new_docs_to_add"])
            all_new_ids.extend(res["new_ids_to_add"])

    # Batch operations on Chroma Vector Store
    if all_delete_embed_ids:
        print(f"Deleting {len(all_delete_embed_ids)} stale chunks from vector store...")
        try:
            vector_store.delete(ids=all_delete_embed_ids)
        except Exception as e:
            print(f"❌ Error deleting from vector store: {e}")

    if all_new_docs:
        print(f"Embedding and adding {len(all_new_docs)} new chunks to vector store...")
        try:
            vector_store.add_documents(
                documents=all_new_docs,
                ids=all_new_ids
            )
        except Exception as e:
            print(f"❌ Error adding to vector store: {e}")

    end = time.perf_counter()
    return {
        "indexed_files": files_indexed_count,
        "time_taken_seconds": round(end - start, 4),
    }