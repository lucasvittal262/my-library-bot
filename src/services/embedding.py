from openai import OpenAI
from config.config import get_configs
from models.search import EmbeddingResponse

from abc import ABC, abstractmethod




class EmbeddingService(ABC):
    @abstractmethod
    def get_embedding(self, text: str) -> EmbeddingResponse:
        """
        Generate an embedding for a single text input.
        """
        pass


class OpenAIEmbeddingService(EmbeddingService):
    def __init__(self, embedding_model: str):
        app_configs = get_configs()
        self.openai_client = OpenAI(api_key=app_configs.openai_api_key)
        self.embedding_model = embedding_model

    def get_embedding(self, text: str) -> EmbeddingResponse:
        response = self.openai_client.embeddings.create(
            model=self.embedding_model, input=text
        )

        return EmbeddingResponse(
            tokens_consumed=response.usage.total_tokens,
            embedding=response.data[0].embedding,
        )
