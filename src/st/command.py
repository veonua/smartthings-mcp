from pydantic import BaseModel

from .literals import Capability

class Command(BaseModel):
    component: str
    capability: Capability
    command: str
    arguments: list | None = None

    def to_dict(self) -> dict:
        return {
            "component": self.component or "main",
            "capability": self.capability,
            "command": self.command,
            "arguments": self.arguments or []
        }