import abc
import asyncio
import ipaddress
import json
import logging
from copy import deepcopy
from enum import StrEnum
from typing import Type, Any, Sequence

from pydantic.json_schema import model_json_schema

import logging_config
from re import search

from pydantic import ValidationError, BaseModel



# from sdp_lib.management_controllers.tests import host_id
from sdp_lib.utils_common import check_is_ipv4
from .schemas import (
    AllowedControllers,
    AllowedMonitoringEntity, AllowedProtocolsRequest,
    TrafficLightsObjectsTableFields, DataHostFields, ModelFromDb,
    AllowedDataHostFields, BaseSearchHostsInDb
)

from sdp_lib.management_controllers import controller_management


logger = logging.getLogger(__name__)

logger.debug('TEEEEEEEEEEST LOGGER')


class Messages(StrEnum):
    invalid_ip_or_num_for_search_in_db = 'invalid data for search host in database'
    invalid_ip_or_num = 'invalid number or ip v4 address'
    invalid_ip = 'invalid ip v4 address'
    invalid_host_data = 'invalid host data'
    not_found_in_database = 'not found in database'





# class BaseDataHostsSorter:
#     """
#     Базовый класс обработки данных и запросов с дорожных контроллеров.
#     """
#
#     def __init__(self, income_data: dict):
#         self.income_data = income_data
#         self.model = self.get_model()
#
#         self.allowed_hosts: dict[str, BaseModel] = {}
#         self.bad_hosts: dict = {}
#         self.no_search_in_db_hosts: dict = {}
#         self.search_in_db_hosts: dict = {}
#         self.current_name_or_ipv4: str | None = None
#         self.current_data_host: dict | None = None
#         self._check_data_host_temp_model: BaseModel | None = None
#         self.hosts_after_search_in_db = None
#         self.current_data_host_pydantic_model: BaseModel | None = None
#
#
#     def __repr__(self):
#         # return (f'self.income_data:\n{json.dumps(self.income_data, indent=2)}\n'
#         #         f'self.good_hosts: {json.dumps(self.allowed_hosts, indent=2)}\n'
#         #         f'self.search_in_db_hosts: {json.dumps(self.search_in_db_hosts, indent=2)}\n'
#         #         f'self.no_search_in_db_hosts: {json.dumps(self.no_search_in_db_hosts, indent=2)}\n'
#         #         f'self.bad_hosts: {json.dumps(self.bad_hosts, indent=2)}')
#
#         return (f'self.income_data:\n{self.income_data}\n'
#                 f'self.search_in_db_hosts: {self.search_in_db_hosts}\n'
#                 f'self.no_search_in_db_hosts: {self.no_search_in_db_hosts}\n'
#                 # f'self.hosts_after_search_in_db: {self.hosts_after_search_in_db}\n'
#                 f'self.bad_hosts: {self.bad_hosts}\n'
#                 f'self.hosts_after_search_in_db: {self.hosts_after_search_in_db}\n'
#                 f'self.allowed_hosts: {self.allowed_hosts}\n')
#
#     def sorting_income_data(self):
#         for self.current_name_or_ipv4, self.current_data_host in self.income_data.items():
#
#             self.add_error_field_to_current_data_host()
#             if self.current_data_host.get(AllowedDataHostFields.search_in_db):
#                 if self.get_pydantic_model_or_none(self.current_data_host, self._check_data_host_temp_model) is None:
#                     self.add_bad_host(str(Messages.invalid_host_data))
#                     continue
#                 else:
#                     self.model = self.get_model()
#             else:
#                 if self.get_pydantic_model_or_none(self.current_data_host, self._check_data_host_temp_model) is None:
#                     self.add_bad_host(str(Messages.invalid_host_data))
#                     continue
#
#
#             self.current_data_host_pydantic_model = self.get_pydantic_model_or_none(self.get_kwargs_for_pydantic_model())
#             # logger.debug(f'data_host_pydantic_model: {data_host_pydantic_model}' )
#             if self.current_data_host_pydantic_model is not None:
#                 self.sorting_search_in_db_hosts_or_no()
#             else:
#                 self.model = self.get_model()
#
#     def add_error_field_to_current_data_host(self) -> None:
#         self.current_data_host |= {self.field_errors: []}
#
#     def get_pydantic_model_or_none(self, data_host: dict, model) -> BaseModel | None:
#         logger.debug(f'data_host get_model_host_data: {data_host}')
#         try:
#             return model(**data_host)
#         except ValidationError:
#             return None
#
#
#     def get_kwargs_for_pydantic_model(self) -> dict:
#         """
#         Формирует словарь для передачи в модель pydantic как kwargs аргументы.
#         :param ip_or_num: Название или ip хоста.
#         :param data_host: Данные хоста.
#         :return: Словарь с kwargs аргументами для создания экземпляра pydantic модели.
#         """
#
#         return {str(AllowedDataHostFields.ip_or_name_from_user): self.current_name_or_ipv4} | self.current_data_host
#
#     def add_bad_host(self, message: str) -> None:
#         """
#         Добавляет хост в "контейнер" с хостами, в данных которых содержатся ошибки.
#         # :param ip_or_num: Ip v4/номер(наименование) хоста.
#         # :param data_host: Данные хоста.
#         :param message: Сообщение, которое будет добавлено в поле data_host["errors"].
#         :return: None
#         """
#         self.current_data_host[str(DataHostFields.ERRORS)].append(message)
#         self.bad_hosts |= {self.current_name_or_ipv4: self.current_data_host}
#
#     def sorting_search_in_db_hosts_or_no(self):
#         if self.current_data_host_pydantic_model.search_in_db:
#             self.search_in_db_hosts |= {self.current_name_or_ipv4: self.current_data_host_pydantic_model}
#         else:
#             if check_is_ipv4(self.current_name_or_ipv4):
#                 self.no_search_in_db_hosts |= {self.current_name_or_ipv4: self.current_data_host_pydantic_model}
#             else:
#                 self.add_bad_host(str(Messages.invalid_ip))
#
#     def sorting_hosts_after_search_from_db(self):
#
#         stack = deepcopy(self.hosts_after_search_in_db)
#         logger.debug(f'stack: {stack}')
#         logger.debug(f'self.search_in_db_hosts: {self.search_in_db_hosts}')
#         for self.current_name_or_ipv4, self.current_data_host in self.search_in_db_hosts.items():
#             _found_record = None
#             for i, found_record in enumerate(stack):
#                 logger.debug(f'found_record: {found_record}')
#                 logger.debug(f'stack: {stack}')
#                 if self.current_name_or_ipv4 in found_record.values():
#                     _found_record = stack.pop(i)
#                     break
#             if _found_record is not None:
#                 self.current_data_host.search_in_db_result = ModelFromDb(**_found_record)
#             else:
#                 self.current_data_host.errors.append(str(Messages.not_found_in_database))
#
#     @abc.abstractmethod
#     def get_model(self):
#         """
#         Возвращает pydantic модель, соответсвующую классу.
#         :return:
#         """
#         ...

class BaseHostsSorters:
    def __init__(self, income_data: dict | list):
        self.income_data = income_data

    def get_pydantic_model_or_none(self, data_host: dict, model) -> BaseModel | None:
        logger.debug(f'data_host get_model_host_data: {data_host}')
        try:
            return model(**data_host)
        except ValidationError:
            return None

class HostsMonitoringAndManagementDataBroker(BaseHostsSorters):
    def __init__(self, income_data: list | dict):
        BaseHostsSorters.__init__(self, income_data)
        self.model_for_search_in_db = self.get_model_for_search_in_db()
        self.search_data = self.get_search_db_entity()
        self.hosts_after_search_in_db = None
        self.current_ip = None
        self.current_data_host = None
        self.base_model = self.get_base_model()

    def __repr__(self):
        return (
            f'self.income_data: {self.income_data}\n'
            f'self.model: {self.model_for_search_in_db}\n'
            f'self.search_data: {self.search_data}\n'
            f'self.hosts_after_search_in_db: {self.hosts_after_search_in_db}\n'
        )

    @abc.abstractmethod
    def get_model_for_search_in_db(self):
        return NotImplemented

    @abc.abstractmethod
    def get_search_db_entity(self):
        return NotImplemented

    @abc.abstractmethod
    def get_base_model(self):
        return NotImplemented

class BaseSortersWithSearchInDb(HostsMonitoringAndManagementDataBroker):

    def get_model_for_search_in_db(self):
        return BaseSearchHostsInDb

    def get_search_db_entity(self):
        return [self.model_for_search_in_db(ip_or_name_from_user=host) for host in self.income_data]

    def sorting_hosts(self):
        pass


class SortersWithSearchInDbMonitoring(BaseSortersWithSearchInDb):

    def __init__(self, income_data: dict):
        BaseHostsSorters.__init__(self, income_data)
        self.current_ip = None
        self.current_data_host = None
        self.base_model = self.get_base_model()

    def get_base_model(self):
        ...

    def get_search_db_entity(self):
        return [self.model_for_search_in_db(ip_or_name_from_user=host) for host in self.income_data.keys()]

    def sorting_hosts(self):
        for self.current_ip, self.current_data_host in self.income_data.items():


class BaseDataHostsSorter:
    """
    Базовый класс обработки данных и запросов с дорожных контроллеров.
    """

    def __init__(self, income_data: dict | list):
        self.income_data = income_data
        self.bad_hosts = {}
        self.model = self.get_model()



        # self.allowed_hosts: dict[str, BaseModel] = {}
        # self.bad_hosts: dict = {}
        # self.no_search_in_db_hosts: dict = {}
        # self.search_in_db_hosts: dict = {}
        # self.current_name_or_ipv4: str | None = None
        # self.current_data_host: dict | None = None
        # self._check_data_host_temp_model: BaseModel | None = None
        # self.hosts_after_search_in_db = None
        # self.current_data_host_pydantic_model: BaseModel | None = None

    def __repr__(self):
        # return (f'self.income_data:\n{json.dumps(self.income_data, indent=2)}\n'
        #         f'self.good_hosts: {json.dumps(self.allowed_hosts, indent=2)}\n'
        #         f'self.search_in_db_hosts: {json.dumps(self.search_in_db_hosts, indent=2)}\n'
        #         f'self.no_search_in_db_hosts: {json.dumps(self.no_search_in_db_hosts, indent=2)}\n'
        #         f'self.bad_hosts: {json.dumps(self.bad_hosts, indent=2)}')

        return (f'self.income_data:\n{self.income_data}\n'   
                f'self.search_in_db_hosts: {self.search_in_db_hosts}\n'
                f'self.no_search_in_db_hosts: {self.no_search_in_db_hosts}\n'
                # f'self.hosts_after_search_in_db: {self.hosts_after_search_in_db}\n'
                f'self.bad_hosts: {self.bad_hosts}\n'
                f'self.hosts_after_search_in_db: {self.hosts_after_search_in_db}\n'
                f'self.allowed_hosts: {self.allowed_hosts}\n')

    def sorting_income_data(self):
        for self.current_name_or_ipv4, self.current_data_host in self.income_data.items():

            self.add_error_field_to_current_data_host()
            if self.current_data_host.get(AllowedDataHostFields.search_in_db):
                if self.get_pydantic_model_or_none(self.current_data_host, self._check_data_host_temp_model) is None:
                    self.add_bad_host(str(Messages.invalid_host_data))
                    continue
                else:
                    self.model = self.get_model()
            else:
                if self.get_pydantic_model_or_none(self.current_data_host, self._check_data_host_temp_model) is None:
                    self.add_bad_host(str(Messages.invalid_host_data))
                    continue


            self.current_data_host_pydantic_model = self.get_pydantic_model_or_none(self.get_kwargs_for_pydantic_model())
            # logger.debug(f'data_host_pydantic_model: {data_host_pydantic_model}' )
            if self.current_data_host_pydantic_model is not None:
                self.sorting_search_in_db_hosts_or_no()
            else:
                self.model = self.get_model()

    def add_error_field_to_current_data_host(self) -> None:
        self.current_data_host |= {self.field_errors: []}

    def get_pydantic_model_or_none(self, data_host: dict, model) -> BaseModel | None:
        logger.debug(f'data_host get_model_host_data: {data_host}')
        try:
            return model(**data_host)
        except ValidationError:
            return None

    def get_kwargs_for_pydantic_model(self) -> dict:
        """
        Формирует словарь для передачи в модель pydantic как kwargs аргументы.
        :param ip_or_num: Название или ip хоста.
        :param data_host: Данные хоста.
        :return: Словарь с kwargs аргументами для создания экземпляра pydantic модели.
        """

        return {str(AllowedDataHostFields.ip_or_name_from_user): self.current_name_or_ipv4} | self.current_data_host

    def add_bad_host(self, message: str) -> None:
        """
        Добавляет хост в "контейнер" с хостами, в данных которых содержатся ошибки.
        # :param ip_or_num: Ip v4/номер(наименование) хоста.
        # :param data_host: Данные хоста.
        :param message: Сообщение, которое будет добавлено в поле data_host["errors"].
        :return: None
        """
        self.current_data_host[str(DataHostFields.ERRORS)].append(message)
        self.bad_hosts |= {self.current_name_or_ipv4: self.current_data_host}

    def sorting_search_in_db_hosts_or_no(self):
        if self.current_data_host_pydantic_model.search_in_db:
            self.search_in_db_hosts |= {self.current_name_or_ipv4: self.current_data_host_pydantic_model}
        else:
            if check_is_ipv4(self.current_name_or_ipv4):
                self.no_search_in_db_hosts |= {self.current_name_or_ipv4: self.current_data_host_pydantic_model}
            else:
                self.add_bad_host(str(Messages.invalid_ip))

    def sorting_hosts_after_search_from_db(self):

        stack = deepcopy(self.hosts_after_search_in_db)
        logger.debug(f'stack: {stack}')
        logger.debug(f'self.search_in_db_hosts: {self.search_in_db_hosts}')
        for self.current_name_or_ipv4, self.current_data_host in self.search_in_db_hosts.items():
            _found_record = None
            for i, found_record in enumerate(stack):
                logger.debug(f'found_record: {found_record}')
                logger.debug(f'stack: {stack}')
                if self.current_name_or_ipv4 in found_record.values():
                    _found_record = stack.pop(i)
                    break
            if _found_record is not None:
                self.current_data_host.search_in_db_result = ModelFromDb(**_found_record)
            else:
                self.current_data_host.errors.append(str(Messages.not_found_in_database))

    def get_model(self):
        """
        Возвращает pydantic модель, соответсвующую классу.
        :return:
        """
        return NotImplemented


class DataHostsSorterWithSearchInDb(BaseDataHostsSorter):
    def __init__(self, income_data: dict | list):
        BaseDataHostsSorter.__init__(self, income_data)
        self.allowed_search_in_db_hosts: dict[str, Any] = {}





class GetHostsStaticDataWithSearchInDb(DataHostsSorterWithSearchInDb):

    def __init__(self, income_data: list):
        BaseDataHostsSorter.__init__(self, income_data)
        self.income_data = self._income_data_from_list_to_dict(income_data)

    def _income_data_from_list_to_dict(self, income_data: list[str]) -> dict[str, dict]:
        data_host = {'entity': str(AllowedMonitoringEntity.GET_FROM_DB)}
        return {host: data_host  for host in income_data}

    def get_model(self):
        return  HostPropertiesForGetStaticDataFromDb

    def create_responce(self):
        all_hosts = {} | self.bad_hosts
        for ipv4, data in self.allowed_hosts.items():
            data.search_result = ModelFromDb(**data.search_result)
            all_hosts |= {ipv4: data}
        return all_hosts




# class GetStates(BaseDataHostsSorter):
#     """
#     Класс обрабывает и получает данные состояния дорожных контроллеров
#     """
#
#     def get_model(self) -> Type[Monitoring]:
#
#         return Monitoring
#
#     def get_class(self, data: dict):
#         data = GetStateByIpv4(**data)
#         matches = {
#             (AllowedControllers.SWARCO,
#              AllowedMonitoringEntity.GET_STATE,
#              AllowedProtocolsRequest.SNMP
#              ): controller_management.SwarcoSTCIP,
#
#             # (AllowedControllers.PEEK.value, 'get_state'):
#             #     controller_management.PeekGetModeWeb,
#             # (AvailableControllers.PEEK.value, 'get_states'):
#             #     controller_management.GetDifferentStatesFromWeb,
#             # (AvailableControllers.POTOK_P.value, 'get_state'):
#             #     controller_management.PotokP,
#             # (AvailableControllers.POTOK_S.value, 'get_state'):
#             #     controller_management.PotokS,
#         }
#         return matches.get(
#             (data.type_controller, data.entity, data.type_request)
#         )
#
#     async def main(self):
#         objs = []
#         for ip, data_host in self.allowed_hosts.items():
#             a_class = self.get_class(data_host)
#             if a_class is None:
#                 data_host['errors'] = 'Некорректные данные хоста'
#                 self.bad_hosts |= {ip: data_host}
#                 continue
#             objs.append(
#                 a_class(ip, data_host.get('scn'))
#             )
#
#         async with asyncio.TaskGroup() as tg:
#             res = [tg.create_task(obj.get_request(get_mode=True), name=obj.ip_adress) for obj in objs]
#             print(f'res: {res}')


