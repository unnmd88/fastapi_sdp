from api_v1.controller_management.sorters._core import _HostSorterMonitoringAndManagement
from api_v1.controller_management.checkers.pydantic_checkers import MonitoringHostDataChecker


class HostSorterMonitoring(_HostSorterMonitoringAndManagement):

    def _get_checker_class(self):
        """
        Возвращает класс для валидации данных полей, применяемый в методе self.sort.
        :return:
        """
        return MonitoringHostDataChecker