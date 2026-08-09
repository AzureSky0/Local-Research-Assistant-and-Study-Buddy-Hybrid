from dataclasses import dataclass


@dataclass(slots=True)
class WorkspaceCreateDTO:
    name: str
    description: str | None = None
    icon: str = "folder"
    color: str = "blue"