import abc
from sdp_lib.management_controllers.fields_names import FieldsNames
from sdp_lib.management_controllers.parsers.parsers_core import Parsers
from sdp_lib.management_controllers.parsers.snmp_parsers.processors import (
    SwarcoProcessor,
    PotokPProcessor, PotokSProcessor
)
from sdp_lib.management_controllers.snmp.response_structure import SnmpResponseStructure


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
        # self._processor_config = host_instance.processor_config
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


class PotokSStandardParser(BaseSnmpParser):

    def get_processor(self):
        return PotokSProcessor(
            host_instance=self.host_instance
        )


class PotokPStandardParser(BaseSnmpParser):

    def get_processor(self):
        return PotokPProcessor(
            host_instance=self.host_instance
        )