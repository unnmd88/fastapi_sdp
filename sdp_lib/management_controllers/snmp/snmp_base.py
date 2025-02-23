import abc
from collections.abc import KeysView
from typing import Callable

from pysnmp.hlapi.v3arch.asyncio import *

from sdp_lib.management_controllers.hosts import *
from sdp_lib.management_controllers.snmp.oids import Oids
from sdp_lib.management_controllers.responce import FieldsNames
from sdp_lib.management_controllers.controller_modes import NamesMode


snmp_engine = SnmpEngine()


async def get_request_base(
        ip_v4: str,
        community: str,
        oids: list[str],
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
        snmp_engine,
        CommunityData(community),
        await UdpTransportTarget.create((ip_v4, 161), timeout=timeout, retries=retries),
        ContextData(),
        *[ObjectType(ObjectIdentity(oid)) for oid in oids]
    )
    return error_indication, var_binds


class BaseSnmp(SnmpHost):
    """
    Базовый класс отправки snmp запросов.
    """

    async def get_request(
            self,
            oids: list[str | Oids] | KeysView[str | Oids],
            timeout: float = 0.2,
            retries: int = 0
    ) -> tuple:
        """
        Метод get запросов по протоколу snmp.
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
            snmp_engine,
            CommunityData(self.community_r),
            await UdpTransportTarget.create((self.ip_v4, 161), timeout=timeout, retries=retries),
            ContextData(),
            *[ObjectType(ObjectIdentity(oid)) for oid in oids]
        )
        return error_indication, var_binds


class SnmpAllProtocols(BaseSnmp):
    """
    Интерфейс отправки snmp запросов для протоколов STCIP, UG405, UTMC.
    Предназначен для обобщения атрибутов подклассов.
    Не предназначен для создания экземпляров напрямую.
    """

    stage_values_get: dict
    stage_values_set: dict
    parse_response: Callable

    async def get_request_and_parse_response(
            self,
            oids: list[str | Oids] | KeysView[str | Oids],
            timeout: float = 0.2,
            retries: int = 0
    ) -> tuple:

        error_indication, var_binds = await self.get_request(
            oids=oids,
            timeout=timeout,
            retries=retries
        )
        return error_indication, self.parse_response(var_binds)

    def get_plan(self, value: str) -> str:
        return value

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