"""Local embeddings via sentence-transformers. Free, offline after first model download."""
from __future__ import annotations

from functools import lru_cache

from .config import load_config


@lru_cache(maxsize=1)
def get_model():
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(load_config()["embedding"]["model"])


def embed_texts(texts: list[str]):
    """Embed texts, L2-normalized so cosine similarity is a plain dot product."""
    return get_model().encode(texts, normalize_embeddings=True, show_progress_bar=False)
