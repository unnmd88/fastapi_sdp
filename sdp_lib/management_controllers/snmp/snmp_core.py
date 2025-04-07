import functools
import typing
from functools import cached_property
from typing import Self, TypeVar
from collections.abc import KeysView, Callable

from pysnmp.hlapi.v3arch.asyncio import *
from typing_extensions import Literal

from sdp_lib.management_controllers.exceptions import BadControllerType
from sdp_lib.management_controllers.hosts import *
from sdp_lib.management_controllers.fields_names import FieldsNames
from sdp_lib.management_controllers.parsers.snmp_parsers.processors import ConfigsProcessor
from sdp_lib.management_controllers.snmp.host_data import HostStaticData
from sdp_lib.management_controllers.snmp import host_data
from sdp_lib.management_controllers.snmp.oids import Oids
from sdp_lib.management_controllers.snmp.response_checkers import ErrorResponseCheckers
from sdp_lib.management_controllers.snmp.set_commands import AvailableGetCommands, AvailableSetCommands
from sdp_lib.management_controllers.snmp.snmp_utils import SwarcoConverters, PotokSConverters, PotokPConverters
from sdp_lib.management_controllers.snmp.snmp_requests import SnmpRequests
from sdp_lib.management_controllers.snmp.varbinds import potok_stcip_varbinds, swarco_sctip_varbinds, VarbindsSwarco, \
    VarbindsPotokS, WrappersVarbindsByScnPotokP

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


# RequestModes: typing.TypeAlias = Literal['get', 'set', 'get_next']

def ug405_dependency(type_controller):
    def wrapper(func: Callable):
        @functools.wraps(func)
        async def wrapped(instance, value=None, *args, **kwargs):
            if instance.scn_as_ascii_string is None:
                instance.last_response = await instance._method_for_get_scn()(varbinds=[instance.converter_class.scn_varbind])
                if ErrorResponseCheckers(instance).check_response_errors_and_add_to_host_data_if_has():
                    return instance
                try:
                    instance._set_scn_from_response()
                except BadControllerType as e:
                    instance.add_data_to_data_response_attrs(e)

                if instance.ERRORS:
                    return instance

            instance._varbinds_for_request = WrappersVarbindsByScnPotokP.get_varbinds_current_states_by_scn(instance.scn_as_ascii_string)

            print(f'param: {type_controller}')
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
        self._processor_config = default_config_processor
        self._parser = self._get_parser(self)
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

        # self.parser_class = parser(self) # Think about refactoring
        self._parser.parse()

        if not self._parser.data_for_response:
            self.add_data_to_data_response_attrs(BadControllerType())
            return self

        self.add_data_to_data_response_attrs(data=self._parser.data_for_response)
        return self

    @abc.abstractmethod
    def process_oid(self, oid: str) -> str:
        ...

    def process_oid_val(self, val: Any) -> str | int:
        return val.prettyPrint()

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


class AbstractUg405Hosts(SnmpHosts):

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
        self.scn_as_ascii_string = self.get_scn_as_ascii_from_scn_as_chars_attr()

    @abc.abstractmethod
    def _method_for_get_scn(self) -> Callable:
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

    def get_scn_as_ascii_from_scn_as_chars_attr(self) -> str | None:
        if self.scn_as_chars is not None:
            return self.convert_chars_string_to_ascii_string(self.scn_as_chars)
        return None

    def get_scn_as_chars_from_scn_as_ascii(self) -> str:
        if self.scn_as_ascii_string is not None:
            return self.convert_ascii_string_to_chars(self.scn_as_ascii_string)

    @staticmethod
    def add_CO_to_scn(scn: str) -> str | None:
        if not isinstance(scn, str) or not scn.isdigit():
            return None
        return f'CO{scn}'

    @staticmethod
    def convert_chars_string_to_ascii_string(scn_as_chars: str) -> str:
        """
        Генерирует SCN
        :param scn -> символы строки, которые необходимо конвертировать в scn
        :return -> возвращет scn
        """
        return f'.1.{str(len(scn_as_chars))}.{".".join([str(ord(c)) for c in scn_as_chars])}'

    @staticmethod
    def convert_ascii_string_to_chars(scn_as_ascii: str) -> str:
        """
        Генерирует SCN
        :param scn -> символы строки, которые необходимо конвертировать в scn
        :return -> возвращет scn
        .1.6.67.79.50.48.56.48
        """
        splitted = scn_as_ascii.split('.')
        num_chars = int(splitted[2])
        scn_as_chars = ''.join([chr(int(c)) for c in splitted[3:]])
        print(f'scn_as_chars: {scn_as_chars}')
        assert num_chars == len(scn_as_chars)
        return scn_as_chars

    def _add_scn_to_oids(
            self,
            oids: tuple[Oids, ...] | list[Oids]
    ) -> list[Oids]:
        return [
            f'{oid}{self.scn_as_ascii_string}' if oid in self.host_properties.oids_scn_required else oid
            for oid in oids
        ]

    def _set_scn_from_response(self):
        raise NotImplementedError()

    def process_oid(self, oid: str) -> str:
        return str(oid).replace(self.scn_as_ascii_string, '')

    @ug405_dependency('potok__ug405')
    async def get_states(self):
        self._processor_config = pretty_processing_config_processor
        return await self._make_request_and_build_response(
            method=self._request_sender.snmp_get,
            varbinds=self._varbinds_for_request,
            parser=self.parser_class
        )

    # async def get_request(self, oids: list[Oids | str]):
    #
    #     self.processor_config = ConfigsProcessor()
    #
    #     return await self._make_request_and_build_response(
    #         method=self.request_sender.snmp_get,
    #         oids=oids,
    #         parser=self.states_parser
    #     )

    # def async_dependency(self, type_dependency):
    #     def wrapper(func: Callable) -> Callable:
    #         @functools.wraps(func)
    #         async def wrapped(*args, **kwargs):
    #             print(f'type_dependency: {type_dependency}')
    #             print(f'args: {args}')
    #             print(f'kwargs: {kwargs}')
    #             if type_dependency == 'operation_mode':
    #                 self.last_response = self.request_sender.snmp_get(
    #                     [ObjectType(ObjectIdentity(Oids.utcType2OperationMode))]
    #                 )
    #                 print(f'self.last_response ?? {self.last_response}')
    #             else:
    #                 pass
    #             self.last_response = await func(*args, **kwargs)
    #             print(f'self.last_response2: {self.last_response}')
    #
    #             return wrapped
    #
    #         return wrapper


class AbstractStcipHosts(SnmpHosts):

    host_data: host_data.HostStaticData
    parser_class: Any
    converter_class: SwarcoConverters | PotokSConverters
    varbinds: VarbindsSwarco | VarbindsPotokS

    def process_oid(self, oid: str) -> str:
        return str(oid)

    async def get_states(self):
        self._processor_config = pretty_processing_config_processor
        return await self._make_request_and_build_response(
            method=self._request_sender.snmp_get,
            varbinds=self.varbinds.get_varbinds_current_states(),
        )





