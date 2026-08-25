from pathlib import Path

# --index-ai
# ├── 1. [x] Trova vault/main.md
# ├── 2. [x] Ricostruisce il tree ricorsivamente
# ├── 3. [x] Trova tutte le note effettive
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


def fill_ai_dir(
    matchingFiles: list[str],
    configPath: Path,
    documentPath: Path,
    chunkPath: Path,
    manifestPath: Path,
) -> None:

    print("[AI] Writing: .ai/config.json")
    create_config(matchingFiles, configPath)

    print("[AI] Writing: .ai/documents.json")
    create_documents(matchingFiles, configPath)

    print("[AI] Writing: .ai/chunks.jsonl")
    create_chunks(matchingFiles, chunkPath)

    print("[AI] Writing: .ai/manufest.json")
    create_manifest(matchingFiles, manifestPath)


def create_config(matchingFiles: list[str], dst: Path) -> None:
    """
    Create a config file that serves to make the index reproducible.
    """
    print("A")
    print(dst)


def create_documents(matchingFiles: list[str], dst: Path) -> None:
    """
    Create an index of all notes with the specifics of each one
    """
    print("B")
    print(dst)


def create_chunks(matchingFiles: list[str], dst: Path) -> None:
    """
    Result of the chunking procedure,
    with the max and min parameters selected in config.json
    """
    print("C")
    print(dst)


def create_manifest(matchingFiles: list[str], dst: Path) -> None:
    """
    This is to know the general state.
    """
    print("D")
    print(dst)
