from typing import List
from uuid import uuid4
from pathlib import Path
import hashlib

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from server.models import Chunks, File
from reviewbot.config import SNAPSHOT_PATH

splitter = RecursiveCharacterTextSplitter(
    chunk_size=400,
    chunk_overlap=60,
    separators=[
        "\n\n",  # logical blocks
        "\n",    # lines
        "{",     # code block start
        "}",     # code block end
        ";",     # statement end
        " ",
        ""
    ]
)



async def document_splitter(documents: List[Document]):
    chunks = splitter.split_documents(documents)

    new_docs = []
    ids = []

    snapshot_root = Path(SNAPSHOT_PATH)
    snapshot_root.mkdir(parents=True, exist_ok=True)

    for i, chunk in enumerate(chunks):
        file_path = chunk.metadata.get("path", "unknown")
        session = chunk.metadata.get("session")
        filename = Path(file_path).name

        # safer folder name
        safe_name = filename.replace(".", "_")
        file_snapshot_dir = snapshot_root / safe_name
        file_snapshot_dir.mkdir(parents=True, exist_ok=True)

        chunk_id = str(uuid4())

        # hash for chunk
        chunk_hash = hashlib.sha1(chunk.page_content.encode()).hexdigest()

        # snapshot file path
        chunk_file = file_snapshot_dir / f"{safe_name}_{chunk_hash}.txt"

        if not chunk_file.exists():
            try:
                chunk_file.write_text(chunk.page_content, encoding="utf-8")
            except Exception as e:
                print(f"❌ Snapshot write failed: {e}")

        new_docs.append(
            Document(
                page_content=f"File: {filename}\nPath: {file_path}\n\n{chunk.page_content}",
                metadata={
                    "path": file_path,
                    "filename": filename,
                    "chunk": i,
                    "session": session,
                    "chunk_hash": chunk_hash
                },
                id=chunk_id
            )
        )

        ids.append(chunk_id)

        file = await File.filter(file_path=file_path).first()
        if file:
            await Chunks.create(
                chunk_content=chunk.page_content,
                chunk_index=i,
                chunk_embed_id=chunk_id,
                chunk_hash=chunk_hash,
                file=file
            )

    return new_docs, ids