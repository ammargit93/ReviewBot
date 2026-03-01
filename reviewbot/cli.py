import argparse
from .indexer import index_files

def build_parser():
    parser = argparse.ArgumentParser(prog="reviewbot", description="AI code review assistant")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # index command
    index_parser = subparsers.add_parser("index", help="Index files for review")
    index_parser.add_argument("files", nargs="+", help="Files or directories to index")
    index_parser.set_defaults(func=index_files)

    return parser