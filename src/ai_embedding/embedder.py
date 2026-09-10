import json

from ollama import Client

from src.ai_embedding.config_ai import (
    AI_EMBEDDING_PATH,
    AI_CHUNK_PATH,
    OLLAMA_HOST,
    EMBEDDING_MODEL,
)


#################
# GENERIC UTILS #
#################
def _embed_chunk(
    client: Client,
    chunk: dict,
) -> dict:

    chunk_id = chunk["id"]
    content = chunk["content"]
    chunk_hash = chunk["hash"]

    response = client.embed(model=EMBEDDING_MODEL, input=content)

    embeddings = response.get("embeddings")

    if not embeddings:
        raise RuntimeError(f"Ollama returned no embedding " f"for chunk '{chunk_id}'.")

    vector = embeddings[0]

    if not vector:
        raise RuntimeError(
            f"Ollama returned an empty vector " f"for chunk '{chunk_id}'."
        )

    return {
        "chunk_id": chunk_id,
        "chunk_hash": chunk_hash,
        "model": EMBEDDING_MODEL,
        "dimensions": len(vector),
        "embedding": vector,
    }


def _is_embedding_valid(
    existing: dict,
    chunk: dict,
) -> bool:
    embedding = existing.get("embedding")

    if not isinstance(embedding, list):
        return False

    return (
        existing.get("chunk_hash") == chunk.get("hash")
        and existing.get("model") == EMBEDDING_MODEL
        and isinstance(existing.get("embedding"), list)
    )


####################
# PRINCIPAL METHOD #
####################
def embedding_ai() -> None:
    """
    Generate embeddings for all chunks in chunks.jsonl.
    All existing embeddings are overwritten.
    """

    print("[AI] Connecting to Ollama...")

    client = Client(host=OLLAMA_HOST)

    print(f"[AI] Using embedding model: {EMBEDDING_MODEL}")
    print(f"[AI] Reading chunks: {AI_CHUNK_PATH}")
    print(f"[AI] Writing embeddings: {AI_EMBEDDING_PATH}")

    if not AI_CHUNK_PATH.exists():
        raise FileNotFoundError(f"Chunks file not found: {AI_CHUNK_PATH}")

    AI_EMBEDDING_PATH.parent.mkdir(parents=True, exist_ok=True)

    chunk_count = 0

    with (
        AI_CHUNK_PATH.open("r", encoding="utf-8") as chunk_file,
        AI_EMBEDDING_PATH.open("w", encoding="utf-8") as embedding_file,
    ):
        for line_number, line in enumerate(chunk_file, start=1):
            line = line.strip()

            if not line:
                continue

            try:
                chunk = json.loads(line)
            except json.JSONDecodeError as exc:
                raise RuntimeError(
                    f"Invalid JSON in chunks.jsonl " f"at line {line_number}."
                ) from exc

            chunk_id = chunk.get("id")
            content = chunk.get("content")
            chunk_hash = chunk.get("hash")

            if not isinstance(chunk_id, str) or not chunk_id:
                raise RuntimeError(f"Chunk at line {line_number} " f"has invalid 'id'.")

            if not isinstance(content, str) or not content:
                raise RuntimeError(f"Chunk '{chunk_id}' has invalid 'content'.")

            if not isinstance(chunk_hash, str) or not chunk_hash:
                raise RuntimeError(f"Chunk '{chunk_id}' has invalid 'hash'.")

            print(f"[AI] Embedding chunk: {chunk_id}")

            embedding = _embed_chunk(client, chunk)

            embedding_file.write(
                json.dumps(
                    embedding,
                    ensure_ascii=False,
                    separators=(",", ":"),
                )
                + "\n"
            )

            embedding_file.flush()
            chunk_count += 1

    print("[AI] Embedding completed.")
    print(f"[AI] Chunks processed: {chunk_count}")
    print(f"[AI] Embeddings generated: {chunk_count}")


def embedding_upgrade() -> None:
    """
    Incrementally update embeddings.

    Existing embeddings are reused when the chunk has not changed
    and the embedding is still compatible with the current model.

    Only new or modified chunks are sent to Ollama.
    Removed chunks are removed from the embedding database.
    """

    print("[AI] Connecting to Ollama...")

    client = Client(host=OLLAMA_HOST)

    print(f"[AI] Using embedding model: {EMBEDDING_MODEL}")
    print(f"[AI] Reading chunks: {AI_CHUNK_PATH}")
    print(f"[AI] Reading embeddings: {AI_EMBEDDING_PATH}")

    if not AI_CHUNK_PATH.exists():
        raise FileNotFoundError(f"Chunks file not found: {AI_CHUNK_PATH}")

    # ####################################################################
    # # Read existing embeddings
    # ####################################################################

    existing_embeddings: dict[str, dict] = {}

    if AI_EMBEDDING_PATH.exists():
        with AI_EMBEDDING_PATH.open("r", encoding="utf-8") as embedding_file:

            for line_number, line in enumerate(embedding_file, start=1):
                line = line.strip()

                if not line:
                    continue

                try:
                    embedding = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise RuntimeError(
                        "Invalid JSON in embeddings.jsonl " f"at line {line_number}."
                    ) from exc

                chunk_id = embedding.get("chunk_id")

                if not isinstance(chunk_id, str) or not chunk_id:
                    raise RuntimeError(
                        "Embedding at line " f"{line_number} has invalid 'chunk_id'."
                    )

                if chunk_id in existing_embeddings:
                    raise RuntimeError(
                        f"Duplicate embedding for chunk " f"'{chunk_id}'."
                    )

                existing_embeddings[chunk_id] = embedding

    print(f"[AI] Existing embeddings: " f"{len(existing_embeddings)}")

    # ####################################################################
    # # Process chunks
    # ####################################################################

    updated_embeddings: dict[str, dict] = {}

    new_count = 0
    updated_count = 0
    unchanged_count = 0

    with AI_CHUNK_PATH.open("r", encoding="utf-8") as chunk_file:

        for line_number, line in enumerate(chunk_file, start=1):
            line = line.strip()

            if not line:
                continue

            try:
                chunk = json.loads(line)
            except json.JSONDecodeError as exc:
                raise RuntimeError(
                    "Invalid JSON in chunks.jsonl " f"at line {line_number}."
                ) from exc

            chunk_id = chunk.get("id")
            content = chunk.get("content")
            chunk_hash = chunk.get("hash")

            if not isinstance(chunk_id, str) or not chunk_id:
                raise RuntimeError(f"Chunk at line {line_number} " f"has invalid 'id'.")

            if not isinstance(content, str) or not content:
                raise RuntimeError(f"Chunk '{chunk_id}' has invalid 'content'.")

            if not isinstance(chunk_hash, str) or not chunk_hash:
                raise RuntimeError(f"Chunk '{chunk_id}' has invalid 'hash'.")

            if chunk_id in updated_embeddings:
                raise RuntimeError(
                    f"Duplicate chunk id " f"'{chunk_id}' at line {line_number}."
                )

            existing = existing_embeddings.get(chunk_id)

            # ------------------------------------------------------------
            # Existing and valid -> reuse embedding
            # ------------------------------------------------------------

            if existing is not None and _is_embedding_valid(existing, chunk):

                updated_embeddings[chunk_id] = existing
                unchanged_count += 1
                # print(f"[AI] Unchanged: {chunk_id}")
                continue

            # ------------------------------------------------------------
            # New or modified -> generate embedding
            # ------------------------------------------------------------

            if existing is None:
                new_count += 1
                print(f"[AI] New: {chunk_id}")

            else:
                updated_count += 1
                print(f"[AI] Changed: {chunk_id}")

            embedding = _embed_chunk(client, chunk)
            updated_embeddings[chunk_id] = embedding

    # ####################################################################
    # # Detect removed chunks
    # ####################################################################

    removed_ids = existing_embeddings.keys() - updated_embeddings.keys()
    removed_count = len(removed_ids)

    # ####################################################################
    # # Write updated embeddings
    # ####################################################################

    print(f"[AI] Writing embeddings: " f"{AI_EMBEDDING_PATH}")

    # Write to temporary file first.
    #
    # This prevents destroying the existing embeddings file if
    # something goes wrong during serialization/writing.

    temp_path = AI_EMBEDDING_PATH.with_suffix(".tmp")

    try:
        with temp_path.open("w", encoding="utf-8") as embedding_file:

            for embedding in updated_embeddings.values():
                embedding_file.write(
                    json.dumps(
                        embedding,
                        ensure_ascii=False,
                        separators=(",", ":"),
                    )
                    + "\n"
                )

        # Atomic replacement of the old database.
        temp_path.replace(AI_EMBEDDING_PATH)

    except Exception:
        if temp_path.exists():
            temp_path.unlink()

        raise

    # ####################################################################
    # # Summary
    # ####################################################################

    print("[AI] Embedding update completed.")
    print(f"[AI] Unchanged: {unchanged_count}")
    print(f"[AI] New:       {new_count}")
    print(f"[AI] Updated:   {updated_count}")
    print(f"[AI] Removed:   {removed_count}")
    print(f"[AI] Total:     {len(updated_embeddings)}")
