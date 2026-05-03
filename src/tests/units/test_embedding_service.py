from types import SimpleNamespace
from unittest.mock import Mock

import pytest

import services.embedding as embedding_module
from services.embedding import (
    EmbeddingService,
    EmbeddingResponse,
    OpenAIEmbeddingService,
)


@pytest.fixture
def openai_client_mock(monkeypatch: pytest.MonkeyPatch) -> Mock:
    client = Mock()
    openai_constructor = Mock(return_value=client)

    monkeypatch.setattr(
        embedding_module,
        "get_configs",
        Mock(return_value=SimpleNamespace(openai_api_key="test-api-key")),
    )
    monkeypatch.setattr(embedding_module, "OpenAI", openai_constructor)

    return client


def make_embedding_response(
    embedding: list[float] | None = None,
    total_tokens: int = 7,
) -> SimpleNamespace:
    return SimpleNamespace(
        usage=SimpleNamespace(total_tokens=total_tokens),
        data=[
            SimpleNamespace(
                embedding=embedding or [0.1, 0.2, 0.3],
            )
        ],
    )


def test_get_embedding_calls_openai_with_model_and_input(
    openai_client_mock: Mock,
) -> None:
    openai_client_mock.embeddings.create.return_value = make_embedding_response()
    service = OpenAIEmbeddingService(embedding_model="text-embedding-3-small")

    service.get_embedding("library search query")

    openai_client_mock.embeddings.create.assert_called_once_with(
        model="text-embedding-3-small",
        input="library search query",
    )


def test_get_embedding_returns_openai_embedding_response(
    openai_client_mock: Mock,
) -> None:
    openai_client_mock.embeddings.create.return_value = make_embedding_response(
        embedding=[0.4, 0.5, 0.6],
        total_tokens=12,
    )
    service = OpenAIEmbeddingService(embedding_model="text-embedding-3-small")

    response = service.get_embedding("some text")

    assert isinstance(response, EmbeddingResponse)
    assert response.tokens_consumed == 12
    assert response.embedding == [0.4, 0.5, 0.6]


def test_openai_embedding_service_implements_embedding_service() -> None:
    service = OpenAIEmbeddingService(embedding_model="text-embedding-3-small")

    assert isinstance(service, EmbeddingService)


def test_get_embedding_propagates_openai_api_exceptions(
    openai_client_mock: Mock,
) -> None:
    expected_error = RuntimeError("rate limit exceeded")
    openai_client_mock.embeddings.create.side_effect = expected_error
    service = OpenAIEmbeddingService(embedding_model="text-embedding-3-small")

    with pytest.raises(RuntimeError, match="rate limit exceeded") as exc_info:
        service.get_embedding("some text")

    assert exc_info.value is expected_error


@pytest.mark.parametrize(
    "input_text",
    [
        "",
        "   \n\t   ",
        "long text " * 10_000,
    ],
)
def test_get_embedding_handles_boundary_text_inputs(
    openai_client_mock: Mock,
    input_text: str,
) -> None:
    openai_client_mock.embeddings.create.return_value = make_embedding_response(
        embedding=[0.9],
        total_tokens=1,
    )
    service = OpenAIEmbeddingService(embedding_model="text-embedding-3-small")

    response = service.get_embedding(input_text)

    openai_client_mock.embeddings.create.assert_called_once_with(
        model="text-embedding-3-small",
        input=input_text,
    )
    assert response == EmbeddingResponse(tokens_consumed=1, embedding=[0.9])
