"""
Retrieval over knowledge/rag_reference.md: Chroma (in-memory, rebuilt
fresh every run) + local MiniLM embeddings. See ARCHITECTURE.md Section 1a
for the locked chunking/retrieval configuration.

Chroma is intentionally NOT persisted (no persist_directory) -- the
corpus is tiny and static, so rebuilding the index on every run is cheap
and entirely avoids a persisted store falling out of sync with
rag_reference.md.
"""

from langchain_chroma import Chroma
from langchain_core.embeddings import Embeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer

from app.config import (
    CHUNK_OVERLAP_TOKENS,
    CHUNK_SEPARATORS,
    CHUNK_SIZE_TOKENS,
    KNOWLEDGE_BASE_PATH,
    TOP_K,
)

# Locked in ARCHITECTURE.md ("Embeddings: local sentence-transformers/all-
# MiniLM-L6-v2") -- not a .env-tunable value like the generator/evaluator
# models, so it lives here rather than in config.py.
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


_cached_model: SentenceTransformer | None = None


class MiniLMEmbeddings(Embeddings):
    """Local, no-API-key embedding function backed by sentence-transformers.

    A small custom wrapper around SentenceTransformer rather than pulling
    in the langchain-huggingface package for a single model -- only
    embed_documents/embed_query are needed to satisfy langchain_chroma.

    The model itself is cached at module level (loaded once, reused across
    calls) -- retrieve_top_k() constructs a new MiniLMEmbeddings on every
    call (once per /generate request, via retrieve_context), and without
    this cache each call reloaded the model weights from scratch. Measured
    live via LangSmith: ~7.5s of retrieve_context latency was pure model-
    load overhead, not retrieval itself. This is unrelated to the locked
    "rebuild the Chroma index fresh every run" decision -- that's about
    the vector index (cheap corpus, avoids staleness), not the static
    model weights, which are safe to share across calls within a process.
    """

    def __init__(self, model_name: str = EMBEDDING_MODEL_NAME) -> None:
        global _cached_model
        if _cached_model is None:
            _cached_model = SentenceTransformer(model_name)
        self._model = _cached_model

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self._model.encode(list(texts), convert_to_numpy=True).tolist()

    def embed_query(self, text: str) -> list[float]:
        return self._model.encode([text], convert_to_numpy=True)[0].tolist()


def _load_and_chunk_knowledge_base() -> list[str]:
    with open(KNOWLEDGE_BASE_PATH, "r", encoding="utf-8") as f:
        text = f.read()

    splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        encoding_name="cl100k_base",
        chunk_size=CHUNK_SIZE_TOKENS,
        chunk_overlap=CHUNK_OVERLAP_TOKENS,
        separators=CHUNK_SEPARATORS,
    )
    return splitter.split_text(text)


def retrieve_top_k(query: str, top_k: int = TOP_K) -> list[str]:
    """Build a fresh in-memory Chroma index from the knowledge base and
    return the top_k chunks most relevant to `query`.

    Called exactly once per run (by the retrieve_context graph node,
    added in build step 9) -- not re-run on retries, since the topic
    doesn't change between generation attempts.
    """
    chunks = _load_and_chunk_knowledge_base()
    vectorstore = Chroma.from_texts(texts=chunks, embedding=MiniLMEmbeddings())
    results = vectorstore.similarity_search(query, k=top_k)
    return [doc.page_content for doc in results]
