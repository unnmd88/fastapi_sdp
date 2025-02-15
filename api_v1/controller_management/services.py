import functools
import json
import logging
from enum import StrEnum
from typing import Any

from pydantic import ValidationError, BaseModel

from .schemas import (
    AllowedMonitoringEntity,
    TrafficLightsObjectsTableFields,
    AllowedDataHostFields,
    BaseSearchHostsInDb
)
import logging_config


logger = logging.getLogger(__name__)


class ErrorMessages(StrEnum):
    invalid_ip_or_num_for_search_in_db = 'invalid data for search host in database'
    invalid_ip_or_num = 'invalid number or ip v4 address'
    invalid_ip = 'invalid ip v4 address'
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

    def _add_errors_field_to_current_data_host_if_have_not(self) -> None:
        """
        Добавляет к self.properties свойство в виде dict: {"errors": []}.
        :return: None.
        """
        if self.properties.get(AllowedDataHostFields.errors) is None:
            self.properties |= {str(AllowedDataHostFields.errors): []}

    def add_message_to_error_field_to_current_host(self, message: str) -> None:
        """
        Добавляет сообщение с текстом ошибки.
        :param message: Строка с текстом сообщения
        :return: None
        """
        self._add_errors_field_to_current_data_host_if_have_not()
        self.properties[str(AllowedDataHostFields.errors)].append(message)

    def get_full_host_data_as_dict(self) -> dict[str, dict[str, Any]]:
        """
        Возвращает словарь вида {self.ip_or_name: self.properties}
        :return:
        """
        return {self.ip_or_name: self.properties}


class BaseHostsSorters:
    """
    Базовый класс сортировок хостов, переданных пользователем.
    """
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
        BaseHostsSorters.__init__(self, income_data)
        self._stack_hosts = self._get_income_data_as_dict(income_data.hosts)
        self.hosts_after_search: list | None = None
        self.model_for_search_in_db = self._get_model_for_search_in_db()

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
        """
        Возвращает словарь всех хостов(прошедших валидацию и хостов с ошибками)
        :return: Словарь со всеми хостами запроса.
        """
        return self.hosts | self.get_bad_hosts_as_dict()

    def get_bad_hosts_as_dict(self) -> dict:
        """
        Возвращает self.bad_hosts в виде списка.
        :return: self.bad_hosts в виде списка.
        """
        return functools.reduce(lambda x, y: x | y, self.bad_hosts, {})

    def _get_income_data_as_dict(self, income_hosts: list | dict) -> dict[str, dict[str, str]]:
        """
        Преобразует list хостов в dict, если income_hosts является list.
        Если income_hosts является dict, возвращает себя(income_hosts).
        :param income_hosts: income_hosts от пользователя.
                             Пример: ["string", "3190", "10.45.154.16", "192.168.45.18", "230"] будет пре
                             преобразован в словарь со свойством {'entity': 'get_host_property'}:
                             {'string': {'entity': 'get_host_property'},
                             '3190': {'entity': 'get_host_property'}, '
                             10.45.154.16': {'entity': 'get_host_property'},
                             '192.168.45.18': {'entity': 'get_host_property'},
                             '230': {'entity': 'get_host_property'},
                             }
        :return: income_hosts в виде dict.
        """
        if isinstance(income_hosts, list):
            return {
                ip_or_num: {str(AllowedDataHostFields.entity): str(AllowedMonitoringEntity.GET_FROM_DB)} for ip_or_num
                in income_hosts
            }
        elif isinstance(income_hosts, dict):
            return income_hosts
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
        return [self.model_for_search_in_db(ip_or_name_from_user=host) for host in self._stack_hosts.keys()]

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
        for found_record in self.hosts_after_search:
            found_record = dict(found_record)
            self._pop_found_host_from_stack_hosts(found_record)
            founded_in_db_hosts |= self._build_properties_for_good_host(found_record)

        for current_name_or_ipv4, current_data_host in self._stack_hosts.items():
            current_host = HostData(ip_or_name=current_name_or_ipv4, properties=current_data_host)
            current_host.add_message_to_error_field_to_current_host(str(ErrorMessages.not_found_in_database))
            self.add_host_to_container_with_bad_hosts(current_host.ip_or_name_and_properties_as_dict)
        self.hosts = founded_in_db_hosts
        return self.hosts

    def _pop_found_host_from_stack_hosts(self, found_host: dict[str, str]):
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
            self._stack_hosts.pop(found_host[str(TrafficLightsObjectsTableFields.NUMBER)])
        elif found_host[str(TrafficLightsObjectsTableFields.IP_ADDRESS)] in self._stack_hosts:
            self._stack_hosts.pop(found_host[str(TrafficLightsObjectsTableFields.IP_ADDRESS)])
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
