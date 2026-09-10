import json
import math
import time

from ollama import Client
from typing import TypedDict

from src.ai_embedding.config_ai import (
    AI_EMBEDDING_PATH,
    AI_CHUNK_PATH,
    OLLAMA_HOST,
    EMBEDDING_MODEL,
    LLM_MODEL,
    TOP_K,
)


class SearchResult(TypedDict):
    chunk_id: str
    content: str
    similarity: float


class ChunkData(TypedDict):
    id: str
    content: str


###############
# ENTRY POINT #
###############
def chat_loop() -> None:
    """
    Start an interactive terminal chat with the LLM.
    """

    print("Interactive LLM chat")
    print("Type 'q' or 'quit' to exit.\n")

    while True:
        question = input("> ").strip()

        # Handle {Q, QUIT, Quit, q, quit}
        if question.lower() in {"q", "quit"}:
            print("Goodbye!")
            break

        if not question:
            continue

        try:
            answer = make_query_to_LLM(question)

            print()
            print(answer)
            print()

        except Exception as exc:
            print(f"[ERROR] {exc}")


#################
# GENERIC UTILS #
#################
def _embed_query(
    client: Client,
    question: str,
) -> list[float]:
    """Generate an embedding for a user query."""

    response = client.embed(model=EMBEDDING_MODEL, input=question)
    embeddings = response.get("embeddings")

    if not embeddings:
        raise RuntimeError("Ollama returned no embedding for the query.")

    vector = embeddings[0]

    if not vector:
        raise RuntimeError("Ollama returned an empty query embedding.")

    return vector


def _cosine_similarity(
    vector_a: list[float],
    vector_b: list[float],
) -> float:
    """
    Calculate cosine similarity between two vectors.
    """

    if len(vector_a) != len(vector_b):
        raise ValueError("Vectors must have the same dimensions.")

    dot_product = sum((a * b) for a, b in zip(vector_a, vector_b))

    norm_a = math.sqrt(sum(a * a for a in vector_a))
    norm_b = math.sqrt(sum(b * b for b in vector_b))

    if norm_a == 0 or norm_b == 0:
        return 0.0

    return dot_product / (norm_a * norm_b)


def _search_similar_chunks(
    query_embedding: list[float],
    top_k: int = TOP_K,
) -> list[SearchResult]:
    """
    Find the most relevant chunks for a query.
    """

    if not AI_EMBEDDING_PATH.exists():
        raise FileNotFoundError(f"Embeddings file not found: " f"{AI_EMBEDDING_PATH}")

    if not AI_CHUNK_PATH.exists():
        raise FileNotFoundError(f"Chunks file not found: " f"{AI_CHUNK_PATH}")

    # ---------------------------------------------------------------
    # Load chunk contents
    # ---------------------------------------------------------------

    chunks: dict[str, ChunkData] = {}

    with AI_CHUNK_PATH.open("r", encoding="utf-8") as chunk_file:

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

            if not isinstance(chunk_id, str):
                raise RuntimeError(f"Invalid chunk id at line " f"{line_number}.")

            chunks[chunk_id] = chunk

    # ---------------------------------------------------------------
    # Calculate similarity
    # ---------------------------------------------------------------

    results: list[SearchResult] = []

    with AI_EMBEDDING_PATH.open("r", encoding="utf-8") as embedding_file:

        for line_number, line in enumerate(embedding_file, start=1):
            line = line.strip()

            if not line:
                continue

            try:
                embedding_data = json.loads(line)
            except json.JSONDecodeError as exc:
                raise RuntimeError(
                    f"Invalid JSON in embeddings.jsonl " f"at line {line_number}."
                ) from exc

            chunk_id = embedding_data.get("chunk_id")

            if not isinstance(chunk_id, str):
                raise RuntimeError(
                    f"Invalid chunk_id in embeddings.jsonl " f"at line {line_number}."
                )

            chunk = chunks.get(chunk_id)

            if chunk is None:
                continue

            chunk_embedding = embedding_data.get("embedding")

            if not isinstance(chunk_embedding, list):
                continue

            similarity = _cosine_similarity(query_embedding, chunk_embedding)

            results.append(
                {
                    "chunk_id": chunk_id,
                    "content": chunk["content"],
                    "similarity": similarity,
                }
            )

    results.sort(
        key=lambda item: item["similarity"],
        reverse=True,
    )

    return results[:top_k]


####################
# PRINCIPAL METHOD #
####################

# ########################################################################
# # Performance considerations
# ########################################################################
#
# The current implementation performs a linear scan of the entire
# embeddings.jsonl file for every user query.
#
# For each query the pipeline is therefore:
#
#     user question
#          |
#          v
#     generate query embedding
#          |
#          v
#     read all embeddings from embeddings.jsonl
#          |
#          v
#     calculate cosine similarity for every chunk
#          |
#          v
#     select the most relevant chunks
#          |
#          v
#     send the selected context to the LLM
#
# This approach is simple and perfectly acceptable for a small knowledge
# base, but its cost grows linearly with the number of stored embeddings.
# For example, with 50,000 chunks, every query requires approximately
# 50,000 similarity calculations and a complete scan of the embeddings
# file.
#
# The current JSONL-based approach is therefore intended as a simple
# first implementation rather than a scalable vector-search solution.
#
# For a larger vault, the embeddings should eventually be stored in a
# dedicated vector index/database such as FAISS, sqlite-vec, Chroma or
# Qdrant. The vector index would allow retrieving the top-K most similar
# chunks without scanning every embedding on each query.
#
# Another small optimization is avoiding a complete sort of all results
# when only the top-K chunks are required. Instead of:
#
#     results.sort(
#         key=lambda item: item["similarity"],
#         reverse=True,
#     )
#
#     results = results[:top_k]
#
# heapq.nlargest() can be used:
#
#     results = heapq.nlargest(
#         top_k,
#         results,
#         key=lambda item: item["similarity"],
#     )
#
# This avoids sorting the entire result set when only a small number of
# top results is required.
#
# Finally, chunk IDs should remain stable between indexing operations.
# The chunk hash should represent only the actual chunk content.
# This allows the incremental embedding process to distinguish between:
#
#     unchanged chunk -> reuse existing embedding
#     modified chunk  -> generate new embedding
#     new chunk       -> generate new embedding
#     removed chunk   -> remove existing embedding
#
# This prevents unnecessary calls to the embedding model and is especially
# important when the Markdown vault contains a large number of chunks.


def make_query_to_LLM(question: str) -> str:
    """
    Answer a user question using RAG.

    The question is embedded, the most relevant chunks are
    retrieved from the embedding database, and those chunks
    are passed as context to the LLM.
    """

    total_start = time.perf_counter()

    client = Client(host=OLLAMA_HOST)

    # ---------------------------------------------------------------
    # Embed question
    # ---------------------------------------------------------------

    print("[AI] Embedding query...")

    embedding_start = time.perf_counter()

    query_embedding = _embed_query(client, question)

    embedding_time = time.perf_counter() - embedding_start

    print(f"[AI] Query embedding completed in {embedding_time:.3f}s")

    # ---------------------------------------------------------------
    # Retrieve relevant chunks
    # ---------------------------------------------------------------

    print(f"[AI] Searching top {TOP_K} chunks...")

    search_start = time.perf_counter()

    relevant_chunks = _search_similar_chunks(
        query_embedding,
        top_k=TOP_K,
    )

    search_time = time.perf_counter() - search_start

    print(f"[AI] Vector search completed in {search_time:.3f}s")

    if not relevant_chunks:
        total_time = time.perf_counter() - total_start

        print(f"[AI] Total query time: {total_time:.3f}s")

        return "I couldn't find any relevant information " "in the knowledge base."

    # ---------------------------------------------------------------
    # Build context
    # ---------------------------------------------------------------

    context_parts: list[str] = []

    for index, chunk in enumerate(
        relevant_chunks,
        start=1,
    ):
        context_parts.append(
            f"--- Context {index} "
            f"(similarity: {chunk['similarity']:.4f}) ---\n"
            f"{chunk['content']}"
        )

    context = "\n\n".join(context_parts)

    # ---------------------------------------------------------------
    # Prompt
    # ---------------------------------------------------------------

    prompt = f"""
You are an assistant answering questions using
a private knowledge base.

Use the context below to answer the user's question.

Rules:
- Answer using the provided context whenever possible.
- Do not invent information that is not present in the context.
- If the context does not contain enough information,
clearly say that you don't know.
- Be concise but informative.
- Answer in the same language of the User question.

Context:

{context}

User question:

{question}
"""

    # ---------------------------------------------------------------
    # Ask LLM
    # ---------------------------------------------------------------

    print(f"[AI] Asking LLM: {LLM_MODEL}")

    llm_start = time.perf_counter()

    response = client.chat(
        model=LLM_MODEL,
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
    )

    llm_time = time.perf_counter() - llm_start

    print(f"[AI] LLM response received in {llm_time:.3f}s")

    answer = response.get(
        "message",
        {},
    ).get("content")

    if not isinstance(answer, str):
        raise RuntimeError("Ollama returned an invalid LLM response.")

    # ---------------------------------------------------------------
    # Total time
    # ---------------------------------------------------------------

    total_time = time.perf_counter() - total_start

    print(f"[AI] Total query time: {total_time:.3f}s")

    return answer
