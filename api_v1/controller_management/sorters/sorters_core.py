import abc
import functools
import logging
from collections.abc import KeysView
from collections.abc import Callable
from typing import Any, Type, TypeVar

from pydantic import BaseModel

from ..checkers.checkers import MonitoringHostDataChecker

import logging_config


logger = logging.getLogger(__name__)


T_PydanticModel = TypeVar("T_PydanticModel", bound=BaseModel)


class _BaseHostsSorters:
    """
    Базовый класс сортировок хостов, переданных пользователем.
    """
    def __init__(
            self,
            income_data: T_PydanticModel | dict[str, Any],
            bad_hosts: list[dict] | None= None,
    ):
        self.income_data = income_data
        self.income_hosts = income_data if isinstance(income_data, dict)  else income_data.hosts
        self.good_hosts: dict | None = None
        self.bad_hosts = bad_hosts or []

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

