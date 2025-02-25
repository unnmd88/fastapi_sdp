from typing import KeysView

from pysnmp.hlapi.v3arch.asyncio import *

from sdp_lib.management_controllers.snmp.oids import Oids


snmp_engine = SnmpEngine()


async def get(
        ip_v4: str,
        community: str,
        oids: list[str],
        engine: SnmpEngine = snmp_engine,
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
        CommunityData(community),
        await UdpTransportTarget.create((ip_v4, 161), timeout=timeout, retries=retries),
        ContextData(),
        *[ObjectType(ObjectIdentity(oid)) for oid in oids]
    )
    return error_indication, var_binds



class SnmpGet:
    """
    Базовый класс отправки snmp запросов.
    """

    async def get(
            self,
            ipv4: str,
            community: str,
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

        # print(f'snmp_engine: < {snmp_engine} >')
        # print(f'snmp_engine: < {snmp_engine.cache} >')

        # snmp_engine = SnmpEngine()
        error_indication, error_status, error_index, var_binds = await get_cmd(
            snmp_engine,
            CommunityData(community),
            await UdpTransportTarget.create((ipv4, 161), timeout=timeout, retries=retries),
            ContextData(),
            *[ObjectType(ObjectIdentity(oid)) for oid in oids]
        )
        return error_indication, var_binds