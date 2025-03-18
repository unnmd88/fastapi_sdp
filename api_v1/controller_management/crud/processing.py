from typing import Any

from api_v1.controller_management.checkers.checkers import AfterSearchInDbChecker
from api_v1.controller_management.checkers.checkers_core import HostData
from api_v1.controller_management.host_entity import BaseHost
from api_v1.controller_management.schemas import NumbersOrIpv4, SearchinDbHostBody, ResponseSearchinDb, \
    AllowedDataHostFields, TrafficLightsObjectsTableFields, SearchinDbHostBodyMonitoringAndManagement


class AfterRead(BaseHost):
    """
    Класс сортировок хостов, преданных пользователем для последующего
    поиска в БД.
    """
    pydantic_class = SearchinDbHostBody

    def __init__(self, source_data: NumbersOrIpv4):
        super().__init__(source_data)
        self.hosts_data = self.create_hosts_data(self.source_data.hosts)
        self.hosts_after_search: list | None = None

    def __repr__(self):
        return (
            f'self.income_data: {self.source_data}\n'
            f'self.hosts_after_search: {self.hosts_after_search}\n'
            f'self.hosts: {self.hosts_data}\n'
        )

    def create_hosts_data(self, hosts: list | dict) -> dict[str, SearchinDbHostBody]:
        return {
            host: self.pydantic_class(
                ip_or_name_source=host,
                search_in_db_field=host,
                db_records=[]
            )
            for host in hosts
        }

    def process_data_hosts_after_request(self):

        for found_record in self.hosts_after_search:
            self._add_record_to_hosts_data(dict(found_record))
        print(f'self.hosts_data: {self.hosts_data}')
        print(f'self.source_data: {self.source_data}')

    def _add_record_to_hosts_data(
            self,
            found_record: dict[str, Any],
    ):

        number, ip = found_record[TrafficLightsObjectsTableFields.NUMBER], found_record[TrafficLightsObjectsTableFields.IP_ADDRESS]
        if number and number in self.hosts_data:
            key = number
        elif ip and found_record[TrafficLightsObjectsTableFields.IP_ADDRESS] in self.hosts_data:
            key = ip
        else:
            return
        # self.hosts_data[key][AllowedDataHostFields.db_records].append(found_record)
        self.hosts_data[key].db_records.append(found_record)

    @property
    def response_as_model(self):
        return ResponseSearchinDb(source_data=self.source_data, results=[self.hosts_data])

    @property
    def response_dict(self):
        return {
            AllowedDataHostFields.source_data: self.source_data,
            AllowedDataHostFields.results: [self.hosts_data],
        }

    @property
    def data_hosts_as_dict(self):
        return {
            ip_or_name: body.model_dump() for ip_or_name, body in self.hosts_data.items()
        }

    def build_data_hosts_as_dict_and_merge_data_from_record_to_body(self):
        return {
            ip_or_name: body.model_dump() | body.db_records[0] if body.count_records == 1 else body.model_dump()
            for ip_or_name, body in self.hosts_data.items()
        }

class ForMonitoringAndManagement(AfterRead):
    pydantic_class = SearchinDbHostBodyMonitoringAndManagement


    def __init__(self, source_data: NumbersOrIpv4):
        super().__init__(source_data)
        self.hosts_data_for_monitoring_and_management = None
        self.good_hosts = {}
        self.bad_hosts = []

    def sort(self):

        for curr_host_ipv4, current_data_host in self.hosts_data.items():

            current_host = AfterSearchInDbChecker(ip_or_name=curr_host_ipv4, properties=current_data_host)
            print(f'current_host.validate_all(): {current_host.validate_all()}')
            print(f'current_host.properties: {current_host}')
            # self._sort_current_host(current_host)
        return self.good_hosts

