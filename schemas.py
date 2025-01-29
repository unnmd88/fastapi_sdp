from pydantic import BaseModel, IPvAnyAddress, Field
from typing import Annotated


class GetIntersectionData(BaseModel):
    ipv4: Annotated[IPvAnyAddress, Field(default=None)]
    num: Annotated[str, Field(default=None)]

