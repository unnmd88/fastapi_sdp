import abc
import functools
import logging
from collections.abc import KeysView
from collections.abc import Callable
from typing import Any, Type, TypeVar


from api_v1.controller_management.sorters._core import _HostSorterMonitoringAndManagement
from api_v1.controller_management.checkers.custom_checkers import MonitoringHostDataChecker

import logging_config


logger = logging.getLogger(__name__)


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
