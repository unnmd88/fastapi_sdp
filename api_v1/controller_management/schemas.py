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
    ipv4: Annotated[IPvAnyAddress, Field(alias='ipv4Address')]


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


class GetStateResponse(BaseModel):

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "Foo",
                    "description": "A very nice Item",
                    "price": 35.4,
                    "tax": 3.2,
                    "dict": {
                        "raw_data": "VA"
                    }
                }
            ]
        }
    }


    # {
    #     "start_time": 1738355663,
    #     "request_errors": null,
    #     "host_id": 1,
    #     "protocol": "http",
    #     "valid_data_request": null,
    #     "type_controller": "Swarco",
    #     "address": null,
    #     "type": null,
    #     "request_execution_time": 1,
    #     "request_entity": [
    #         "get_state"
    #     ],
    #     "responce_entity": {
    #         "raw_data": {
    #             "current_states": {
    #                 "basic": {
    #                     "current_mode": "VA",
    #                     "current_stage": "S1/S1",
    #                     "current_stage_time": "0",
    #                     "current_cyc": "190",
    #                     "current_plan": "P1Ка",
    #                     "system_time": "31.01-23:35:17",
    #                     "current_state_buttons": "SIGNALS=ON",
    #                     "web_content": [
    #                         "*** ITC-2 Linux  ***",
    #                         "13703 31.01-23:35:17",
    #                         "P1Ка      VA     190",
    #                         "1-1 ВКЛ_ОШ S1/S1 0  ",
    #                         "1 0 0 0 0 0 0 0",
    #                         "SIGNALS=ON"
    #                     ]
    #                 }
    #             }
    #         }
    #     },
    #     "request_time": "2025-01-31 23:34:23"
    # }

