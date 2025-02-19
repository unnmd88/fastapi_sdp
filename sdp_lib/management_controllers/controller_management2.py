import os

from pysnmp.hlapi.v3arch.asyncio import *

from .snmp_oids import Oids
from sdp_lib.utils_common import check_is_ipv4




class Host:
    """
    Базовый класс для любого хоста.
    """
    def __init__(self, ip_v4: str, host_id=None, scn=None):
        self.ip_v4 = ip_v4
        self.host_id = host_id
        self.scn = scn
        self.query_data = []

    def __repr__(self):
        return (
            f'ip_v4: {self.ip_v4}\n'
            f'host_id: {self.host_id}\n'
            f'scn: {self.scn}'
        )

    def __setattr__(self, key, value):
        if key == 'ip_v4':
            if check_is_ipv4(value):
                self.__dict__[key] = value
            else:
                raise ValueError(f'Значение < self.ipv4 > должно быть валидным ipv4 адресом: {value}')

        elif key == 'scn':
            if value is None or len(value) <= 10:
                self.__dict__[key] = value
            else:
                raise ValueError('Значение < self.scn > не должно превышать 10 символов ')
        else:
            self.__dict__[key] = value


class SnmpRequest(Host):
    """
    Интерфейс отправки snmp запросов.
    """
    snmp_engine = SnmpEngine()

    async def get_request_base(
            self,
            ip_v4: str,
            community: str,
            oids: list[str],
            timeout: float = 0.2,
            retries: int = 0
    ) -> tuple:
        """
        Метод get запросов по snmp
        :param ip_v4:
        :arg ip_adress: ip хоста
        :arg community: коммьюнити хоста
        :arg oids: список oids, которые будут отправлены в get запросе
        :arg timeout: таймаут запроса, в секундах
        :arg retries: количество попыток запроса
        :return: tuple вида:
                 index[0] -> если есть ошибка в snmp запросе, то текст ошибки, иначе None
                 index[1] -> ответные данные. список вида [(oid, payload), (oid, payload)...]
                 index[2] -> self, ссылка на объект

        Examples
        --------
        ip_adress = '192.168.0.1'\n
        community = 'community'\n
        oids = [Oids.swarcoUTCTrafftechPhaseStatus.value,
               Oids.swarcoUTCTrafftechPlanStatus.value]


        asyncio.run(set_request(ip_adress, community, oids))
        ******************************
        """
        error_indication, error_status, error_index, var_binds = await get_cmd(
            self.snmp_engine,
            CommunityData(community),
            await UdpTransportTarget.create((ip_v4, 161), timeout=timeout, retries=retries),
            ContextData(),
            *[ObjectType(ObjectIdentity(oid)) for oid in oids]
        )
        return error_indication, var_binds


class BaseSTCIP(SnmpRequest):
    community_write = os.getenv('communitySTCIP_w')
    community_read = os.getenv('communitySTCIP_r')

    async def get_multiple(self, oids: list[str | Oids]):
        print('я в функции get_multiple')
        res = await self.get_request_base(
            ip_v4=self.ip_v4,
            community=self.community_write,
            oids=oids
        )
        print('я в функции get_multiple перед return')

        return res


class SwarcoSNMP(BaseSTCIP):

    async def get_stage(self):
        res = await self.get_request_base(
            ip_v4=self.ip_v4,
            community=self.community_write,
            oids=[Oids.swarcoUTCTrafftechPhaseStatus]
        )
        return res







