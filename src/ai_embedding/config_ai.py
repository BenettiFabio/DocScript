import os
from pathlib import Path

from src.config import (
    _PRJ_ROOT_DIR,
)

###########
# Defines #
###########
_AI_DIR = Path(os.path.join(_PRJ_ROOT_DIR, "..", ".ai")).resolve()

AI_CONFIG_JSON_NAME = "config.json"
AI_DOCUMENTS_JSON_NAME = "documents.json"
AI_CHUNKS_JSONL_NAME = "chunks.jsonl"
AI_MANIFEST_JSON_NAME = "manifest.json"

AI_CONFIG_PATH = Path(os.path.join(_AI_DIR, AI_CONFIG_JSON_NAME)).resolve()
AI_DOCUMENTS_PATH = Path(os.path.join(_AI_DIR, AI_DOCUMENTS_JSON_NAME)).resolve()
AI_CHUNK_PATH = Path(os.path.join(_AI_DIR, AI_CHUNKS_JSONL_NAME)).resolve()
AI_MANIFEST_PATH = Path(os.path.join(_AI_DIR, AI_MANIFEST_JSON_NAME)).resolve()


def is_ai() -> bool:
    """
    Check if the directory is .ai/ exists
    """
    return bool(os.path.exists(_AI_DIR))


def create_ai_dir() -> None:
    """
    Create a .ai/ dir in the correct location
    """
    if not os.path.exists(_AI_DIR):
        os.makedirs(_AI_DIR, exist_ok=True)
