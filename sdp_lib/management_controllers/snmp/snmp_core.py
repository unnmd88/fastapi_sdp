from typing import Self, TypeVar
import asyncio
from collections.abc import KeysView, Callable

from pysnmp.hlapi.v3arch.asyncio import *

from sdp_lib.management_controllers.exceptions import BadControllerType
from sdp_lib.management_controllers.hosts import *
from sdp_lib.management_controllers.fields_names import FieldsNames
from sdp_lib.management_controllers.parsers.snmp_parsers.stcip_parsers import (
    SwarcoStcipMonitoringParser,
    PotokSMonitoringParser
)
from sdp_lib.management_controllers.snmp.host_data import HostStaticData
from sdp_lib.management_controllers.snmp import host_data
from sdp_lib.management_controllers.snmp.oids import Oids
from sdp_lib.management_controllers.snmp.response_checkers import ErrorResponseCheckers
from sdp_lib.management_controllers.snmp.snmp_requests import SnmpRequests


T_DataHosts = TypeVar('T_DataHosts', bound=HostStaticData)


class SnmpHosts(Host):
    """
    Класс абстрактного хоста, в котором реализована логика формирования snmp-запросов,
    получение и обработка snmp-ответов.
    """

    protocol = FieldsNames.protocol_snmp
    host_properties: T_DataHosts

    def __init__(
            self,
            ip_v4: str,
            *,
            engine: SnmpEngine = None,
            host_id: str = None
    ):
        super().__init__(ip_v4, host_id)
        self._engine = engine or SnmpEngine()
        self.request_sender = SnmpRequests(
            self.ip_v4, self.host_properties.community_r, self.host_properties.community_w, self._engine
        )
        self.parser = None
        self.last_response = None

    async def make_get_request_and_parse_response(
            self,
            oids: tuple[Oids, ...] | list[Oids],
            parser
    ) -> Self:
        """
        Метод обертка для _common_parse_and_response. В данном методе определяется
        параметр method для передачи и вызова _common_parse_and_response.
        """
        return await self._common_parse_and_response(
            oids=oids,
            method=self.request_sender.snmp_get,
            parser=parser
        )

    async def _common_parse_and_response(
            self,
            oids: tuple[Oids, ...] | list[Oids],
            method: Callable,
            parser
    ):
        """
        Осуществляет вызов соответствующего snmp-запроса и передает
        self.__parse_response_all_types_requests полученный ответ для парса response.
        """
        self.last_response = await method(oids=oids)
        print(f'self.last_response: {self.last_response}')
        return self.__parse_response_all_types_requests(parser)

    def __parse_response_all_types_requests(self, parser) -> Self:
        """
        Осуществляет проверку snmp-response и передает его парсеру для формирования
        response из полученных значений оидов.
        """
        if ErrorResponseCheckers(self).check_response_errors_and_add_to_host_data_if_has():
            return self

        self.parser = parser(self) # Think about refactoring
        self.parser.parse()

        if not self.parser.data_for_response:
            self.add_data_to_data_response_attrs(BadControllerType())
            return self

        self.add_data_to_data_response_attrs(data=self.parser.data_for_response)
        return self


class AbstractUg405Hosts(SnmpHosts):

    host_data: host_data.HostStaticDataWithScn

    def __init__(
            self,
            ip_v4: str,
            *,
            engine=None,
            host_id=None,
            scn=None
    ):
        super().__init__(ip_v4, engine=engine, host_id=host_id)
        self.scn_as_chars = scn
        self.scn_as_ascii_string = self.get_scn_as_ascii_from_scn_as_chars_attr()

    async def _common_parse_and_response(self, oids, method, parser):

        if self.scn_as_ascii_string is None:
            self.last_response = await self.request_sender.snmp_get(oids=[Oids.utcReplySiteID])

            if ErrorResponseCheckers(self).check_response_errors_and_add_to_host_data_if_has():
                return self
            try:
                self.set_scn_from_response()
            except BadControllerType as e:
                self.add_data_to_data_response_attrs(e)
        if self.ERRORS:
            return self

        return await super()._common_parse_and_response(
            oids=self._add_scn_to_oids(oids=oids),
            method=method,
            parser=parser
        )

    def get_scn_as_ascii_from_scn_as_chars_attr(self) -> str | None:
        if self.scn_as_chars is not None:
            return self.convert_chars_string_to_ascii_string(self.scn_as_chars)
        return None

    @staticmethod
    def add_CO_to_scn(scn: str) -> str | None:
        if not isinstance(scn, str) or not scn.isdigit():
            return None
        return f'CO{scn}'

    @staticmethod
    def convert_chars_string_to_ascii_string(scn: str) -> str:
        """
        Генерирует SCN
        :param scn -> символы строки, которые необходимо конвертировать в scn
        :return -> возвращет scn
        """
        return f'.1.{str(len(scn))}.{".".join([str(ord(c)) for c in scn])}'

    def _add_scn_to_oids(
            self,
            oids: tuple[Oids, ...] | list[Oids]
    ) -> list[Oids]:
        return [
            f'{oid}{self.scn_as_ascii_string}' if oid in self.host_properties.oids_scn_required else oid
            for oid in oids
        ]

    def set_scn_from_response(self):
        raise NotImplementedError()


class AbstractStcipHosts(SnmpHosts):

    host_data: host_data.HostStaticData
    states_parser: Any

    async def get_states(self):
        return await self.make_get_request_and_parse_response(
            self.host_properties.oids_get_state, self.states_parser
        )










