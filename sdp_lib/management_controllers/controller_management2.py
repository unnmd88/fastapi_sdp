

from pysnmp.hlapi.asyncio import *

from .snmp_oids import Oids





class SnmpRequest:
    """
    Интерфейс отправки snmp запросов.
    """

    async def get_request_base(
            self,
            ip_v4: str,
            community: str,
            oids: list[str],
            timeout: float = 0,
            retries: int = 1
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
        error_indication, error_status, error_index, var_binds = await getCmd(
            SnmpEngine(),
            CommunityData(community),
            UdpTransportTarget((ip_v4, 161), timeout=timeout, retries=retries),
            ContextData(),
            *[ObjectType(ObjectIdentity(oid)) for oid in oids]
        )
        return error_indication, var_binds


class SwarcoWebBase:
    pass


class Host:
    """
    Базовый класс для любого хоста.
    """
    def __init__(self, ip_v4: str, host_id=None, scn=None):
        self.ip_v4 = ip_v4
        self.host_id = host_id
        self.scn = scn
        self.query_data = []




