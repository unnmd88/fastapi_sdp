import datetime
from enum import StrEnum
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


class Ipv4(BaseModel):
    ipv4: IPvAnyAddress


class AllowedControllers(StrEnum):
    SWARCO = 'Swarco'
    POTOK_P = 'Поток (P)'
    POTOK_S = 'Поток (S)'
    PEEK = 'Peek'


class AllowedTypeRequestGetState(StrEnum):
    SNMP = 'snmp'
    HTTP = 'http'


class GetStateByIpv4(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    type_controller: AllowedControllers
    host_id: str | None
    scn: str | None
    type_request: AllowedTypeRequestGetState


class GetStateRequest:
    hosts: dict
