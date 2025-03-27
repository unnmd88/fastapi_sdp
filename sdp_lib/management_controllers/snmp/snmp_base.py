from collections.abc import KeysView
from typing import Self

from pysnmp.hlapi.v3arch.asyncio import *
from pysnmp.proto import errind

from sdp_lib.management_controllers.exceptions import BadControllerType
from sdp_lib.management_controllers.hosts import *
from sdp_lib.management_controllers.fields_names import FieldsNames
# from sdp_lib.management_controllers.parsers.snmp_parsers.parsers_snmp_core import SwarcoStcipBase
from sdp_lib.management_controllers.snmp.oids import Oids


class SnmpHost(Host):

    oids_state: tuple[Oids]
    parser_class: Any

    @classmethod
    def get_parser(cls, var_binds, instance):
        return cls.parser_class(var_binds, instance)

    def __init__(self, ip_v4: str, host_id: str = None):
        super().__init__(ip_v4, host_id)
        self.community_r, self.community_w = self.get_community()
        self.parser = None

    def get_community(self) -> tuple[str, str]:
        raise NotImplementedError()

    def get_oids(self):
        raise NotImplementedError()

    @classmethod
    def get_oids_for_get_state(cls):
        return cls.oids_state

    @property
    def protocol(self):
        return str(FieldsNames.protocol_snmp)

    async def get(
            self,
            oids: list[str | Oids] | tuple[str | Oids, ...] | KeysView[str | Oids],
            engine: SnmpEngine,
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
            engine or SnmpEngine(),
            CommunityData(self.community_r),
            await UdpTransportTarget.create((self.ip_v4, 161), timeout=timeout, retries=retries),
            ContextData(),
            *[ObjectType(ObjectIdentity(oid)) for oid in oids]
        )
        # print(f'error_indication: {error_indication}\n'
        #       f'error_status: {error_status}\n'
        #       f'error_index: {error_index}\n'
        #       f'var_binds: {var_binds}')
        return error_indication, error_status, error_index, var_binds

        # return self.check_response_and_add_error_if_has(error_indication, error_status, error_index), var_binds

    async def set(
            self,
            oids: list[tuple[str | Oids, Any]],
            engine: SnmpEngine,
            timeout: float = 1,
            retries: int = 0
    ):
        error_indication, error_status, error_index, var_binds = await set_cmd(
            SnmpEngine() or engine,
            CommunityData(self.community_w),
            await UdpTransportTarget.create((self.ip_v4, 161), timeout=timeout, retries=retries),
            ContextData(),
            *[ObjectType(ObjectIdentity(oid), val) for oid, val in oids]
            # *[ObjectType(ObjectIdentity('1.3.6.1.4.1.1618.3.7.2.11.1.0'), Unsigned32('2')) for oid, val in oids]
        )
        print(error_indication, error_status, error_index, var_binds)
        return error_indication, error_status, error_index, var_binds

    def __check_response_and_add_error_if_has(
            self,
            error_indication: errind.ErrorIndication,
            error_status: Integer32 | int,
            error_index: Integer32 | int
    ) -> bool:
        if error_indication is not None:
            self.add_data_to_data_response_attrs(error_indication)
        elif error_status or error_index:
            self.add_data_to_data_response_attrs(BadControllerType())
        return self.ERRORS

    def __parse_response_all_types_requests(
            self,
            error_indication: errind.ErrorIndication,
            error_status: Integer32 | int,
            error_index: Integer32 | int,
            var_binds: tuple[ObjectType, ...]
    ) -> Self:

        if self.__check_response_and_add_error_if_has(error_indication, error_status, error_index):
            return self

        self.parser = self.get_parser(self, var_binds)
        self.parser.parse()

        if not self.parser.data_for_response:
            self.add_data_to_data_response_attrs(BadControllerType())
            return self

        # self.parser.data_for_response = self.add_extras_for_response(self.parser.data_for_response)
        self.add_data_to_data_response_attrs(data=self.parser.data_for_response)
        return self

    async def get_basic_states_and_parse(self, engine: SnmpEngine) -> Self:

        response = await self.get(
            oids=self.get_oids_for_get_state(),
            engine=engine
        )
        return self.__parse_response_all_types_requests(*response)
        # if self.check_response_and_add_error_if_has(error_indication, error_status, error_index):
        #     return self
        #
        # self.parser = self.get_parser(self, var_binds)
        # self.parser.parse()
        #
        # if not self.parser.data_for_response:
        #     self.add_data_to_data_response_attrs(BadControllerType())
        #     return self
        #
        # # self.parser.data_for_response = self.add_extras_for_response(self.parser.data_for_response)
        # self.add_data_to_data_response_attrs(data=self.parser.data_for_response)
        # return self




    # def convert_val_to_num_stage_get_req(self, val: str) -> int | None:
    #     """
    #     Конвертирует значение из oid фазы в номер фазы из get заспроа
    #     :param val: значение, которое будет сконвертировано в десятичный номер фазы.
    #     :return: номер фазы в десятичном представлении
    #     """
    #     return self.stage_values_get.get(val)
    #
    # def convert_val_to_num_stage_set_req(self, val: str) -> int | None:
    #     """
    #     Конвертирует номер фазы в значение для установки в oid фазы
    #     :param val: номер фазы, который будет сконвертирован в соответствующее значение
    #     :return: Значение фазы, которое будет установлено.
    #     """
    #     return self.stage_values_set.get(val)

    # def get_val_as_str(self, val: str | int) -> str:
    #     return str(val)