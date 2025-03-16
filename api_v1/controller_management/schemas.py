from enum import StrEnum
from typing import Annotated, Any
from annotated_types import MinLen, MaxLen

from pydantic import (
    BaseModel,
    IPvAnyAddress,
    Field,
    ConfigDict,
    computed_field,
    AfterValidator, SkipValidation
)
from pydantic_core import ValidationError

from sdp_lib.utils_common import check_is_ipv4, remove_duplicates


class AllowedControllers(StrEnum):
    SWARCO = 'Swarco'
    POTOK_P = 'Поток (P)'
    POTOK_S = 'Поток (S)'
    PEEK = 'Peek'


class AllowedMonitoringEntity(StrEnum):
    BASE = 'base'
    INPUTS = 'inputs'
    ADVANCED = 'advanced'
    BASE_AND_INPUTS = 'base_and_inputs'


class AllowedManagementEntity(StrEnum):
    SET_STAGE = 'set_stage'
    SET_DARK = 'set_dark'


class AllowedProtocolsRequest(StrEnum):
    SNMP = 'snmp'
    HTTP = 'http'
    AUTO = 'auto'


class AllowedDataHostFields(StrEnum):
    errors = 'errors'
    host_id = 'host_id'
    type_controller = 'type_controller'
    scn = 'scn'
    search_in_db = 'search_in_db'
    ip_or_name_from_user = 'ip_or_name_from_user'
    entity = 'entity'
    ipv4 = 'ip_address'
    ip_or_name = 'ip/name'
    options = 'options'


class TrafficLightsObjectsTableFields(StrEnum):
    IP_ADDRESS = 'ip_adress'
    NUMBER = 'number'
    ALL = '*'


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


ip_or_name = Annotated[str, Field(min_length=1, max_length=20)]


class SearchHostsInDb(BaseModel):

    ip_or_name_from_user: ip_or_name

    @computed_field
    @property
    def search_in_db_field(self) -> str:
        if check_is_ipv4(self.ip_or_name_from_user):
            return str(TrafficLightsObjectsTableFields.IP_ADDRESS)
        else:
            return str(TrafficLightsObjectsTableFields.NUMBER)


""" Проверка данных(свойств) определённого хоста """

# class DataHostIfSearchInDbFalseBase(BaseModel):
#
#     ip_or_name_from_user: Annotated[IPvAnyAddress, AfterValidator(get_value_as_string)]
#     search_in_db: bool
#     entity: AllowedMonitoringEntity
#     type_controller: Annotated[AllowedControllers, AfterValidator(get_value_as_string)]
#     number: Annotated[str, Field(default=None, max_length=20, alias='host_id')]
#     scn: Annotated[str, Field(default=None, max_length=10)]




""" Входные данные запроса """

class GetHostsStaticDataFromDb(BaseModel):

    hosts: Annotated[list[ip_or_name], MinLen(1), MaxLen(30), AfterValidator(remove_duplicates)]


class T(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    type_controller: AllowedControllers
    # entity: AllowedMonitoringEntity
    host_id: str
    # host_fields_monitoring: Annotated[dict[AllowedMonitoringEntity, str], Field(repr=True)]


class RequestMonitoringAndManagement(BaseModel):
    hosts: Annotated[dict[ip_or_name, dict[str, str]], Field(repr=True)]


class FastRequestMonitoringAndManagement(BaseModel):

    hosts: Annotated[dict[IPvAnyAddress, T], Field(repr=True), SkipValidation]


""" Модели БД """
class ModelFromDb(BaseModel):
    model_config = ConfigDict(use_enum_values=True, from_attributes=True)

    # id: int
    number: str
    description: str | None
    type_controller: str
    # group: int
    ip_adress: str
    address: str | None
    # time_create: datetime.datetime
    # time_update: datetime.datetime


""" Тестовые модели """
class Nested(BaseModel):
    t1: str
    num: int

class T1(BaseModel):
    id: int
    hosts: list[Nested]

if __name__ == '__main__':
    data = {'type_controller': 'Swarc', 'entity': 'get_state_base', 'host_id': '1557'}

    try:
        o = BaseMonitoringHostBody(**data)
        print(f'o: {o}')
    except ValidationError as err:
        print(f'err: {err}')
        print(f'err.errors(): {err.errors()}')
        print(f'err.args: {err.args}')
        print(f'err.json(): {err.json()}')
        print(f'err.error_count(): {err.error_count()}')



    # j_data = json.dumps(data)
    # print(j_data)
    # print(type(j_data))
    # obj = _MonitoringAndManagementBase(**{'type_controller': 'Swarco', 'host_id': 'string', 'scn': 'string',
    #                   'entity': AllowedMonitoringEntity.GET_STATE_BASE, 'search_in_db': True,
    #                                       })
    # print(obj.model_dump())
############################

