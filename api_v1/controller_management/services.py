import abc
import asyncio
import ipaddress
import json
import logging

from pydantic.json_schema import model_json_schema

import logging_config
from re import search

from pydantic import ValidationError, BaseModel
from sqlalchemy import text, select, or_, and_

from core.models import db_helper, TrafficLightsObjects
from sdp_lib.utils_common import check_ipv4
from .schemas import (
    AllowedControllers,
    AllowedMonitoringEntity, AllowedProtocolsRequest, RequestBase,
    GetCommands, GetCommandsWithSearchInDb, TrafficLightsObjectsTableFields
)

from sdp_lib.management_controllers import controller_management


logger = logging.getLogger(__name__)

logger.debug('TEEEEEEEEEEST LOGGER')


class DatabaseApi:

    def get_stmt_for_request_to_db(self, hosts: dict):
        acc = []
        print(f'self.search_in_db_hosts.items(): {self.search_in_db_hosts}')

        for ip_or_num, data_host in hosts.items():
            acc.append(f"{data_host.search_in_db_field} = '{ip_or_num}' ")
        return " OR ".join(acc)

    async def get_data_from_db(self):
        stmt = self.get_stmt_for_request_to_db()
        print(f'stmt: {stmt}')
        async with db_helper.engine.connect() as conn:
            stmt = (f'SELECT * '
                    f'FROM toolkit_trafficlightsobjects '
                    f'WHERE {stmt}')

            res = await conn.execute(text(stmt))
            print(f'res: {res.mappings().all()}')
            return res


class BaseDataHosts:
    """
    Базовый класс обработки данных и запросов с дорожных контроллеров.
    """

    base_model = RequestBase
    msg_invalid_ip_or_num = 'invalid data for search host in database'
    msg_invalid_ip = 'invalid ip v4 address'
    msg_invalid_host_data = 'invalid host data'

    def __init__(self, income_data: dict):
        self.income_data = income_data
        self.allowed_hosts: dict = {}
        self.bad_hosts: dict = {}
        self.no_search_in_db_hosts: dict = {}
        self.search_in_db_hosts: dict = {}
        self.classes_for_request: list[dict] = []


    def __repr__(self):
        # return (f'self.income_data:\n{json.dumps(self.income_data, indent=2)}\n'
        #         f'self.good_hosts: {json.dumps(self.allowed_hosts, indent=2)}\n'
        #         f'self.search_in_db_hosts: {json.dumps(self.search_in_db_hosts, indent=2)}\n'
        #         f'self.no_search_in_db_hosts: {json.dumps(self.no_search_in_db_hosts, indent=2)}\n'
        #         f'self.bad_hosts: {json.dumps(self.bad_hosts, indent=2)}')
        return (f'self.income_data:\n{self.income_data}\n'
                f'self.good_hosts: {self.allowed_hosts}\n'
                f'self.search_in_db_hosts: {self.search_in_db_hosts}\n'
                f'self.no_search_in_db_hosts: {self.no_search_in_db_hosts}\n'
                f'self.bad_hosts: {self.allowed_hosts}')

    def parse_income_data(self):
        for ip_or_num, data_host in self.income_data.items():
            checked_data_host = self.validate_entity(data_host, self.base_model, err_msg=self.msg_invalid_host_data)
            # logger.debug(base_model)
            if isinstance(checked_data_host, str):
                data_host['errors'] = checked_data_host
                self.bad_hosts |= {ip_or_num: data_host}
                continue

            _data_host = checked_data_host

            if _data_host.search_in_db:
                search_field = self.get_search_field(ip_or_num)
                if search_field is None:
                    data_host['errors'] = self.msg_invalid_ip_or_num
                    self.bad_hosts |= {ip_or_num: data_host}
                    continue
                _data_host.search_in_db_field = search_field
                self.search_in_db_hosts |= {ip_or_num: _data_host}
            else:
                self.no_search_in_db_hosts |= {ip_or_num: _data_host}


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

    # def get_stmt_for_request_to_db(self):
    #     acc = []
    #     print(f'self.search_in_db_hosts.items(): {self.search_in_db_hosts}')
    #
    #     for ip_or_num, data_host in self.search_in_db_hosts.items():
    #         acc.append(f"{data_host.search_in_db_field} = '{ip_or_num}' ")
    #     return " OR ".join(acc)

    def get_stmt_for_request_to_db(self):

        matches = {
            str(TrafficLightsObjectsTableFields.NUMBER): TrafficLightsObjects.number,
            str(TrafficLightsObjectsTableFields.IP_ADDRESS): TrafficLightsObjects.ip_adress,
        }
        stmt = [
            f'{matches.get(obj.search_in_db_field) == ip_or_num}' for ip_or_num, obj in self.search_in_db_hosts.items()
        ]
        logger.debug(stmt)
        return stmt
        # acc = []
        # print(f'self.search_in_db_hosts.items(): {self.search_in_db_hosts}')
        #
        # for ip_or_num, data_host in self.search_in_db_hosts.items():
        #     acc.append(f"{data_host.search_in_db_field} = '{ip_or_num}' ")
        # return " OR ".join(acc)

    async def get_data_from_db(self):

        stmt = self.get_stmt_for_request_to_db()
        print(f'stmt: {stmt}')
        async with db_helper.engine.connect() as conn:
            stmt_ = select(TrafficLightsObjects).where(or_(*stmt))
            res = await conn.execute(stmt_)
            print(f'res: {res.mappings().all()}')
            return res




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