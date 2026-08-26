import sys
from pathlib import Path

from src.config import (
    _VAULT_DIR,
    is_bank,
    is_vault,
    get_all_files_from_main,
    get_all_files_from_root,
    check_inconsistency,
)
from src.ai_embedding.config_ai import (
    AI_CONFIG_PATH,
    AI_DOCUMENTS_PATH,
    AI_CHUNK_PATH,
    AI_MANIFEST_PATH,
    is_ai,
    create_ai_dir,
    remove_ai_dir,
)
from src.ai_embedding.indexer import (
    fill_ai_dir,
)
from src.modes import CMode


# --index-ai
# ├── 1. Trova vault/main.md
# ├── 2. Ricostruisce il tree ricorsivamente
# ├── 3. Trova tutte le note effettive
# ├── 4. Per ogni nota:
# │     ├── legge Markdown
# │     ├── estrae H1/H2/H3/H4...
# │     ├── crea sezioni semantiche
# │     ├── controlla dimensione
# │     ├── se piccola:
# │     │      └── 1 chunk
# │     └── se grande:
# │            ├── divide per heading
# │            ├── poi per paragrafi
# │            └── poi eventualmente per frasi
# ├── 5. Aggiunge metadata:
# │     ├── file sorgente
# │     ├── main hierarchy
# │     ├── folder hierarchy
# │     ├── filename hierarchy
# │     └── heading hierarchy
# ├── 6. Crea embedding_text
# \---------------------------------------------
# ├── 7. Chiama embedder
# ├── 8. Salva:
# │     ├── chunk originale
# │     ├── metadata
# │     └── vettore
# └── 9. Aggiorna manifest/hash


def init_index() -> None:
    if is_bank():
        print("Error: The AI functionalities works only in local Vault.")
        sys.exit(1)

    try:
        if not is_vault():
            print("Error: The AI Index needs a initialized Vault!.")
            sys.exit(1)

        print("[AI] Reading vault...")
        file_found_root: list[str] = []
        file_found_main: list[str] = []
        mode: CMode = CMode.ALL

        file_found_root = get_all_files_from_root()
        file_found_main = get_all_files_from_main(mode)

        checkVaultFlag = False
        check_inconsistency(file_found_main, file_found_root, checkVaultFlag)

        # Create a list of files to be chunkized
        root_map = {Path(p).name: p for p in file_found_root}
        only_used_files = [root_map[Path(name).name] for name in file_found_main]

        num_docs = len(only_used_files)
        print(f"[AI] Document Found: {num_docs}")

        print("[AI] Creating .ai/ directory...")
        # Create the Index Destination Directory
        create_ai_dir()

        # Effective chunkizzation
        if is_ai():
            fill_ai_dir(
                only_used_files,
                _VAULT_DIR,
                AI_CONFIG_PATH,
                AI_DOCUMENTS_PATH,
                AI_CHUNK_PATH,
                AI_MANIFEST_PATH,
            )

        print("[AI] Indexing Done!")

    except Exception as e:
        print(f"Error while building the AI Index: {e}")
        sys.exit(1)


def clean_index() -> None:
    if is_bank():
        print("Error: The AI functionalities works only in local Vault.")
        sys.exit(1)

    try:
        if not is_vault():
            print("Error: The AI Index needs a initialized Vault!")
            sys.exit(1)

        if not is_ai():
            print("Error: The AI dir .ai/ already deleted!")
            sys.exit(1)
        else:
            remove_ai_dir()
            if not is_ai():
                print("[AI] .ai/ directory cleared!")
            else:
                print("Error: Impossible cleaning .ai/ dir!")

    except Exception as e:
        print(f"Error while building the AI Index: {e}")
        sys.exit(1)
