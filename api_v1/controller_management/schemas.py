import datetime
from enum import StrEnum
from typing import Annotated, Literal

from pydantic import BaseModel, IPvAnyAddress, Field, ConfigDict, field_validator, computed_field, AfterValidator
from pydantic.json_schema import model_json_schema

from sdp_lib.utils_common import check_is_ipv4


class AllowedControllers(StrEnum):
    SWARCO = 'Swarco'
    POTOK_P = 'Поток (P)'
    POTOK_S = 'Поток (S)'
    PEEK = 'Peek'


class AllowedMonitoringEntity(StrEnum):
    GET_STATE_BASE = 'get_state_base'
    GET_STATE_FULL = 'get_state_full'
    GET_FROM_DB = 'get_property'
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


def from_enum_to_str(value: StrEnum) -> str:
    """
    Конвертирует экземпляр в строковый тип.
    :param value: Значение, которое будет сконвертировано в строковый тип.
    :return: Строковое представление value.
    """
    return str(value)


ip_or_name = Annotated[str, Field(min_length=1, max_length=20)]

class HostPropertiesBase(BaseModel):

    ip_or_name_from_user: ip_or_name

    search_in_db: Annotated[bool, Field(default=False, exclude=True)]
    search_in_db_field: Annotated[str, Field(default=None, exclude=True)]
    search_in_db_result: Annotated[str, Field(default=None, exclude=False)]
    errors: Annotated[list, Field(default=[])]

    def model_post_init(self, __context):
        self.set_search_in_db_field()

    def set_search_in_db_field(self):
        """
        Устанавливает значение поля self.search_in_db_field, по которому будет
        производиться поиск хоста в БД.
        :return:
        """
        if check_is_ipv4(self.ip_or_name_from_user):
            self.search_in_db_field = str(TrafficLightsObjectsTableFields.IP_ADDRESS)
        else:
            self.search_in_db_field = str(TrafficLightsObjectsTableFields.NUMBER)


class HostPropertiesForGetStaticDataFromDb(HostPropertiesBase):

    entity: Annotated[Literal[AllowedMonitoringEntity.GET_FROM_DB], AfterValidator(from_enum_to_str)]
    search_in_db: Annotated[bool, Field(default=True, exclude=True)]

# class _MonitoringAndManagementBase(HostsStaticData):
#
#     type_controller: Annotated[AllowedControllers, AfterValidator(from_enum_to_str)]
#     host_id: Annotated[str, Field(default=None, max_length=20)]
#     scn: Annotated[str, Field(default=None, max_length=10)]
#     entity: AllowedMonitoringEntity | AllowedManagementEntity
#     search_in_db: Annotated[bool, Field(default=False)]
#
#     # @field_validator('type_controller', 'entity', mode='before')
#     # def to_string(cls, value: str) -> str:
#     #     return str(value)


# class Monitoring(_MonitoringAndManagementBase):
#     entity: Annotated[AllowedMonitoringEntity, AfterValidator(from_enum_to_str)]


""" Входные данные запроса """

class GetHostsStaticDataFromDb(BaseModel):
    """
    Базовый класс с настройками и полями для любого запроса(Monitoring/Management)
    """

    hosts: Annotated[list[ip_or_name], Field(repr=True)]
    # entity: Annotated[Hosts, AfterValidator(from_enum_to_str)]
    # search_in_db: Annotated[bool, Field(default=True)]
    # _ipv4: Annotated[str, Field(default=None,exclude=True)]
    # _number: Annotated[str, Field(default=None, exclude=True)]
    # _search_in_db_field: Annotated[str, Field(default=None, exclude=True)]
    # _search_in_db_result: Annotated[str, Field(default=None, exclude=True)]


class RequestMonitoringAndManagement(BaseModel):
    pass
    # hosts: Annotated[dict[ip_or_num_from_user, Monitoring], Field(repr=True)]


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


# Annotated[str, Field(strict=True)

""" Тестовые модели """
class T1(BaseModel):
    hosts: Annotated[list[str], Field(repr=True)]


if __name__ == '__main__':
    data = {
        'type_controller': 'Swarco', 'host_id': 'string', 'scn': 'string',
        'entity': AllowedMonitoringEntity.GET_STATE_BASE, 'search_in_db': True
    }

    objs = ['2725', '3323', 'baza_bereg', '10.45.154.16', '192.168.45.19']
    for o in objs:
        obj1 = HostPropertiesBase(ip_or_name_from_user=o)

        print(obj1)

    # j_data = json.dumps(data)
    # print(j_data)
    # print(type(j_data))
    # obj = _MonitoringAndManagementBase(**{'type_controller': 'Swarco', 'host_id': 'string', 'scn': 'string',
    #                   'entity': AllowedMonitoringEntity.GET_STATE_BASE, 'search_in_db': True,
    #                                       })
    # print(obj.model_dump())
############################

