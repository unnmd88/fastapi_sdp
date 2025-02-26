from collections.abc import KeysView
from typing import Any

from pysnmp.hlapi.v3arch.asyncio import *

from sdp_lib.management_controllers.hosts import *
from sdp_lib.management_controllers.responce import FieldsNames
from sdp_lib.management_controllers.snmp.oids import Oids


snmp_engine = SnmpEngine()

async def snmp_get(
        ipv4: str,
        community: str,
        oids: list[str | Oids] | KeysView[str | Oids],
        engine: SnmpEngine = snmp_engine or SnmpEngine(),
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
        engine: SnmpEngine = snmp_engine or SnmpEngine(),
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

    async def get(
            self,
            oids: list[str | Oids] | KeysView[str | Oids],
            engine: SnmpEngine = snmp_engine or SnmpEngine(),
            timeout: float = 0.2,
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
            engine,
            CommunityData(self.community_r),
            await UdpTransportTarget.create((self.ip_v4, 161), timeout=timeout, retries=retries),
            ContextData(),
            *[ObjectType(ObjectIdentity(oid)) for oid in oids]
        )
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

    async def get_and_parse(self):
        error_indication, var_binds = await self.get(
            engine=snmp_engine,
            oids=self.matches.keys()
        )
        if error_indication is not None or not var_binds:
            return error_indication, var_binds
        parsed_response = self.parse_response(
            response=var_binds,
        )
        return error_indication, parsed_response

    def parse_response(
            self,
            response: [tuple[ObjectIdentity, OctetString | Gauge32 | Integer | Unsigned32]],
            include_current_mode=True
    ) -> dict[str, str]:
        resp = {}
        for oid, val in response:
            oid, val = str(oid), str(val)
            field_name, fn = self.matches.get(oid)
            resp[str(field_name)] = fn(val)
        if include_current_mode and resp:
            resp[str(FieldsNames.curr_mode)] = self.get_current_mode(resp)
        print(f'ip: {self.ip_v4} | resp: {resp}')
        return resp

    def get_stage_values(self) -> tuple[dict, dict]:
        raise NotImplemented

    def get_current_mode(self, response):
        raise NotImplemented

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

