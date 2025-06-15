from typing import Optional
from pydantic import BaseModel


class Links(BaseModel):
    class Link(BaseModel):
        href: str

    next: Optional[Link] = None
    previous: Optional[Link] = None