from typing import KeysView

from pysnmp.hlapi.v3arch.asyncio import *
from pysnmp.proto import errind

from sdp_lib.management_controllers.snmp.oids import Oids



class SnmpRequests:

    def __init__(self, ip, community_r, community_w, engine):
        self.ip = ip
        self.community_r = community_r
        self.community_w = community_w
        self.engine = engine

    async def snmp_get(
            self,
            oids: list[str | Oids] | tuple[str | Oids, ...] | KeysView[str | Oids],
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
            self.engine,
            CommunityData(self.community_r),
            await UdpTransportTarget.create((self.ip, 161), timeout=timeout, retries=retries),
            ContextData(),
            *[ObjectType(ObjectIdentity(oid)) for oid in oids]
        )
        # print(f'error_indication: {error_indication}\n'
        #       f'error_status: {error_status}\n'
        #       f'error_index: {error_index}\n'
        #       f'var_binds: {var_binds}')
        return error_indication, error_status, error_index, var_binds

        # return self.check_response_and_add_error_if_has(error_indication, error_status, error_index), var_binds