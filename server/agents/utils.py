import re
from langchain.tools import tool

SUPPORTED_TECH = {
    "python": ["requirements.txt", "pyproject.toml"],
    "node": ["package.json"],
    "go": ["go.mod"],
    "rust": ["Cargo.toml"],
}

