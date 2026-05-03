from unittest.mock import Mock

import pytest
from qdrant_client import models

import repositories.qdrant as qdrant_repository
from repositories.qdrant import QdrantVectorDB


class ArrayLike:
    def __init__(self, values: list[int] | list[float]) -> None:
        self._values = values

    def tolist(self) -> list[int] | list[float]:
        return self._values


class SparseEmbeddingStub:
    def __init__(self, indices: list[int], values: list[float]) -> None:
        self.indices = ArrayLike(indices)
        self.values = ArrayLike(values)


class QueryResponseStub:
    def __init__(self, points: list[models.ScoredPoint]) -> None:
        self.points = points


@pytest.fixture
def qdrant_client_mock(monkeypatch: pytest.MonkeyPatch) -> Mock:
    client = Mock()
    monkeypatch.setattr(qdrant_repository, "QdrantClient", Mock(return_value=client))
    return client


def test_hybrid_search_builds_qdrant_prefetches(qdrant_client_mock: Mock) -> None:
    dense_vector = [0.1, 0.2, 0.3]
    sparse_embedding = SparseEmbeddingStub(indices=[10, 20], values=[0.7, 0.9])
    vector_db = QdrantVectorDB(collection_name="cities", url="http://localhost:6333")

    vector_db.get_docs_by_hibrid_search(
        dense_vector_input=dense_vector,
        sparse_vector_input=sparse_embedding,
        top_k=3,
    )

    qdrant_client_mock.query_points.assert_called_once()

    _, kwargs = qdrant_client_mock.query_points.call_args
    assert kwargs["prefetch"][0] == models.Prefetch(
        query=dense_vector,
        using="dense",
        limit=6,
    )
    assert kwargs["prefetch"][1] == models.Prefetch(
        query=models.SparseVector(indices=[10, 20], values=[0.7, 0.9]),
        using="sparse",
        limit=6,
    )
    assert kwargs["query"] == models.FusionQuery(fusion=models.Fusion.RRF)
    assert kwargs["with_payload"] is True
    assert kwargs["limit"] == 3


def test_hybrid_search_returns_qdrant_output(qdrant_client_mock: Mock) -> None:
    expected_output = QueryResponseStub(
        points=[
            models.ScoredPoint(
                id=2,
                version=1,
                score=1.0,
                payload={"city": "New York"},
            ),
            models.ScoredPoint(
                id=0,
                version=1,
                score=0.6666667,
                payload={"city": "London"},
            ),
            models.ScoredPoint(
                id=3,
                version=1,
                score=0.45,
                payload={"city": "Beijing"},
            ),
        ]
    )
    qdrant_client_mock.query_points.return_value = expected_output
    vector_db = QdrantVectorDB(collection_name="cities", url="http://localhost:6333")

    result = vector_db.get_docs_by_hibrid_search(
        dense_vector_input=[0.1],
        sparse_vector_input=SparseEmbeddingStub(indices=[1], values=[1.0]),
        top_k=1,
    )

    assert result.points == expected_output.points
    assert [point.payload for point in result.points] == [
        {"city": "New York"},
        {"city": "London"},
        {"city": "Beijing"},
    ]
    assert [point.score for point in result.points] == [1.0, 0.6666667, 0.45]


def test_hybrid_search_uses_collection_name(qdrant_client_mock: Mock) -> None:
    vector_db = QdrantVectorDB(collection_name="my_collection", url="http://localhost:6333")

    vector_db.get_docs_by_hibrid_search(
        dense_vector_input=[0.1],
        sparse_vector_input=SparseEmbeddingStub(indices=[1], values=[1.0]),
        top_k=1,
    )

    args, _ = qdrant_client_mock.query_points.call_args
    assert args == ("my_collection",)
