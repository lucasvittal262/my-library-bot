from dataclasses import dataclass, asdict
from typing import List, Dict, Any


@dataclass
class EmbeddingResponse:
    tokens_consumed: int
    embedding: List[float]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EmbeddingResponse":
        return cls(
            tokens_consumed=data["tokens_consumed"],
            embedding=data["embedding"],
        )

@dataclass
class BookMetadata:
    description: str
    pages: int
    title: str
    domain: str
    launch_year: int

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BookMetadata":
        return cls(
            description=data["description"],
            pages=data["pages"],
            title=data["title"],
            domain=data["domain"],
            launch_yer=data["launch_year"],
        )
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class BookChunk:
    text: str
    page: int
    tokens_size: int
    book_metadata: BookMetadata

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BookChunk":
        return cls(
            text=data["text"],
            tokens_size=data["tokens_size"],
            tokens=data["title"],
            book_metadata=BookMetadata.from_dict(data["book_metadata"]),
        )