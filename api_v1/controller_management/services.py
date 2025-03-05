from asyncio import TaskGroup
from enum import nonmember
from typing import Type, Coroutine

import aiohttp
from mypyc.ir.ops import TypeVar
from pysnmp.entity.engine import SnmpEngine

from api_v1.controller_management.crud import SearchHosts
from api_v1.controller_management.schemas import GetHostsStaticDataFromDb, AllowedControllers, AllowedProtocolsRequest, \
    AllowedDataHostFields, AllowedMonitoringEntity
from api_v1.controller_management.sorters import HostSorterSearchInDB
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

    has_scn_classes = {
        ug405.PotokP, stcip.PotokS, ug405.PotokP
    }

    need_snmp_engine_classes = {
        stcip.SwarcoSTCIP
    }
    need_http_session_classes = {

    }

    def __init__(self, allowed_hosts: dict, bad_hosts: list):
        self.allowed_hosts = allowed_hosts
        self.bad_hosts = bad_hosts


T = TypeVar('T', stcip.SwarcoSTCIP, stcip.PotokS, ug405.PotokP, peek_web.PeekWeb)


class StatesMonitoring(Controllers):

    classes_for_request = {

        (str(AllowedControllers.SWARCO), None): stcip.SwarcoSTCIP,
        (str(AllowedControllers.POTOK_S), None): stcip.PotokS,
        (str(AllowedControllers.POTOK_S), None): ug405.PotokP,
        (str(AllowedControllers.PEEK), None): peek_web.MainPage,

        # (str(AllowedControllers.SWARCO),  None): (stcip.SwarcoSTCIP, AllowedProtocolsRequest.SNMP),
        # (str(AllowedControllers.POTOK_S), None): (stcip.PotokS, AllowedProtocolsRequest.SNMP),
        # (str(AllowedControllers.POTOK_S), None): (ug405.PotokP, AllowedProtocolsRequest.SNMP),
        # (str(AllowedControllers.PEEK),    None): (peek_web.MainPage, AllowedProtocolsRequest.HTTP),

        # (str(AllowedControllers.SWARCO), AllowedMonitoringEntity.ADVANCED):
        #     (stcip.SwarcoSTCIP, AllowedProtocolsRequest.SNMP),

    }

    def _get_task(self, ipv4: str, data_host: dict[str, str]) -> Coroutine:
        type_controller = data_host[AllowedDataHostFields.type_controller]
        option = data_host.get(AllowedDataHostFields.options)
        scn = data_host.get(AllowedDataHostFields.scn)
        a_class, protocol = self.classes_for_request.get((type_controller, option))

        if protocol == AllowedProtocolsRequest.SNMP and a_class in self.has_scn_classes:
             obj = a_class(ipv4=ipv4, scn=scn)
             return obj.get_and_parse(engine=snmp_engine)
        elif protocol == AllowedProtocolsRequest.SNMP:
            return a_class(ipv4=ipv4)



        return matches.get(data_for_match)

    def get_class_and_protocol(self, type_controller: str, **kwargs) -> tuple[Type[T], AllowedProtocolsRequest]:
        option = kwargs.get(AllowedDataHostFields.options)
        return self.classes_for_request.get((type_controller, option))

    async def main(self):
        tasks = []
        print(f'self.allowed_hosts: {self.allowed_hosts}')
        async with aiohttp.ClientSession() as session:
            async with TaskGroup() as tg:
                for ipv4, data_host in self.allowed_hosts.items():
                    a_class, protocol = self.get_class_and_protocol(**data_host)


                    if protocol == AllowedProtocolsRequest.SNMP:
                        tasks.append(tg.create_task(c.get_and_parse(engine=snmp_engine), name=ipv4))
                    else:
                        tasks.append(tg.create_task(c.get_and_parse(session=session), name=ipv4))

        print(tasks)
        for r in tasks:
            print(f'res: {r.result().response}')
















