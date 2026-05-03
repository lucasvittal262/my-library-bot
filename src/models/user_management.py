from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class UserData:
    id: str
    name: str
    jwt_token: str

    def from_dict(cls, data: Dict[str, Any]) -> "UserData":
        return cls(id=data["id"], name=data["name"], jwt_token=data["token"])
