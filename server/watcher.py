from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from pathlib import Path


class FileChangeHandler(FileSystemEventHandler):

    def __init__(self, index_func):
        self.index_func = index_func

    def on_modified(self, event):
        if event.is_directory:
            return

        path = Path(event.src_path)

        ALLOWED_EXT = {
            ".py",
            ".js",
            ".ts",
            ".go",
            ".java",
            ".cpp",
            ".c",
            ".rs"
        }

        if path.suffix not in ALLOWED_EXT:
            return

        print(f"File changed: {path}")

        # trigger your indexing logic
        self.index_func(path)


def start_watcher(path, index_func):

    event_handler = FileChangeHandler(index_func)

    observer = Observer()
    observer.schedule(event_handler, path=str(path), recursive=True)
    observer.start()

    return observer