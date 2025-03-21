import time
from typing import Any, TypeVar, Type

from core.models import db_helper, TrafficLightsObjects
from sqlalchemy import select, or_, Select
from sqlalchemy.engine.row import RowMapping

from api_v1.controller_management.checkers.checkers import AfterSearchInDbChecker
from api_v1.controller_management.host_entity import BaseDataHosts
from api_v1.controller_management.schemas import (
    TrafficLightsObjectsTableFields,
    AllowedDataHostFields,
    NumbersOrIpv4,
    SearchinDbHostBody,
    ResponseSearchinDb,
    DataHostMonitoring,
    DataHostManagement
)


class BaseRead:
    """
    Базовый класс поиска в БД.
    """
    async def get_hosts_where(self, stmt) -> list[RowMapping]:
        """
        Осуществляет запрос поиска в БД.
        :param stmt: Сущность запроса.
        :return: list с найденными записями RowMapping.
        """
        async with db_helper.engine.connect() as conn:
            result = await conn.execute(stmt)
            return result.mappings().all()


class ReadHostsByIpOrNum(BaseRead):
    """
    Поиск хостов в БД по определённым полям.
    """

    def __init__(self, all_columns: bool = False):
        self.all_columns = all_columns

    def get_stmt_where(self, hosts_models: dict[str, SearchinDbHostBody]) -> Select[tuple[TrafficLightsObjects]]:
        """
        Формирует сущность запроса поиска записей в БД для каждого хоста из hosts.
        :param hosts_models: Список вида с объектами моделей, в которых содержаться
                              данные для поиска. Например:
                              [BaseSearchHostsInDb(ip_or_name_from_user='10.45.154.16',
                              search_in_db_field='ip_adress'), BaseSearchHostsInDb(ip_or_name_from_user='3245']
        :return: Select[tuple[TrafficLightsObjects]]
        """
        matches = {
            str(TrafficLightsObjectsTableFields.NUMBER): TrafficLightsObjects.number,
            str(TrafficLightsObjectsTableFields.IP_ADDRESS): TrafficLightsObjects.ip_adress,
        }
        # stmt: list = [
        #     matches.get(model.search_in_db_field) == model.ip_or_name_from_user for model in hosts_models
        # ]
        stmt: list = [
            matches.get(data_hots.search_in_db_field) == ip_or_name_from_user
            for ip_or_name_from_user, data_hots in hosts_models.items()
        ]

        if self.all_columns:
            return select(TrafficLightsObjects).where(or_(*stmt))
        return select(*self.get_columns()).where(or_(*stmt))

    def get_columns(self) -> tuple:
        """
        Возвращает список столбцов, данные которых будут являться полями
        найденной записи.
        :return: tuple из столбцов, данные которых будут являться полями
                 найденной записи.
        """
        return (
            TrafficLightsObjects.number,
            TrafficLightsObjects.ip_adress,
            TrafficLightsObjects.type_controller,
            TrafficLightsObjects.address,
            TrafficLightsObjects.description
        )


class BaseProcessor(BaseDataHosts):

    search_in_db_class = ReadHostsByIpOrNum

    def __init__(self, source_data: NumbersOrIpv4):
        super().__init__(source_data)
        self.hosts_after_search: list | None = None
        self.db = self._get_search_in_db_instance()
        self.start_time = time.time()

    @classmethod
    def _get_search_in_db_instance(cls):
        return cls.search_in_db_class()

    def __repr__(self):
        return (
            f'self.income_data: {self.source_data}\n'
            f'self.hosts_after_search: {self.hosts_after_search}\n'
            f'self.hosts: {self.hosts_data}\n'
        )

    def _create_hosts_data(self) -> dict[str, SearchinDbHostBody]:
        return {
            host: SearchinDbHostBody(
                ip_or_name_source=host,
                search_in_db_field=host,
                db_records=[]
            )
            for host in self.source_data.hosts
        }

    def _process_data_hosts_after_request(self):

        for found_record in self.hosts_after_search:
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

        if number in self.hosts_data:
            key = number
        elif found_record[TrafficLightsObjectsTableFields.IP_ADDRESS] in self.hosts_data:
            key = ip
        else:
            raise ValueError('DEBUG: Значение не найдено. Должно быть найдено')
        # self.hosts_data[key][AllowedDataHostFields.db_records].append(found_record)
        self.hosts_data[key].db_records.append(found_record)
        return key

    async def search_hosts_and_processing(self):
        self.hosts_after_search = await self.db.get_hosts_where(
            self.db.get_stmt_where(self.hosts_data)
        )
        self._process_data_hosts_after_request()
        return self.hosts_data


class HostPropertiesProcessors(BaseProcessor):

    @property
    def response_as_model(self):
        try:
            return ResponseSearchinDb(
                source_data=self.source_data,
                results=[self.hosts_data],
                time_execution=time.time() - self.start_time
            )
        except ValueError:
            return self.response_dict

    @property
    def response_dict(self):
        return {
            AllowedDataHostFields.source_data: self.source_data,
            AllowedDataHostFields.results: [self.hosts_data],
        }


# T_Checker = TypeVar('T_Checker', bound=AfterSearchInDbChecker)

T_HostModels = TypeVar(
    'T_HostModels',
    DataHostMonitoring,
    DataHostManagement
)

class _MonitoringAndManagementProcessors(BaseProcessor):

    checker = AfterSearchInDbChecker
    host_model: Type[T_HostModels]

    def _process_data_hosts_after_request(self):
        super()._process_data_hosts_after_request()
        processed_data_hosts = {}
        for curr_host_ipv4, current_data_host in self.hosts_data.items():
            current_host = self.checker(ip_or_name=curr_host_ipv4, properties=current_data_host)
            if current_host.validate_record():
                record = current_host.properties.db_records[0]
                key_ip = record[TrafficLightsObjectsTableFields.IP_ADDRESS]
                model = self.host_model(
                    **(current_data_host.model_dump() | record)
                )
                processed_data_hosts[key_ip] = model
            else:
                processed_data_hosts[curr_host_ipv4] = current_data_host
        self.hosts_data = processed_data_hosts


class MonitoringProcessors(_MonitoringAndManagementProcessors):
    host_model = DataHostMonitoring


class ManagementProcessors(_MonitoringAndManagementProcessors):
    host_model = DataHostManagement
