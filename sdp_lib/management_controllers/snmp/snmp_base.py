from collections.abc import KeysView
from typing import Callable

from pysnmp.hlapi.v3arch.asyncio import *

from sdp_lib.management_controllers.hosts import *
from sdp_lib.management_controllers.responce import FieldsNames
from sdp_lib.management_controllers.snmp.oids import Oids
from sdp_lib.management_controllers.snmp.request import get


class SnmpApi(SnmpHost):
    """
    Интерфейс отправки snmp запросов для протоколов STCIP, UG405, UTMC.
    Предназначен для обобщения атрибутов подклассов.
    Не предназначен для создания экземпляров напрямую.
    """

    stage_values_get: dict
    stage_values_set: dict
    matches: dict

    async def get_request_and_parse_response(
            self,
            oids: list[str | Oids] | KeysView[str | Oids],
            timeout: float = 0.2,
            retries: int = 0,
            include_current_mode=False
    ) -> tuple:
        # print(f'func.name: < get_request_and_parse_response >')
        error_indication, var_binds = await get(
            community=self.community_r,
            ip_v4=self.ip_v4,
            oids=oids,
            timeout=timeout,
            retries=retries
        )
        return error_indication, self.parse_response(var_binds, include_current_mode=include_current_mode)

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

    def parse_response(
            self,
            response: [tuple[ObjectIdentity, OctetString | Gauge32 | Integer | Unsigned32]],
            include_current_mode=False
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


    def get_current_mode(
            self,
            response: dict,
    ):
        raise NotImplemented()





























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

        # print(f'snmp_engine: < {snmp_engine} >')
        # print(f'snmp_engine: < {snmp_engine.cache} >')

        # snmp_engine = SnmpEngine()
        error_indication, error_status, error_index, var_binds = await get_cmd(
            snmp_engine,
            CommunityData(self.community_r),
            await UdpTransportTarget.create((self.ip_v4, 161), timeout=timeout, retries=retries),
            ContextData(),
            *[ObjectType(ObjectIdentity(oid)) for oid in oids]
        )
        return error_indication, var_binds