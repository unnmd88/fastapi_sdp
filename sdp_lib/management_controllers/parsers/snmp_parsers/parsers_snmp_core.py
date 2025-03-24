import abc
import math

from pysnmp.smi.rfc1902 import ObjectType

from sdp_lib.management_controllers.fields_names import FieldsNames
from sdp_lib.management_controllers.parsers.parsers_core import Parsers


class BaseSnmpParser(Parsers):

    stage_values_get: dict
    protocol_: str
    # stage_values_set: dict

    def __init__(
            self,
            host_instance,
            content: tuple[ObjectType, ...]
    ):
        super().__init__(content)
        self.host_instance = host_instance
        self.current_oid = None
        self.current_val = None

    @property
    @abc.abstractmethod
    def matches(self):
        ...

    @classmethod
    def host_protocol(cls):
        return cls.protocol_

    def get_current_mode(self):
        raise NotImplementedError()

    def get_status(self, val):
        raise NotImplementedError()

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

    @classmethod
    def get_val_as_str(cls, val) -> str:
        return str(val)

    @classmethod
    def processing_oid_from_response(cls, oid: str) -> str:
        return oid

    @classmethod
    def parse_varbinds_base(cls, varbinds: tuple[ObjectType, ...]):
        for oid, val in varbinds:
            oid, val = str(oid), val.prettyPrint()
            print(f'oid: {oid}  >>>> val: {val}')

    def parse(self) : # Рефакторинг

        try:
            _matches = self.matches
            for oid, val in self.content:
                oid, val = self.processing_oid_from_response(str(oid)), val.prettyPrint()
                field_name, fn = _matches.get(oid)
                self.parsed_content_as_dict[str(field_name)] = fn(val)
            self.parsed_content_as_dict[str(FieldsNames.curr_mode)] = self.get_current_mode()
        except TypeError:
            return self.parsed_content_as_dict
        print(f'ip: {self.host_instance.ip_v4} | resp: {self.parsed_content_as_dict}')
        self.data_for_response = self.parsed_content_as_dict
        return self.data_for_response



