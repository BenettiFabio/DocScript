import os
from pathlib import Path

from src.config import (
    _PRJ_ROOT_DIR,
)
from src.utils import (
    remove_dir,
)

###########
# Defines #
###########
_AI_DIR = Path(os.path.join(_PRJ_ROOT_DIR, "..", ".ai")).resolve()

AI_CONFIG_JSON_NAME = "config.json"
AI_DOCUMENTS_JSON_NAME = "documents.json"
AI_CHUNKS_JSONL_NAME = "chunks.jsonl"
AI_MANIFEST_JSON_NAME = "manifest.json"
AI_EMBEDDING_JSONL_NAME = "embedding.jsonl"

AI_CONFIG_PATH = Path(os.path.join(_AI_DIR, AI_CONFIG_JSON_NAME)).resolve()
AI_DOCUMENTS_PATH = Path(os.path.join(_AI_DIR, AI_DOCUMENTS_JSON_NAME)).resolve()
AI_CHUNK_PATH = Path(os.path.join(_AI_DIR, AI_CHUNKS_JSONL_NAME)).resolve()
AI_MANIFEST_PATH = Path(os.path.join(_AI_DIR, AI_MANIFEST_JSON_NAME)).resolve()
AI_EMBEDDING_PATH = Path(os.path.join(_AI_DIR, AI_EMBEDDING_JSONL_NAME)).resolve()

OLLAMA_HOST = "http://localhost:11434"
EMBEDDING_MODEL = "qwen3-embedding:0.6b"
LLM_MODEL = "qwen3:4b"
TOP_K = 5


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


def remove_ai_dir() -> None:
    """
    Remove a .ai/ dir in the correct location
    """
    remove_dir(_AI_DIR)
