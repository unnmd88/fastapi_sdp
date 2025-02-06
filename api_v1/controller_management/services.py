import abc
import asyncio
import ipaddress
import json
import logging

from pydantic.json_schema import model_json_schema

import logging_config
from re import search

from pydantic import ValidationError, BaseModel
from sqlalchemy import text, select, or_, and_, BooleanClauseList, Select

from core.models import db_helper, TrafficLightsObjects
# from sdp_lib.management_controllers.tests import host_id
from sdp_lib.utils_common import check_ipv4
from .schemas import (
    AllowedControllers,
    AllowedMonitoringEntity, AllowedProtocolsRequest, RequestBase,
    GetCommands, GetCommandsWithSearchInDb, TrafficLightsObjectsTableFields, DataHostFields
)

from sdp_lib.management_controllers import controller_management


logger = logging.getLogger(__name__)

logger.debug('TEEEEEEEEEEST LOGGER')


class BaseRequestsToDb:

    async def get_hosts_where(self, stmt):
        async with db_helper.engine.connect() as conn:
            result =  await conn.execute(stmt)
            return result.mappings().all()


class SearchHosts(BaseRequestsToDb):

    def get_stmt_where(self, hosts: dict) -> Select[tuple[TrafficLightsObjects]]:

        matches = {
            str(TrafficLightsObjectsTableFields.NUMBER): TrafficLightsObjects.number,
            str(TrafficLightsObjectsTableFields.IP_ADDRESS): TrafficLightsObjects.ip_adress,
        }
        stmt: list = [
            matches.get(obj.search_in_db_field) == ip_or_num for ip_or_num, obj in hosts.items()
        ]
        logger.debug(select(TrafficLightsObjects).where(or_(*stmt)))
        return select(TrafficLightsObjects).where(or_(*stmt))


class BaseDataHosts:
    """
    Базовый класс обработки данных и запросов с дорожных контроллеров.
    """

    base_model = RequestBase
    field_errors = 'errors'
    msg_invalid_ip_or_num = 'invalid data for search host in database'
    msg_invalid_ip = 'invalid ip v4 address'
    msg_invalid_host_data = 'invalid host data'
    msg_not_found_in_database = 'not found in database'

    def __init__(self, income_data: dict):
        self.income_data = income_data
        self.allowed_hosts: dict = {}
        self.bad_hosts: dict = {}
        self.no_search_in_db_hosts: dict = {}
        self.search_in_db_hosts: dict = {}
        self.hosts_after_search_in_db = None
        self.classes_for_request: list[dict] = []


    def __repr__(self):
        # return (f'self.income_data:\n{json.dumps(self.income_data, indent=2)}\n'
        #         f'self.good_hosts: {json.dumps(self.allowed_hosts, indent=2)}\n'
        #         f'self.search_in_db_hosts: {json.dumps(self.search_in_db_hosts, indent=2)}\n'
        #         f'self.no_search_in_db_hosts: {json.dumps(self.no_search_in_db_hosts, indent=2)}\n'
        #         f'self.bad_hosts: {json.dumps(self.bad_hosts, indent=2)}')
        return (f'self.income_data:\n{self.income_data}\n'
                f'self.allowed_hosts: {self.allowed_hosts}\n'
                f'self.search_in_db_hosts: {self.search_in_db_hosts}\n'
                f'self.no_search_in_db_hosts: {self.no_search_in_db_hosts}\n'
                f'self.hosts_after_search_in_db: {self.hosts_after_search_in_db}\n'
                f'self.bad_hosts: {self.bad_hosts}')

    def sorting_income_data(self):
        for ip_or_num, data_host in self.income_data.items():
            data_host[DataHostFields.ERRORS] = []
            checked_data_host = self.validate_entity(data_host, self.base_model, err_msg=self.msg_invalid_host_data)
            # logger.debug(base_model)
            if isinstance(checked_data_host, str):
                self.put_bad_host(ip_or_num, data_host, checked_data_host)
                continue

            _data_host = checked_data_host
            if _data_host.search_in_db:
                search_field = self.get_search_field(ip_or_num)
                if search_field is None:
                    self.put_bad_host(ip_or_num, data_host, self.msg_invalid_ip_or_num)
                    continue
                _data_host.search_in_db_field = search_field
                self.search_in_db_hosts |= {ip_or_num: _data_host}
            else:
                self.no_search_in_db_hosts |= {ip_or_num: _data_host}

    def put_bad_host(self, ip_or_num: str, data_host: dict, message: str) -> None:
        data_host[DataHostFields.ERRORS].append(message)
        self.bad_hosts |= {ip_or_num: data_host}

    def get_search_field(self, ip_or_num: str) -> str | None:
        """
        Определяет по какому полю будет произваодится поиск хоста в бд
        :param ip_or_num:
        :return:
        """
        if not ip_or_num or len(ip_or_num) > 20:
            return None
        if check_ipv4(ip_or_num):
            return str(TrafficLightsObjectsTableFields.IP_ADDRESS)
        return str(TrafficLightsObjectsTableFields.NUMBER)

    def validate_entity(self, data_host: dict, model, err_msg: str = None) -> BaseModel | str:
        try:
            _model = model(**data_host)
            return _model
        except ValidationError:
            return err_msg

    def sorting_hosts_after_get_grom_db(self):

        stack = self.search_in_db_hosts
        for found_host in self.hosts_after_search_in_db:
            number = found_host.get(str(TrafficLightsObjectsTableFields.NUMBER))
            ip_v4 = found_host.get(str(TrafficLightsObjectsTableFields.IP_ADDRESS))
            if number and number in stack:
                key = number
            elif ip_v4 and ip_v4 in stack:
                key = ip_v4
            else:
                continue
            curr_host = stack.pop(key)
            curr_host.search_result = found_host
            curr_host.host_id = number
            self.allowed_hosts |= {ip_v4: curr_host}

        for ip_or_num, data in stack.items():
            self.put_bad_host(ip_or_num, data.model_dump(), self.msg_not_found_in_database)

    @abc.abstractmethod
    def get_model(self, search_in_db: bool):
        ...


class GetStates(BaseDataHosts):
    """
    Класс обрабывает и получает данные состояния дорожных контроллеров
    """

    def get_model(self, search_in_db: bool) -> GetCommands | GetCommandsWithSearchInDb:

        return GetCommandsWithSearchInDb if search_in_db else GetCommands

    def get_class(self, data: dict):
        data = GetStateByIpv4(**data)
        matches = {
            (AllowedControllers.SWARCO,
             AllowedMonitoringEntity.GET_STATE,
             AllowedProtocolsRequest.SNMP
             ): controller_management.SwarcoSTCIP,

            # (AllowedControllers.PEEK.value, 'get_state'):
            #     controller_management.PeekGetModeWeb,
            # (AvailableControllers.PEEK.value, 'get_states'):
            #     controller_management.GetDifferentStatesFromWeb,
            # (AvailableControllers.POTOK_P.value, 'get_state'):
            #     controller_management.PotokP,
            # (AvailableControllers.POTOK_S.value, 'get_state'):
            #     controller_management.PotokS,
        }
        return matches.get(
            (data.type_controller, data.entity, data.type_request)
        )

    async def main(self):
        objs = []
        for ip, data_host in self.allowed_hosts.items():
            a_class = self.get_class(data_host)
            if a_class is None:
                data_host['errors'] = 'Некорректные данные хоста'
                self.bad_hosts |= {ip: data_host}
                continue
            objs.append(
                a_class(ip, data_host.get('scn'))
            )

        async with asyncio.TaskGroup() as tg:
            res = [tg.create_task(obj.get_request(get_mode=True), name=obj.ip_adress) for obj in objs]
            print(f'res: {res}')