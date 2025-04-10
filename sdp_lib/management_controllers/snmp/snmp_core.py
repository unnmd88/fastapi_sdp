import abc
import asyncio
import functools
import time
from functools import cached_property
from typing import Self, TypeVar
from collections.abc import KeysView, Callable

from pysnmp.hlapi.v3arch.asyncio import *

from sdp_lib.management_controllers.exceptions import BadControllerType
from sdp_lib.management_controllers.hosts import *
from sdp_lib.management_controllers.fields_names import FieldsNames
from sdp_lib.management_controllers.parsers.snmp_parsers.varbinds_parsers import (
    pretty_processing_stcip,
    BaseSnmpParser,
    ConfigsParser,
    StandartVarbindsParsersSwarco,
    StandardVarbindsParserPotokS,
    PotokPStandardParser,
    PeekStandardParser
)
from sdp_lib.management_controllers.snmp.host_data import HostStaticData
from sdp_lib.management_controllers.snmp import host_data
from sdp_lib.management_controllers.snmp.response_structure import SnmpResponseStructure
from sdp_lib.management_controllers.snmp.set_commands import SnmpEntity
from sdp_lib.management_controllers.snmp.snmp_utils import (
    SwarcoConverters,
    PotokSConverters,
    PotokPConverters,
    ScnConverterMixin,
    PeekConverters
)
from sdp_lib.management_controllers.snmp.snmp_requests import SnmpRequests
from sdp_lib.management_controllers.snmp.varbinds import (
    VarbindsSwarco,
    VarbindsPotokS,
    swarco_sctip_varbinds,
    potok_stcip_varbinds,
    potok_ug405_varbinds,
    VarbindsUg405
)
from sdp_lib.management_controllers.snmp._types import (
    T_Oids,
    T_Varbinds,
    T_Parsers
)


T_DataHosts = TypeVar('T_DataHosts', bound=HostStaticData)


def ug405_dependency(
        type_request_entity: SnmpEntity,
        varbinds_builder_method: Callable
):
    def wrapper(func: Callable):
        @functools.wraps(func)
        async def wrapped(instance, value=None, *args, **kwargs):
            # print(f'dependency_varbinds: {dependency_varbinds}')
            await instance.get_dependency_data_and_add_error_if_has()
            if instance.response_errors:
                return instance

            if isinstance(instance, PeekUg405) and type_request_entity == SnmpEntity.snmp_set:
                 if instance.current_opeartion_mode == 1: # TO DO in Peek get_dependency_data_and_add_error_if_has()
                    await instance.set_operation_mode2()
                    if instance.response_errors:
                        return instance

            if value is None:
                instance.set_varbinds_for_request(varbinds_builder_method(instance.scn_as_ascii_string))
            else:
                instance.set_varbinds_for_request(varbinds_builder_method(instance.scn_as_ascii_string, value))

            print(f'varbinds_for_req: {instance._varbinds_for_request}')

            print(f'param: {instance.host_properties.type_controller}')
            print(f'value: {value}')
            print(f'func_name: {func.__name__}')
            print(f'args: {args}, kwargs: {kwargs}')
            # print(f'instanse: {instance}')
            if type_request_entity == SnmpEntity.snmp_set:
                return await func(instance, value)
            return await func(instance)

        return wrapped
    return wrapper


class SnmpHosts(Host):
    """
    Класс абстрактного хоста, в котором реализована логика формирования snmp-запросов,
    получение и обработка snmp-ответов.
    """

    protocol = FieldsNames.protocol_snmp
    host_properties: T_DataHosts
    parser_class: Any
    converter_class: Any
    varbinds: Any

    def __init__(
            self,
            *,
            ip_v4: str = None,
            host_id: str = None,
            engine: SnmpEngine = None
    ):
        super().__init__(ip_v4=ip_v4, host_id=host_id)
        self._engine = engine
        self._request_sender = SnmpRequests(self)
        self._request_method: Callable | None = None
        self._parse_method_config = None
        self._parser: BaseSnmpParser = self._get_parser()
        self._varbinds_for_request = None

    def set_engine(self, engine: SnmpEngine):
        if isinstance(engine, SnmpEngine):
            self._engine = engine
        else:
            raise TypeError(f'engine должен быть типа "SnmpEngine", передан: {type(engine)}')

    @classmethod
    def _get_parser(cls, *args, **kwargs):
        # print(f'*args" {args}, kwargs: {kwargs}')
        return cls.parser_class(*args, **kwargs)

    def set_varbinds_for_request(self, varbinds: T_Varbinds):
        self._varbinds_for_request = varbinds

    def reset_varbinds_for_request(self):
        self._varbinds_for_request = None

    def set_current_request_method(self, method: Callable):
        self._request_method = method

    def reset_current_request_method(self):
        self._request_method = None

    def set_varbinds_and_method_for_request(self, varbinds: T_Varbinds, method: Callable):
        self._varbinds_for_request = varbinds
        self._request_method = method

    def reset_varbinds_and_method_for_request(self):
        self.reset_varbinds_for_request()
        self.reset_current_request_method()

    def check_snmp_response_errors_and_add_to_host_data_if_has(self):
        """
            self.__response[ResponseStructure.ERROR_INDICATION] = error_indication: errind.ErrorIndication,
            self.__response[ResponseStructure.ERROR_STATUS] = error_status: Integer32 | int,
            self.__response[ResponseStructure.ERROR_INDEX] = error_index: Integer32 | int
        """
        if self.last_response[SnmpResponseStructure.ERROR_INDICATION] is not None:
            self.add_data_to_data_response_attrs(self.last_response[SnmpResponseStructure.ERROR_INDICATION])
        elif (
            self.last_response[SnmpResponseStructure.ERROR_STATUS]
            or self.last_response[SnmpResponseStructure.ERROR_INDEX]
        ):
            self.add_data_to_data_response_attrs(BadControllerType())
        return bool(self.response_errors)

    async def _make_request_and_build_response(self):
        """
        Осуществляет вызов соответствующего snmp-запроса и передает
        self.__parse_response_all_types_requests полученный ответ для парса response.
        """

        self.last_response = await self._request_method(varbinds=self._varbinds_for_request)
        print(f'self.last_response: {self.last_response}')
        return self.__parse_and_processing_response_all_types_requests()

    def __parse_and_processing_response_all_types_requests(self) -> Self:
        """
        Осуществляет проверку snmp-response и передает его парсеру для формирования
        response из полученных значений оидов.
        """
        # if ErrorResponseCheckers(self).check_response_errors_and_add_to_host_data_if_has():
        #     return self

        if self.check_snmp_response_errors_and_add_to_host_data_if_has():
            return self

        self._parser.parse(
            varbinds=self.last_response[SnmpResponseStructure.VAR_BINDS],
            config=self._parse_method_config
        )

        if not self._parser.data_for_response:
            self.add_data_to_data_response_attrs(BadControllerType())
            self.reset_varbinds_and_method_for_request()
            return self

        self.add_data_to_data_response_attrs(data=self._parser.data_for_response)
        self.reset_varbinds_and_method_for_request()
        return self


class Ug405Hosts(SnmpHosts, ScnConverterMixin):

    host_data: host_data.HostStaticDataWithScn
    converter_class: PotokPConverters

    def __init__(
            self,
            *,
            ip_v4: str = None,
            engine=None,
            host_id=None,
            scn=None
    ):
        super().__init__(ip_v4=ip_v4, engine=engine, host_id=host_id)
        self._curr_operation_mode = None
        self.scn_as_chars = scn
        self.scn_as_ascii_string = self._get_scn_as_ascii_from_scn_as_chars_attr()

    @property
    @abc.abstractmethod
    def method_for_get_scn(self) -> Callable:
        ...

    @abc.abstractmethod
    async def get_dependency_data_and_add_error_if_has(self):
        ...

    @property
    def current_opeartion_mode(self):
        return self._curr_operation_mode

    async def _collect_data_and_send_snmp_request_ug405(
            self,
            *,
            method: Callable,
            varbinds_generate_method: Callable,
            value: int | str = None
    ):
        """
        Осуществляет вызов соответствующего snmp-запроса и передает
        self.__parse_response_all_types_requests полученный ответ для парса response.
        """

        await self.get_dependency_data_and_add_error_if_has()
        if self.response_errors:
            return self

        if method == self._request_sender.snmp_get:
            self.set_varbinds_and_method_for_request(
                varbinds=varbinds_generate_method(self.scn_as_ascii_string),
                method=method
            )
            # self.set_varbinds_for_request(varbinds_generate_method(self.scn_as_ascii_string))
        elif method == self._request_sender.snmp_set:
            self.set_varbinds_and_method_for_request(
                varbinds=varbinds_generate_method(self.scn_as_ascii_string, value),
                method=method
            )
            # self.set_varbinds_for_request(varbinds_generate_method(self.scn_as_ascii_string, value))
        else:
            raise TypeError

        self._parse_method_config = self._get_pretty_processed_config_with_scn()

        return await self._make_request_and_build_response()

        # self.last_response = await method(varbinds=varbinds)
        # print(f'self.last_response: {self.last_response}')
        # # return self.__parse_and_processing_response_all_types_requests(parser)
        # return self.__parse_and_processing_response_all_types_requests()

    async def get_states(self):
        return await self._collect_data_and_send_snmp_request_ug405(
            method=self._request_sender.snmp_get,
            varbinds_generate_method=self.varbinds.get_varbinds_current_states,
            value=None
        )

    async def set_operation_mode(self, value: int):
        self.last_response = await self._request_sender.snmp_set(
            varbinds=[VarbindsUg405.get_operation_mode_varbinds(value)]
        )

    async def set_operation_mode1(self):
        await self.set_operation_mode(1)

    async def set_operation_mode2(self):
        await self.set_operation_mode(2)

    async def set_operation_mode3(self):
        await self.set_operation_mode(3)

    def _get_scn_as_ascii_from_scn_as_chars_attr(self) -> str | None:
        return self.get_scn_as_ascii_from_scn_as_chars_attr(self.scn_as_chars)

    def _get_scn_as_chars_from_scn_as_ascii(self) -> str:
        return self.get_scn_as_ascii_from_scn_as_chars_attr(self.scn_as_ascii_string)

    def _set_scn_from_response(self):
        raise NotImplementedError()

    def _get_pretty_processed_config_with_scn(self):
        return ConfigsParser(
            extras=True,
            scn=self.scn_as_ascii_string
        )

    def _get_default_processed_config_with_scn(self):
        return ConfigsParser(
            oid_handler=str,
            scn=self.scn_as_ascii_string
        )


class StcipHosts(SnmpHosts):

    host_data: host_data.HostStaticData
    parser_class: Any
    converter_class: SwarcoConverters | PotokSConverters
    varbinds: VarbindsSwarco | VarbindsPotokS

    async def get_states(self):
        self._parse_method_config = pretty_processing_stcip
        self.set_varbinds_and_method_for_request(
            varbinds=self.varbinds.get_varbinds_current_states(),
            method=self._request_sender.snmp_get
        )
        return await self._make_request_and_build_response()


class SwarcoStcip(StcipHosts):

    host_properties = host_data.swarco_stcip
    parser_class = StandartVarbindsParsersSwarco
    converter_class = SwarcoConverters
    varbinds = swarco_sctip_varbinds


class PotokS(StcipHosts):

    host_properties = host_data.potok_s
    parser_class = StandardVarbindsParserPotokS
    converter_class = PotokSConverters
    varbinds = potok_stcip_varbinds


class PotokP(Ug405Hosts):

    parser_class = PotokPStandardParser
    host_properties = host_data.potok_p
    converter_class = PotokPConverters
    varbinds = potok_ug405_varbinds

    @property
    def method_for_get_scn(self) -> Callable:
        return self._request_sender.snmp_get

    def _set_scn_from_response(self) -> None | BadControllerType:
        try:
            self.scn_as_chars = str(self.last_response[SnmpResponseStructure.VAR_BINDS][0][1])
            self.scn_as_ascii_string = self._get_scn_as_ascii_from_scn_as_chars_attr()
        except IndexError:
            raise  BadControllerType()
        return None

    async def get_dependency_data_and_add_error_if_has(self):

        self.last_response = await self._request_sender.snmp_get(varbinds=[potok_ug405_varbinds.site_id_varbind])

        # if ErrorResponseCheckers(self).check_response_errors_and_add_to_host_data_if_has():
        #     return

        if self.check_snmp_response_errors_and_add_to_host_data_if_has():
            return

        try:
            self._set_scn_from_response()
            print(f'self.scn_as_ascii_string {self.scn_as_ascii_string}')
            print(f' self.scn_as_chars {self.scn_as_chars}')
        except BadControllerType as e:
            self.add_data_to_data_response_attrs(e)


class PeekUg405(Ug405Hosts):

    parser_class = PeekStandardParser
    host_properties = host_data.potok_p
    converter_class = PeekConverters
    # varbinds = peek_ug405_varbinds

    def _method_for_get_scn(self) -> Callable:
        return self._request_sender.snmp_get_next


async def main():

    obj = PotokS(ip_v4='10.179.68.177',)
    # obj = SwarcoStcip(ip_v4='10.179.20.129')
    # obj = SwarcoStcip(ip_v4='10.179.68.105')
    # obj = SwarcoStcip(ip_v4='10.179.57.1')
    # obj = SwarcoStcip(ip_v4='10.179.61.33', host_id='3205')
    # obj = PotokS(ip_v4='10.179.68.177',)
    obj = SwarcoStcip(ip_v4='10.179.57.1')

    # obj = PotokP(ip_v4='10.179.69.65', host_id='2600')
    # obj = PotokP(ip_v4='10.179.56.105', host_id='155')
    obj = PotokP(ip_v4='10.179.108.129', host_id='2822')
    # obj = SwarcoStcip(ip_v4='10.179.20.129')

    # obj.ip_v4 = '10.179.20.129'
    # obj.set_engine(SnmpEngine())

    start_time = time.time()

    r = await obj.get_states()
    # print(obj.response_as_dict)
    # print(json.dumps(obj.response_as_dict, indent=4))
    print(r)
    print(f'время составло: {time.time() - start_time}')

    """set command test"""

    # res = await obj.set_stage(0)

    # print(res.response_as_dict)

    return obj.response


if __name__ == '__main__':

    asyncio.run(main())