from dataclasses import dataclass, asdict
from typing import Dict, Any

@dataclass
class LlmResponse:
    model: str
    respose_txt: str
    input_tokens: int
    output_tokens: int
    response_time: float

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LllmResponse":
        return cls(
            model=data["model"],
            respose_txt=data["respose_txt"],
            input_tokens=data["input_tokens"],
            output_tokens=data["output_tokens"],
            response_time=data["response_time"],
        )
