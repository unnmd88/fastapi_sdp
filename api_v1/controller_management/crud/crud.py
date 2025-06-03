import logging
import time
from collections.abc import (
    Sequence,
    Iterable,
    Collection,
    Callable
)

from sqlalchemy.ext.asyncio import AsyncSession

from core.models import (
    db_helper,
    TrafficLightsObjects
)
from sqlalchemy import (
    select,
    or_,
    Select
)
from sqlalchemy.engine.row import RowMapping

from api_v1.controller_management.schemas import (
    AllowedDataHostFields,
    BaseSearchTrafficLightsInDb,
    SearchinDbFields,
    ResponseSearchinDb,
    TrafficLightDbRecords,
)
from core.models.intersections import (
    ControllerManagementOptions,
    TrafficLightsTableFields
)
from core.utils import get_field_for_search_in_db
from sdp_lib import logging_config
from sdp_lib.management_controllers.fields_names import FieldsNames

logger = logging.getLogger(__name__)


async def search_hosts_base_properties(query) -> list[RowMapping]:
    """
    Осуществляет запрос поиска в БД.
    :param query: Сущность запроса.
    :return: list с найденными записями RowMapping.
    """
    async with db_helper.engine.connect() as conn:
        result = await conn.execute(query)
        return result.mappings().all()

async def get_controller_management_options(session: AsyncSession):
    columns = (
        ControllerManagementOptions.type_controller,
        ControllerManagementOptions.group,
        ControllerManagementOptions.commands,
        ControllerManagementOptions.max_stage,
        ControllerManagementOptions.options,
        ControllerManagementOptions.sources,
    )

    query = select(*columns)
    res = await session.execute(query)
    # options = res.scalars().all()
    return res.mappings().all()
    # for o in options:
    #     print(f'o: {dict(o)}')


all_traffic_lights_table_columns = (
    TrafficLightsObjects.number,
    TrafficLightsObjects.ip_adress,
    TrafficLightsObjects.type_controller,
    TrafficLightsObjects.address,
    TrafficLightsObjects.description,
    TrafficLightsObjects.time_create,
    TrafficLightsObjects.time_update,
)


class TrafficLights:

    response_model = ResponseSearchinDb
    standard_columns = all_traffic_lights_table_columns[:5]
    all_columns = all_traffic_lights_table_columns

    matches = {
        str(TrafficLightsTableFields.number): TrafficLightsObjects.number,
        str(TrafficLightsTableFields.ip_address): TrafficLightsObjects.ip_adress,
    }

    def __init__(self, src_data: BaseSearchTrafficLightsInDb):
        self._src_data = src_data
        self._src_hosts = src_data.hosts
        self._host_data = self._create_hosts_data()
        self._hosts_after_search: list | None = None
        self.start_time = time.time()

    def _create_hosts_data(self) -> dict[str, SearchinDbFields]:
        return {
            name_or_ipv4: SearchinDbFields(
                ip_or_name_source=name_or_ipv4,
                search_in_db_field=get_field_for_search_in_db(name_or_ipv4),
                db_records=[]
            )
            for name_or_ipv4 in self._src_hosts
        }

    def _get_query(
            self,
            columns: Collection[TrafficLightsObjects] = standard_columns
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
            self.matches.get(data_host.search_in_db_field) == ip_or_name_from_user
            for ip_or_name_from_user, data_host in self._host_data.items()
        )
        return select(*columns).where(or_(*query))

    async def search_hosts_and_processing(self):

        self._hosts_after_search = await search_hosts_base_properties(self._get_query())
        for found_record in self._hosts_after_search:
            self._add_record_to_hosts_data(TrafficLightDbRecords(**found_record))
        return self._host_data

    # def _add_record_to_hosts_data(
    #         self,
    #         found_record: dict[str, Any]
    # ) -> str | None:
    #
    #     host_name, ip = (
    #         found_record[TrafficLightsObjectsTableFields.NUMBER],
    #         found_record[TrafficLightsObjectsTableFields.IP_ADDRESS]
    #     )
    #     if host_name is None and ip is None:
    #         return None
    #
    #     if host_name in self._host_data:
    #         key = host_name
    #     elif found_record[TrafficLightsObjectsTableFields.IP_ADDRESS] in self._host_data:
    #         key = ip
    #     else:
    #         raise ValueError('DEBUG: Значение не найдено. Должно быть найдено')
    #     # self.hosts_data[key][AllowedDataHostFields.db_records].append(found_record)
    #     self._host_data[key].db_records.append(found_record)
    #     return key

    def _add_record_to_hosts_data(
            self,
            found_record: TrafficLightDbRecords
    ) -> str | None:

        if found_record.number is None and found_record.ip_adress is None:
            return None

        if found_record.number in self._host_data:
            key = found_record.number
        elif found_record.ip_adress in self._host_data:
            key = found_record.ip_adress
        else:
            raise ValueError('DEBUG: Значение не найдено. Должно быть найдено')
        self._host_data[key].db_records.append(found_record)
        return key

    @property
    def src_data(self):
        return self._src_data

    @property
    def src_hosts(self):
        return self._src_hosts

    @property
    def host_data(self) -> dict[str, SearchinDbFields]:
        return self._host_data

    @property
    def hosts_after_search(self):
        return self._hosts_after_search

    @hosts_after_search.setter
    def hosts_after_search(self, data):
        self._hosts_after_search = data

    def get_as_dict(self):

        res = {}
        for name, host_model in self._host_data.items():
            try:
                db_data: TrafficLightDbRecords = host_model.db_records[0]
                key = db_data.ip_adress
                type_controller = db_data.type_controller
                number = db_data.number
            except IndexError:
                type_controller = number = None
                key = name

            res[key] = {
                str(TrafficLightsTableFields.type_controller): type_controller,
                str(TrafficLightsTableFields.number): number,
                str(AllowedDataHostFields.database): host_model
            }
        logger.debug(f'This is res: {res}')
        return res

    def get_response_as_pydantic_model(self, **extra_fields):

        try:
            return self.response_model(
                source_data=self._src_data.source_data,
                results=[self._host_data],
                time_execution=time.time() - self.start_time,
                **extra_fields
            )
        except ValueError:
            return self.get_response_as_dict()

    def get_response_as_dict(self):
        return {
            AllowedDataHostFields.source_data: self._src_data,
            AllowedDataHostFields.results: [self._host_data],
        }


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
