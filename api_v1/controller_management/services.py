import abc
import asyncio
import logging
import time
from typing import Coroutine, Type, TypeVar
from asyncio import TaskGroup
import aiohttp
from pysnmp.entity.engine import SnmpEngine
from typing_extensions import deprecated

# from api_v1.controller_management.crud.crud import (
#     MonitoringProcessors,
#     ManagementProcessors
# )

from api_v1.controller_management.schemas import (
    AllowedControllers,
    AllowedMonitoringEntity,
    AllowedManagementEntity,
    # BaseFields,
    ManagementFields, AllowedManagementSources, MonitoringFields,
)
from api_v1.controller_management.sorters import sorters
from api_v1.controller_management.sorters.sorters_core import (
    HostSorterMonitoring,
    HostSorterManagement
)
# from api_v1.controller_management.sorters.sorters import (
#     HostSorterMonitoring,
#     HostSorterManagement
# )
from core.shared import SWARCO_SSH_CONNECTIONS
from sdp_lib.management_controllers.http.peek import peek_http

import logging_config
from sdp_lib.management_controllers.http.peek.peek_http import DataFromWeb
from sdp_lib.management_controllers import api as cm_api
from sdp_lib.management_controllers.ssh import ssh_core


logger = logging.getLogger(__name__)

T = TypeVar(
    'T',
    # snmp_core.SwarcoStcip,
    # snmp_core.PotokP,
    # snmp_core.PotokS,
    # peek_MainPage
)
S = TypeVar('S', HostSorterMonitoring, HostSorterManagement)
# P = TypeVar('P', MonitoringProcessors, ManagementProcessors)


# class Controllers:
#
#     snmp_engine = cm_api.snmp_engine
#
#     def __init__(
#             self,
#             *,
#             income_data,
#             session: aiohttp.ClientSession = None
#     ):
#         self.income_data = income_data
#         self.hosts = self.income_data.hosts
#         self.result_tasks = None
#         self._session = session
#
#
#     @abc.abstractmethod
#     def get_coro(
#             self, ip_v4: str,
#             data_host: MonitoringFields | ManagementFields
#     ) -> Coroutine:
#         ...
#
#     async def _make_request(self):
#
#         self.result_tasks = []
#         if self._session is None:
#             async with aiohttp.ClientSession() as self._session:
#                 async with TaskGroup() as tg:
#                     for ip_v4, data_host in self.hosts.items():
#                         if data_host.allowed:
#                             self.result_tasks.append(tg.create_task(
#                                 self.get_coro(ip_v4, data_host),
#                                 name=ip_v4
#                             ))
#         else:
#             async with TaskGroup() as tg:
#                 for ip_v4, data_host in self.hosts.items():
#                     if data_host.allowed:
#                         self.result_tasks.append(tg.create_task(
#                             self.get_coro(ip_v4, data_host),
#                             name=ip_v4
#                         ))
#         return self.result_tasks
#
#     async def compose_request(self):
#
#         start_time = time.time()
#
#         await self._make_request()
#         self.add_response_to_data_hosts()
#         self.hosts['Время составило'] = time.time() - start_time
#         return self.income_data.hosts
#
#     def get_all_hosts_as_dict(self):
#         return self.allowed_to_request_hosts | {'bad_hosts': self.bad_hosts}
#
#     def add_response_to_data_hosts(self):
#         for t in self.result_tasks:
#             instance = t.result()
#             self.income_data.hosts[t.get_name()].response = instance.response_as_dict
#             # Заглушка, добавляет в шаренный словарь ssh соединение swarco
#             if isinstance(instance, ssh_core.SwarcoSSH):
#                 SWARCO_SSH_CONNECTIONS[instance.ip_v4] = instance.driver


class Controllers:

    snmp_engine = cm_api.snmp_engine

    def __init__(
            self,
            *,
            income_data,
            session: aiohttp.ClientSession = None
    ):
        self.income_data = income_data
        self.hosts = self.income_data.hosts
        self.result_tasks = None
        self._session = session


    @abc.abstractmethod
    def get_coro(
            self, ip_v4: str,
            data_host: MonitoringFields | ManagementFields
    ) -> Coroutine:
        ...

    # async def _make_request(self):
    #
    #     self.result_tasks = []
    #     if self._session is None:
    #         async with aiohttp.ClientSession() as self._session:
    #             async with TaskGroup() as tg:
    #                 for ip_v4, data_host in self.hosts.items():
    #                     if data_host.allowed:
    #                         self.result_tasks.append(tg.create_task(
    #                             self.get_coro(ip_v4, data_host),
    #                             name=ip_v4
    #                         ))
    #     else:
    #         async with TaskGroup() as tg:
    #             for ip_v4, data_host in self.hosts.items():
    #                 if data_host.allowed:
    #                     self.result_tasks.append(tg.create_task(
    #                         self.get_coro(ip_v4, data_host),
    #                         name=ip_v4
    #                     ))
    #     return self.result_tasks

    async def compose_request(self):

        start_time = time.time()

        pending = []
        if self._session is None:
            async with aiohttp.ClientSession() as self._session:
                for ip_v4, data_host in self.hosts.items():
                    if data_host.allowed:
                        pending.append(asyncio.create_task(
                            self.get_coro(ip_v4, data_host),
                            name=ip_v4
                        ))

        else:

            for ip_v4, data_host in self.hosts.items():
                if data_host.allowed:
                    pending.append(asyncio.create_task(
                        self.get_coro(ip_v4, data_host),
                        name=ip_v4
                    ))

        while pending:
            done, pending = await asyncio.wait(pending, return_when=asyncio.FIRST_COMPLETED)

            for done_task in done:
                await done_task
                instance = done_task.result()
                self.income_data.hosts[done_task.get_name()].response =  instance.response.build_response_as_dict_from_raw_data_responses(instance.ip_v4)
                # self.income_data.hosts[task.get_name()].response = instance.response_as_dict
                # Заглушка, добавляет в шаренный словарь ssh соединение swarco
                if isinstance(instance, ssh_core.SwarcoSSH):
                    SWARCO_SSH_CONNECTIONS[instance.ip_v4] = instance.driver

        # await self._make_request()
        # self.add_response_to_data_hosts()
        self.hosts['Время составило'] = time.time() - start_time
        return self.income_data.hosts

    def get_all_hosts_as_dict(self):
        return self.allowed_to_request_hosts | {'bad_hosts': self.bad_hosts}

    def add_response_to_data_hosts(self):
        for t in self.result_tasks:
            instance = t.result()
            self.income_data.hosts[t.get_name()].response = instance.response_as_dict
            # Заглушка, добавляет в шаренный словарь ssh соединение swarco
            if isinstance(instance, ssh_core.SwarcoSSH):
                SWARCO_SSH_CONNECTIONS[instance.ip_v4] = instance.driver


class StatesMonitoring(Controllers):

    def get_coro(
            self, ip: str,
            data_host
    ) -> Coroutine:
        # print(f'ip > {ip}\ndata_host > {data_host}')
        type_controller = data_host.type_controller
        option = data_host.option
        match (type_controller, option):
            case (AllowedControllers.SWARCO, None):
                # return stcip_monitoring.CurrentStatesSwarco(ip_v4=ip).request_and_parse_response(engine=self.snmp_engine)
                # return snmp_core.SwarcoStcip(ip_v4=ip, engine=self.snmp_engine).get_states()
                return cm_api.SwarcoStcip(ipv4=ip, engine=self.snmp_engine).get_states()
            case (AllowedControllers.POTOK_S, None):
                # return snmp_core.PotokS(ip_v4=ip, engine=self.snmp_engine).get_states()
                return cm_api.PotokS(ipv4=ip, engine=self.snmp_engine).get_states()
            case (AllowedControllers.POTOK_P, None):
                scn = cm_api.PotokP.add_CO_to_scn(data_host.number)
                # scn = ug405_monitoring.MonitoringPotokP.add_CO_to_scn(data_host.number)
                # return ug405_monitoring.MonitoringPotokP(ip_v4=ip, scn=scn).request_and_parse_response(engine=self.snmp_engine)
                # return snmp_core.PotokP(ip_v4=ip, engine=self.snmp_engine, scn=scn).get_states()
                return cm_api.PotokP(ipv4=ip, engine=self.snmp_engine, scn=scn).get_states()
            case(AllowedControllers.PEEK, None):
                # return peek_MainPage(ipv4=ip, session=self._session).get_and_parse()
                return peek_http.PeekWebHosts(ipv4=ip, session=self._session).get_states()
            case(AllowedControllers.PEEK, AllowedMonitoringEntity.ADVANCED):
                # return peek_MultipleData(ipv4=ip, session=self._session).get_and_parse()
                return peek_http.PeekWebHosts(ipv4=ip, session=self._session).fetch_all_pages(
                    DataFromWeb.main_page_get, DataFromWeb.inputs_page_get,
                )
            case(AllowedControllers.PEEK, AllowedMonitoringEntity.INPUTS):
                return peek_http.PeekWebHosts(ipv4=ip, session=self._session).get_inputs()
        raise TypeError('DEBUG')


class Management(Controllers):

    def get_coro(
            self, ip: str,
            data_host: ManagementFields
    ) -> Coroutine:
        type_controller = data_host.type_controller
        source = data_host.source
        option = data_host.option
        command = data_host.command
        value = data_host.value
        print(f'type_controller: {type_controller}\n'
              f'source: {source} | '
              f'option: {option} | '
              f'command: {command} | '
              f'value: {value}')
        match (type_controller, command, source):
            case (AllowedControllers.SWARCO, AllowedManagementEntity.set_stage, None):
                return cm_api.SwarcoStcip(ipv4=ip, engine=self.snmp_engine).set_stage(value)
            case (AllowedControllers.POTOK_S, AllowedManagementEntity.set_stage, AllowedManagementSources.central):
                return cm_api.PotokS(ipv4=ip, engine=self.snmp_engine).set_stage(value)
            case (AllowedControllers.POTOK_P, AllowedManagementEntity.set_stage, AllowedManagementSources.central):
                scn = cm_api.PotokP.add_CO_to_scn(data_host.number)
                return cm_api.PotokP(ipv4=ip, engine=self.snmp_engine).set_stage(value)
            case (AllowedControllers.PEEK, AllowedManagementEntity.set_stage, AllowedManagementSources.man):
                # print('fFF')
                return peek_http.PeekWebHosts(ipv4=ip, session=self._session).set_stage(value)
            case (AllowedControllers.PEEK, AllowedManagementEntity.set_stage, AllowedManagementSources.central):
                # print('fFF')
                return cm_api.PeekUg405(ipv4=ip, engine=self.snmp_engine).set_stage(value)
            case (AllowedControllers.SWARCO, AllowedManagementEntity.set_stage, AllowedManagementSources.man):
                if ip in SWARCO_SSH_CONNECTIONS:
                    print('case (AllowedControllers.SWARCO, Al')
                    driver = SWARCO_SSH_CONNECTIONS.get(ip)
                else:
                    driver = ssh_core.SwarcoItcUserConnectionsSSH(ip)
                    # return SWARCO_SSH_CONNECTIONS[ip].set_stage(value)
                return ssh_core.SwarcoSSH(ip=ip, driver=driver).set_stage(value)

        raise TypeError('DEBUG')








""" Archive """


# class Controllers:
#
#     snmp_engine = snmp_api.snmp_engine
#     sorter: Type[S]
#     processor: Type[P]
#
#     def __init__(
#             self,
#             *,
#             income_data,
#             search_in_db: bool,
#             session: aiohttp.ClientSession = None
#     ):
#
#         self.income_data = income_data
#         self.search_in_db = search_in_db
#         self.allowed_to_request_hosts: dict | None = None
#         self.bad_hosts: list | None = None
#         self.result_tasks = None
#         self._session = session
#
#     @classmethod
#     def _get_sorter_class(cls) -> Type[S]:
#         return cls.sorter
#
#     @classmethod
#     def _get_processor_class(cls) -> Type[P]:
#         return cls.processor
#
#     @abc.abstractmethod
#     def get_coro(self, ip_v4: str, data_host: dict) -> Coroutine:
#         ...
#
#     async def _make_request(self):
#
#         self.result_tasks = []
#         if self._session is None:
#             async with aiohttp.ClientSession() as self._session:
#                 async with TaskGroup() as tg:
#                     for ip_v4, data_host in self.allowed_to_request_hosts.items():
#                         self.result_tasks.append(tg.create_task(
#                             self.get_coro(ip_v4, data_host),
#                             name=ip_v4
#                         ))
#         else:
#             async with TaskGroup() as tg:
#                 for ip_v4, data_host in self.allowed_to_request_hosts.items():
#                     self.result_tasks.append(tg.create_task(
#                         self.get_coro(ip_v4, data_host),
#                         name=ip_v4
#                     ))
#         return self.result_tasks
#
#     async def compose_request(self):
#
#         start_time = time.time()
#         if self.search_in_db:
#             hosts_from_db: P = self._get_processor_class()(self.income_data)
#             await hosts_from_db.search_hosts_and_processing()
#             data_hosts = self._get_sorter_class()(hosts_from_db.processed_data_hosts)
#         else:
#             data_hosts = self._get_sorter_class()(self.income_data.hosts)
#
#         data_hosts.sort()
#
#         self.allowed_to_request_hosts = data_hosts.hosts_without_errors
#         self.bad_hosts = data_hosts.hosts_with_errors
#
#         await self._make_request()
#         self.add_response_to_data_hosts()
#         # for t in self.result_tasks:
#         #     print(f't: {t.result().response_as_dict}')
#         return {'Время составило': time.time() - start_time} | self.get_all_hosts_as_dict()
#
#     def get_all_hosts_as_dict(self):
#         return self.allowed_to_request_hosts | {'bad_hosts': self.bad_hosts}
#
#     def add_response_to_data_hosts(self):
#         for t in self.result_tasks:
#             instance = t.result()
#             self.allowed_to_request_hosts[t.get_name()].response = instance.response_as_dict
#             # Заглушка, добавляет в шаренный словарь ssh соединение swarco
#             if isinstance(instance, ssh_core.SwarcoSSH):
#                 SWARCO_SSH_CONNECTIONS[instance.ip_v4] = instance.driver
#
#
# class StatesMonitoring(Controllers):
#
#     sorter = HostSorterMonitoring
#     processor = MonitoringProcessors
#
#     def get_coro(
#             self, ip: str,
#             data_host: BaseFields
#     ) -> Coroutine:
#         type_controller = data_host.type_controller
#         option = data_host.option
#         match (type_controller, option):
#             case (AllowedControllers.SWARCO, None):
#                 # return stcip_monitoring.CurrentStatesSwarco(ip_v4=ip).request_and_parse_response(engine=self.snmp_engine)
#                 # return snmp_core.SwarcoStcip(ip_v4=ip, engine=self.snmp_engine).get_states()
#                 return snmp_api.SwarcoStcip(ipv4=ip, engine=self.snmp_engine).get_states()
#             case (AllowedControllers.POTOK_S, None):
#                 # return snmp_core.PotokS(ip_v4=ip, engine=self.snmp_engine).get_states()
#                 return snmp_api.PotokS(ipv4=ip, engine=self.snmp_engine).get_states()
#             case (AllowedControllers.POTOK_P, None):
#                 scn = snmp_api.PotokP.add_CO_to_scn(data_host.number)
#                 # scn = ug405_monitoring.MonitoringPotokP.add_CO_to_scn(data_host.number)
#                 # return ug405_monitoring.MonitoringPotokP(ip_v4=ip, scn=scn).request_and_parse_response(engine=self.snmp_engine)
#                 # return snmp_core.PotokP(ip_v4=ip, engine=self.snmp_engine, scn=scn).get_states()
#                 return snmp_api.PotokP(ipv4=ip, engine=self.snmp_engine, scn=scn).get_states()
#             case(AllowedControllers.PEEK, None):
#                 # return peek_MainPage(ipv4=ip, session=self._session).get_and_parse()
#                 return peek_http.PeekWebHosts(ipv4=ip, session=self._session).get_states()
#             case(AllowedControllers.PEEK, AllowedMonitoringEntity.ADVANCED):
#                 # return peek_MultipleData(ipv4=ip, session=self._session).get_and_parse()
#                 return peek_http.PeekWebHosts(ipv4=ip, session=self._session).fetch_all_pages(
#                     DataFromWeb.main_page_get, DataFromWeb.inputs_page_get,
#                 )
#             case(AllowedControllers.PEEK, AllowedMonitoringEntity.INPUTS):
#                 return peek_http.PeekWebHosts(ipv4=ip, session=self._session).get_inputs()
#         raise TypeError('DEBUG')
#
#
# class Management(Controllers):
#
#     sorter = HostSorterManagement
#
#     def get_coro(
#             self, ip: str,
#             data_host: ManagementFields
#     ) -> Coroutine:
#         type_controller = data_host.type_controller
#         source = data_host.source
#         option = data_host.option
#         command = data_host.command
#         value = data_host.value
#         match (type_controller, command, source):
#             case (AllowedControllers.SWARCO, AllowedManagementEntity.set_stage, None):
#                 return snmp_api.SwarcoStcip(ipv4=ip, engine=self.snmp_engine).set_stage(value)
#             case (AllowedControllers.SWARCO, AllowedManagementEntity.set_stage, None):
#                 return snmp_api.PotokS(ipv4=ip, engine=self.snmp_engine).set_stage(value)
#             case (AllowedControllers.SWARCO, AllowedManagementEntity.set_stage, None):
#                 scn = snmp_api.PotokP.add_CO_to_scn(data_host.number)
#                 return snmp_api.PotokP(ipv4=ip, engine=self.snmp_engine).set_stage(value)
#             case (AllowedControllers.PEEK, AllowedManagementEntity.set_stage, None):
#                 # print('fFF')
#                 return peek_http.PeekWebHosts(ipv4=ip, session=self._session).set_stage(value)
#             case (AllowedControllers.PEEK, AllowedManagementEntity.set_stage, AllowedManagementSources.central):
#                 # print('fFF')
#                 return snmp_api.PeekUg405(ipv4=ip, engine=self.snmp_engine).set_stage(value)
#             case (AllowedControllers.SWARCO, AllowedManagementEntity.set_stage, AllowedManagementSources.man):
#                 if ip in SWARCO_SSH_CONNECTIONS:
#                     print('case (AllowedControllers.SWARCO, Al')
#                     driver = SWARCO_SSH_CONNECTIONS.get(ip)
#                 else:
#                     driver = ssh_core.SwarcoItcUserConnectionsSSH(ip)
#                     # return SWARCO_SSH_CONNECTIONS[ip].set_stage(value)
#                 return ssh_core.SwarcoSSH(ip=ip, driver=driver).set_stage(value)
#
#         raise TypeError('DEBUG')