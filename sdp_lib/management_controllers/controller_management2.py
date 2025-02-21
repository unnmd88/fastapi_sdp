from collections.abc import KeysView
import os
from typing import Generator

from pysnmp.hlapi.v3arch.asyncio import *

from .snmp_oids import Oids
from .responce import FieldsNames
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

    status_equipment = {
        '0': 'noInformation',
        '1': str(FieldsNames.three_light),
        '2': str(FieldsNames.power_up),
        '3': str(FieldsNames.dark),
        '4': str(FieldsNames.flash),
        '6': str(FieldsNames.all_red),
    }

    def convert_val_to_num_stage_get_req(self, val: str) -> int | None:
        """
        Конвертирует значение из oid фазы в номер фазы из get заспроа
        :param val: значение, которое будет сконвертировано в десятичный номер фазы.
        :return: номер фазы в десятичном представлении
        """

        values = {'2': 1, '3': 2, '4': 3, '5': 4, '6': 5, '7': 6, '8': 7, '1': 8, '0': 0}
        return values.get(val)

    def convert_val_to_num_stage_set_req(self, val: str) -> int | None:
        """
        Конвертирует номер фазы в значение для установки в oid фазы
        :param val: номер фазы, который будет сконвертирован в соответствующее значение
        :return: Значение фазы, которое будет установлено.
        """

        values = {'1': 2, '2': 3, '3': 4, '4': 5, '5': 6, '6': 7, '7': 8, '8': 1, 'ЛОКАЛ': 0, '0': 0}
        return values.get(val)

    def get_status(self, value: str) -> str:
        return self.status_equipment.get(value)

    def get_plan(self, value: str) -> str:
        return value

    def get_num_det(self, value: str) -> str:
        return value

    def get_soft_flags_status(self, octet_string: str, start: int = 180, stop: int = 182, ) -> str:
        return octet_string[start: stop]

    def get_oid_val(self, var_binds: tuple[ObjectType]):
        return [x.prettyPrint() for x in var_binds]

    async def get_stage(self):
        error_indication, var_binds = await self.get_request(
            oids=[Oids.swarcoUTCTrafftechPhaseStatus]
        )
        if error_indication is None:
            # print(f'ip: {self.ip_v4}\nstage: {var_binds[0][1]}')
            print(f'ip: {self.ip_v4}\nstage: {self.convert_val_to_num_stage_get_req(str(var_binds[0][1]))}')
            return self.convert_val_to_num_stage_get_req(var_binds)
        return error_indication

        # return error_indication, [(str(x[0]), str(x[1])) for x in var_binds]

    def parse_raw_data_for_basic_current_state(self, raw_data: tuple):
        # print(f'raw_data:: {raw_data}')
        # print(f'len(raw_data):: {len(raw_data)}')
        # print(f'raw_data[0]:: {raw_data[0]}')
        print([(x[0].prettyPrint(), x[1].prettyPrint()) for x in raw_data])
        print([(str(x[0]), str(x[1])) for x in raw_data])

        for varBind in raw_data:
            # print(f'varBind:: {varBind}')
            # print(f'type(varBind):: {type(varBind)}')

            print(" <><> ".join([x.prettyPrint() for x in varBind]))
            print([x.prettyPrint() for x in varBind])


class SwarcoSnmpCurrentStates(SwarcoSnmp):

    state_base: dict = {
        Oids.swarcoUTCStatusEquipment: (FieldsNames.curr_status, SwarcoSnmp.get_status),
        Oids.swarcoUTCTrafftechPhaseStatus: (FieldsNames.curr_stage, SwarcoSnmp.convert_val_to_num_stage_get_req),
        Oids.swarcoUTCTrafftechPlanCurrent: (FieldsNames.curr_plan, SwarcoSnmp.get_plan),
        Oids.swarcoUTCDetectorQty: (FieldsNames.num_detectors, SwarcoSnmp.get_num_det),
        Oids.swarcoSoftIOStatus: (FieldsNames.status_soft_flag180_181, SwarcoSnmp.get_soft_flags_status)
    }

    def parse_response(self, response: Generator) -> dict[str, str]:
        resp = {}
        for oid, val in response:
            field_name, fn = SwarcoSnmpCurrentStates.state_base.get(oid)
            resp[str(field_name)] = fn(self, val)
        print(f'resp: {resp}')
        return resp

    async def get_data_for_basic_current_state(self):
        error_indication, var_binds = await self.get_request(
            oids=SwarcoSnmpCurrentStates.state_base.keys()
        )

        return error_indication, self.parse_response(((str(x[0]), str(x[1])) for x in var_binds))


