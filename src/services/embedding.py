from openai import OpenAI
from config.config import get_configs
from dataclasses import dataclass, asdict
from typing import List, Dict, Any
from abc import ABC, abstractmethod


@dataclass
class OpenAIEmbeddingResponse:
    tokens_consumed: int
    embedding: List[float]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class EmbeddingService(ABC):
    @abstractmethod
    def get_embedding(self, text: str) -> OpenAIEmbeddingResponse:
        """
        Generate an embedding for a single text input.
        """
        pass


class OpenAIEmbeddingService(EmbeddingService):
    def __init__(self, embedding_model: str):
        app_configs = get_configs()
        self.openai_client = OpenAI(api_key=app_configs.openai_api_key)
        self.embedding_model = embedding_model

    def get_embedding(self, text: str) -> OpenAIEmbeddingResponse:
        response = self.openai_client.embeddings.create(
            model=self.embedding_model, input=text
        )

        return OpenAIEmbeddingResponse(
            tokens_consumed=response.usage.total_tokens,
            embedding=response.data[0].embedding,
        )
