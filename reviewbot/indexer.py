import hashlib
from pathlib import Path
from uuid import uuid4
from langchain_core.documents import Document
from langchain_chroma import Chroma

from .config import COLLECTION, CHROMA_PATH, EMBEDDING_MODEL
from .models import File

IGNORE_DIRS = {".git", ".venv", "__pycache__", ".reviewbot", "node_modules"}

def should_ignore(path: Path):
    return any(part in IGNORE_DIRS for part in path.parts)

async def index_files(args):
    all_files = []
    for input_path in args.files:
        path = Path(input_path).resolve()
        if not path.exists():
            print(f"File not found: {path}")
            continue
        if path.is_file() and not should_ignore(path):
            all_files.append(path)
        else:
            all_files.extend(p for p in path.rglob("*") if p.is_file() and not should_ignore(p))

    if not all_files:
        print("No files to index")
        return

    vector_store = Chroma(
        collection_name=COLLECTION,
        persist_directory=str(CHROMA_PATH),
        embedding_function=EMBEDDING_MODEL
    )

    documents, uuids = [], []

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

        await File.create(file_path=str(filepath), file_hash=filehash, file_content= content, file_embed_id=file_id)
        print(f"Indexed: {filepath}")

    if documents:
        vector_store.add_documents(documents=documents, ids=uuids)
        print(f"\nIndexed {len(documents)} files successfully.")