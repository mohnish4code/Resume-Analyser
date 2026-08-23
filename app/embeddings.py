"""
Embedding-based semantic similarity.

This module converts resume and job-description text into
sentence embeddings and calculates cosine similarity.

This module is intentionally independent from the existing
ATS scoring pipeline so existing functionality is not affected.
"""

from functools import lru_cache

import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity


# Lightweight and reliable general-purpose embedding model.
MODEL_NAME = "all-MiniLM-L6-v2"


@lru_cache(maxsize=1)
def get_embedding_model() -> SentenceTransformer:
    """
    Load the embedding model once and reuse it.

    The model is cached so every API request does not reload
    the model from disk/memory.
    """
    return SentenceTransformer(MODEL_NAME)


def generate_embedding(text: str) -> np.ndarray:
    """
    Generate an embedding vector for the supplied text.
    """

    if not text or not text.strip():
        raise ValueError("Text cannot be empty.")

    model = get_embedding_model()

    embedding = model.encode(
        text,
        convert_to_numpy=True,
        normalize_embeddings=True,
    )

    return embedding


def calculate_similarity(
    text_a: str,
    text_b: str,
) -> float:
    """
    Calculate cosine similarity between two text inputs.

    Returns:
        Similarity score between 0 and 100.
    """

    if not text_a or not text_a.strip():
        return 0.0

    if not text_b or not text_b.strip():
        return 0.0

    embedding_a = generate_embedding(text_a)
    embedding_b = generate_embedding(text_b)

    similarity = cosine_similarity(
        embedding_a.reshape(1, -1),
        embedding_b.reshape(1, -1),
    )[0][0]

    # Cosine similarity normally lies between -1 and 1.
    # Convert it to a 0-100 percentage-like score.
    score = ((float(similarity) + 1.0) / 2.0) * 100.0

    return round(min(100.0, max(0.0, score)), 2)


def test_embeddings() -> dict:
    """
    Simple standalone test for the embedding module.

    This can be used before integrating embeddings into
    the existing ATS pipeline.
    """

    text_a = (
        "Python machine learning engineer with experience "
        "in NumPy, Pandas and Scikit-learn."
    )

    text_b = (
        "AI/ML engineer skilled in Python and machine learning "
        "using Pandas, NumPy and Scikit-learn."
    )

    score = calculate_similarity(text_a, text_b)

    return {
        "model": MODEL_NAME,
        "similarity_score": score,
    }


if __name__ == "__main__":
    result = test_embeddings()

    print("Embedding test")
    print("-------------------------")
    print(f"Model: {result['model']}")
    print(f"Similarity Score: {result['similarity_score']}%")