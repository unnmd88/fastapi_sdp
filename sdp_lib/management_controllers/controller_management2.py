import abc
import os

from pysnmp.hlapi.v3arch.asyncio import *

from .snmp_oids import Oids
from sdp_lib.utils_common import check_is_ipv4




class Host:
    """
    Базовый класс для любого хоста.
    """
    def __init__(self, ip_v4: str, host_id=None):
        self.ip_v4 = ip_v4
        self.host_id = host_id
        # self.scn = scn
        # self.query_data = []

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


class SnmpHost(Host):
    def __init__(self, ip_v4: str, host_id: str = None, scn: str = None):
        Host.__init__(self, ip_v4, host_id)
        self.scn = scn
        self.community_r, self.community_w = self.get_community()

    def get_community(self) -> tuple[str, str]:
        ...


class SnmpRequest(SnmpHost):
    """
    Интерфейс отправки snmp запросов.
    """
    snmp_engine = SnmpEngine()

    @classmethod
    async def get_request_base(
            cls,
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
            cls.snmp_engine,
            CommunityData(community),
            await UdpTransportTarget.create((ip_v4, 161), timeout=timeout, retries=retries),
            ContextData(),
            *[ObjectType(ObjectIdentity(oid)) for oid in oids]
        )
        return error_indication, var_binds

    async def get_request(
            self,
            oids: list[str | Oids],
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
            SnmpRequest.snmp_engine,
            CommunityData(self.community_r),
            await UdpTransportTarget.create((self.ip_v4, 161), timeout=timeout, retries=retries),
            ContextData(),
            *[ObjectType(ObjectIdentity(oid)) for oid in oids]
        )
        return error_indication, var_binds


class BaseSTCIP(SnmpRequest):

    def get_community(self) -> tuple[str, str]:
        return os.getenv('communitySTCIP_r'), os.getenv('communitySTCIP_w')

    async def get_multiple(self, oids: list[str | Oids]):
        print('я в функции get_multiple')
        res = await self.get_request(oids=oids)
        print('я в функции get_multiple перед return')
        return res


class SwarcoSnmp(BaseSTCIP):

    oids_get_state_base = [
        Oids.swarcoUTCStatusEquipment,
        Oids.swarcoUTCTrafftechPhaseStatus,
        Oids.swarcoUTCTrafftechPlanCurrent,
        Oids.swarcoUTCDetectorQty,
        Oids.swarcoSoftIOStatus
    ]

    @staticmethod
    def convert_val_to_num_stage_get_req(val: str) -> int | None:
        """
        Конвертирует значение из oid фазы в номер фазы из get заспроа
        :param val: значение, которое будет сконвертировано в десятичный номер фазы.
        :return: номер фазы в десятичном представлении
        """

        values = {'2': 1, '3': 2, '4': 3, '5': 4, '6': 5, '7': 6, '8': 7, '1': 8, '0': 0}
        return values.get(val)

    @staticmethod
    def convert_val_to_num_stage_set_req(val: str) -> int | None:
        """
        Конвертирует номер фазы в значение для установки в oid фазы
        :param val: номер фазы, который будет сконвертирован в соответствующее значение
        :return: Значение фазы, которое будет установлено.
        """

        values = {'1': 2, '2': 3, '3': 4, '4': 5, '5': 6, '6': 7, '7': 8, '8': 1, 'ЛОКАЛ': 0, '0': 0}
        return values.get(val)

    async def get_stage(self):
        error_indication, var_binds = await self.get_request(
            oids=[Oids.swarcoUTCTrafftechPhaseStatus]
        )
        if error_indication is None:
            # print(f'ip: {self.ip_v4}\nstage: {var_binds[0][1]}')
            print(f'ip: {self.ip_v4}\nstage: {self.convert_val_to_num_stage_get_req(str(var_binds[0][1]))}')
            return self.convert_val_to_num_stage_get_req(var_binds)
        return error_indication

    async def get_data_for_basic_current_state(self):
        error_indication, var_binds = await self.get_request(
            oids=SwarcoSnmp.oids_get_state_base
        )

        self.parse_raw_data_for_basic_current_state(var_binds)
        return error_indication, var_binds

    def parse_raw_data_for_basic_current_state(self, raw_data: tuple[ObjectType]):
        for varBind in raw_data:
            print(" = ".join([x.prettyPrint() for x in varBind]))

class SwarcoSnmpCurrentStates(SwarcoSnmp):
    pass





