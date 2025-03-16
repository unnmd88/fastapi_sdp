import abc
import functools
import logging
from typing import Any, Type, TypeVar

from pydantic import BaseModel

from api_v1.controller_management.checkers.archive.custom_checkers import HostData, MonitoringHostDataChecker
from core.user_exceptions.validate_exceptions import NotFoundInDB
from .schemas import (
    TrafficLightsObjectsTableFields,
    SearchHostsInDb,
    NumbersOrIpv4, AllowedDataHostFields
)

logger = logging.getLogger(__name__)


T_PydanticModel = TypeVar("T_PydanticModel", bound=BaseModel)


class _BaseHostsSorters:
    """
    Базовый класс сортировок хостов, переданных пользователем.
    """
    def __init__(self, income_data: T_PydanticModel):
        self.income_data = income_data
        self.income_hosts = income_data.hosts
        self.good_hosts: dict | None = None
        self.bad_hosts = []

    def __repr__(self):
        return (
            f'self.income_data: {self.income_data}\n'
            f'self.income_hosts: {self.income_hosts}\n'
            f'self.good_hosts: {self.good_hosts}\n'
            f'self.bad_hosts: {self.bad_hosts}\n'
        )

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


class HostSorterSearchInDB(_BaseHostsSorters):
    """
    Класс сортировок хостов, преданных пользователем для последующего
    поиска в БД.
    """

    def __init__(self, income_data: NumbersOrIpv4):
        super().__init__(income_data)
        self._stack_hosts: set | None = None
        self.hosts_after_search: list | None = None

    def __repr__(self):
        return (
            f'self.income_data: {self.income_data}\n'
            f'self.hosts_after_search: {self.hosts_after_search}\n'
            f'self._stack_hosts: {self._stack_hosts}\n'
            f'self.good_hosts: {self.good_hosts}\n'
            f'self.hosts: {self.income_hosts}\n'
            f'self.bad_hosts: {self.bad_hosts}\n'
            # f'self.hosts_after_search_in_db: {self.hosts_after_search}\n'
        )

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

    def get_hosts_data_for_search_in_db(self) -> list[SearchHostsInDb]:
        """
        Возвращает список с экземплярами модели, полученной в self._get_model_for_search_in_db(),
        для формирования stmt.
        :return: list с экземплярами модели, полученной self._get_model_for_search_in_db().
                 Пример:
                 [
                 SearchHostsInDb(ip_or_name_from_user='10.45.154.16', search_in_db_field='ip_adress'),
                 SearchHostsInDb(ip_or_name_from_user='11', search_in_db_field='number'),
                 SearchHostsInDb(ip_or_name_from_user='abracadabra', search_in_db_field='number'),
                 SearchHostsInDb(ip_or_name_from_user='413-P', search_in_db_field='number')
                 ]
        """
        return [SearchHostsInDb(ip_or_name_from_user=host) for host in self.income_hosts]

    def sorting_hosts_after_search_from_db(self) -> dict[str, dict[str, Any]]:
        """
        Сортирует хосты: если хост был найден в БД, отправляет в self.good_hosts, иначе в self.bad_hosts.
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
                        {'string': {'errors': ['not found in database']}},
                        {'abra': {'errors': ['not found in database']}},
                        {'cadabra': {'errors': ['not found in database']}}
                        ]
        :return: Атрибут self.good_hosts с хостами, найденными в БД.
        """

        self.good_hosts = {}
        self._stack_hosts = self._get_income_hosts_as_set(self.income_hosts)
        for found_record in self.hosts_after_search:
            found_record = dict(found_record)
            self._remove_found_host_from_stack_hosts(found_record)
            self.good_hosts |= self._build_properties_for_good_host(found_record)
        self._process_hosts_not_found_in_db()
        return self.good_hosts

    def _process_hosts_not_found_in_db(self) -> None:
        """
        Обрабатывает хосты из self._stack_hosts, которые не были найдены в БД. Добавляет
        словарь с полем errors(list) и текстом ошибки методом self.add_host_to_container_with_bad_hosts.
        Пример:
            "abra": {
                "errors": ["Не найден в базе данных, ip: 'abra'"]
            }
        :return: None.
        """
        for current_name_or_ipv4 in self._stack_hosts:
            current_host = HostData(ip_or_name=current_name_or_ipv4, properties={})
            e = NotFoundInDB(field_name=str(AllowedDataHostFields.ip_or_name), input_val=current_name_or_ipv4)
            current_host.add_error_entity_for_current_host(e)
            self.add_host_to_container_with_bad_hosts(current_host.ip_or_name_and_properties_as_dict)

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


class _HostSorterMonitoringAndManagement(_BaseHostsSorters):

    @abc.abstractmethod
    def _get_checker_class(self) -> Type[MonitoringHostDataChecker]:
        """
        Возвращает класс для валидации данных полей, применяемый в методе self.sort.
        Необходимо использовать класс из модуля custom_checkers.py.
        :return:
        """
        pass

    def sort(self):
        """
        Основной метод сортировки данных из json.
        :return: None.
        """
        self.good_hosts = {}
        checker_class = self._get_checker_class()
        for curr_host_ipv4, current_data_host in self.income_hosts.items():
            current_host = checker_class(ip_or_name=curr_host_ipv4, properties=current_data_host)
            self._sort_current_host(current_host)
        return self.good_hosts

    def _sort_current_host(self, current_host: MonitoringHostDataChecker) -> None:
        if all(validate_method() for validate_method in current_host.get_validate_methods()):
            self.good_hosts |= current_host.ip_or_name_and_properties_as_dict
        else:
            self.add_host_to_container_with_bad_hosts(current_host.ip_or_name_and_properties_as_dict)


class HostSorterMonitoring(_HostSorterMonitoringAndManagement):

    def _get_checker_class(self):
        """
        Возвращает класс для валидации данных полей, применяемый в методе self.sort.
        :return:
        """
        return MonitoringHostDataChecker


class HostSorterManagement(_HostSorterMonitoringAndManagement):

    def _get_checker_class(self):
        raise NotImplementedError
