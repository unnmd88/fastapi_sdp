import abc
import math
from collections.abc import Callable

from pysnmp.smi.rfc1902 import ObjectType

from sdp_lib.management_controllers.fields_names import FieldsNames
from sdp_lib.management_controllers.parsers.parsers_core import Parsers
from sdp_lib.management_controllers.snmp.response_structure import ResponseStructure


class BaseSnmpParser(Parsers):

    stage_values_get: dict

    def __init__(
            self,
            host_instance,
            # content: tuple[ObjectType, ...]
    ):
        super().__init__(content=host_instance.last_response[ResponseStructure.VAR_BINDS])
        self.host_instance = host_instance
        self.current_oid = None
        self.current_val = None

    def call_after_parse_methods(self):
        self.add_extras_to_response()
        self.add_depends_data_to_response()
        self.add_host_protocol_to_response()

    @property
    @abc.abstractmethod
    def matches(self):
        ...

    def add_extras_to_response(self):
        pass

    def add_depends_data_to_response(self):
        pass

    def get_status(self, val):
        pass

    def get_current_mode(self):
        pass

    def get_current_status_mode(self):
        pass

    def convert_val_to_num_stage_get_req(self, val) -> int | None:
        raise NotImplementedError()

    @classmethod
    def convert_hex_to_decimal(cls, val: str) -> int | None:
        """
        Конвертирует значение, полученное из oid фазы в номер фазы десятичного представления
        :param val: значение, необходимое отобразить в десятичном виде
        :return: значение(номер) фазы в десятичном виде
        """

        try:
            if val not in (' ', '@'):
                return int(math.log2(int(val, 16))) + 1
            elif val == ' ':
                return 6
            elif val == '@':
                return 7
        except ValueError:
            print(f'Значение val: {val}')

    def get_val_as_str(self, val) -> str:
        return str(val)

    def processing_oid_from_response(self, oid: str) -> str:
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
            _matches = self.matches
            for oid, val in self.content:
                oid, val = self.processing_oid_from_response(str(oid)), val.prettyPrint()
                field_name, fn = _matches.get(oid)
                self.parsed_content_as_dict[str(field_name)] = fn(val)

            self.call_after_parse_methods()
            # self.add_current_mode_to_response()
            # self.add_extras_to_response()
            # self.add_depends_data_to_response()
            # self.add_host_protocol_to_response()

            print('-----DEBUG------')

            # self.parse_varbinds_base(self.content)
            # self.parsed_content_as_dict[str(FieldsNames.curr_mode)] = self.get_current_mode()
        except TypeError as err:
            print(f'except TypeError:: {err}')
            return self.parsed_content_as_dict
        print(f'ip: {self.host_instance.ip_v4} | resp: {self.parsed_content_as_dict}')
        self.data_for_response = self.parsed_content_as_dict
        return self.data_for_response


class SnmpSetRequestParser(BaseSnmpParser):

    def get_current_status_mode(self):
        pass