import abc
import math
from collections.abc import Callable
from functools import cached_property
from typing import Any

from pysnmp.smi.rfc1902 import ObjectType

from sdp_lib.management_controllers.controller_modes import NamesMode
from sdp_lib.management_controllers.fields_names import FieldsNames
from sdp_lib.management_controllers.parsers.parsers_core import Parsers
from sdp_lib.management_controllers.parsers.snmp_parsers.mixins import StcipMixin
from sdp_lib.management_controllers.parsers.snmp_parsers.processors import SwarcoProcessor
from sdp_lib.management_controllers.snmp.oids import Oids
from sdp_lib.management_controllers.snmp.response_structure import SnmpResponseStructure
from sdp_lib.management_controllers.snmp.smmp_utils import SwarcoConverters


# class BaseSnmpParser(Parsers):
#
#     def __init__(
#             self,
#             host_instance,
#             # content: tuple[ObjectType, ...]
#     ):
#         super().__init__(content=host_instance.last_response[SnmpResponseStructure.VAR_BINDS])
#         self.host_instance = host_instance
#         self.current_oid = None
#         self.current_val = None
#
#     def call_after_parse_methods(self):
#         self.add_extras_to_response()
#         self.add_depends_data_to_response()
#         self.add_host_protocol_to_response()
#
#     def add_extras_to_response(self):
#         pass
#
#     def add_depends_data_to_response(self):
#         pass
#
#     @classmethod
#     def convert_hex_to_decimal(cls, val: str) -> int | None:
#         """
#         Конвертирует значение, полученное из oid фазы в номер фазы десятичного представления
#         :param val: значение, необходимое отобразить в десятичном виде
#         :return: значение(номер) фазы в десятичном виде
#         """
#
#         try:
#             if val not in (' ', '@'):
#                 return int(math.log2(int(val, 16))) + 1
#             elif val == ' ':
#                 return 6
#             elif val == '@':
#                 return 7
#         except ValueError:
#             print(f'Значение val: {val}')
#
#     def get_val_as_str(self, val) -> str:
#         return str(val)
#
#     def processing_oid_from_response(self, oid: str) -> str:
#         pass
#
#     def add_fields_to_response(self, **kwargs):
#         for field_name, val in kwargs.items():
#             self.parsed_content_as_dict[field_name] = val
#
#     def add_host_protocol_to_response(self):
#         self.add_fields_to_response(**{FieldsNames.host_protocol: self.host_instance.host_properties.host_protocol})
#
#     @classmethod
#     def parse_varbinds_base(cls, varbinds: tuple[ObjectType, ...]):
#         for oid, val in varbinds:
#             oid, val = str(oid), val.prettyPrint()
#             print(f'oid: {oid}  >>>> val: {val}')
#             print(f'oid: {oid}  >>>> type(val): {type(val)}')
#
#     def parse(self) : # Рефакторинг
#
#         try:
#             _matches = self.matches
#             for oid, val in self.content:
#                 print(f'oid: {str(oid)}::: val: {str(val)}')
#                 oid, val = self.processing_oid_from_response(str(oid)), val.prettyPrint()
#                 field_name, fn = _matches.get(oid)
#                 self.parsed_content_as_dict[str(field_name)] = fn(val)
#             self.call_after_parse_methods()
#              # self.add_current_mode_to_response()
#             # self.add_extras_to_response()
#             # self.add_depends_data_to_response()
#             # self.add_host_protocol_to_response()
#             print('-----DEBUG------')
#         except IndexError as err:
#             print(f'except TypeError:: {err}')
#             return self.parsed_content_as_dict
#         print(f'ip: {self.host_instance.ip_v4} | resp: {self.parsed_content_as_dict}')
#         self.data_for_response = self.parsed_content_as_dict
#         return self.data_for_response


class BaseSnmpParser(Parsers):

    def __init__(
            self,
            host_instance,
            # content: tuple[ObjectType, ...]
    ):
        super().__init__(content=host_instance.last_response[SnmpResponseStructure.VAR_BINDS])
        self.host_instance = host_instance
        self.current_oid = None
        self.current_val = None
        self._processor = self.get_processor()

    @abc.abstractmethod
    def get_processor(self):
        ...

    def call_after_parse_methods(self):
        self.add_extras_to_response()
        self.add_depends_data_to_response()
        self.add_host_protocol_to_response()

    def add_extras_to_response(self):
        pass

    def add_depends_data_to_response(self):
        pass

    def add_fields_to_response(self, **kwargs):
        for field_name, val in kwargs.items():
            self.parsed_content_as_dict[field_name] = val

    def add_host_protocol_to_response(self):
        self.add_fields_to_response(**{FieldsNames.host_protocol: self.host_instance.host_properties.host_protocol})

    @classmethod
    def parse_varbinds_base(cls, varbinds: tuple[ObjectType, ...]):
        for oid, val in varbinds:
            oid, val = str(oid), val.prettyPrint()
            print(f'oid: {oid}  >>>> val: {val}')
            print(f'oid: {oid}  >>>> type(val): {type(val)}')

    def parse(self) : # Рефакторинг

        try:
            self.parsed_content_as_dict = self._processor.process_varbinds()
             # self.add_current_mode_to_response()
            # self.add_extras_to_response()
            # self.add_depends_data_to_response()
            # self.add_host_protocol_to_response()
            print('-----DEBUG------')
            print(f'self.parsed_content_as_dict: {self.parsed_content_as_dict}')
        except IndexError as err:
            print(f'except TypeError:: {err}')
            return self.parsed_content_as_dict
        print(f'ip: {self.host_instance.ip_v4} | resp: {self.parsed_content_as_dict}')
        self.data_for_response = self.parsed_content_as_dict
        return self.data_for_response


class SwarcoStandardParser(BaseSnmpParser):

    def get_processor(self):
        return SwarcoProcessor(
            host_instance=self.host_instance
        )
