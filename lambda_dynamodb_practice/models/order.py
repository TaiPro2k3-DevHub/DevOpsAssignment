import time
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any

@dataclass
class Order:
    userId: str
    orderId: str
    total: Any
    status: str = "pending"
    created_at: Optional[int] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = int(time.time())

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        return {k: v for k, v in data.items() if v is not None}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Order":
        return cls(
            userId=data.get("userId", ""),
            orderId=data.get("orderId", ""),
            total=data.get("total", 0),
            status=data.get("status", "pending"),
            created_at=data.get("created_at")
        )
