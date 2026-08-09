from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class Workspace:
    id: str
    name: str
    description: str | None
    icon: str
    color: str
    created_at: datetime
    updated_at: datetime
    last_opened_at: datetime | None
    is_archived: bool