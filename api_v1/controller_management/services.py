import abc
from asyncio import TaskGroup
from typing import Coroutine
import aiohttp
from typing import TypeVar
from pysnmp.entity.engine import SnmpEngine

from api_v1.controller_management.schemas import (
    AllowedControllers,
    AllowedDataHostFields, AllowedMonitoringEntity,
)
from sdp_lib.management_controllers.fields_names import FieldsNames
from sdp_lib.management_controllers.snmp import stcip, ug405
from sdp_lib.management_controllers.http.peek import peek_web_monitoring

T = TypeVar('T', stcip.SwarcoSTCIP, stcip.PotokS, ug405.PotokP, peek_web_monitoring.MainPage)


class Controllers(metaclass=abc.ABCMeta):

    snmp_engine = SnmpEngine()

    def __init__(self, allowed_hosts: dict, bad_hosts: list):
        self.allowed_to_request_hosts = allowed_hosts
        self.bad_hosts = bad_hosts
        self.result_tasks = None
        self._session = None

    @abc.abstractmethod
    def get_coro(self, ip_v4: str, data_host: dict) -> Coroutine:
        ...

    async def main(self):
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

    def get_all_hosts_as_dict(self):
        return self.allowed_to_request_hosts | {'bad_hosts': self.bad_hosts}

    def add_response_to_data_hosts(self):
        for t in self.result_tasks:
            instance = t.result()
            self.allowed_to_request_hosts[t.get_name()][str(FieldsNames.response)] = instance.response_as_dict
            print(f'res: {instance.response}')


class StatesMonitoring(Controllers):

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
                return peek_web_monitoring.MainPage(ip_v4=ip, session=self._session).get_and_parse()
            case(AllowedControllers.PEEK, AllowedMonitoringEntity.ADVANCED):
                return peek_web_monitoring.MultipleData(ip_v4=ip, session=self._session).get_and_parse()
            case(AllowedControllers.PEEK, AllowedMonitoringEntity.INPUTS):
                return peek_web_monitoring.MultipleData(ip_v4=ip, session=self._session).get_and_parse(main_page=False)
        raise TypeError('DEBUG')
















