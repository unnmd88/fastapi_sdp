from api_v1.controller_management.crud.processing import AfterRead, ForMonitoringAndManagement
from api_v1.controller_management.schemas import TrafficLightsObjectsTableFields, NumbersOrIpv4, AllowedDataHostFields, \
    SearchinDbHostBody
# from api_v1.controller_management.sorters import logger
from core.models import db_helper, TrafficLightsObjects
from sqlalchemy import select, or_, Select
from sqlalchemy.engine.row import RowMapping


# async def search_hosts_from_db(income_data: NumbersOrIpv4) -> HostSorterSearchInDB:
#     """
#     Производит поиск и сортировку хостов после поиска в БД.
#     Возвращает экземпляр класса HostSorterSearchInDB, который содержит
#     атрибуты с данными о результатах поиска.
#     :param income_data: Экземпляр модели pydantic с хостами из views.py.
#     :return: Экземпляр модели HostSorterSearchInDB.
#     """
#     print(f'income_data!!! ++ {income_data}')
#     data_hosts = HostSorterSearchInDB(income_data)
#     search_entity = data_hosts.get_hosts_data_for_search_in_db()
#     db = SearchHosts()
#
#     data_hosts.hosts_after_search = await db.get_hosts_where(db.get_stmt_where(search_entity))
#     # return data_hosts.hosts_after_search
#
#     data_hosts.sorting_hosts_after_search_from_db()
#     return data_hosts


async def search_hosts_from_db(source_hosts_data: NumbersOrIpv4) -> AfterRead:
    """
    Производит поиск и сортировку хостов после поиска в БД.
    Возвращает экземпляр класса HostSorterSearchInDB, который содержит
    атрибуты с данными о результатах поиска.
    :param source_hosts_data: Экземпляр модели pydantic с хостами из views.py.
    :return: Экземпляр модели HostSorterSearchInDB.
    """
    print(f'income_data!!! ++ {source_hosts_data}')
    data_hosts = AfterRead(source_hosts_data)
    db = ReadHostsByIpOrNum()

    data_hosts.hosts_after_search = await db.get_hosts_where(db.get_stmt_where(data_hosts.hosts_data))
    print(f'daT: {data_hosts.hosts_after_search}')
    data_hosts.process_data_hosts_after_request()
    return data_hosts


async def search_hosts_from_db_for_monitoring_and_management(source_hosts_data: NumbersOrIpv4) -> ForMonitoringAndManagement:
    """
    Производит поиск и сортировку хостов после поиска в БД.
    Возвращает экземпляр класса HostSorterSearchInDB, который содержит
    атрибуты с данными о результатах поиска.
    :param source_hosts_data: Экземпляр модели pydantic с хостами из views.py.
    :return: Экземпляр модели HostSorterSearchInDB.
    """
    print(f'income_data!!! ++ {source_hosts_data}')
    data_hosts = ForMonitoringAndManagement(source_hosts_data)
    db = ReadHostsByIpOrNum()

    data_hosts.hosts_after_search = await db.get_hosts_where(db.get_stmt_where(data_hosts.hosts_data))
    print(f'daT: {data_hosts.hosts_after_search}')
    data_hosts.process_data_hosts_after_request()
    return data_hosts


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
            TrafficLightsObjects.number, TrafficLightsObjects.ip_adress, TrafficLightsObjects.type_controller,
            TrafficLightsObjects.address, TrafficLightsObjects.description
        )



