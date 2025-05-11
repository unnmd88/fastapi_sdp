import ipaddress
import pprint
from collections import Counter
from collections.abc import Callable, Iterable
from enum import StrEnum
from functools import cached_property
from typing import Annotated, Any, TypeVar, Self, AnyStr, ClassVar
from annotated_types import MinLen, MaxLen

from pydantic import (
    BaseModel,
    Field,
    ConfigDict,
    computed_field,
    ValidationError,
    AfterValidator,
    SkipValidation,
    field_validator,
    IPvAnyAddress,
    model_validator, BeforeValidator
)
from pydantic_core import PydanticCustomError

from api_v1.controller_management.available_services import (
    AllowedManagementSources,
    AllowedManagementEntity
)
from api_v1.controller_management import available_services
from core.user_exceptions.validate_exceptions import ErrMessages
from core.constants import AllowedControllers, AllowedDataHostFields


class AllowedMonitoringEntity(StrEnum):
    # BASE = 'base'
    INPUTS = 'inputs'
    ADVANCED = 'advanced'
    # BASE_AND_INPUTS = 'base_and_inputs'


class AllowedMonitoringOptions(StrEnum):
    base = 'base'
    advanced = 'advanced'
    inputs = 'inputs'
    base_and_inputs = 'base_and_inputs'


class AllowedProtocolsRequest(StrEnum):
    SNMP = 'snmp'
    HTTP = 'http'
    AUTO = 'auto'


ip_or_name = Annotated[str, Field(min_length=1, max_length=20)]


# class BaseFields(BaseModel):
#
#     model_config = ConfigDict(extra='allow')
#
#     number: Annotated[str | None, Field(default=None)]
#     ip_adress: Annotated[str | None, Field(default=None)]
#     type_controller: Annotated[str | None, Field(default=None)]
#     address: Annotated[str | None, Field(default=None)]
#     description: Annotated[str | None, Field(default=None)]
#     option: Annotated[AllowedMonitoringOptions | None, Field(default=None)]
#
#
# class ManagementFields(BaseFields):
#
#     model_config = ConfigDict(use_enum_values=True)
#     command: str
#     value: Annotated[int | str, Field()]
#     source: Annotated[AllowedManagementSources, Field(default=None), SkipValidation]


""" Взаимосвязаны с запросом в БД. """


class BaseSearchTrafficLightsInDb(BaseModel):

    model_config = ConfigDict(json_schema_extra={
        "examples": [
            {
                "hosts": ["11", "2390"]
            },
        ],
    })
    # hosts: Annotated[list[ip_or_name], MinLen(1), MaxLen(30), AfterValidator(remove_duplicates), Field(frozen=True)]
    hosts: Annotated[list[ip_or_name], MinLen(1), MaxLen(30)]
    source_data: Annotated[dict, Field(default=None)]

    def model_post_init(self, __context) -> None:
        self.source_data = {
            'hosts': self.hosts,
            'doubles': {}
        }
        counter = Counter(self.hosts)
        hosts_without_doubles = []
        for k, v in counter.items():
            if v > 1:
                self.source_data['doubles'][k] = v
            hosts_without_doubles.append(k)
        self.hosts = hosts_without_doubles


class TrafficLightDbRecords(BaseModel):

    model_config = ConfigDict(from_attributes=True)

    number: str | None
    ip_adress: str | None
    type_controller: str | None
    address: str | None
    description: str | None


class SearchinDbFields(BaseModel):

    ip_or_name_source: Annotated[str, Field(min_length=1, max_length=20, frozen=True)]
    search_in_db_field:  Annotated[str, Field(frozen=True)]
    db_records: Annotated[list[TrafficLightDbRecords], Field(default=[])]

    # @computed_field
    @property
    def found(self)-> bool:
        return bool(self.db_records)

    @computed_field
    @property
    def count_records(self) -> int:
        return len(self.db_records)


# class BaseFieldsWithSearchInDb(SearchinDbFields, BaseFields):
#     """ Класс агрегатор полей хоста категории "мониторинг"
#         с опцией предварительного поиска в БД.
#     """
#
#
# class DataHostManagement(SearchinDbFields, ManagementFields):
#     """ Класс агрегатор полей хоста категории "управление"
#         с опцией предварительного поиска в БД.
#     """


def splitter(data, splitter=';') -> list:
    try:
        if data is None:
            return []
        return data.split(splitter)
    except AttributeError:
        return [data]


# class ControllerManagementOptions(BaseModel):
#
#     model_config = ConfigDict(from_attributes=True)
#     type_controller: str
#     group: Annotated[int, Field(exclude=True)]
#     commands: Annotated[str, AfterValidator(splitter)]
#     max_stage: int
#     options: Annotated[str | list | None, AfterValidator(splitter)]
#     sources: Annotated[str | list | None, AfterValidator(splitter)]

""" Без запроса в БД. """


class MonitoringFields(BaseModel):

    model_config = ConfigDict(extra='allow', use_enum_values=True)

    number: Annotated[str | None, Field(default=None)]
    ip_v4: Annotated[str | None, Field(default=None, exclude=True)]
    type_controller: Annotated[str | None, Field(default=None)]
    errors: Annotated[list, Field(default=[])]
    response: Annotated[dict, Field(default={})]
    option: Annotated[str | None, Field(default=None)]
    database: Annotated[dict | SearchinDbFields, Field(default={})]
    allowed: Annotated[bool, Field(default=False)]

    stop_check_flag: Annotated[bool, Field(default=False, exclude=True)]
    


    # @field_validator('type_controller', mode='after')
    # @classmethod
    # def check_type_controller(cls, type_controller):
    #     try:
    #         AllowedControllers(type_controller)
    #     except ValueError:
    #         cls.add_to_errors('Некорректный тип контроллера')
    #     return type_controller

    def add_err(self, exc_or_err: Exception | AnyStr):
        self.errors.append(str(exc_or_err))

    def check_type_controller(self):
        try:
            AllowedControllers(self.type_controller)
        except ValueError:
            self.add_err(ErrMessages.get_bad_controller_pretty(self.type_controller))

    def check_ipv4(self):
        try:
            ipaddress.IPv4Address(self.ip_v4)
        except ValueError as e:
            self.add_err(ErrMessages.get_bad_ip_pretty(self.ip_v4))

    def check_database(self):
        try:
            if self.database['count'] > 1:
                self.add_err('Более 1 записи найдено в БД')
        except KeyError:
            pass

    def model_post_init(self, __context) -> None:
        self.validate_all()
        if not self.errors:
            self.allowed = True

    def validate_all(self):
        self.check_ipv4()
        self.check_type_controller()

    # @model_validator(mode='after')
    # def check_type_controller(self) -> Self:
    #     try:
    #         AllowedControllers(self.type_controller)
    #     except ValueError:
    #         self.errors.append('Некорректный тип контроллера')
    #     return self




class ManagementFields(MonitoringFields):

    # set_stage_options: ClassVar = {
    #     str(AllowedControllers.SWARCO): available_services.swarco,
    #     # str(AllowedControllers.PEEK): available_services.peek_set_stage_options,
    #     # str(AllowedControllers.POTOK_P): available_services.potok_p_set_stage_options,
    #     # str( AllowedControllers.POTOK_S): available_services.potok_s_set_stage_options
    # }

    matches_command_to_controller: ClassVar = {
        str(AllowedControllers.SWARCO): available_services.swarco,
    }

    # matches_sources: ClassVar = {
    #     AllowedControllers.SWARCO: {AllowedManagementSources.man},
    #     AllowedControllers.PEEK: {AllowedManagementSources.central}
    # }

    command: Annotated[str, SkipValidation]
    value: Annotated[int | str | None, Field(default=None), SkipValidation]
    source: Annotated[AllowedManagementSources, Field(default=None), SkipValidation]

    command_entity: Annotated[available_services.T_CommandOptions | None, Field(default=None, exclude=True)]

    def set_settings_and_options(self):
        self.command_entity: available_services.T_Services = self.matches_command_to_controller.get(self.type_controller)

    # @cached_property
    # def matches_command_to_controller(self):
    #     """
    #     Возвращает словарь, ключами которого являются типы доступных команд
    #     в строковом представлении, а ключи - последовательности методов валидации
    #     для данного типа команды.
    #     """
    #     return {
    #         str(AllowedControllers.SWARCO): available_services.swarco,
    #     }

    @cached_property
    def matches_commands(self):
        """
        Возвращает словарь, ключами которого являются типы доступных команд
        в строковом представлении, а ключи - последовательности методов валидации
        для данного типа команды.
        """
        return {
            str(AllowedManagementEntity.set_stage): (self.check_num_stage, )
        }

    def check_command_for_current_controller_type(self) -> bool:
        if self.command not in self.command_entity.available_commands:
            self.add_err(f'Невалидная команда: < {self.command} >')
            return False
        return True

    def check_num_stage(self):
        # controller_options: available_services.Stage = self.set_stage_options[self.type_controller]
        vals_range: available_services.T_Services = self.command_entity.services_entity.get(self.command)

        if not int(self.value) in vals_range.values_range_as_set:
            msg = (
                f'Некорректный номер фазы. Должен быть в диапазоне '
                f'[{vals_range.min_val}...{vals_range.max_val}]'
            )
            self.add_err(msg)
            return False
        return True

    def check_source(self):
        pass


    def validate_all(self) -> None:
        super().validate_all()
        self.set_settings_and_options()
        self.command_entity = self.matches_command_to_controller.get(self.type_controller)

        # print(f'self.settings_and_options')

        if self.errors:
            return
        try:
            for method in self.matches_commands[self.command]:
                if self.stop_check_flag: # На будущее, если после какого либо метода требуется прервать валидацию
                    return
                method()
        except KeyError:
            self.add_err(f'Невалидная команда: < {self.command} >')


class Monitoring(BaseModel):

    model_config = ConfigDict(
        extra='allow',
        json_schema_extra= {
            "examples": [
                {
                    "hosts":
                        {
                            "192.168.0.2": {
                                AllowedDataHostFields.type_controller: "Swarco(required field)",
                            },

                            "192.168.0.1": {
                                AllowedDataHostFields.host_id: "1111(optional field)",
                                AllowedDataHostFields.scn: "CO1111(optional field)",
                                AllowedDataHostFields.option: f'{", ".join([o for o in AllowedMonitoringEntity])} (optional field)',
                                AllowedDataHostFields.type_controller: "Swarco(required field)",
                            }
                        },
                }
            ],
        }
    )

    _model = MonitoringFields

    hosts: Annotated[
        dict[str, MonitoringFields | ManagementFields], MinLen(1), MaxLen(30), SkipValidation
    ]

    @field_validator('hosts', mode='before')
    @classmethod
    def body_to_pydantic_model(cls, hosts: dict[str, Any]) -> dict[str, MonitoringFields | ManagementFields]:
        # a_a = {k: cls._model(**v) for k, v in hosts.items()}
        # print(f'a_a: {a_a}')
        return {k: cls._model(ip_v4=k, **v) for k, v in hosts.items()}


class Management(Monitoring):

    model_config = ConfigDict(
        extra='allow',
        json_schema_extra= {
            "examples": [
                {
                    "hosts":
                        {
                            "192.168.0.2": {
                                AllowedDataHostFields.type_controller: "Peek",
                                AllowedDataHostFields.command: AllowedManagementEntity.set_stage,
                                AllowedDataHostFields.value: 1
                            },

                            # "192.168.0.1": {
                            #     AllowedDataHostFields.host_id: "1111(optional field)",
                            #     AllowedDataHostFields.scn: "CO1111(optional field)",
                            #     AllowedDataHostFields.option: f'{", ".join([o for o in AllowedMonitoringEntity])} (optional field)',
                            #     AllowedDataHostFields.type_controller: "Swarco(required field)",
                            # }
                        },
                }
            ],
        }
    )

    _model = ManagementFields


    # hosts: Annotated[
    #     dict[str, ManagementFields], MinLen(1), MaxLen(30), SkipValidation
    # ]
    #
    # @field_validator('hosts', mode='before')
    # def add_m(cls, hosts: dict[str, Any]) -> dict[str, ManagementFields]:
    #     return {k: ManagementFields(**v) for k, v in hosts.items()}


""" Response """


class ResponseSearchinDb(BaseModel):

    source_data: Annotated[Any, Field(default=None)]
    results: list[dict[str, SearchinDbFields]]
    time_execution: Annotated[float, Field(default=0)]

    model_config = ConfigDict(
        extra='allow',
        json_schema_extra={
            "examples": [
                {

                    "source_data": {
                        "hosts": [
                            "11",
                            "2390"
                        ]
                    },
                    "results": [
                        {
                            "11": {
                                "ip_or_name_source": "11",
                                "search_in_db_field": "number",
                                "db_records": [
                                    {
                                        "number": "11",
                                        "ip_adress": "10.179.28.9",
                                        "type_controller": "Swarco",
                                        "address": "Бережковская наб. д.22, 24    ЗАО (ЗАО-9)",
                                        "description": "Приоритет ОТ"
                                    }
                                ],
                                "count_records": 1
                            },
                            "2390": {
                                "ip_or_name_source": "2390",
                                "search_in_db_field": "number",
                                "db_records": [
                                    {
                                        "number": "2390",
                                        "ip_adress": "10.179.16.121",
                                        "type_controller": "Peek",
                                        "address": "Зеленоград г. Панфиловский (пр.пр. 648) пр-т - Андреевка (пр.пр. 647) ул. (САО-7)",
                                        "description": "Приоритет ОТ. Переведен в фикс по особому распоряжению.07.08.2024"
                                    }
                                ],
                                "count_records": 1
                            }
                        }
                    ],
                    "time_execution": 0

                },
            ],
        }
    )


json_schema_monitoring_response = {
        "examples": [
            {
                "10.179.18.41": {
                    "number": None,
                    "ip_adress": "10.179.18.41",
                    "type_controller": "Поток (P)",
                    "address": None,
                    "description": None,
                    "option": None,
                    "errors": [],
                    "response": {
                        "protocol": "snmp",
                        "ip_address": "10.179.18.41",
                        "errors": [],
                        "data": {
                            "operation_mode": "1",
                            "dark": "0",
                            "flash": "0",
                            "current_stage": 2,
                            "current_plan": "2",
                            "local_adaptive_status": "1",
                            "num_detectors": "27",
                            "has_det_faults": "0",
                            "is_mode_man": "0",
                            "curr_status_mode": "3_light",
                            "current_mode": "VA"
                        }
                    }
                },

                "10.179.16.121": {
                    "number": None,
                    "ip_adress": "10.179.16.121",
                    "type_controller": "Peek",
                    "address": None,
                    "description": None,
                    "option": None,
                    "errors": [],
                    "response": {
                        "protocol": "http",
                        "ip_address": "10.179.16.121",
                        "errors": [],
                        "data": {
                            "current_address": "Moscow: Панфиловс пр / Андреевка",
                            "current_plan": "002",
                            "current_plan_parameter": "002",
                            "current_time": "2025-03-20 12:42:31",
                            "current_alarms": "",
                            "number_of_streams": 2,
                            "streams_data": [
                                {
                                    "xp": "1",
                                    "current_status": "УПРАВЛЕНИЕ",
                                    "current_mode": "FT",
                                    "current_stage": "1"
                                },
                                {
                                    "xp": "2",
                                    "current_status": "УПРАВЛЕНИЕ",
                                    "current_mode": "FT",
                                    "current_stage": "6"
                                }
                            ]
                        }
                    }
                }
            },
        ],
    }


class ResponseGetState(BaseModel):
    model_config = ConfigDict(
        extra='allow',
        json_schema_extra=json_schema_monitoring_response
    )


""" Проверка данных(свойств) определённого хоста """

# T_PydanticModel = TypeVar(
#     "T_PydanticModel",
#     DataHostMonitoring,
#     DataHostManagement,
#     FastMonitoring,
#     FastManagement
# )

T_PydanticModel = TypeVar("T_PydanticModel", bound=BaseModel)


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
    data = ['1', "11", "192.168.45.16"]

    data_command = {
        'hosts': {
            '10.45.154.15': {
                'type_controller': 'Swarco',
                'command': 'set_stage',
                'value': 1
            }
        }
    }
    swarco2 = {
        'ip_v4': '10.45.154.15',
        'type_controller': 'Swarco',
        'command': 'set_stage',
        'value': 9
    }

    swarco2_set_stage = ManagementFields(**swarco2)
    # swarco2_set_stage = ManagementFields(
    #     ip_v4='10.45.154.15',
    #     type_controller='Swarco',
    #     command='set_stage',
    #     value=1
    # )
    print(swarco2_set_stage)
    pprint.pprint(swarco2_set_stage)
    pprint.pprint(swarco2_set_stage.model_dump_json())
    pprint.pprint(available_services.swarco.model_dump_json())