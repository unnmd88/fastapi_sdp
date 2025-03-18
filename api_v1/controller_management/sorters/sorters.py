import pprint
from typing import Any

from cryptography.hazmat.primitives.asymmetric.ec import EllipticCurveSignatureAlgorithm

from api_v1.controller_management.sorters.sorters_core import (
    _BaseHostsSorters,
    _HostSorterMonitoringAndManagement
)
from api_v1.controller_management.schemas import (
    NumbersOrIpv4,
    SearchHostsInDb,
    AllowedDataHostFields,
    TrafficLightsObjectsTableFields, SearchinDbHostBody, ResponseSearchinDb
)
from api_v1.controller_management.checkers.checkers import HostData, MonitoringHostDataChecker
from core.user_exceptions.validate_exceptions import NotFoundInDB


# class HostProcessorAfterSearchInDB(_BaseHostsSorters):
#     """
#     Класс сортировок хостов, преданных пользователем для последующего
#     поиска в БД.
#     """
#
#     def __init__(self, source_data: NumbersOrIpv4):
#         super().__init__(source_data)
#         self.hosts_data = self.create_hosts_data(self.source_data.hosts)
#         self._stack_hosts: set | None = None
#         self.hosts_after_search: list | None = None
#
#     def __repr__(self):
#         return (
#             f'self.income_data: {self.source_data}\n'
#             f'self.hosts_after_search: {self.hosts_after_search}\n'
#             f'self._stack_hosts: {self._stack_hosts}\n'
#             f'self.good_hosts: {self.good_hosts}\n'
#             f'self.hosts: {self.hosts_data}\n'
#             f'self.bad_hosts: {self.bad_hosts}\n'
#             # f'self.hosts_after_search_in_db: {self.hosts_after_search}\n'
#         )
#
#     def create_hosts_data(self, hosts: list | dict) -> dict[str, SearchinDbHostBody]:
#         return {
#             host: SearchinDbHostBody(
#                 ip_or_name_source=host,
#                 search_in_db_field=host,
#                 db_records=[]
#             )
#             for host in hosts
#         }
#
#     def process_data_hosts_after_request(self):
#
#         for found_record in self.hosts_after_search:
#             self._add_record_to_hosts_data(dict(found_record))
#         print(f'self.hosts_data: {self.hosts_data}')
#         print(f'self.source_data: {self.source_data}')
#
#     def _add_record_to_hosts_data(
#             self,
#             found_record: dict[str, Any],
#     ):
#
#         number, ip = found_record[TrafficLightsObjectsTableFields.NUMBER], found_record[TrafficLightsObjectsTableFields.IP_ADDRESS]
#         if number and number in self.hosts_data:
#             key = number
#         elif ip and found_record[TrafficLightsObjectsTableFields.IP_ADDRESS] in self.hosts_data:
#             key = ip
#         else:
#             return
#         # self.hosts_data[key][AllowedDataHostFields.db_records].append(found_record)
#         self.hosts_data[key].db_records.append(found_record)
#
#     @property
#     def response_as_model(self):
#         return ResponseSearchinDb(source_data=self.source_data, results=[self.hosts_data])
#
#     @property
#     def response_dict(self):
#         return {
#             AllowedDataHostFields.source_data: self.source_data,
#             AllowedDataHostFields.results: [self.hosts_data],
#         }

class AfterSearchInDb(_BaseHostsSorters):
    pass





class HostSorterMonitoring(_HostSorterMonitoringAndManagement):

    def _get_checker_class(self):
        """
        Возвращает класс для валидации данных полей, применяемый в методе self.sort.
        :return:
        """
        return MonitoringHostDataChecker


class HostSorterMonitoringAfterSearchInDb(_HostSorterMonitoringAndManagement):

    def _get_checker_class(self):
        """
        Возвращает класс для валидации данных полей, применяемый в методе self.sort.
        :return:
        """
        return MonitoringHostDataChecker