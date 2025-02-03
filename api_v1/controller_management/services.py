import abc
import asyncio
import ipaddress
import json
import logging
import logging_config
from re import search

from pydantic import ValidationError, BaseModel
from sqlalchemy import text

from core.models import db_helper
from sdp_lib.utils_common import check_ipv4
from .schemas import (
    AllowedControllers,
    AllowedMonitoringEntity, AllowedProtocolsRequest, RequestBase, SearchInDb, RequestBaseWithSearchInDb, RequestCommon
)
from sdp_lib.management_controllers import controller_management


logger = logging.getLogger(__name__)

logger.debug('TEEEEEEEEEEST LOGGER')


class DatabaseApi:
    pass

class BaseDataHosts:
    """
    Базовый класс обработки данных и запросов с дорожных контроллеров.
    """

    search_field_in_db_model = SearchInDb
    # search_in_db_model = RequestBaseWithSearchInDb

    def __init__(self, income_data: dict):
        self.income_data = income_data
        self.allowed_hosts = {}
        self.bad_hosts = {}
        self.search_in_db_hosts = {}
        self.classes_for_request = []


    # def __repr__(self):
    #     return (f'self.income_data:\n{json.dumps(self.income_data, indent=4)}\n'
    #             f'self.good_hosts: {json.dumps(self.allowed_hosts, indent=4)}\n'
    #             # f'self.search_in_db_hosts: {json.dumps(self.search_in_db_hosts, indent=4)}\n'
    #             f'self.bad_hosts: {json.dumps(self.bad_hosts, indent=4)}')

    def parse_income_data(self):
        base_model = RequestBase
        for ip_or_num, data_host in self.income_data.items():
            res = self.validate_entity(data_host, base_model)
            logger.debug(res)
            if isinstance(res, str):
                data_host['errors'] = res
                self.bad_hosts |= {ip_or_num: data_host}
                continue
            if res.search_in_db:
                _data_host = data_host | {'ip_or_num': ip_or_num}
                model = self.validate_entity(_data_host, RequestCommon)
                logger.debug('DDDDDDDDEEEEEBUGGGGGGGGGG')
                logger.debug(model)
                if isinstance(model, str):
                    data_host['errors'] = res
                    self.bad_hosts |= {ip_or_num: data_host}
                else:
                    self.search_in_db_hosts |= {ip_or_num: model}
            else:
                if check_ipv4(ip_or_num):
                    self.allowed_hosts |= {ip_or_num: res}
                else:
                    self.bad_hosts |= {ip_or_num: data_host}
                    data_host['errors'] = 'invalid ip v4 address'

    def validate_entity(self, data_host: dict, model):
        try:
            _model = model(**data_host)
            return _model
        except ValidationError:
            return 'invalid host data'

    def get_search_field(self, field: str) -> SearchInDb | str:
        try:
            _model = self.search_field_in_db_model(search_in_db_field=field)
            return _model
        except ValidationError:
            return 'invalid data for search host in database'

    def get_stmt_for_request_to_db(self):
        acc = []
        print(f'self.search_in_db_hosts.items(): {self.search_in_db_hosts}')

        for ip_or_num, data_host in self.search_in_db_hosts.items():
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




    @abc.abstractmethod
    def get_model(self) -> RequestBase:
        ...


class GetStates(BaseDataHosts):
    """
    Класс обрабывает и получает данные состояния дорожных контроллеров
    """

    def get_model(self):
        return RequestCommon

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