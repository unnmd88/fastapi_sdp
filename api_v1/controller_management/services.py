import abc
import logging
import time
from typing import Coroutine, Type, TypeVar
from asyncio import TaskGroup
import aiohttp
from pysnmp.entity.engine import SnmpEngine

from api_v1.controller_management.crud.crud import (
    MonitoringProcessors,
    ManagementProcessors
)

from api_v1.controller_management.schemas import (
    AllowedControllers,
    AllowedMonitoringEntity,
    AllowedManagementEntity,
    HostBodyMonitoringMixin,
    HostBodyManagementMixin,
)
from api_v1.controller_management.sorters import sorters
from api_v1.controller_management.sorters.sorters import (
    HostSorterMonitoring,
    HostSorterManagement
)

# from sdp_lib.management_controllers.snmp import snmp_api, snmp_core
from sdp_lib.management_controllers.http.peek.monitoring.main_page import MainPage as peek_MainPage
from sdp_lib.management_controllers.http.peek.monitoring.multiple import MultipleData as peek_MultipleData
from sdp_lib.management_controllers.http.peek.management.set_inputs import SetStage as peek_SetStage

import logging_config
from sdp_lib.management_controllers.snmp import snmp_core, snmp_api

logger = logging.getLogger(__name__)

T = TypeVar(
    'T',
    # snmp_core.SwarcoStcip,
    # snmp_core.PotokP,
    # snmp_core.PotokS,
    # peek_MainPage
)
S = TypeVar('S', HostSorterMonitoring, HostSorterManagement)
P = TypeVar('P', MonitoringProcessors, ManagementProcessors)


class Controllers(metaclass=abc.ABCMeta):

    snmp_engine = SnmpEngine()
    sorter: Type[S]
    processor: Type[P]

    def __init__(
            self,
            *,
            income_data,
            search_in_db: bool
    ):

        self.income_data = income_data
        self.search_in_db = search_in_db
        self.allowed_to_request_hosts: dict | None = None
        self.bad_hosts: list | None = None
        self.result_tasks = None
        self._session = None

    @classmethod
    def _get_sorter_class(cls) -> Type[S]:
        return cls.sorter

    @classmethod
    def _get_processor_class(cls) -> Type[P]:
        return cls.processor

    @abc.abstractmethod
    def get_coro(self, ip_v4: str, data_host: dict) -> Coroutine:
        ...

    async def _make_request(self):

        self.result_tasks = []
        async with aiohttp.ClientSession() as self._session:
            async with TaskGroup() as tg:
                for ip_v4, data_host in self.allowed_to_request_hosts.items():
                    self.result_tasks.append(tg.create_task(
                        self.get_coro(ip_v4, data_host),
                        name=ip_v4
                    ))
        return self.result_tasks

    # async def compose_request(self):
    #
    #     start_time = time.time()
    #     if self.search_in_db:
    #         hosts_from_db = await search_hosts_from_db_for_monitoring_and_management(self.income_data)
    #         data_hosts = self.get_sorter_class()(
    #             hosts_from_db.hosts_data
    #         )
    #     else:
    #         data_hosts = self.get_sorter_class()(self.income_data.hosts)
    #
    #     data_hosts.sort()
    #
    #     self.allowed_to_request_hosts = data_hosts.hosts_without_errors
    #     self.bad_hosts = data_hosts.hosts_with_errors
    #
    #     await self._make_request()
    #     self.add_response_to_data_hosts()
    #     for t in self.result_tasks:
    #         print(f't: {t.result().response_as_dict}')
    #     return {'Время составило': time.time() - start_time} | self.get_all_hosts_as_dict()

    async def compose_request(self):

        start_time = time.time()
        if self.search_in_db:
            hosts_from_db: P = self._get_processor_class()(self.income_data)
            await hosts_from_db.search_hosts_and_processing()
            data_hosts = self._get_sorter_class()(hosts_from_db.hosts_data)
        else:
            data_hosts = self._get_sorter_class()(self.income_data.hosts)

        data_hosts.sort()

        self.allowed_to_request_hosts = data_hosts.hosts_without_errors
        self.bad_hosts = data_hosts.hosts_with_errors

        await self._make_request()
        self.add_response_to_data_hosts()
        for t in self.result_tasks:
            print(f't: {t.result().response_as_dict}')
        return {'Время составило': time.time() - start_time} | self.get_all_hosts_as_dict()

    def get_all_hosts_as_dict(self):
        return self.allowed_to_request_hosts | {'bad_hosts': self.bad_hosts}

    def add_response_to_data_hosts(self):
        for t in self.result_tasks:
            instance = t.result()
            self.allowed_to_request_hosts[t.get_name()].response = instance.response_as_dict


class StatesMonitoring(Controllers):

    sorter = sorters.HostSorterMonitoring
    processor = MonitoringProcessors


    def get_coro(
            self, ip: str,
            data_host: HostBodyMonitoringMixin
    ) -> Coroutine:
        type_controller = data_host.type_controller
        option = data_host.option
        match (type_controller, option):
            case (AllowedControllers.SWARCO, None):
                # return stcip_monitoring.CurrentStatesSwarco(ip_v4=ip).request_and_parse_response(engine=self.snmp_engine)
                # return snmp_core.SwarcoStcip(ip_v4=ip, engine=self.snmp_engine).get_states()
                return snmp_api.SwarcoStcip(ip_v4=ip, engine=self.snmp_engine).get_states()
            case (AllowedControllers.POTOK_S, None):
                # return snmp_core.PotokS(ip_v4=ip, engine=self.snmp_engine).get_states()
                return snmp_api.PotokS(ip_v4=ip, engine=self.snmp_engine).get_states()
            case (AllowedControllers.POTOK_P, None):
                scn = snmp_core.PotokP.add_CO_to_scn(data_host.number)
                # scn = ug405_monitoring.MonitoringPotokP.add_CO_to_scn(data_host.number)
                # return ug405_monitoring.MonitoringPotokP(ip_v4=ip, scn=scn).request_and_parse_response(engine=self.snmp_engine)
                # return snmp_core.PotokP(ip_v4=ip, engine=self.snmp_engine, scn=scn).get_states()
                return snmp_api.PotokP(ip_v4=ip, engine=self.snmp_engine, scn=scn).get_states()
            case(AllowedControllers.PEEK, None):
                return peek_MainPage(ip_v4=ip, session=self._session).get_and_parse()
            case(AllowedControllers.PEEK, AllowedMonitoringEntity.ADVANCED):
                return peek_MultipleData(ip_v4=ip, session=self._session).get_and_parse()
            case(AllowedControllers.PEEK, AllowedMonitoringEntity.INPUTS):
                return peek_MultipleData(ip_v4=ip, session=self._session).get_and_parse(main_page=False)
        raise TypeError('DEBUG')


class Management(Controllers):

    sorter = sorters.HostSorterManagement

    def get_coro(
            self, ip: str,
            data_host: HostBodyManagementMixin
    ) -> Coroutine:
        type_controller = data_host.type_controller
        option = data_host.option
        command = data_host.command
        value = data_host.value
        match (type_controller, command):
            case (AllowedControllers.SWARCO, None):
                return stcip.SwarcoSTCIP(ip_v4=ip).request_and_parse_response(engine=self.snmp_engine)
            case (AllowedControllers.POTOK_S, None):
                return stcip.PotokS(ip_v4=ip).request_and_parse_response(engine=self.snmp_engine)
            case (AllowedControllers.POTOK_P, None):
                scn = data_host.number
                # return ug405.PotokP(ip_v4=ip, scn=scn).request_and_parse_response(engine=self.snmp_engine)
                pass
            case(AllowedControllers.PEEK, AllowedManagementEntity.SET_STAGE):
                return peek_SetStage(ip_v4=ip, session=self._session).set_entity(value)
            case(AllowedControllers.PEEK, AllowedMonitoringEntity.ADVANCED):
                return peek_MultipleData(ip_v4=ip, session=self._session).get_and_parse()
            case(AllowedControllers.PEEK, AllowedMonitoringEntity.INPUTS):
                return peek_MultipleData(ip_v4=ip, session=self._session).get_and_parse(main_page=False)
        raise TypeError('DEBUG')