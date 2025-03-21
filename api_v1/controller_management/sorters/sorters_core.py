import abc
import copy
import functools
import logging
from collections.abc import Callable, KeysView
from typing import Any, Type, TypeVar

from pydantic import BaseModel

import logging_config
from api_v1.controller_management.checkers.checkers import MonitoringHostDataChecker
from api_v1.controller_management.host_entity import BaseDataHosts
from api_v1.controller_management.schemas import (
    DataHostMonitoring,
    DataHostManagement,
    FastMonitoring,
    FastManagement
)


logger = logging.getLogger(__name__)

T_PydanticModel = TypeVar(
    "T_PydanticModel",
    DataHostMonitoring,
    DataHostManagement,
    FastMonitoring,
    FastManagement
)


class BaseHostsSorters(BaseDataHosts):
    """
    Базовый класс сортировок хостов, переданных пользователем.
    """
    def __init__(self, source_data: dict[str, T_PydanticModel]):
        super().__init__(source_data)
        self.hosts_without_errors = {}
        self.hosts_with_errors = {}

    def __repr__(self):
        return (
            f'self.income_data: {self.source_data}\n'
            f'self.income_hosts: {self.hosts_data}\n'
            f'self.good_hosts: {self.hosts_without_errors}\n'
            f'self.bad_hosts: {self.hosts_with_errors}\n'
        )

    def _create_hosts_data(self) -> dict:
        return copy.deepcopy(self.source_data)

    def add_host_to_container_with_bad_hosts(self, host: dict[str, Any]):
        """
        Добавляет хост с ошибками в контейнер self.bad_hosts
        :param host: Хост, который будет добавлен в контейнер self.bad_hosts.
        :return: None
        """
        if isinstance(self.hosts_with_errors, list):
            self.hosts_with_errors.append(host)
        elif isinstance(self.hosts_with_errors, dict):
            self.hosts_with_errors |= host
        else:
            raise TypeError(f'DEBUG: Тип контейнера < self.bad_hosts > должен быть dict или list')

    def get_good_hosts_and_bad_hosts_as_dict(self) -> dict:
        """
        Возвращает словарь всех хостов(прошедших валидацию и хостов с ошибками)
        :return: Словарь со всеми хостами запроса.
        """
        return self.hosts_without_errors | self.get_bad_hosts_as_dict()

    def get_bad_hosts_as_dict(self) -> dict:
        """
        Возвращает self.bad_hosts в виде списка.
        :return: self.bad_hosts в виде списка.
        """
        return functools.reduce(lambda x, y: x | y, self.hosts_with_errors, {})

    def _get_income_hosts(self):

        if isinstance(self.source_data, dict):
            return copy.deepcopy(self.source_data)
        elif isinstance(self.source_data, BaseModel):
            return copy.deepcopy(self.source_data.hosts)
        raise ValueError('self.income_data должен быть типом dict или экземпляром Pydantic Model с атрибутом hosts')

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
        self.hosts_without_errors = {}
        checker_class = self._get_checker_class()
        for curr_host_ipv4, current_data_host in self.hosts_data.items():

            current_host = checker_class(ip_or_name=curr_host_ipv4, properties=current_data_host)
            if current_host.properties.errors:
                # print(f'current_host.full_host_data_as_dict: {current_host.full_host_data_as_dict}')
                self.add_host_to_container_with_bad_hosts(current_host.full_host_data_as_dict)
                # self.hosts_with_errors.append(current_host.full_host_data_as_dict)
                continue
            self._sort_current_host(current_host)
        # print(f'self.hosts_with_eER: {self.hosts_with_errors}')
        return self.hosts_without_errors

    def _sort_current_host(self, current_host: MonitoringHostDataChecker) -> None:
        if all(validate_method() for validate_method in current_host.get_validate_methods()):
            self.hosts_without_errors |= current_host.full_host_data_as_dict
        else:
            self.add_host_to_container_with_bad_hosts(current_host.full_host_data_as_dict)

