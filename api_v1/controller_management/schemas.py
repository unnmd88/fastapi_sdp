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


class AllowedManagementEntity(StrEnum):
    SET_STAGE = 'set_stage'
    SET_DARK = 'set_dark'


class AllowedProtocolsRequest(StrEnum):
    SNMP = 'snmp'
    HTTP = 'http'
    AUTO = 'auto'


class TrafficLightsObjectsTableFields(StrEnum):
    IP_ADDRESS = 'ip_adress'
    NUMBER = 'number'
    ALL = '*'


class DataHostFields(StrEnum):
    ERRORS = 'errors'

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


class RequestBase(BaseModel):
    """
    Базовый класс с настройками и полями для любого запроса(Monitoring/Management)
    """

    model_config = ConfigDict(use_enum_values=True, extra='allow')

    type_controller: AllowedControllers
    host_id: Annotated[str, Field(default=None, max_length=20)]
    scn: Annotated[str, Field(default=None, max_length=10)]
    entity: AllowedMonitoringEntity | AllowedManagementEntity
    search_in_db: Annotated[bool, Field(default=False)]

    @field_validator('type_controller', 'entity', mode='before')
    def to_string(cls, value: str) -> str:
        return str(value)




# class RequestBase(BaseModel):
#     """
#     Базовый класс с настройками и полями для любого запроса(Monitoring/Management)
#     """
#
#     model_config = ConfigDict(use_enum_values=True)
#
#     ip_or_num: Annotated[str, Field(max_length=20)]
#     type_controller: AllowedControllers
#     host_id: Annotated[str, Field(default=None, max_length=20)]
#     scn: Annotated[str, Field(default=None, max_length=10)]
#     entity: AllowedMonitoringEntity | AllowedManagementEntity
#     search_in_db: Annotated[bool, Field(default=False)]
#     errors: Annotated[list[str], Field(default_factory=list)]
#
#     @field_validator('type_controller', 'entity', mode='before')
#     def to_string(cls, value: str) -> str:
#         return str(value)
#
#     @computed_field
#     def search_in_db_field(self) -> str:
#         if check_ipv4(self.ip_or_num):
#             return TrafficLightsObjectsTableFields.IP_ADDRESS.value
#         return TrafficLightsObjectsTableFields.NUMBER.value


class _RequestWithSearchInDb(RequestBase):
    """
    Класс настройки полей при поиске хоста в БД для любого запроса(Monitoring/Management)
    """
    ip_or_num: Annotated[str, Field(min_length=1, max_length=20)]

    @computed_field
    def search_in_db_field(self) -> str:
        if check_ipv4(self.ip_or_num):
            return TrafficLightsObjectsTableFields.IP_ADDRESS.value
        return TrafficLightsObjectsTableFields.NUMBER.value


class GetCommands(RequestBase):
    """
    Класс типа получения данных с контроллера.
    """
    entity: AllowedMonitoringEntity


class GetCommandsWithSearchInDb(_RequestWithSearchInDb):
    """
    Класс типа получения данных с контроллера с поиском хоста в БД
    """
    entity: AllowedMonitoringEntity


# """ Первая версия """
# class RequestBase(BaseModel):
#     model_config = ConfigDict(use_enum_values=True)
#
#     type_controller: AllowedControllers
#     host_id: str | None
#     scn: str | None
#     entity: str
#     search_in_db: bool
#
#
# class RequestCommon(RequestBase):
#
#     ip_or_num: Annotated[str, Field(min_length=2, max_length=20)]
#     # search_in_db_field: Annotated[str, Field(strict=True)]
#
#     # @field_validator('search_in_db_field', mode='after')
#     # def get_field_value(cls, value: str) -> str:
#     #     """
#     #     Определяет имя поля для поиска объекта в модели TrafficLightsObjects
#     #     """
#     #     if check_ipv4(value):
#     #         return TrafficLightsObjectsTableFields.IP_ADDRESS
#     #     return TrafficLightsObjectsTableFields.NUMBER
#
#     @computed_field
#     def search_in_db_field(self) -> str:
#         if check_ipv4(self.ip_or_num):
#             return TrafficLightsObjectsTableFields.IP_ADDRESS
#         return TrafficLightsObjectsTableFields.NUMBER
#
#
# class RequestBaseWithSearchInDb(RequestBase):
#     search_in_db_field: Annotated[str, Field(min_length=2, max_length=20)]
#
#     @field_validator('search_in_db_field', mode='after')
#     def get_field_value(cls, value: str) -> str:
#         """
#         Определяет имя поля для поиска объекта в модели TrafficLightsObjects
#         """
#         if check_ipv4(value):
#             return TrafficLightsObjectsTableFields.IP_ADDRESS
#         return TrafficLightsObjectsTableFields.NUMBER
#
#
# class SearchInDb(BaseModel):
#     search_in_db_field: Annotated[str, Field(min_length=2, max_length=20)]
#
#     @field_validator('search_in_db_field', mode='after')
#     def get_field_value(cls, value: str) -> str:
#         """
#         Определяет имя поля для поиска объекта в модели TrafficLightsObjects
#         """
#         if check_ipv4(value):
#             return TrafficLightsObjectsTableFields.IP_ADDRESS
#         return TrafficLightsObjectsTableFields.NUMBER
#
#
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
    obj2 = GetCommandsWithSearchInDb(
        **{'type_controller': 'Swarco', 'host_id': 'string', 'scn': 'string',
          'entity': AllowedMonitoringEntity.GET_STATE_BASE, 'search_in_db': True,
           'ip_or_num': '123'
    })
    print(obj2)
    print(obj2.model_dump())
