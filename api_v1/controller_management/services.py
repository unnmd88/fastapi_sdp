import abc
import asyncio
import functools
import itertools
from dataclasses import dataclass
import ipaddress
import json
import logging
from copy import deepcopy
from enum import StrEnum
from itertools import zip_longest
from typing import Type, Any, Sequence

from more_itertools.more import raise_
from pydantic.json_schema import model_json_schema

import logging_config
from re import search

from pydantic import ValidationError, BaseModel, field_validator

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


class ErrorMessages(StrEnum):
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
    def __init__(self, income_data: BaseModel):
        self.income_data = income_data
        self.hosts: dict[str, str] | list[str] = income_data.hosts
        self.bad_hosts = []

    def get_pydantic_model_or_none(self, data_host: dict, model) -> BaseModel | None:
        logger.debug(f'data_host get_model_host_data: {data_host}')
        try:
            return model(**data_host)
        except ValidationError:
            return None

    def add_host_to_container_with_bad_hosts(self, host: dict[str, str]):

        self.bad_hosts.append(host)


class CurrentHostData:

    def __init__(self, ip_or_name: str, properties: dict):
        self.ip_or_name = ip_or_name
        self.properties = properties
        self.ip_or_name_and_properties_as_dict = self.get_full_host_data_as_dict()

    def _add_errors_field_to_current_data_host_if_have_not(self):

        if self.properties.get(AllowedDataHostFields.errors) is None:
            self.properties |= {str(AllowedDataHostFields.errors): []}

    def add_message_to_error_field_to_current_host(self, message: str):
        self._add_errors_field_to_current_data_host_if_have_not()
        self.properties[str(AllowedDataHostFields.errors)].append(message)

    def get_full_host_data_as_dict(self):
        return {self.ip_or_name: self.properties}


class HostSorterSearchInDB(BaseHostsSorters):

    def __init__(self, income_data: BaseModel):
        BaseHostsSorters.__init__(self, income_data)
        self._stack_hosts = self._get_income_data_as_dict(income_data.hosts)
        self.hosts_after_search: list | None = None
        self.model_for_search_in_db = self._get_model_for_search_in_db()
        self._current_record = None

    def __repr__(self):
        return (
            f'self.income_data: {self.income_data}\n'
            f'self.model_for_search_in_db: {self.model_for_search_in_db}\n'
            f'self.hosts_after_search: {self.hosts_after_search}\n'
            f'self._stack_hosts: {self._stack_hosts}\n'
            f'self.hosts: {self.hosts}\n'
            f'self.bad_hosts: {self.bad_hosts}\n'
            # f'self.hosts_after_search_in_db: {self.hosts_after_search}\n'
        )

    def get_hosts_and_bad_hosts_as_dict(self) -> dict:
        return self.hosts | self.get_bad_hosts_as_dict()

    def get_bad_hosts_as_dict(self) -> dict:
        return functools.reduce(lambda x, y: x | y, self.bad_hosts, {})

    def _get_income_data_as_dict(self, hosts_for_response: list | dict) -> dict[str, dict[str, str]]:
        if isinstance(hosts_for_response, list):
            return {
                ip_or_num: {str(AllowedDataHostFields.entity): str(AllowedMonitoringEntity.GET_FROM_DB)} for ip_or_num
                in hosts_for_response
            }
        elif isinstance(hosts_for_response, dict):
            return hosts_for_response
        raise ValueError('Переданный тип должен быть list или dict')

    def _get_model_for_search_in_db(self):
        return BaseSearchHostsInDb

    def get_hosts_data_for_search_db(self):
        return [self.model_for_search_in_db(ip_or_name_from_user=host) for host in self._stack_hosts.keys()]

    def sorting_hosts_after_search_from_db(self) -> dict[str, dict[str, Any]]:

        # self.hosts_after_search = self.convert_hosts_after_search_to_dicts()
        founded_in_db_hosts = {}
        # logger.debug(f'!! self.hosts_after_search >> {self.hosts_after_search}')

        for found_record in self.hosts_after_search:
            found_record = dict(found_record)
            self._pop_found_host_from_stack_hosts(found_record)
            founded_in_db_hosts |= self._build_properties_for_good_host(found_record)

        logger.debug(f'!! self._stack_hosts >> {self._stack_hosts}')
        logger.debug(f'!! len self._stack_hosts >> {len(self._stack_hosts)}')

        for current_name_or_ipv4, current_data_host in self._stack_hosts.items():
            current_host = CurrentHostData(ip_or_name=current_name_or_ipv4, properties=current_data_host)
            current_host.add_message_to_error_field_to_current_host(str(ErrorMessages.not_found_in_database))
            self.add_host_to_container_with_bad_hosts(current_host.ip_or_name_and_properties_as_dict)
        self.hosts = founded_in_db_hosts
        return self.hosts

    def _pop_found_host_from_stack_hosts(self, found_host: dict[str, str]):

        if found_host[str(TrafficLightsObjectsTableFields.NUMBER)] in self._stack_hosts:
            self._stack_hosts.pop(found_host[str(TrafficLightsObjectsTableFields.NUMBER)])
        elif found_host[str(TrafficLightsObjectsTableFields.IP_ADDRESS)] in self._stack_hosts:
            self._stack_hosts.pop(found_host[str(TrafficLightsObjectsTableFields.IP_ADDRESS)])
        else:
            raise ValueError('DEBUG: Найденный хост в БД должен содержаться в self.hosts_for_response!!')

    def _build_properties_for_good_host(self, record_from_db) -> dict[str, str]:
        ipv4 = record_from_db.pop(str(TrafficLightsObjectsTableFields.IP_ADDRESS))
        return {ipv4: record_from_db}


