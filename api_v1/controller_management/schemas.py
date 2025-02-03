import datetime
import ipaddress
import json
from enum import StrEnum
from typing import Annotated, Any

from pydantic import BaseModel, IPvAnyAddress, Field, ConfigDict, field_validator, computed_field, AfterValidator
from pydantic.json_schema import model_json_schema

from sdp_lib.utils_common import check_ipv4


class AllowedControllers(StrEnum):
    SWARCO = 'Swarco'
    POTOK_P = 'Поток (P)'
    POTOK_S = 'Поток (S)'
    PEEK = 'Peek'


class AllowedMonitoringEntity(StrEnum):
    GET_STATE_BASE = 'get_state_base'
    GET_STATE_FULL = 'get_state_full'
    # GET_FULL_DATA = 'get_all_states'
    # SET_STAGE = 'set_stage'
    # SET_FLASH = 'set_flash'


class AllowedProtocolsRequest(StrEnum):
    SNMP = 'snmp'
    HTTP = 'http'
    AUTO = 'auto'


class TrafficLightsObjectsTableFields(StrEnum):
    IP_ADDRESS = 'ip_adress'
    NUMBER = 'number'


# class TrafficLightsObjectsRequest(BaseModel):
#     ipv4: Annotated[IPvAnyAddress, Field(default=None)]
#     num: Annotated[str, Field(default=None)]


# class TrafficLightsObjectsResponce(BaseModel):
#     model_config = ConfigDict()
#     id: int
#     number: Any
#     description: Any
#     type_controller: Any
#     group: Any
#     ip_adress: Any
#     address: Any
#     time_create: datetime.datetime
#     time_update: datetime.datetime


class GetStateResponse(BaseModel):

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "start_time": 1738355663,
                    "request_errors": None,
                    "host_id": 1,
                    "protocol": "http",
                    "valid_data_request": None,
                    "type_controller": "Swarco",
                    "address": None,
                    "type": None,
                    "request_execution_time": 1,
                    "request_entity": [
                        "get_state"
                    ],
                    "responce_entity": {
                        "raw_data": {
                            "current_states": {
                                "basic": {
                                    "current_mode": "VA",
                                    "current_stage": "S1/S1",
                                    "current_stage_time": "0",
                                    "current_cyc": "190",
                                    "current_plan": "P1Ка",
                                    "system_time": "31.01-23:35:17",
                                    "current_state_buttons": "SIGNALS=ON",
                                    "web_content": [
                                        "*** ITC-2 Linux  ***",
                                        "13703 31.01-23:35:17",
                                        "P1Ка      VA     190",
                                        "1-1 ВКЛ_ОШ S1/S1 0  ",
                                        "1 0 0 0 0 0 0 0",
                                        "SIGNALS=ON"
                                    ]
                                }
                            }
                        }
                    },
                    "request_time": "2025-01-31 23:34:23"
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


class RequestBase(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    type_controller: AllowedControllers
    host_id: str | None
    scn: str | None
    entity: str
    search_in_db: bool


class RequestCommon(RequestBase):

    ip_or_num: Annotated[str, Field(min_length=2, max_length=20)]
    # search_in_db_field: Annotated[str, Field(strict=True)]

    # @field_validator('search_in_db_field', mode='after')
    # def get_field_value(cls, value: str) -> str:
    #     """
    #     Определяет имя поля для поиска объекта в модели TrafficLightsObjects
    #     """
    #     if check_ipv4(value):
    #         return TrafficLightsObjectsTableFields.IP_ADDRESS
    #     return TrafficLightsObjectsTableFields.NUMBER

    @computed_field
    def search_in_db_field(self) -> str:
        if check_ipv4(self.ip_or_num):
            return TrafficLightsObjectsTableFields.IP_ADDRESS
        return TrafficLightsObjectsTableFields.NUMBER

class RequestBaseWithSearchInDb(RequestBase):
    search_in_db_field: Annotated[str, Field(min_length=2, max_length=20)]

    @field_validator('search_in_db_field', mode='after')
    def get_field_value(cls, value: str) -> str:
        """
        Определяет имя поля для поиска объекта в модели TrafficLightsObjects
        """
        if check_ipv4(value):
            return TrafficLightsObjectsTableFields.IP_ADDRESS
        return TrafficLightsObjectsTableFields.NUMBER


class SearchInDb(BaseModel):
    search_in_db_field: Annotated[str, Field(min_length=2, max_length=20)]

    @field_validator('search_in_db_field', mode='after')
    def get_field_value(cls, value: str) -> str:
        """
        Определяет имя поля для поиска объекта в модели TrafficLightsObjects
        """
        if check_ipv4(value):
            return TrafficLightsObjectsTableFields.IP_ADDRESS
        return TrafficLightsObjectsTableFields.NUMBER


# class GetStateAndSearchInDb(_SearchInDb):
#     entity: AllowedMonitoringEntity
#
#
# class GetState(RequestBase):
#     entity: AllowedMonitoringEntity


class GetStateRequest(BaseModel):
    model_config = ConfigDict(use_enum_values=True)
    hosts: dict[str, RequestBase]



# Annotated[str, Field(strict=True)
if __name__ == '__main__':
    data = {
        'type_controller': 'Swarco', 'host_id': 'string', 'scn': 'string',
        'entity': AllowedMonitoringEntity.GET_STATE_BASE, 'search_in_db': True
    }

    # j_data = json.dumps(data)
    # print(j_data)
    # print(type(j_data))
    # obj = MonitoringBase(**{'type_controller': 'Swarco', 'host_id': 'string', 'scn': 'string',
    #                   'entity': AllowedMonitoringEntity.GET_STATE_BASE, 'search_in_db': True,
    #                   })
    # print(obj.model_dump())
#############################
    obj2 = _SearchInDb(
        **{'type_controller': 'Swarco', 'host_id': 'string', 'scn': 'string',
          'entity': AllowedMonitoringEntity.GET_STATE_BASE, 'search_in_db': True,
           'field_value': '10.45.154.16'
    })
    print(obj2)
    print(obj2.field_value)
    print(obj2.model_dump())
