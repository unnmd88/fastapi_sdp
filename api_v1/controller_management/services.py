import abc
import time
from typing import Coroutine, Type, TypeVar
from asyncio import TaskGroup
import aiohttp
from pysnmp.entity.engine import SnmpEngine

from api_v1.controller_management.crud.crud import (
    search_hosts_from_db,
    search_hosts_from_db_for_monitoring_and_management
)
from api_v1.controller_management.schemas import (
    AllowedControllers,
    AllowedMonitoringEntity,
    SearchinDbHostBodyForMonitoring
)
from api_v1.controller_management.sorters import sorters

from sdp_lib.management_controllers.snmp import stcip, ug405
from sdp_lib.management_controllers.http.peek.monitoring.main_page import MainPage as peek_MainPage
from sdp_lib.management_controllers.http.peek.monitoring.multiple import MultipleData as peek_MultipleData


T = TypeVar('T', stcip.SwarcoSTCIP, stcip.PotokS, ug405.PotokP, peek_MainPage)
# S = TypeVar('S', sorters.HostSorterMonitoring, sorters.SearchHostsInDb)
S = TypeVar('S')
# P = TypeVar('P', NumbersOrIpv4, FastRequestMonitoringAndManagement)
P = TypeVar('P')


class Controllers(metaclass=abc.ABCMeta):

    snmp_engine = SnmpEngine()
    sorter: Type[S]

    def __init__(
            self, *,
            income_data: P,
            search_in_db: bool
    ):

        self.income_data = income_data
        self.search_in_db = search_in_db
        self.allowed_to_request_hosts: dict | None = None
        self.bad_hosts: list | None = None
        self.result_tasks = None
        self._session = None

    @classmethod
    def get_sorter_class(cls):
        return cls.sorter

    @abc.abstractmethod
    def get_coro(self, ip_v4: str, data_host: dict) -> Coroutine:
        ...

    async def _make_request(self):

        self.result_tasks = []
        print(f'self.allowed_hosts: {self.allowed_to_request_hosts}')
        async with aiohttp.ClientSession() as self._session:
            async with TaskGroup() as tg:
                for ip_v4, data_host in self.allowed_to_request_hosts.items():
                    self.result_tasks.append(tg.create_task(
                        self.get_coro(ip_v4, data_host),
                        name=ip_v4
                    ))
        return self.result_tasks

    async def compose_request(self):

        start_time = time.time()
        if self.search_in_db:
            hosts_from_db = await search_hosts_from_db_for_monitoring_and_management(self.income_data)
            data_hosts = self.get_sorter_class()(
                hosts_from_db.hosts_data
            )
        else:
            data_hosts = self.get_sorter_class()(self.income_data.hosts)

        data_hosts.sort()

        self.allowed_to_request_hosts = data_hosts.hosts_without_errors
        self.bad_hosts = data_hosts.hosts_with_errors

        await self._make_request()
        self.add_response_to_data_hosts()
        return {'Время составило': time.time() - start_time} | self.get_all_hosts_as_dict()

    def get_all_hosts_as_dict(self):
        return self.allowed_to_request_hosts | {'bad_hosts': self.bad_hosts}

    def add_response_to_data_hosts(self):
        for t in self.result_tasks:
            instance = t.result()
            self.allowed_to_request_hosts[t.get_name()].response = instance.response_as_dict


class StatesMonitoring(Controllers):

    sorter = sorters.HostSorterMonitoring

    def get_coro(
            self, ip: str,
            data_host: dict | SearchinDbHostBodyForMonitoring
    ) -> Coroutine:
        type_controller = data_host.type_controller
        option = data_host.option
        match (type_controller, option):
            case (AllowedControllers.SWARCO, None):
                return stcip.SwarcoSTCIP(ip_v4=ip).get_and_parse(engine=self.snmp_engine)
            case (AllowedControllers.POTOK_S, None):
                return stcip.PotokS(ip_v4=ip).get_and_parse(engine=self.snmp_engine)
            case (AllowedControllers.POTOK_P, None):
                scn = data_host.number
                return ug405.PotokP(ip_v4=ip, scn=scn).get_and_parse(engine=self.snmp_engine)
            case(AllowedControllers.PEEK, None):
                return peek_MainPage(ip_v4=ip, session=self._session).get_and_parse()
            case(AllowedControllers.PEEK, AllowedMonitoringEntity.ADVANCED):
                return peek_MultipleData(ip_v4=ip, session=self._session).get_and_parse()
            case(AllowedControllers.PEEK, AllowedMonitoringEntity.INPUTS):
                return peek_MultipleData(ip_v4=ip, session=self._session).get_and_parse(main_page=False)
        raise TypeError('DEBUG')