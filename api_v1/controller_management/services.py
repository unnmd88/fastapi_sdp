import abc
import time
from asyncio import TaskGroup
from typing import Coroutine, Any, Type, TypeVar
import aiohttp
from pysnmp.entity.engine import SnmpEngine

from api_v1.controller_management.crud import search_hosts_from_db
from api_v1.controller_management.schemas import (
    AllowedControllers,
    AllowedDataHostFields,
    AllowedMonitoringEntity
)
from sdp_lib.management_controllers.fields_names import FieldsNames
from sdp_lib.management_controllers.snmp import stcip, ug405
from sdp_lib.management_controllers.http.peek.monitoring.main_page import MainPage as peek_MainPage
from sdp_lib.management_controllers.http.peek.monitoring.inputs import InputsPage as peek_InputsPage
from sdp_lib.management_controllers.http.peek.monitoring.multiple import MultipleData as peek_MultipleData
from api_v1.controller_management.sorters import sorters


T = TypeVar('T', stcip.SwarcoSTCIP, stcip.PotokS, ug405.PotokP, peek_MainPage)
S = TypeVar('S', sorters.HostSorterMonitoring, sorters.SearchHostsInDb)


class Controllers(metaclass=abc.ABCMeta):

    snmp_engine = SnmpEngine()
    sorter: Type[S]

    def __init__(self, income_data, search_in_db: bool):

        self.income_data = income_data
        self.search_in_db = search_in_db

        self.allowed_to_request_hosts = {}
        self.bad_hosts = []
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
            hosts_from_db = await search_hosts_from_db(self.income_data)
            data_hosts = self.get_sorter_class()(
                income_data=hosts_from_db.good_hosts, bad_hosts=hosts_from_db.bad_hosts
            )
        else:
            data_hosts = self.get_sorter_class()(self.income_data)

        data_hosts.sort()
        self.allowed_to_request_hosts = data_hosts.good_hosts
        self.bad_hosts += data_hosts.bad_hosts

        await self._make_request()
        self.add_response_to_data_hosts()
        return {'Время составило': time.time() - start_time} | self.get_all_hosts_as_dict()

    def get_all_hosts_as_dict(self):
        return self.allowed_to_request_hosts | {'bad_hosts': self.bad_hosts}

    def add_response_to_data_hosts(self):
        for t in self.result_tasks:
            instance = t.result()
            self.allowed_to_request_hosts[t.get_name()][str(FieldsNames.response)] = instance.response_as_dict
            print(f'res: {instance.response}')


class StatesMonitoring(Controllers):

    sorter = sorters.HostSorterMonitoring

    def get_coro(self, ip: str, data_host: dict) -> Coroutine:
        type_controller = data_host[AllowedDataHostFields.type_controller]
        option = data_host.get(AllowedDataHostFields.options)
        match (type_controller, option):
            case (AllowedControllers.SWARCO, None):
                return stcip.SwarcoSTCIP(ip_v4=ip).get_and_parse(engine=self.snmp_engine)
            case (AllowedControllers.POTOK_S, None):
                return stcip.PotokS(ip_v4=ip).get_and_parse(engine=self.snmp_engine)
            case (AllowedControllers.POTOK_P, None):
                scn = data_host.get(AllowedDataHostFields.scn)
                return ug405.PotokP(ip_v4=ip, scn=scn).get_and_parse(engine=self.snmp_engine)
            case(AllowedControllers.PEEK, None):
                return peek_MainPage(ip_v4=ip, session=self._session).get_and_parse()
            case(AllowedControllers.PEEK, AllowedMonitoringEntity.ADVANCED):
                return peek_MultipleData(ip_v4=ip, session=self._session).get_and_parse()
            case(AllowedControllers.PEEK, AllowedMonitoringEntity.INPUTS):
                return peek_MultipleData(ip_v4=ip, session=self._session).get_and_parse(main_page=False)
        raise TypeError('DEBUG')

