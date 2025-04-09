import asyncio
import functools
import time
import typing
from functools import cached_property
from typing import Self, TypeVar
from collections.abc import KeysView, Callable

from pysnmp.hlapi.v3arch.asyncio import *
from typing_extensions import Literal
from watchfiles import awatch

from api_v1.controller_management.schemas import AllowedControllers
from sdp_lib.management_controllers.exceptions import BadControllerType
from sdp_lib.management_controllers.hosts import *
from sdp_lib.management_controllers.fields_names import FieldsNames
from sdp_lib.management_controllers.parsers.snmp_parsers.new_parsers_snmp_core import pretty_processing_stcip, \
    BaseSnmpParser, ConfigsParser, StandartVarbindsParsersSwarco, StandardVarbindsParserPotokS, PotokPStandardParser, \
    PeekStandardParser
from sdp_lib.management_controllers.parsers.snmp_parsers.processors import ConfigsProcessor
from sdp_lib.management_controllers.snmp.host_data import HostStaticData
from sdp_lib.management_controllers.snmp import host_data, oids
from sdp_lib.management_controllers.snmp.oids import Oids
from sdp_lib.management_controllers.snmp.response_checkers import ErrorResponseCheckers
from sdp_lib.management_controllers.snmp.response_structure import SnmpResponseStructure
from sdp_lib.management_controllers.snmp.set_commands import AvailableGetCommands, AvailableSetCommands
from sdp_lib.management_controllers.snmp.snmp_utils import SwarcoConverters, PotokSConverters, PotokPConverters, \
    ScnConverterMixin, PeekConverters
from sdp_lib.management_controllers.snmp.snmp_requests import SnmpRequests
from sdp_lib.management_controllers.snmp.varbinds import VarbindsSwarco, \
    VarbindsPotokS, WrapperVarbindsByScnPotokP, swarco_sctip_varbinds, potok_stcip_varbinds, potok_ug405_varbinds, \
    VarbindsPotokP, VarbindsUg405

T_DataHosts = TypeVar('T_DataHosts', bound=HostStaticData)
T_Oids = TypeVar('T_Oids', tuple[Oids | str, ...], list[Oids | str])
T_Varbinds = TypeVar('T_Varbinds', tuple[ObjectType, ...], list[ObjectType])
T_Parsers = TypeVar('T_Parsers')


class RequestConfig(typing.NamedTuple):
    method: Callable
    oids: T_Oids | T_Varbinds
    parser: Any


pretty_processing_config_processor = ConfigsProcessor()
default_config_processor = ConfigsProcessor(oid_handler=str)


RequestModes: typing.TypeAlias = Literal['get', 'set', 'get_next']


# def ug405_dependency(type_controller):
#     def wrapper(func: Callable):
#         @functools.wraps(func)
#         async def wrapped(instance, value=None, *args, **kwargs):
#             if instance.scn_as_ascii_string is None:
#                 instance.last_response = await instance.method_for_get_scn(varbinds=[instance.converter_class.scn_varbind])
#                 if ErrorResponseCheckers(instance).check_response_errors_and_add_to_host_data_if_has():
#                     return instance
#                 try:
#                     instance._set_scn_from_response()
#                 except BadControllerType as e:
#                     instance.add_data_to_data_response_attrs(e)
#
#                 if instance.response_errors:
#                     return instance
#
#             instance._varbinds_for_request = WrappersVarbindsByScnPotokP.get_varbinds_current_states_by_scn(instance.scn_as_ascii_string)
#
#             print(f'param: {type_controller}')
#             print(f'value: {value}')
#             print(f'func_name: {func.__name__}')
#             print(f'args: {args}, kwargs: {kwargs}')
#             # print(f'instanse: {instance}')
#
#             return await func(instance)
#         return wrapped
#     return wrapper


def ug405_dependency(
        type_request_entity: RequestModes,
        varbinds_builder_method: Callable
):
    def wrapper(func: Callable):
        @functools.wraps(func)
        async def wrapped(instance, value=None, *args, **kwargs):
            # print(f'dependency_varbinds: {dependency_varbinds}')
            await instance.get_dependency_data_and_add_error_if_has()
            if instance.response_errors:
                return instance

            print(f'isinstance(instance, PeekUg405): {isinstance(instance, PeekUg405)}')
            print(f'isinstance(instance, PotokP): {isinstance(instance, PotokP)}')

            if isinstance(instance, PeekUg405) and type_request_entity == 'set':
                 if instance.current_opeartion_mode == 1:
                    await instance.set_operation_mode2()
                    if instance.response_errors:
                        return instance


            if value is None:
                instance.set_varbinds_for_request(varbinds_builder_method(instance.scn_as_ascii_string))
            else:
                instance.set_varbinds_for_request(varbinds_builder_method(instance.scn_as_ascii_string, value))


            print(f'param: {instance.host_properties.type_controller}')
            print(f'value: {value}')
            print(f'func_name: {func.__name__}')
            print(f'args: {args}, kwargs: {kwargs}')
            # print(f'instanse: {instance}')

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
        self._engine = engine or SnmpEngine()
        self._request_sender = SnmpRequests(self)
        self._curr_operation_mode = None
        self._parse_method_config = None
        self._processor_config = default_config_processor
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

    @property
    def processor_config(self):
        return self._processor_config

    @property
    def current_opeartion_mode(self):
        return self._curr_operation_mode

    async def _make_request_and_build_response(
            self,
            *,
            method: Callable,
            varbinds,
    ):
        """
        Осуществляет вызов соответствующего snmp-запроса и передает
        self.__parse_response_all_types_requests полученный ответ для парса response.
        """
        self.last_response = await method(varbinds=varbinds)
        print(f'self.last_response: {self.last_response}')
        # return self.__parse_and_processing_response_all_types_requests(parser)
        return self.__parse_and_processing_response_all_types_requests()

    def __parse_and_processing_response_all_types_requests(self) -> Self:
        """
        Осуществляет проверку snmp-response и передает его парсеру для формирования
        response из полученных значений оидов.
        """
        if ErrorResponseCheckers(self).check_response_errors_and_add_to_host_data_if_has():
            return self

        self._parser.parse(
            varbinds=self.last_response[SnmpResponseStructure.VAR_BINDS],
            config=self._parse_method_config
        )

        if not self._parser.data_for_response:
            self.add_data_to_data_response_attrs(BadControllerType())
            return self

        self.add_data_to_data_response_attrs(data=self._parser.data_for_response)
        return self

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

    # def process_oid(self, oid: str) -> str:
    #     return str(oid)
    #
    # def process_oid_val(self, val: Any) -> str | int:
    #     return val.prettyPrint()

    # @abc.abstractmethod
    # def _get_config_for_curr_state(self) -> RequestConfig:
    #     ...

    # async def get_states(self):
    #     return await self._make_request_and_build_response(
    #         *self._get_config_for_curr_state()
    #     )


    # Set command section
    
    # def _get_config_for_set_request(self) -> RequestConfig:
    # 
    #     self.processor_config = set_request_config_processor
    # 
    #     return RequestConfig(
    #         method=self.request_sender.snmp_set,
    #         oids=self.varbinds_for_get_state,
    #         parser=self.states_parser,
    #     )
    
    # async def set_stage(self, num_stage: int):
    #     self.processor_config = set_request_config_processor
    #     return await self._make_request_and_build_response(
    #         *RequestConfig(
    #             method=self.request_sender.snmp_set,
    #             oids=self.converter_class.get_varbinds_for_set_stage(num_stage),
    #             parser=self.states_parser
    #         )
    #     )


class AbstractUg405Hosts(SnmpHosts, ScnConverterMixin):

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
        self.scn_as_chars = scn
        self.scn_as_ascii_string = self._get_scn_as_ascii_from_scn_as_chars_attr()

    @property
    @abc.abstractmethod
    def method_for_get_scn(self) -> Callable:
        ...

    @abc.abstractmethod
    async def get_dependency_data_and_add_error_if_has(self):
        ...

    async def set_scn_and_add_err_to_data_response_if_has(self):

        self.last_response = await self._method_for_get_scn()(varbinds=[self.converter_class.scn_varbind])
        # print(f'MY: {self.last_response}')
        # print(f'MY: {self.last_response[3][0][0]}')
        # print(f'MY: {str(self.last_response[3][0][0]).replace(Oids.utcReplyGn, "")}')

        if ErrorResponseCheckers(self).check_response_errors_and_add_to_host_data_if_has():
            return

        try:
            self._set_scn_from_response()
            print(f'self.scn_as_ascii_string {self.scn_as_ascii_string}')
            print(f' self.scn_as_chars {self.scn_as_chars}')
        except BadControllerType as e:
            self.add_data_to_data_response_attrs(e)

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

    def set_varbinds_for_request(self, varbinds: ObjectType):
        self._varbinds_for_request = varbinds


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


class AbstractStcipHosts(SnmpHosts):

    host_data: host_data.HostStaticData
    parser_class: Any
    converter_class: SwarcoConverters | PotokSConverters
    varbinds: VarbindsSwarco | VarbindsPotokS

    async def get_states(self):
        self._parse_method_config = pretty_processing_stcip
        return await self._make_request_and_build_response(
            method=self._request_sender.snmp_get,
            varbinds=self.varbinds.get_varbinds_current_states(),
        )


class SwarcoStcip(AbstractStcipHosts):

    host_properties = host_data.swarco_stcip
    parser_class = StandartVarbindsParsersSwarco
    converter_class = SwarcoConverters
    varbinds = swarco_sctip_varbinds


class PotokS(AbstractStcipHosts):

    host_properties = host_data.potok_s
    parser_class = StandardVarbindsParserPotokS
    converter_class = PotokSConverters
    varbinds = potok_stcip_varbinds


class PotokP(AbstractUg405Hosts):

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

        if ErrorResponseCheckers(self).check_response_errors_and_add_to_host_data_if_has():
            return

        try:
            self._set_scn_from_response()
            print(f'self.scn_as_ascii_string {self.scn_as_ascii_string}')
            print(f' self.scn_as_chars {self.scn_as_chars}')
        except BadControllerType as e:
            self.add_data_to_data_response_attrs(e)

    @ug405_dependency(
        request_entity=AvailableGetCommands.current_state,
        type_request_entity='get',
        varbinds_builder_method=potok_ug405_varbinds.get_varbinds_current_states
    )
    async def get_states(self):
        self._parse_method_config = self._get_pretty_processed_config_with_scn()
        return await self._make_request_and_build_response(
            method=self._request_sender.snmp_get,
            varbinds=self._varbinds_for_request,
        )


class PeekUg405(AbstractUg405Hosts):

    parser_class = PeekStandardParser
    host_properties = host_data.potok_p
    converter_class = PeekConverters


    async def _set_operation_mode(self):
        self.response = await self._request_sender.snmp_get(self.converter_class.get_operation_mode_varbind)
        if ErrorResponseCheckers(self).check_response_errors_and_add_to_host_data_if_has():
            return
        if str(self.response[SnmpResponseStructure.VAR_BINDS][0][1]) == '1':
            await self._request_sender.snmp_set(self.converter_class.set_operation_mode2_varbind)
            if ErrorResponseCheckers(self).check_response_errors_and_add_to_host_data_if_has():
                return
        await self._request_sender.snmp_set(self.converter_class.set_operation_mode3_varbind)
        ErrorResponseCheckers(self).check_response_errors_and_add_to_host_data_if_has()

    async def _make_request_and_build_response(
            self,
            method: Callable,
            oids: T_Oids,
            parser: typing.Any,
    ):
        # if self.scn_as_ascii_string is None:
        #     self.last_response = await self._method_for_get_scn()(varbinds=[self.converter_class.scn_varbind])
        #     if ErrorResponseCheckers(self).check_response_errors_and_add_to_host_data_if_has():
        #         return self
        #     try:
        #         self._set_scn_from_response()
        #     except BadControllerType as e:
        #         self.add_data_to_data_response_attrs(e)

        await self.set_scn_and_add_err_to_data_response_if_has()

        if self.ERRORS:
            return self

        return await super()._make_request_and_build_response(
            method=method,
            varbinds=self.converter_class.add_scn_to_oids(
                oids_without_val=oids,
                scn_as_ascii_string=self.scn_as_ascii_string,
                scn_as_chars_string=self.scn_as_chars,
                wrap_oid_by_object_identity=True
                ),
            parser=parser
        )

        # return await super()._make_request_and_build_response(
        #     method=method,
        #     varbinds=self.converter_class.get_varbinds_for_get_state(
        #         scn_as_ascii_string=self.scn_as_ascii_string,
        #         scn_as_chars_string=self.scn_as_chars
        #         ),
        #     parser=parser
        # )

    def _set_scn_from_response(self) -> None | BadControllerType:
        print(f'1: {str(self.last_response[SnmpResponseStructure.VAR_BINDS][0][1])}')
        try:
            self.scn_as_ascii_string = str(self.last_response[SnmpResponseStructure.VAR_BINDS][0][0]).replace(Oids.utcReplyGn, "")
            self.scn_as_chars = self.get_scn_as_chars_from_scn_as_ascii()
        except IndexError:
            raise  BadControllerType()
        return None


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
    obj = PotokP(ip_v4='10.179.56.105', host_id='155')
    # obj = SwarcoStcip(ip_v4='10.179.20.129')

    # obj.ip_v4 = '10.179.20.129'
    # obj.set_engine(SnmpEngine())

    start_time = time.time()

    r = await obj.get_states()
    print(obj.response_as_dict)
    print(r.response)
    print(f'время составло: {time.time() - start_time}')

    return obj.response


if __name__ == '__main__':

    asyncio.run(main())