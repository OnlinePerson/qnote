from dataclasses import dataclass, field
from datetime import datetime
from typing import List


@dataclass
class Note:
    content: str
    tags: List[str] = field(default_factory=list)
    id: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def tags_str(self) -> str:
        return ",".join(self.tags) if self.tags else ""

    @classmethod
    def from_row(cls, row: tuple) -> "Note":
        id_, content, tags_str, created_at, updated_at = row
        tags = [t.strip() for t in tags_str.split(",") if t.strip()] if tags_str else []
        return cls(
            id=id_,
            content=content,
            tags=tags,
            created_at=datetime.fromisoformat(created_at),
            updated_at=datetime.fromisoformat(updated_at),
        )
