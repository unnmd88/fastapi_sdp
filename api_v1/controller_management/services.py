from asyncio import TaskGroup
from typing import Type

import aiohttp
from mypyc.ir.ops import TypeVar
from pysnmp.entity.engine import SnmpEngine

from api_v1.controller_management.crud import SearchHosts
from api_v1.controller_management.schemas import GetHostsStaticDataFromDb, AllowedControllers, AllowedProtocolsRequest, \
    AllowedDataHostFields
from api_v1.controller_management.sorters import HostSorterSearchInDB
from sdp_lib.management_controllers.snmp import stcip, ug405
from sdp_lib.management_controllers.http import peek_web


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
        self.allowed_hosts = allowed_hosts
        self.bad_hosts = bad_hosts


T = TypeVar('T', stcip.SwarcoSTCIP, stcip.PotokS, ug405.PotokP, peek_web.PeekWeb)


class StatesMonitoring(Controllers):
    pass

    def get_class(self, data_for_match: str) -> tuple[Type[T], AllowedControllers]:
        matches = {
            str(AllowedControllers.SWARCO): (stcip.SwarcoSTCIP, AllowedProtocolsRequest.SNMP),
            str(AllowedControllers.POTOK_S): (stcip.PotokS, AllowedProtocolsRequest.SNMP),
            str(AllowedControllers.POTOK_S): (ug405.PotokP, AllowedProtocolsRequest.SNMP),
            str(AllowedControllers.PEEK): (peek_web.MainPage, AllowedProtocolsRequest.HTTP)
        }
        return matches.get(data_for_match)

    async def main(self):
        engine = SnmpEngine()
        tasks = []
        print(self.allowed_hosts)
        async with aiohttp.ClientSession() as session:
            async with TaskGroup() as tg:
                for ipv4, data_host in self.allowed_hosts.items():
                    if data_host.get('errors'):
                        continue
                    a_class, protocol = self.get_class(data_for_match=data_host[AllowedDataHostFields.type_controller])
                    print(f'a_class: {a_class}')
                    print(f'ipv4: {ipv4}')
                    c = a_class(ipv4)
                    if protocol == AllowedProtocolsRequest.SNMP:
                        tasks.append(tg.create_task(c.get_and_parse(engine=engine), name=ipv4))
                    else:
                        tasks.append(tg.create_task(c.get_and_parse(session=session), name=ipv4))
        print(tasks)
        for r in tasks:
            print(f'res: {r.result().response}')
















