import os
from collections.abc import KeysView, Callable
from typing import Self

from pysnmp.hlapi.v3arch.asyncio import *
from pysnmp.proto import errind

from sdp_lib.management_controllers.exceptions import BadControllerType
from sdp_lib.management_controllers.hosts import *
from sdp_lib.management_controllers.fields_names import FieldsNames
from sdp_lib.management_controllers.parsers.snmp_parsers.stcip_parsers import SwarcoStcipParser
# from sdp_lib.management_controllers.parsers.snmp_parsers.parsers_snmp_core import SwarcoStcipBase
from sdp_lib.management_controllers.snmp.oids import Oids


class SnmpHost(Host):

    method: Callable
    oids: tuple[Oids]
    parser_class: Any

    @classmethod
    def get_parser(cls, var_binds, instance):
        return cls.parser_class(var_binds, instance)

    def __init__(self, ip_v4: str, host_id: str = None):
        super().__init__(ip_v4, host_id)
        self.community_r, self.community_w = self.get_community()
        self.parser = None

    def get_community(self) -> tuple[str, str]:
        raise NotImplementedError()

    def get_request_method(self):
        raise NotImplementedError()

    def get_oids(self):
        raise NotImplementedError()

    #Deprecated
    @classmethod
    def get_oids_for_get_state(cls):
        return cls.oids

    @property
    def protocol(self):
        return str(FieldsNames.protocol_snmp)

    async def snmp_get(
            self,
            oids: list[str | Oids] | tuple[str | Oids, ...] | KeysView[str | Oids],
            engine: SnmpEngine,
            timeout: float = 1,
            retries: int = 0
    ) -> tuple[errind.ErrorIndication, Integer32 | int, Integer32 | int, tuple[ObjectType, ...]]:
        """
        Метод get запросов по snmp
        :param ip_v4:
        :param community: коммьюнити хоста
        :param oids: список oids, которые будут отправлены в get запросе
        :param timeout: таймаут запроса, в секундах
        :param retries: количество попыток запроса
        :return: tuple вида:
                 index[0] -> если есть ошибка в snmp запросе, то текст ошибки, иначе None
                 index[1] -> ответные данные. список вида [(oid, payload), (oid, payload)...]
                 index[2] -> self, ссылка на объект

        Examples
        --------
        ip_adress = '192.168.0.1'\n
        community = 'community'\n
        oids = [Oids.swarcoUTCTrafftechPhaseStatus,
               Oids.swarcoUTCTrafftechPlanStatus]


        asyncio.run(set_request(ip_adress, community, oids))
        ******************************
        """
        print(f'oids: {oids}')
        error_indication, error_status, error_index, var_binds = await get_cmd(
            engine or SnmpEngine(),
            CommunityData(self.community_r),
            await UdpTransportTarget.create((self.ip_v4, 161), timeout=timeout, retries=retries),
            ContextData(),
            *[ObjectType(ObjectIdentity(oid)) for oid in oids]
        )
        # print(f'error_indication: {error_indication}\n'
        #       f'error_status: {error_status}\n'
        #       f'error_index: {error_index}\n'
        #       f'var_binds: {var_binds}')
        return error_indication, error_status, error_index, var_binds

        # return self.check_response_and_add_error_if_has(error_indication, error_status, error_index), var_binds

    async def snmp_set(
            self,
            oids: list[tuple[str | Oids, Any]],
            engine: SnmpEngine,
            timeout: float = 1,
            retries: int = 0
    ):
        error_indication, error_status, error_index, var_binds = await set_cmd(
            SnmpEngine() or engine,
            CommunityData(self.community_w),
            await UdpTransportTarget.create((self.ip_v4, 161), timeout=timeout, retries=retries),
            ContextData(),
            *[ObjectType(ObjectIdentity(oid), val) for oid, val in oids]
            # *[ObjectType(ObjectIdentity('1.3.6.1.4.1.1618.3.7.2.11.1.0'), Unsigned32('2')) for oid, val in oids]
        )
        print(error_indication, error_status, error_index, var_binds)
        return error_indication, error_status, error_index, var_binds

    def __check_response_and_add_error_if_has(
            self,
            error_indication: errind.ErrorIndication,
            error_status: Integer32 | int,
            error_index: Integer32 | int
    ) -> bool:
        if error_indication is not None:
            self.add_data_to_data_response_attrs(error_indication)
        elif error_status or error_index:
            self.add_data_to_data_response_attrs(BadControllerType())
        return self.ERRORS

    def __parse_response_all_types_requests(
            self,
            error_indication: errind.ErrorIndication,
            error_status: Integer32 | int,
            error_index: Integer32 | int,
            var_binds: tuple[ObjectType, ...]
    ) -> Self:

        if self.__check_response_and_add_error_if_has(error_indication, error_status, error_index):
            return self

        self.parser = self.get_parser(self, var_binds)
        self.parser.parse()

        if not self.parser.data_for_response:
            self.add_data_to_data_response_attrs(BadControllerType())
            return self

        # self.parser.data_for_response = self.add_extras_for_response(self.parser.data_for_response)
        self.add_data_to_data_response_attrs(data=self.parser.data_for_response)
        return self

    # async def get_and_parse(self, engine: SnmpEngine) -> Self:
    #
    #     response = await self.get(
    #         oids=self.get_oids_for_get_state(),
    #         engine=engine
    #     )
    #     return self.__parse_response_all_types_requests(*response)

    async def request_and_parse_response(self, engine: SnmpEngine) -> Self:

        print(f'method: {self.method.__name__}\noids: {self.get_oids()}')

        response = await self.method(
            oids=self.get_oids(),
            engine=engine
        )
        return self.__parse_response_all_types_requests(*response)

    async def set_and_parse_response(self, engine: SnmpEngine):

        response = await self.snmp_set(
            oids=self.get_oids()
        )
        return self.__parse_response_all_types_requests(*response)


class StcipHost(SnmpHost):

    host_protocol = FieldsNames.protocol_stcip

    def get_community(self) -> tuple[str, str]:
        return os.getenv('communitySTCIP_r'), os.getenv('communitySTCIP_w')


class UG405Host(SnmpHost):

    host_protocol = FieldsNames.protocol_ug405

    scn_required_oids = {
        Oids.utcReplyGn, Oids.utcReplyFR, Oids.utcReplyDF, Oids.utcControlTO,
        Oids.utcControlFn, Oids.potokP_utcReplyPlanStatus, Oids.potokP_utcReplyPlanSource,
        Oids.potokP_utcReplyPlanSource, Oids.potokP_utcReplyDarkStatus,
        Oids.potokP_utcReplyLocalAdaptiv, Oids.potokP_utcReplyHardwareErr,
        Oids.potokP_utcReplySoftwareErr, Oids.potokP_utcReplyElectricalCircuitErr,
        Oids.utcReplyMC, Oids.utcReplyCF, Oids.utcReplyVSn, Oids.utcType2ScootDetectorCount
    }

    def __init__(self, ip_v4: str, host_id=None, scn=None):
        super().__init__(ip_v4, host_id)
        self.scn_as_chars = scn
        self.scn_as_dec = self.get_scn_as_ascii()

    def get_community(self) -> tuple[str, str]:
        return os.getenv('communityUG405_r'), os.getenv('communityUG405_w')

    def get_scn_as_ascii(self) -> str | None:
        if self.scn_as_chars is not None:
            return self.convert_scn(self.scn_as_chars)
        return None

    @staticmethod
    def convert_scn(scn: str) -> str:
        """
        Генерирует SCN
        :param scn -> символы строки, которые необходимо конвертировать в scn
        :return -> возвращет scn
        """
        return f'.1.{str(len(scn))}.{".".join([str(ord(c)) for c in scn])}'

    @staticmethod
    def add_CO_to_scn(scn: str) -> str | None:
        if not isinstance(scn, str) or not scn.isdigit():
            return None
        return f'CO{scn}'

    def add_scn_to_oids(self, oids):
        return [f'{oid}{self.scn_as_dec}' if oid in self.scn_required_oids else oid for oid in oids]

    async def request_and_parse_response(self, engine: SnmpEngine = None):
        print(f'scn_as_chars!!!>> {self.scn_as_chars}')
        print(f'scn_as_dec!!!>> {self.scn_as_dec}')
        if self.scn_as_dec is None:
            error_indication, error_status, error_index, var_binds = await self.snmp_get(
                oids=[Oids.utcReplySiteID],
                engine=engine
            )
            try:
                self.set_scn_from_response(error_indication, error_status, error_index, var_binds)
            except BadControllerType as e:
                self.add_data_to_data_response_attrs(e)
        if self.ERRORS:
            return self


        return await super().request_and_parse_response(engine=engine)

    def set_scn_from_response(
            self,
            error_indication,
            error_status,
            error_index,
            var_binds
    ):
        raise NotImplementedError()