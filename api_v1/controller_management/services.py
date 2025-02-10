import abc
import asyncio
import ipaddress
import json
import logging
from copy import deepcopy
from enum import StrEnum
from typing import Type

from pydantic.json_schema import model_json_schema

import logging_config
from re import search

from pydantic import ValidationError, BaseModel
from sqlalchemy import text, select, or_, and_, BooleanClauseList, Select

from core.models import db_helper, TrafficLightsObjects
# from sdp_lib.management_controllers.tests import host_id
from sdp_lib.utils_common import check_is_ipv4
from .schemas import (
    AllowedControllers,
    AllowedMonitoringEntity, AllowedProtocolsRequest,
    TrafficLightsObjectsTableFields, DataHostFields, Monitoring, HostsStaticData, ModelFromDb, HostProperties
)

from sdp_lib.management_controllers import controller_management


logger = logging.getLogger(__name__)

logger.debug('TEEEEEEEEEEST LOGGER')


class Messages(StrEnum):
    invalid_ip_or_num = 'invalid data for search host in database'
    invalid_ip = 'invalid ip v4 address'
    invalid_host_data = 'invalid host data'
    not_found_in_database = 'not found in database'


class BaseSearch:

    async def get_hosts_where(self, stmt):
        async with db_helper.engine.connect() as conn:
            result =  await conn.execute(stmt)
            return result.mappings().all()


class SearchHosts(BaseSearch):
    """
    Поиск хостов в БД по определённым полям.
    """

    def get_stmt_where(self, hosts: dict) -> Select[tuple[TrafficLightsObjects]]:
        """
        Формирует сущность запроса поиска записей в БД для каждого хоста из hosts.
        :param hosts: Словарь вида {"10.45.154.16": ..., "3216": ...}
        :return: Select[tuple[TrafficLightsObjects]]
        """
        matches = {
            str(TrafficLightsObjectsTableFields.NUMBER): TrafficLightsObjects.number,
            str(TrafficLightsObjectsTableFields.IP_ADDRESS): TrafficLightsObjects.ip_adress,
        }
        stmt: list = [
            matches.get(obj.search_in_db_field) == ip_or_num for ip_or_num, obj in hosts.items()
        ]
        # logger.debug(select(TrafficLightsObjects).where(or_(*stmt)))
        return select(TrafficLightsObjects).where(or_(*stmt))


class BaseDataHostsSorter:
    """
    Базовый класс обработки данных и запросов с дорожных контроллеров.
    """

    field_errors = 'errors'
    # msg_invalid_ip_or_num = 'invalid data for search host in database'
    # msg_invalid_ip = 'invalid ip v4 address'
    # msg_invalid_host_data = 'invalid host data'
    # msg_not_found_in_database = 'not found in database'

    def __init__(self, income_data: dict):
        self.income_data = income_data
        self.model = None
        self.allowed_hosts: dict = {}
        self.bad_hosts: dict = {}
        self.no_search_in_db_hosts: dict = {}
        self.search_in_db_hosts: dict = {}
        self.hosts_after_search_in_db = Monitoring
        self.classes_for_request: list[dict] = []

    def __repr__(self):
        # return (f'self.income_data:\n{json.dumps(self.income_data, indent=2)}\n'
        #         f'self.good_hosts: {json.dumps(self.allowed_hosts, indent=2)}\n'
        #         f'self.search_in_db_hosts: {json.dumps(self.search_in_db_hosts, indent=2)}\n'
        #         f'self.no_search_in_db_hosts: {json.dumps(self.no_search_in_db_hosts, indent=2)}\n'
        #         f'self.bad_hosts: {json.dumps(self.bad_hosts, indent=2)}')

        return (f'self.income_data:\n{self.income_data}\n'   
                f'self.search_in_db_hosts: {self.search_in_db_hosts}\n'
                # f'self.no_search_in_db_hosts: {self.no_search_in_db_hosts}\n'
                f'self.hosts_after_search_in_db: {self.hosts_after_search_in_db}\n'
                f'self.bad_hosts: {self.bad_hosts}\n'
                f'self.allowed_hosts: {self.allowed_hosts}\n')



    def sorting_income_data(self):
        for ip_or_num, data_host in self.income_data.items():
            # self.model = self.get_model()
            data_host[str(DataHostFields.ERRORS)] = []
            data_host_pydantic_model = self.get_model_host_data(data_host)
            if data_host_pydantic_model is None:
                self.add_bad_host(ip_or_num, data_host, message=str(Messages.invalid_host_data))
                continue
            self.sorting_search_in_db_or_not(ip_or_num, data_host_pydantic_model)

    def get_model_host_data(self, data_host: dict | str) -> BaseModel | None:
        try:
            return self.model(**data_host)
        except ValidationError:
            return None

    def sorting_search_in_db_or_not(self, ip_or_num: str, data_host_pydantic_model):
        """
        Сортирует данные хоста. Если поле "search_in_db" = True, тогда проверят валидность
        данных для поиска в бд в методе self.validate_data_for_search_in_db().
        Если "search_in_db" = False, тогда проверят валидность ip v4.
        :param ip_or_num: ip v4 или номер(наименование) хоста.
        :param data_host_pydantic_model: экземпляр модели pydantic, определённый методом self.get_model().
        :return: None
        """
        if data_host_pydantic_model.search_in_db:
            self.validate_data_for_search_in_db(ip_or_num, data_host_pydantic_model)
        else:
            self.validate_ipv4(ip_or_num, data_host_pydantic_model)

    def validate_data_for_search_in_db(self, ip_or_num: str, data_host_pydantic_model) -> bool:
        """
        Проверяет валидность номера(наименования хоста)/ip v4 для поиска в БД.
        Если данные валидны, добавляет данные в self.search_in_db_hosts.
        Если номер(наименование хоста)/ip v4 не валидно, вызывает self.add_bad_host(...)
        :param ip_or_num: ip v4 или номер(наименование хоста из поля 'number' модели TrafficLightsObjects)
        :param data_host_pydantic_model: экземпляр модели pydantic, определённый методом self.get_model().
        :return: True, если данные валидны, иначе False
        """
        search_field = self.get_search_field(ip_or_num)
        if search_field is None:
            self.add_bad_host(ip_or_num, data_host_pydantic_model.model_dump(), Messages.invalid_ip_or_num)
            return False
        data_host_pydantic_model.search_in_db_field = search_field
        self.search_in_db_hosts |= {ip_or_num: data_host_pydantic_model}
        return True

    def validate_ipv4(self, ip_v4: str, data_host_pydantic_model):
        """
        Проверяет валидность ip v4. Если ip валидный, добавляет хост в self.allowed_hosts,
        иначе вызывает self.add_bad_host(...)
        :param ip_v4: ip v4.
        :param data_host_pydantic_model: экземпляр модели pydantic, определённый методом self.get_model().
        :return: True, если ip v4 валидный, иначе False.
        """
        ipv4_is_valid = check_is_ipv4(ip_v4)
        if not ipv4_is_valid:
            self.add_bad_host(ip_v4, data_host_pydantic_model.model_dump(), Messages.invalid_ip)
        self.allowed_hosts |= {ip_v4: data_host_pydantic_model}

    def add_bad_host(self, ip_or_num: str, data_host: dict, message: str) -> None:
        """
        Добавляет хост в "контейнер" с хостами, в данных которых содержатся ошибки.
        :param ip_or_num: Ip v4/номер(наименование) хоста.
        :param data_host: Данные хоста.
        :param message: Сообщение, которое будет добавлено в поле data_host["errors"].
        :return: None
        """
        data_host[str(DataHostFields.ERRORS)].append(message)
        self.bad_hosts |= {ip_or_num: data_host}

    def get_search_field(self, ip_or_num: str) -> str | None:
        """
        Определяет по какому полю будет производиться поиск хоста в БД.
        :param ip_or_num: Ip v4/номер(наименование) хоста.
        :return: None, если ip_or_num невалидно, иначе строку с названием поля
                 для поиска в модели TrafficLightsObjects.
        """
        if not ip_or_num or len(ip_or_num) > 20:
            return None
        if check_is_ipv4(ip_or_num):
            return str(TrafficLightsObjectsTableFields.IP_ADDRESS)
        return str(TrafficLightsObjectsTableFields.NUMBER)

    def sorting_hosts_after_get_grom_db(self):

        stack = deepcopy(self.search_in_db_hosts)
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
            self.add_bad_host(ip_or_num, data.model_dump(), Messages.not_found_in_database)

    @abc.abstractmethod
    def get_model(self):
        ...


class GetHostsStaticData(BaseDataHostsSorter):



    def set_model(self):
        self.model = HostProperties

    def sorting_income_data(self):
        self.set_model()
        print(f'self.income_data!! {self.income_data}')

        for host in self.income_data:
            data_host_pydantic_model = self.get_model_host_data(host)
            self.allowed_hosts |= {host: data_host_pydantic_model}
            logger.debug(f'data_host_pydantic_model!! {data_host_pydantic_model}')
        logger.debug(f'self.allowed_hosts!! {self.allowed_hosts}')

    def get_model_host_data(self, data_host: str) -> BaseModel | None:
        try:
            return self.model(ipv4=data_host, name_or_number=data_host)
        except ValidationError:
            return None

    def create_responce(self):
        all_hosts = {} | self.bad_hosts
        for ipv4, data in self.allowed_hosts.items():
            data.search_result = ModelFromDb(**data.search_result)
            all_hosts |= {ipv4: data}
        return all_hosts


class GetStates(BaseDataHostsSorter):
    """
    Класс обрабывает и получает данные состояния дорожных контроллеров
    """

    def get_model(self) -> Type[Monitoring]:

        return Monitoring

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


