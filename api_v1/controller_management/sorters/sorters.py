from api_v1.controller_management.sorters.sorters_core import BaseHostsSorters
from api_v1.controller_management.checkers.checkers import (
    MonitoringHostDataChecker,
    ManagementHostDataChecker
)


# class HostSorterMonitoring(BaseHostsSorters):
#
#     def _get_checker_class(self):
#         """
#         Возвращает класс для валидации данных полей, применяемый в методе self.sort.
#         :return:
#         """
#         return MonitoringHostDataChecker
#
#
# class HostSorterManagement(BaseHostsSorters):
#
#     def _get_checker_class(self):
#         """
#         Возвращает класс для валидации данных полей, применяемый в методе self.sort.
#         :return:
#         """
#         return ManagementHostDataChecker