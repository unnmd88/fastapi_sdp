import datetime
from typing import Annotated, Any

from pydantic import BaseModel, IPvAnyAddress, Field, ConfigDict


class TrafficLightsObjectsRequest(BaseModel):
    ipv4: Annotated[IPvAnyAddress, Field(default=None)]
    num: Annotated[str, Field(default=None)]

class TrafficLightsObjectsResponce(BaseModel):
    model_config = ConfigDict()
    id: int
    number: Any
    description: Any
    type_controller: Any
    group: Any
    ip_adress: Any
    address: Any
    time_create: datetime.datetime
    time_update: datetime.datetime