from pathlib import Path
from reviewbot.config import IGNORE_DIRS


def should_ignore(path: Path):
    return any(part in IGNORE_DIRS for part in path.parts)
from pathlib import Path

def resolve_files(args):
    all_files = []
    for input_path in args.files:
        path = Path(input_path).resolve()
        if not path.exists():
            print(f"File not found: {path}")
            continue
        if path.is_file():
            if not should_ignore(path):
                all_files.append(path)
        elif path.is_dir():
            for file in path.rglob("*"):
                if file.is_file() and not should_ignore(file):
                    all_files.append(file)

    return all_files