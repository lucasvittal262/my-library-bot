import os
from uuid import uuid4

import pytest
from fastembed import SparseTextEmbedding
from fastembed.sparse.sparse_embedding_base import SparseEmbedding
from qdrant_client import QdrantClient, models
from qdrant_client.http.exceptions import ResponseHandlingException, UnexpectedResponse

from repositories.qdrant import QdrantVectorDB


CITIES_DESCRIPTIONS = {
    "London": (
        "A global financial and cultural capital, known for its history, "
        "iconic landmarks like Big Ben and the Thames, and its influence in "
        "finance, fashion, and the arts."
    ),
    "Moscow": (
        "Russia's capital and political center, famous for the Kremlin, Red "
        "Square, and its rich history blending imperial and Soviet eras."
    ),
    "New York": (
        "A fast-paced global hub for finance, media, and culture, home to "
        "Wall Street, Broadway, and landmarks like the Statue of Liberty."
    ),
    "Beijing": (
        "China's capital, combining ancient heritage like the Forbidden City "
        "with modern political and economic significance."
    ),
    "Mumbai": (
        "India's financial powerhouse and entertainment capital, known for "
        "Bollywood, dense urban life, and coastal energy."
    ),
}

DENSE_VECTORS = {
    "London": [0.35, 0.80, 0.15, 0.10],
    "Moscow": [0.15, 0.25, 0.85, 0.05],
    "New York": [0.95, 0.10, 0.10, 0.10],
    "Beijing": [0.20, 0.30, 0.70, 0.35],
    "Mumbai": [0.60, 0.20, 0.10, 0.75],
}

QUERY_TEXT = "A city that is a global center for finance, media, and culture"
QUERY_DENSE_VECTOR = [0.98, 0.08, 0.08, 0.08]


def to_qdrant_sparse_vector(sparse_embedding: SparseEmbedding) -> models.SparseVector:
    return models.SparseVector(
        indices=sparse_embedding.indices.tolist(),
        values=sparse_embedding.values.tolist(),
    )


def create_collection(
    client: QdrantClient,
    collection_name: str,
    dim_dense_vector: int,
) -> None:
    if client.collection_exists(collection_name=collection_name):
        client.delete_collection(collection_name=collection_name)

    client.create_collection(
        collection_name=collection_name,
        vectors_config={
            "dense": models.VectorParams(
                size=dim_dense_vector,
                distance=models.Distance.COSINE,
            )
        },
        sparse_vectors_config={
            "sparse": models.SparseVectorParams(modifier=models.Modifier.IDF)
        },
    )


@pytest.fixture
def qdrant_url() -> str:
    return os.getenv("QDRANT_TEST_URL", "http://localhost:6333")


@pytest.fixture
def qdrant_client(qdrant_url: str) -> QdrantClient:
    client = QdrantClient(url=qdrant_url)
    try:
        client.get_collections()
    except (ResponseHandlingException, UnexpectedResponse) as exc:
        pytest.skip(f"Qdrant is not available at {qdrant_url}: {exc}")
    return client


@pytest.mark.integration
def test_hybrid_search_returns_expected_city_ranking(
    qdrant_client: QdrantClient,
    qdrant_url: str,
) -> None:
    collection_name = f"test_hybrid_cities_{uuid4().hex[:8]}"
    bm25_model = SparseTextEmbedding(model_name="qdrant/bm25")

    create_collection(
        client=qdrant_client,
        collection_name=collection_name,
        dim_dense_vector=len(QUERY_DENSE_VECTOR),
    )

    try:
        qdrant_client.upsert(
            collection_name=collection_name,
            wait=True,
            points=[
                models.PointStruct(
                    id=idx,
                    vector={
                        "dense": DENSE_VECTORS[city],
                        "sparse": to_qdrant_sparse_vector(
                            next(bm25_model.embed(description))
                        ),
                    },
                    payload={"city": city},
                )
                for idx, (city, description) in enumerate(CITIES_DESCRIPTIONS.items())
            ],
        )

        vector_db = QdrantVectorDB(collection_name=collection_name, url=qdrant_url)
        results = vector_db.get_docs_by_hibrid_search(
            dense_vector_input=QUERY_DENSE_VECTOR,
            sparse_vector_input=next(bm25_model.embed(QUERY_TEXT)),
            top_k=3,
        )

        returned_cities = [point.payload["city"] for point in results.points]

        assert len(results.points) == 3
        assert returned_cities[0] == "New York"
        
    finally:
        if qdrant_client.collection_exists(collection_name=collection_name):
            qdrant_client.delete_collection(collection_name=collection_name)
