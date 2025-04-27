from collections import Counter
from enum import StrEnum
from typing import Annotated, Any, TypeVar
from annotated_types import MinLen, MaxLen

from pydantic import (
    BaseModel,
    Field,
    ConfigDict,
    computed_field,
    AfterValidator, SkipValidation, field_validator, model_serializer
)
from pydantic_core import ValidationError

from sdp_lib.utils_common import check_is_ipv4, remove_duplicates


class AllowedControllers(StrEnum):
    SWARCO = 'Swarco'
    POTOK_P = 'Поток (P)'
    POTOK_S = 'Поток (S)'
    PEEK = 'Peek'


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


class AllowedManagementEntity(StrEnum):
    set_stage = 'set_stage'
    set_dark = 'set_dark'


class AllowedManagementSources(StrEnum):
    man = 'man'
    central = 'central'


class AllowedProtocolsRequest(StrEnum):
    SNMP = 'snmp'
    HTTP = 'http'
    AUTO = 'auto'


class AllowedDataHostFields(StrEnum):
    errors = 'errors'
    host_id = 'host_id'
    type_controller = 'type_controller'
    scn = 'scn'

    source_data = 'source_data'
    results = 'results'
    execution_time = 'execution_time'
    ip_or_name_from_user = 'ip_or_name_from_user'
    entity = 'entity'
    ip_adress = 'ip_adress'
    ipv4 = 'ip_address'
    ip_or_name = 'ip/name'
    option = 'option'
    #Database entity
    search_in_db = 'search_in_db'
    search_in_db_field = 'search_in_db_field'
    found = 'found'
    count = 'count'
    db_records = 'db_records'
    #management
    command = 'command'
    value = 'value'


class TrafficLightsObjectsTableFields(StrEnum):
    IP_ADDRESS = 'ip_adress'
    NUMBER = 'number'
    ALL = '*'


ip_or_name = Annotated[str, Field(min_length=1, max_length=20)]


class BaseFields(BaseModel):

    model_config = ConfigDict(extra='allow')

    number: Annotated[str | None, Field(default=None)]
    ip_adress: Annotated[str | None, Field(default=None)]
    type_controller: Annotated[str | None, Field(default=None)]
    address: Annotated[str | None, Field(default=None)]
    description: Annotated[str | None, Field(default=None)]
    option: Annotated[AllowedMonitoringOptions | None, Field(default=None)]


class ManagementFields(BaseFields):
    command: str
    value: Annotated[int | str, Field()]
    source: Annotated[AllowedManagementSources, Field(default=None), SkipValidation]


""" Взаимосвязаны с запросом в БД. """


class BaseFieldsSearchInDb(BaseModel):

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


class SearchinDbFields(BaseModel):

    ip_or_name_source: Annotated[str, Field(min_length=1, max_length=20, frozen=True)]
    # search_in_db_field: Annotated[str, AfterValidator(get_field_for_search_in_db)]
    search_in_db_field:  Annotated[str, Field(frozen=True)]
    db_records: Annotated[list, Field(default=[])]
    errors: Annotated[list, Field(default=[])]

    # @computed_field
    @property
    def found(self)-> bool:
        return bool(self.db_records)

    @computed_field
    @property
    def count_records(self) -> int:
        return len(self.db_records)


class BaseFieldsWithSearchInDb(SearchinDbFields, BaseFields):
    """ Класс агрегатор полей хоста категории "мониторинг"
        с опцией предварительного поиска в БД.
    """


class DataHostManagement(SearchinDbFields, ManagementFields):
    """ Класс агрегатор полей хоста категории "управление"
        с опцией предварительного поиска в БД.
    """


""" Без запроса в БД. """


class FieldsMonitoringWithoutSearchInDb(BaseModel):

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

    hosts: Annotated[
        dict[str, BaseFields], MinLen(1), MaxLen(30), SkipValidation
    ]

    @field_validator('hosts', mode='before')
    def add_m(cls, hosts: dict[str, Any]) -> dict[str, BaseFields]:
        # return {
        #     k: DataHostMixin(**(v | {'errors': [], 'ip_adress': k}))
        #     for k, v in hosts.items()
        # }
        return {
            k: BaseFields(**(v | {str(AllowedDataHostFields.errors): [], str(AllowedDataHostFields.ip_adress): k}))
            for k, v in hosts.items()
        }




class FieldsManagementWithoutSearchInDb(BaseModel):

    model_config = ConfigDict(
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

    hosts: Annotated[
        dict[str, ManagementFields], MinLen(1), MaxLen(30), SkipValidation
    ]

    @field_validator('hosts', mode='before')
    def add_m(cls, hosts: dict[str, Any]) -> dict[str, ManagementFields]:
        # return {
        #     k: DataHostMixin(**(v | {'errors': [], 'ip_adress': k}))
        #     for k, v in hosts.items()
        # }
        return {
            k: ManagementFields(**(v | {str(AllowedDataHostFields.errors): [], str(AllowedDataHostFields.ip_adress): k}))
            for k, v in hosts.items()
        }




""" Response """


class ResponseSearchinDb(BaseModel):

    source_data: Annotated[Any, Field(default=None)]
    result: list[dict[str, SearchinDbFields]]
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

    try:
        o = BaseFieldsSearchInDb(hosts=data)
        print(f'o: {o}')
        print(f'o: {o.hosts.keys()}')
        d = o.model_dump()
        d1 = o.model_dump()
        print(f'o: {d1 is d}')

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

