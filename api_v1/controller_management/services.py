from asyncio import TaskGroup
from typing import Type, Coroutine

import aiohttp
from mypyc.ir.ops import TypeVar
from pysnmp.entity.engine import SnmpEngine

from api_v1.controller_management.crud import SearchHosts
from api_v1.controller_management.schemas import (
    AllowedControllers,
    AllowedProtocolsRequest,
    AllowedDataHostFields,
)

from api_v1.controller_management.sorters._core import HostSorterSearchInDB
from sdp_lib.management_controllers.fields_names import FieldsNames
from sdp_lib.management_controllers.snmp import stcip, ug405
from sdp_lib.management_controllers.http import peek_web


snmp_engine = SnmpEngine()


async def search_hosts_from_db(income_data) -> HostSorterSearchInDB:
    """
    Производит поиск и сортировку хостов после поиска в БД.
    Возвращает экземпляр класса HostSorterSearchInDB, который содержит
    атрибуты с данными о результатах поиска.
    :param income_data: Экземпляр модели pydantic с хостами из views.py.
    :return: Экземпляр модели HostSorterSearchInDB.
    """
    data_hosts = HostSorterSearchInDB(income_data)
    search_entity = data_hosts.get_hosts_data_for_search_in_db()
    db = SearchHosts()

    data_hosts.hosts_after_search = await db.get_hosts_where(db.get_stmt_where(search_entity))
    data_hosts.sorting_hosts_after_search_from_db()
    return data_hosts


class Controllers:

    def __init__(self, allowed_hosts: dict, bad_hosts: list):
        self.allowed_to_request_hosts = allowed_hosts
        self.bad_hosts = bad_hosts
        self.result_tasks = None
        self._session = None


T = TypeVar('T', stcip.SwarcoSTCIP, stcip.PotokS, ug405.PotokP, peek_web.MainPage)


class StatesMonitoring(Controllers):

    def _get_coro(self, ip: str, data_host: dict) -> Coroutine:
        type_controller = data_host[AllowedDataHostFields.type_controller]
        option = data_host.get(AllowedDataHostFields.options)
        match (type_controller, option):
            case (AllowedControllers.SWARCO, None):
                return stcip.SwarcoSTCIP(ip_v4=ip).get_and_parse(engine=snmp_engine)
            case (AllowedControllers.POTOK_S, None):
                return stcip.PotokS(ip_v4=ip).get_and_parse(engine=snmp_engine)
            case (AllowedControllers.POTOK_P, None):
                scn = data_host.get(AllowedDataHostFields.scn)
                return ug405.PotokP(ip_v4=ip, scn=scn).get_and_parse(engine=snmp_engine)
            case(AllowedControllers.PEEK, None):
                return peek_web.MainPage(ip_v4=ip).get_and_parse(session=self._session)
        raise TypeError('DEBUG')

    async def main(self):
        self.result_tasks = []
        print(f'self.allowed_hosts: {self.allowed_to_request_hosts}')
        async with aiohttp.ClientSession() as self._session:
            async with TaskGroup() as tg:
                for ip_v4, data_host in self.allowed_to_request_hosts.items():
                    self.result_tasks.append(tg.create_task(
                        self._get_coro(ip_v4, data_host),
                        name=ip_v4
                    ))
        self._add_response_to_data_host()
        print(self.result_tasks)

        return self.result_tasks

    def _add_response_to_data_host(self):
        for t in self.result_tasks:
            instance = t.result()
            self.allowed_to_request_hosts[t.get_name()][str(FieldsNames.response)] = instance.response_as_dict
            print(f'res: {instance.response}')

    def get_all_hosts_as_dict(self):
        return self.allowed_to_request_hosts | {'bad_hosts': self.bad_hosts}












