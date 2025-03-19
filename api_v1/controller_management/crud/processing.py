from typing import Any

from api_v1.controller_management.checkers.checkers import AfterSearchInDbChecker
from api_v1.controller_management.host_entity import BaseDataHosts
from api_v1.controller_management.schemas import (
    NumbersOrIpv4,
    SearchinDbHostBody,
    ResponseSearchinDb,
    SearchinDbHostBodyForMonitoringAndManagementProxy,
    SearchinDbHostBodyForMonitoring,
    AllowedDataHostFields,
    TrafficLightsObjectsTableFields
)


class AfterRead(BaseDataHosts):
    """
    Класс сортировок хостов, преданных пользователем для последующего
    поиска в БД.
    """

    pydantic_class = SearchinDbHostBody

    def __init__(self, source_data: NumbersOrIpv4):
        super().__init__(source_data)
        self.hosts_after_search: list | None = None

    def __repr__(self):
        return (
            f'self.income_data: {self.source_data}\n'
            f'self.hosts_after_search: {self.hosts_after_search}\n'
            f'self.hosts: {self.hosts_data}\n'
        )

    def create_hosts_data(self) -> dict[str, SearchinDbHostBody | SearchinDbHostBodyForMonitoringAndManagementProxy]:
        return {
            host: self.pydantic_class(
                ip_or_name_source=host,
                search_in_db_field=host,
                db_records=[]
            )
            for host in self.source_data.hosts
        }

    def process_data_hosts_after_request(self):

        for found_record in self.hosts_after_search:
            self._add_record_to_hosts_data(dict(found_record))

    def _add_record_to_hosts_data(
            self,
            found_record: dict[str, Any]
    ) -> str | None:

        number, ip = found_record[TrafficLightsObjectsTableFields.NUMBER], found_record[TrafficLightsObjectsTableFields.IP_ADDRESS]
        if number is None and ip is None:
            return None

        if number in self.hosts_data:
            key = number
        elif found_record[TrafficLightsObjectsTableFields.IP_ADDRESS] in self.hosts_data:
            key = ip
        else:
            raise ValueError('DEBUG: Значение не найдено. Должно быть найдено')
        # self.hosts_data[key][AllowedDataHostFields.db_records].append(found_record)
        self.hosts_data[key].db_records.append(found_record)
        return key

    @property
    def response_as_model(self):
        try:
            return ResponseSearchinDb(source_data=self.source_data, results=[self.hosts_data])
        except ValueError:
            return self.response_dict

    @property
    def response_dict(self):
        return {
            AllowedDataHostFields.source_data: self.source_data,
            AllowedDataHostFields.results: [self.hosts_data],
        }


class ForMonitoringAndManagement(AfterRead):

    pydantic_class = SearchinDbHostBodyForMonitoringAndManagementProxy

    def process_data_hosts_after_request(self):
        super().process_data_hosts_after_request()
        processed_data_hosts = {}
        for curr_host_ipv4, current_data_host in self.hosts_data.items():
            current_host = AfterSearchInDbChecker(ip_or_name=curr_host_ipv4, properties=current_data_host)
            if current_host.validate_all():
                record = current_host.properties.db_records[0]
                key_ip = record[TrafficLightsObjectsTableFields.IP_ADDRESS]
                model = SearchinDbHostBodyForMonitoring(
                    **(current_data_host.model_dump() | record)
                )
                print(f'[key_ip] = {key_ip}')
                print(f'[model] = {model}')
                processed_data_hosts[key_ip] = model
            else:
                processed_data_hosts[curr_host_ipv4] = current_data_host
        self.hosts_data = processed_data_hosts
