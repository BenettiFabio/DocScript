# from ollama import Client

# from src.ai_embedding.config_ai import (
#     AI_EMBEDDING_PATH,
#     AI_CHUNK_PATH,
# )

# OLLAMA_HOST = "http://localhost:11434"
# EMBEDDING_MODEL = "qwen3-embedding:0.6b"


def embedding_ai() -> None:
    """
    Ollama embedding model connection.
    """

    print("[AI] Connecting to Ollama...")

    # client = Client(host=OLLAMA_HOST)

    # print(f"[AI] Using embedding model: {EMBEDDING_MODEL}")

    # ########
    # # TEST #
    # ########
    # response = client.embed(model=EMBEDDING_MODEL,
    #                         input="This is a test document.")

    # embeddings = response["embeddings"]

    # if not embeddings:
    #     raise RuntimeError("Ollama returned no embeddings.")

    # vector = embeddings[0]

    # print("[AI] Embedding generated successfully.")
    # print(f"[AI] Vector dimensions: {len(vector)}")
