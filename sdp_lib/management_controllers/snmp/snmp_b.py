import asyncio
import os
import typing
from collections.abc import KeysView, Callable
from enum import StrEnum, IntEnum
from typing import Self

from pysnmp.hlapi.v3arch.asyncio import *
from pysnmp.proto import errind

from sdp_lib.management_controllers.exceptions import BadControllerType
from sdp_lib.management_controllers.hosts import *
from sdp_lib.management_controllers.fields_names import FieldsNames
from sdp_lib.management_controllers.parsers.snmp_parsers.stcip_parsers import SwarcoStcipMonitoringParser, \
    PotokSMonitoringParser
from sdp_lib.management_controllers.parsers.snmp_parsers.ug405_parsers import ParserPotokP
from sdp_lib.management_controllers.snmp.host_properties import swarco_stcip, potok_p, HostProtocolData, potok_s
# from sdp_lib.management_controllers.parsers.snmp_parsers.parsers_snmp_core import SwarcoStcipBase
from sdp_lib.management_controllers.snmp.oids import Oids
from sdp_lib.management_controllers.snmp.response_checkers import ErrorResponseCheckers
from sdp_lib.management_controllers.snmp.response_structure import ResponseStructure
from sdp_lib.management_controllers.snmp.smmp_utils import build_class_attrs
from sdp_lib.management_controllers.snmp.snmp_requests import SnmpRequests



class SnmpHosts(Host):
    """
    Класс абстрактного хоста, в котором реализована логика формирования snmp-запросов,
    получение и обработка snmp-ответов.
    """

    protocol = FieldsNames.protocol_snmp

    host_properties: HostProtocolData
    type_controller: str
    host_protocol: str
    community_r: str
    community_w: str

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
            self.ip_v4, self.community_r, self.community_w, self._engine
        )
        self.parser = None
        self.last_response = None

    async def make_get_request_and_parse_response(self, oids, parser) -> Self:
        """
        Метод обертка для _common_parse_and_response. В данном методе определяется
        параметр method для передачи и вызова _common_parse_and_response.
        """
        return await self._common_parse_and_response(
            oids=oids,
            method=self.request_sender.snmp_get,
            parser=parser
        )

    async def _common_parse_and_response(self, oids, method, parser):
        """
        Осуществляет вызов соответствующего snmp-запроса и передает
        self.__parse_response_all_types_requests полученный ответ для парса response.
        """
        self.last_response = await method(oids=oids)
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

    scn_required_oids = {
        Oids.utcReplyGn, Oids.utcReplyFR, Oids.utcReplyDF, Oids.utcControlTO,
        Oids.utcControlFn, Oids.potokP_utcReplyPlanStatus, Oids.potokP_utcReplyPlanSource,
        Oids.potokP_utcReplyPlanSource, Oids.potokP_utcReplyDarkStatus,
        Oids.potokP_utcReplyLocalAdaptiv, Oids.potokP_utcReplyHardwareErr,
        Oids.potokP_utcReplySoftwareErr, Oids.potokP_utcReplyElectricalCircuitErr,
        Oids.utcReplyMC, Oids.utcReplyCF, Oids.utcReplyVSn, Oids.utcType2ScootDetectorCount
    }

    def __init__(self, ip_v4: str, engine, host_id=None, scn=None):
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

    def _add_scn_to_oids(self, oids):
        return [f'{oid}{self.scn_as_ascii_string}' if oid in self.scn_required_oids else oid for oid in oids]

    def set_scn_from_response(self):
        raise NotImplementedError()


class AbstractStcipHosts(SnmpHosts):

    get_state_oids_state: tuple[Oids, ...]
    states_parser: Any

    async def get_states(self):
        return await self.make_get_request_and_parse_response(self.get_state_oids_state, self.states_parser)


class PotokP(AbstractUg405Hosts):

    states_parser = ParserPotokP

    type_controller = potok_p.type_controller
    host_protocol = potok_p.host_protocol
    community_r = potok_p.community_r
    community_w = potok_p.community_w

    get_state_oids_state = (
        Oids.utcType2OperationMode,
        Oids.potokP_utcReplyDarkStatus,
        Oids.utcReplyFR,
        Oids.utcReplyGn,
        Oids.potokP_utcReplyPlanStatus,
        Oids.potokP_utcReplyLocalAdaptiv,
        Oids.utcType2ScootDetectorCount,
        Oids.utcReplyDF,
        Oids.utcReplyMC,
    )

    def set_scn_from_response(self) -> None | BadControllerType:
        try:
            self.scn_as_chars = str(self.last_response[ResponseStructure.VAR_BINDS][0][1])
            self.scn_as_ascii_string = self.get_scn_as_ascii_from_scn_as_chars_attr()
        except IndexError:
            raise  BadControllerType()
        return None

    async def get_states(self):
        return await self.make_get_request_and_parse_response(self.get_state_oids_state, self.states_parser)


class SwarcoStcip(AbstractStcipHosts):

    type_controller = swarco_stcip.type_controller
    host_protocol = swarco_stcip.host_protocol
    community_r = swarco_stcip.community_r
    community_w = swarco_stcip.community_w

    get_state_oids_state = (
        Oids.swarcoUTCTrafftechFixedTimeStatus,
        Oids.swarcoUTCTrafftechPlanSource,
        Oids.swarcoUTCStatusEquipment,
        Oids.swarcoUTCTrafftechPhaseStatus,
        Oids.swarcoUTCTrafftechPlanCurrent,
        Oids.swarcoUTCDetectorQty,
        Oids.swarcoSoftIOStatus
    )

    states_parser = SwarcoStcipMonitoringParser

    # async def get_states(self):
    #     return await self.make_get_request_and_parse_response(self.get_state_oids_state, self.states_parser)


class PotokS(AbstractStcipHosts):

    type_controller = potok_s.type_controller
    host_protocol = potok_s.host_protocol
    community_r = potok_s.community_r
    community_w = potok_s.community_w

    get_state_oids_state = (
        Oids.swarcoUTCStatusEquipment,
        Oids.swarcoUTCTrafftechPhaseStatus,
        Oids.swarcoUTCTrafftechPlanCurrent,
        Oids.swarcoUTCStatusMode,
        Oids.swarcoUTCDetectorQty,
    )

    states_parser = PotokSMonitoringParser

    # async def get_states(self):
    #     return await self.make_get_request_and_parse_response(self.get_state_oids_state, self.states_parser)



async def main():

    obj = PotokS(ip_v4='10.179.68.177',engine=SnmpEngine())
    r = await obj.get_states()
    print(obj.response_as_dict)
    print(r.response)
    return obj.response

    pass



if __name__ == '__main__':
    asyncio.run(main())



