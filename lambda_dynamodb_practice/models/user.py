import time
import uuid
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any

@dataclass
class User:
    id: str
    name: str
    email: str
    role: str = "user"
    age: Optional[int] = None
    created_at: Optional[int] = None

    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())
        if self.created_at is None:
            self.created_at = int(time.time())

    def to_dict(self, pk_name: str = "userId") -> Dict[str, Any]:
        data = asdict(self)
        # Gán giá trị vào partition key tương ứng (ví dụ: userId hoặc id)
        data[pk_name] = self.id
        # Loại bỏ các key None để DynamoDB không báo lỗi hoặc rác
        return {k: v for k, v in data.items() if v is not None}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "User":
        user_id = data.get("userId") or data.get("id") or str(uuid.uuid4())
        return cls(
            id=str(user_id),
            name=data.get("name", ""),
            email=data.get("email", ""),
            role=data.get("role", "user"),
            age=data.get("age"),
            created_at=data.get("created_at")
        )
