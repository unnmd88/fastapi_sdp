import time
from collections.abc import Sequence
from functools import cached_property
from typing import Any, TypeVar, Type

from core.models import db_helper, TrafficLightsObjects
from sqlalchemy import select, or_, Select
from sqlalchemy.engine.row import RowMapping

from api_v1.controller_management.checkers.checkers import AfterSearchInDbChecker
from api_v1.controller_management.host_entity import BaseDataHosts
from api_v1.controller_management.schemas import (
    TrafficLightsObjectsTableFields,
    AllowedDataHostFields,
    BaseFieldsSearchInDb,
    SearchinDbFields,
    ResponseSearchinDb,
    BaseFieldsWithSearchInDb,
    DataHostManagement
)
from core.utils import get_field_for_search_in_db


async def search_hosts_base_properties(query) -> list[RowMapping]:
    """
    Осуществляет запрос поиска в БД.
    :param query: Сущность запроса.
    :return: list с найденными записями RowMapping.
    """
    async with db_helper.engine.connect() as conn:
        result = await conn.execute(query)
        return result.mappings().all()

# Deprecated
class BaseRead:
    """
    Базовый класс поиска в БД.
    """
    async def search_hosts_base_properties(self, query) -> list[RowMapping]:
        """
        Осуществляет запрос поиска в БД.
        :param query: Сущность запроса.
        :return: list с найденными записями RowMapping.
        """
        async with db_helper.engine.connect() as conn:
            result = await conn.execute(query)
            return result.mappings().all()


class SearchHostsByIpOrNumQuery:
    """
    Поиск хостов в БД по определённым полям.
    """

    def __init__(self, all_columns: bool = False):
        self.all_columns = all_columns

    def get_query_where(
            self,
            hosts_models: dict[str, SearchinDbFields]
    ) -> Select[tuple[TrafficLightsObjects]]:
        """
        Формирует сущность запроса поиска записей в БД для каждого хоста из hosts.
        :param hosts_models: Список вида с объектами моделей, в которых содержаться
                              данные для поиска. Например:
                              [BaseSearchHostsInDb(ip_or_name_from_user='10.45.154.16',
                              search_in_db_field='ip_adress'), BaseSearchHostsInDb(ip_or_name_from_user='3245']
        :return: Select[tuple[TrafficLightsObjects]]
        """
        query = (
            self.matches.get(data_hots.search_in_db_field) == ip_or_name_from_user
            for ip_or_name_from_user, data_hots in hosts_models.items()
        )
        if self.all_columns:
            return select(TrafficLightsObjects).where(or_(*query))
        return select(*self.standard_columns).where(or_(*query))

    @cached_property
    def standard_columns(self) -> tuple:
        return (
            TrafficLightsObjects.number,
            TrafficLightsObjects.ip_adress,
            TrafficLightsObjects.type_controller,
            TrafficLightsObjects.address,
            TrafficLightsObjects.description
        )

    @cached_property
    def matches(self):
        return {
            TrafficLightsObjectsTableFields.NUMBER: TrafficLightsObjects.number,
            TrafficLightsObjectsTableFields.IP_ADDRESS: TrafficLightsObjects.ip_adress,
        }


# class BaseProcessor(BaseDataHosts):
#
#     search_in_db_class = ReadHostsByIpOrNum
#
#     def __init__(self, source_data: NumbersOrIpv4):
#         super().__init__(source_data)
#         self.hosts_after_search: list | None = None
#         self.db = self._get_search_in_db_instance()
#         self.start_time = time.time()
#
#     @classmethod
#     def _get_search_in_db_instance(cls):
#         return cls.search_in_db_class()
#
#     def __repr__(self):
#         return (
#             f'self.income_data: {self.source_data}\n'
#             f'self.hosts_after_search: {self.hosts_after_search}\n'
#             f'self.hosts: {self.hosts_data}\n'
#         )
#
#     def _create_hosts_data(self) -> dict[str, SearchinDbHostBody]:
#         return {
#             host: SearchinDbHostBody(
#                 ip_or_name_source=host,
#                 search_in_db_field=host,
#                 db_records=[]
#             )
#             for host in self.source_data.hosts
#         }
#
#     def _process_data_hosts_after_request(self):
#
#         for found_record in self.hosts_after_search:
#             self._add_record_to_hosts_data(dict(found_record))
#
#     def _add_record_to_hosts_data(
#             self,
#             found_record: dict[str, Any]
#     ) -> str | None:
#
#         number, ip = (
#             found_record[TrafficLightsObjectsTableFields.NUMBER],
#             found_record[TrafficLightsObjectsTableFields.IP_ADDRESS]
#         )
#         if number is None and ip is None:
#             return None
#
#         if number in self.hosts_data:
#             key = number
#         elif found_record[TrafficLightsObjectsTableFields.IP_ADDRESS] in self.hosts_data:
#             key = ip
#         else:
#             raise ValueError('DEBUG: Значение не найдено. Должно быть найдено')
#         # self.hosts_data[key][AllowedDataHostFields.db_records].append(found_record)
#         self.hosts_data[key].db_records.append(found_record)
#         return key
#
#     async def search_hosts_and_processing(self):
#         self.hosts_after_search = await self.db.get_hosts_where(
#             self.db.get_query_where(self.hosts_data)
#         )
#         self._process_data_hosts_after_request()
#         return self.hosts_data


class SearchDb:

    search_in_db_class = SearchHostsByIpOrNumQuery

    def __init__(self, src_data: BaseFieldsSearchInDb):
        # super().__init__(src_data)
        self._src_data = src_data
        self._src_hosts = src_data.hosts
        self._processed_hosts_data = self._create_hosts_data()
        self._hosts_after_search: list | None = None
        self.db = self.search_in_db_class()
        self.start_time = time.time()

    def __repr__(self):
        return (f'self._src_data: {self._src_data!r}\n'
                f'self._src_hosts: {self._src_hosts!r}\n'
                f'self.processed_hosts_data: {self._processed_hosts_data!r}\n'
                f'self.hosts_after_search: {self._hosts_after_search!r}\n'
                )

        # print(f'DEBUG self._src_data {self._src_data}')
        # print(f'DEBUG self._hosts: {self._src_hosts}')
        # print(f'DEBUG self.hosts_data: {self.processed_hosts_data}')

    def _create_hosts_data(self) -> dict[str, SearchinDbFields]:
        return {
            name_or_ipv4: SearchinDbFields(
                ip_or_name_source=name_or_ipv4,
                search_in_db_field=get_field_for_search_in_db(name_or_ipv4),
                db_records=[]
            )
            for name_or_ipv4 in self._src_hosts
        }

    def _process_data_hosts_after_request(self):

        for found_record in self._hosts_after_search:
            # print(f'found_record: {found_record}')
            self._add_record_to_hosts_data(dict(found_record))

    def _add_record_to_hosts_data(
            self,
            found_record: dict[str, Any]
    ) -> str | None:

        number, ip = (
            found_record[TrafficLightsObjectsTableFields.NUMBER],
            found_record[TrafficLightsObjectsTableFields.IP_ADDRESS]
        )
        if number is None and ip is None:
            return None

        if number in self._src_hosts:
            key = number
        elif found_record[TrafficLightsObjectsTableFields.IP_ADDRESS] in self._processed_hosts_data:
            key = ip
        else:
            raise ValueError('DEBUG: Значение не найдено. Должно быть найдено')
        # self.hosts_data[key][AllowedDataHostFields.db_records].append(found_record)
        self._processed_hosts_data[key].db_records.append(found_record)
        return key

    async def search_hosts_and_processing(self):
        self._hosts_after_search = await search_hosts_base_properties(
            self.db.get_query_where(self._processed_hosts_data)
        )
        self._process_data_hosts_after_request()
        print(f'self.hosts_data: {self._processed_hosts_data}')
        return self._processed_hosts_data

    @property
    def src_data(self):
        return self._src_data

    @property
    def src_hosts(self):
        return self._src_hosts

    @property
    def processed_hosts_data(self) -> dict[str, SearchinDbFields]:
        return self._processed_hosts_data

    @property
    def hosts_after_search(self):
        return self._hosts_after_search


class HostPropertiesFromDb(SearchDb):

    def get_response_as_model(self, **add_to_response):
        try:
            return ResponseSearchinDb(
                source_data=self._src_data.source_data,
                results=[self._processed_hosts_data],
                time_execution=time.time() - self.start_time,
                **add_to_response
            )
        except ValueError:
            return self.get_response_dict

    def get_response_dict(self):
        return {
            AllowedDataHostFields.source_data: self._src_data,
            AllowedDataHostFields.results: [self._processed_hosts_data],
        }


# T_Checker = TypeVar('T_Checker', bound=AfterSearchInDbChecker)

T_HostModels = TypeVar(
    'T_HostModels',
    BaseFieldsWithSearchInDb,
    DataHostManagement
)


class _MonitoringAndManagementProcessors:

    checker = AfterSearchInDbChecker
    host_model: Type[T_HostModels]

    def __init__(self, src_data: BaseFieldsSearchInDb):
        # self._src_data = src_data
        self._db = HostPropertiesFromDb(src_data)
        self._processed_data_hosts = None

    async def search_hosts_and_processing(self):
        await self._db.search_hosts_and_processing()
        self._processed_data_hosts = {}
        for curr_host_ipv4, current_data_host in self._db.processed_hosts_data.items():
            current_host = self.checker(ip_or_name=curr_host_ipv4, properties=current_data_host)
            if current_host.validate_record():
                record = current_host.properties.db_records[0]
                key_ip = record[TrafficLightsObjectsTableFields.IP_ADDRESS]
                model = self.host_model(
                    **(current_data_host.model_dump() | record)
                )
                self._processed_data_hosts[key_ip] = model
            else:
                self._processed_data_hosts[curr_host_ipv4] = current_data_host

    @property
    def processed_data_hosts(self) -> dict[str, T_HostModels]:
        return self._processed_data_hosts

class MonitoringProcessors(_MonitoringAndManagementProcessors):
    host_model = BaseFieldsWithSearchInDb


class ManagementProcessors(_MonitoringAndManagementProcessors):
    host_model = DataHostManagement




""" Archive """


# class _MonitoringAndManagementProcessors(BaseProcessor):
#
#     checker = AfterSearchInDbChecker
#     host_model: Type[T_HostModels]
#
#     def _process_data_hosts_after_request(self):
#         super()._process_data_hosts_after_request()
#         processed_data_hosts = {}
#         for curr_host_ipv4, current_data_host in self.processed_hosts_data.items():
#             current_host = self.checker(ip_or_name=curr_host_ipv4, properties=current_data_host)
#             if current_host.validate_record():
#                 record = current_host.properties.db_records[0]
#                 key_ip = record[TrafficLightsObjectsTableFields.IP_ADDRESS]
#                 model = self.host_model(
#                     **(current_data_host.model_dump() | record)
#                 )
#                 processed_data_hosts[key_ip] = model
#             else:
#                 processed_data_hosts[curr_host_ipv4] = current_data_host
#         self.hosts_data = processed_data_hosts
#
#
# class MonitoringProcessors(_MonitoringAndManagementProcessors):
#     host_model = DataHostMonitoring
#
#
# class ManagementProcessors(_MonitoringAndManagementProcessors):
#     host_model = DataHostManagement
