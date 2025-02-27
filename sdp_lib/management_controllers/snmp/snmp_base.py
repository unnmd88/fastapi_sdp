from collections.abc import KeysView
from typing import Any

from pysnmp.hlapi.v3arch.asyncio import *

from sdp_lib.management_controllers.exceptions import BadControllerType
from sdp_lib.management_controllers.hosts import *
from sdp_lib.management_controllers.responce import FieldsNames, ErrorMessages
from sdp_lib.management_controllers.snmp.oids import Oids


snmp_engine = SnmpEngine()

async def snmp_get(
        ipv4: str,
        community: str,
        oids: list[str | Oids] | KeysView[str | Oids],
        engine: SnmpEngine = SnmpEngine(),
        timeout: float = 0.2,
        retries: int = 0
):
    error_indication, error_status, error_index, var_binds = await get_cmd(
        engine,
        CommunityData(community),
        await UdpTransportTarget.create((ipv4, 161), timeout=timeout, retries=retries),
        ContextData(),
        *[ObjectType(ObjectIdentity(oid)) for oid in oids]
    )
    return error_indication, var_binds

async def snmp_get_next(
        ipv4: str,
        community: str,
        oids: list[str | Oids] | KeysView[str | Oids],
        engine: SnmpEngine = SnmpEngine(),
        timeout: float = 0.2,
        retries: int = 0
):
    error_indication, error_status, error_index, var_binds = await next_cmd(
        engine,
        CommunityData(community),
        await UdpTransportTarget.create((ipv4, 161), timeout=timeout, retries=retries),
        ContextData(),
        *[ObjectType(ObjectIdentity(oid)) for oid in oids]
    )
    return error_indication, var_binds


class SnmpHost(Host):

    stage_values_get: dict
    stage_values_set: dict
    matches: dict

    def __init__(self, ip_v4: str, host_id: str = None):
        super().__init__(ip_v4, host_id)
        self.community_r, self.community_w = self.get_community()

    def get_community(self) -> tuple[str, str]:
        raise NotImplemented

    def get_oids_for_get_request(self):
        raise NotImplemented

    def get_current_mode(self, response):
        raise NotImplemented

    def processing_oid_from_response(self, oid: str) -> str:
        raise NotImplemented

    def add_extras_for_response(self, parsed_responce: dict) -> dict:
        raise NotImplemented

    async def get_and_parse(self, engine: SnmpEngine = None):

        error_indication, var_binds = await self.get(
            oids=self.get_oids_for_get_request(),
            engine=engine
        )
        if error_indication is not None or not var_binds:
            return error_indication, var_binds

        #DEBUG
        # for oid, val in var_binds:
        #     print(f'oid, val: {str(oid)} val: {val.prettyPrint()}')
        #     print(f'type val: {type(val)}')
        #     print(f'type val pretty : {type(val.prettyPrint())}')

        parsed_response = self.parse_var_binds_from_response(var_binds)
        if not parsed_response:
            error_indication = BadControllerType()
            return error_indication, parsed_response
        parsed_response = self.add_extras_for_response(parsed_response)
        print(f'ip: {self.ip_v4} | resp: {parsed_response}')
        return error_indication, parsed_response

    async def get(
            self,
            oids: list[str | Oids] | KeysView[str | Oids],
            engine: snmp_engine or SnmpEngine(),
            timeout: float = 0.8,
            retries: int = 0
    ) -> tuple:
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
        error_indication, error_status, error_index, var_binds = await get_cmd(
            engine or SnmpEngine(),
            CommunityData(self.community_r),
            await UdpTransportTarget.create((self.ip_v4, 161), timeout=timeout, retries=retries),
            ContextData(),
            *[ObjectType(ObjectIdentity(oid)) for oid in oids]
        )
        print(f'error_indication{error_indication}\n'
              f'error_status, {error_status}\n'
              f'error_index, {error_index}\n'
              f'var_binds')
        return error_indication, var_binds

    async def set(
            self,
            oids: list[tuple[str | Oids, Any]],
            engine: SnmpEngine = snmp_engine or SnmpEngine(),
            timeout: float = 0.2,
            retries: int = 0
    ):
        error_indication, error_status, error_index, var_binds = await set_cmd(
            engine,
            CommunityData(self.community_w),
            await UdpTransportTarget.create((self.ip_v4, 161), timeout=timeout, retries=retries),
            ContextData(),
            *[ObjectType(ObjectIdentity(oid), val) for oid, val in oids]
        )
        return error_indication, var_binds

    def parse_var_binds_from_response(
            self,
            response: [tuple[ObjectIdentity, OctetString | Gauge32 | Integer | Unsigned32]],
    ) -> dict[str, str]:
        resp = {}
        try:
            for oid, val in response:
                oid, val = self.processing_oid_from_response(str(oid)), val.prettyPrint()
                field_name, fn = self.matches.get(oid)
                resp[str(field_name)] = fn(val)
        except TypeError:
            return {}
        # print(f'ip: {self.ip_v4} | resp: {resp}')
        return resp

    def convert_val_to_num_stage_get_req(self, val: str) -> int | None:
        """
        Конвертирует значение из oid фазы в номер фазы из get заспроа
        :param val: значение, которое будет сконвертировано в десятичный номер фазы.
        :return: номер фазы в десятичном представлении
        """
        return self.stage_values_get.get(val)

    def convert_val_to_num_stage_set_req(self, val: str) -> int | None:
        """
        Конвертирует номер фазы в значение для установки в oid фазы
        :param val: номер фазы, который будет сконвертирован в соответствующее значение
        :return: Значение фазы, которое будет установлено.
        """
        return self.stage_values_set.get(val)

    def get_val_as_str(self, val: str | int) -> str:
        return str(val)