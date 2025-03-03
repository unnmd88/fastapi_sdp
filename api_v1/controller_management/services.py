import abc
import functools
import json
import logging
from collections.abc import KeysView
from collections.abc import Callable
from enum import StrEnum
from typing import Any

from pydantic import ValidationError, BaseModel

from sdp_lib.utils_common import check_is_ipv4
from sdp_lib.management_controllers import exceptions as client_exceptions
from .schemas import (
    AllowedMonitoringEntity,
    TrafficLightsObjectsTableFields,
    AllowedDataHostFields,
    BaseSearchHostsInDb,
    BaseMonitoringHostBody,
    GetState,
    AllowedControllers
)
import logging_config


logger = logging.getLogger(__name__)


class ErrorMessages(StrEnum):
    invalid_ip_or_num_for_search_in_db = 'invalid data for search host in database'
    invalid_ip_or_num = 'invalid number or ip v4 address'
    invalid_ip = 'invalid ip v4 address'
    invalid_type_controller = 'invalid_type_controller'
    invalid_host_data = 'invalid host data'
    not_found_in_database = 'not found in database'


class HostData:
    """
    Класс - обработчик данных хоста.
    """

    def __init__(self, ip_or_name: str, properties: dict):
        self.ip_or_name = ip_or_name
        self.properties = properties
        self.ip_or_name_and_properties_as_dict = self.get_full_host_data_as_dict()

    def __repr__(self):
        return (
            f'self.ip_or_name: {self.ip_or_name}\n'
            f'self.properties: {json.dumps(self.properties, indent=2)}\n'
            f'self.ip_or_name_and_properties_as_dict: {json.dumps(self.ip_or_name_and_properties_as_dict, indent=2)}\n'
        )

    def _add_errors_field_for_current_data_host_if_have_not(self) -> None:
        """
        Добавляет к self.properties свойство в виде dict: {"errors": []}.
        :return: None.
        """
        if self.properties.get(AllowedDataHostFields.errors) is None:
            self.properties |= {str(AllowedDataHostFields.errors): []}

    def add_message_to_error_field_for_current_host(self, message: str | list | ErrorMessages | Exception) -> None:
        """
        Добавляет сообщение с текстом ошибки.
        :param message: Строка с текстом сообщения
        :return: None
        """
        self._add_errors_field_for_current_data_host_if_have_not()
        if isinstance(message, str):
            self.properties[str(AllowedDataHostFields.errors)].append(str(message))
        elif isinstance(message, Exception):
            self.properties[str(AllowedDataHostFields.errors)].append(str(message))
        elif isinstance(message, list):
            self.properties[str(AllowedDataHostFields.errors)] += message

    def get_full_host_data_as_dict(self) -> dict[str, dict[str, Any]]:
        """
        Возвращает словарь вида {self.ip_or_name: self.properties}
        :return:
        """
        return {self.ip_or_name: self.properties}

    def _get_full_host_data_as_dict(self) -> dict[str, Any]:
        return self.properties | {str(AllowedDataHostFields.ipv4): self.ip_or_name}


class MonitoringHostDataChecker(HostData):

    def validate_ipv4(self, add_to_bad_hosts_if_not_valid=True) -> bool:
        if check_is_ipv4(self.ip_or_name):
            return True
        if add_to_bad_hosts_if_not_valid:
            self.add_message_to_error_field_for_current_host(client_exceptions.BadIpv4())
        return False

    def validate_type_controller(self, add_to_bad_hosts_if_not_valid=True) -> bool:
        try:
            AllowedControllers(self.properties[str(AllowedDataHostFields.type_controller)])
            return True
        except ValueError:
            if add_to_bad_hosts_if_not_valid:
                self.add_message_to_error_field_for_current_host(client_exceptions.BadControllerType())
            return False

    def get_validate_methods(self):
        return [self.validate_ipv4, self.validate_type_controller]


class BaseHostsSorters:
    """
    Базовый класс сортировок хостов, переданных пользователем.
    """
    def __init__(self, income_data: BaseModel):
        self.income_data = income_data
        self.income_hosts: list[str] | dict[str, str] | dict[str, dict[str, str]] = income_data.hosts
        self.good_hosts: dict | None = None
        self.bad_hosts = []

    # def get_pydantic_model_or_none(self, data_host: dict, model) -> BaseModel | None:
    #     logger.debug(f'data_host get_model_host_data: {data_host}')
    #     try:
    #         return model(**data_host)
    #     except ValidationError:
    #         return None
    #
    # def get_model_for_body(self):
    #     raise NotImplemented

    def add_host_to_container_with_bad_hosts(self, host: dict[str, Any]):
        """
        Добавляет хост с ошибками в контейнер self.bad_hosts
        :param host: Хост, который будет добавлен в контейнер self.bad_hosts.
        :return: None
        """
        if isinstance(self.bad_hosts, list):
            self.bad_hosts.append(host)
        elif isinstance(self.bad_hosts, dict):
            self.bad_hosts |= host
        else:
            raise TypeError(f'DEBUG: Тип контейнера < self.bad_hosts > должен быть dict или list')


class HostSorterSearchInDB(BaseHostsSorters):
    """
    Класс сортировок хостов, преданных пользователем с учётом поиска хостов в БД.
    """

    def __init__(self, income_data: BaseModel):
        super().__init__(income_data)
        self._stack_hosts: set | None = None
        self.hosts_after_search: list | None = None
        self.model_for_search_in_db = self._get_model_for_search_in_db()

    def __repr__(self):
        return (
            f'self.income_data: {self.income_data}\n'
            f'self.model_for_search_in_db: {self.model_for_search_in_db}\n'
            f'self.hosts_after_search: {self.hosts_after_search}\n'
            f'self._stack_hosts: {self._stack_hosts}\n'
            f'self.good_hosts: {self.good_hosts}\n'
            f'self.hosts: {self.income_hosts}\n'
            f'self.bad_hosts: {self.bad_hosts}\n'
            # f'self.hosts_after_search_in_db: {self.hosts_after_search}\n'
        )

    def get_good_hosts_and_bad_hosts_as_dict(self) -> dict:
        """
        Возвращает словарь всех хостов(прошедших валидацию и хостов с ошибками)
        :return: Словарь со всеми хостами запроса.
        """
        return self.good_hosts | self.get_bad_hosts_as_dict()

    def get_bad_hosts_as_dict(self) -> dict:
        """
        Возвращает self.bad_hosts в виде списка.
        :return: self.bad_hosts в виде списка.
        """
        return functools.reduce(lambda x, y: x | y, self.bad_hosts, {})

    def _get_income_hosts_as_set(self, income_hosts: list | dict) -> set[str]:
        """
        Преобразует income_hosts хостов в set.
        :param income_hosts: income_hosts от пользователя.
        :return: income_hosts в виде set.
        """
        if isinstance(income_hosts, list):
            return set(income_hosts)
        elif isinstance(income_hosts, dict):
            return set(income_hosts.keys())
        raise ValueError('Переданный тип должен быть list или dict')

    def _get_model_for_search_in_db(self):
        """
        Возвращает модель pydantic, которой будут переданы данные хоста для валидации
        на предмет возможности хоста в БД.
        :return: Модель pydantic.
        """
        return BaseSearchHostsInDb

    def get_hosts_data_for_search_db(self):
        """
        Возвращает список с экземплярами модели, полученной в self._get_model_for_search_in_db()
        для каждого хоста, для формирования stmt запрос.
        :return: list с экземплярами модели, полученной self._get_model_for_search_in_db()
        """
        return [self.model_for_search_in_db(ip_or_name_from_user=host) for host in self.income_hosts]

    def sorting_hosts_after_search_from_db(self) -> dict[str, dict[str, Any]]:
        """
        Сортирует хосты: если хост был найден в БД, отправляет в self.hosts, иначе в self.bad_hosts.
        Также приводит свойства хостов(dict) к общему виду, см. описание founded_in_db_hosts и self.bad_hosts.
        founded_in_db_hosts: dict, в который будут добавляться хосты, найденные в БД.
                             Пример:
                             {
                             "10.179.56.1": {
                             "number": "12",
                             "type_controller": "Поток (P)",
                             "address": "Щербаковская ул. - Вельяминовская ул. д.6к1,32   ВАО (ВАО-4)",
                             "description": "Приоритет ОТ"
                             },
                             "10.179.40.9": {
                             "number": "13",
                             "type_controller": "Swarco",
                             "address": "Шереметьевская ул. д.60,62,29,27к1 - Марьиной Рощи 11-й пр-д (СВАО-2)",
                             "description": null
                             }
                             }
        self.bad_hosts: В контексте данного метода это list с хостами, которые не были найдены в БД.
                        Пример:
                        [
                        {'string': {'entity': 'get_host_property', 'errors': ['not found in database']}},
                        {'abra': {'entity': 'get_host_property', 'errors': ['not found in database']}},
                        {'cadabra': {'entity': 'get_host_property', 'errors': ['not found in database']}}
                        ]
        :return: self.hosts
        """

        founded_in_db_hosts = {}
        self._stack_hosts = self._get_income_hosts_as_set(self.income_hosts)
        for found_record in self.hosts_after_search:
            found_record = dict(found_record)
            self._remove_found_host_from_stack_hosts(found_record)
            founded_in_db_hosts |= self._build_properties_for_good_host(found_record)

        for current_name_or_ipv4 in self._stack_hosts:
            current_host = HostData(ip_or_name=current_name_or_ipv4, properties={})
            current_host.add_message_to_error_field_for_current_host(str(client_exceptions.NotFoundInDB(current_name_or_ipv4)))
            self.add_host_to_container_with_bad_hosts(current_host.ip_or_name_and_properties_as_dict)
        self.good_hosts = founded_in_db_hosts
        return self.good_hosts

    def _remove_found_host_from_stack_hosts(self, found_host: dict[str, str]):
        """
        Удаляет найденный в БД хост из self._stack_hosts.
        :param found_host: Запись о хосте, найденная в БД.
                           Пример:
                           {
                           'number': '11', 'ip_adress': '10.179.28.9', 'type_controller': 'Swarco',
                           'address': 'Бережковская наб. д.22, 24    ЗАО (ЗАО-9)', 'description': 'Приоритет ОТ'
                           }

        :return: None.
        """

        if found_host[str(TrafficLightsObjectsTableFields.NUMBER)] in self._stack_hosts:
            self._stack_hosts.remove(found_host[str(TrafficLightsObjectsTableFields.NUMBER)])
        elif found_host[str(TrafficLightsObjectsTableFields.IP_ADDRESS)] in self._stack_hosts:
            self._stack_hosts.remove(found_host[str(TrafficLightsObjectsTableFields.IP_ADDRESS)])
        else:
            raise ValueError('DEBUG: Найденный хост в БД должен содержаться в self.hosts_for_response!!')

    def _build_properties_for_good_host(self, record_from_db) -> dict[str, str]:
        """
        Формирует свойства хоста в виде словаря.
        :param record_from_db: Запись, найденная в БД.
                               Пример:
                              {
                               'number': '11', 'ip_adress': '10.179.28.9', 'type_controller': 'Swarco',
                               'address': 'Бережковская наб. д.22, 24    ЗАО (ЗАО-9)', 'description': 'Приоритет ОТ'
                               }
        :return: dict со свойствами хоста общего вида, где ключом является ip адрес, а значением остальные
                 свойства dict record_from_db
                 Пример:
                 "10.179.28.9":
                 {
                    "number": "11",
                    "type_controller": "Swarco",
                    "address": "Бережковская наб. д.22, 24    ЗАО (ЗАО-9)",
                    "description": "Приоритет ОТ"
                 }
        """
        ipv4 = record_from_db.pop(str(TrafficLightsObjectsTableFields.IP_ADDRESS))
        return {ipv4: record_from_db}


class BaseHostSorterNoSearchInDB(BaseHostsSorters):

    @abc.abstractmethod
    def get_checker_class(self):
        ...

    def sorting(self):
        allowed_to_request_hosts = {}
        checker_class = self.get_checker_class()
        for curr_host_ipv4, current_data_host in self.income_hosts.items():
            current_host = checker_class(ip_or_name=curr_host_ipv4, properties=current_data_host)
            for validate_method in current_host.get_validate_methods():
                if validate_method():
                    allowed_to_request_hosts |= current_host.ip_or_name_and_properties_as_dict
                else:
                    self.add_host_to_container_with_bad_hosts(current_host.ip_or_name_and_properties_as_dict)
            print(f"current_host.properties: {current_host.properties}")
        self.hosts = allowed_to_request_hosts
        return self.hosts


class HostSorterNoSearchInDBMonitoring(BaseHostSorterNoSearchInDB):

    def get_checker_class(self):
        return MonitoringHostDataChecker
