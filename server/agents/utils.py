import re
from server.container import ContainerManager
from langchain.tools import tool

SUPPORTED_TECH = {
    "python": ["requirements.txt", "pyproject.toml"],
    "node": ["package.json"],
    "go": ["go.mod"],
    "rust": ["Cargo.toml"],
}

