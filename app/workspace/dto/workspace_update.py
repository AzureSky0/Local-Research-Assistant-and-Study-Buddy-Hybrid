from dataclasses import dataclass


@dataclass(slots=True)
class WorkspaceUpdateDTO:
    name: str | None = None
    description: str | None = None
    icon: str | None = None
    color: str | None = None
    is_archived: bool | None = None