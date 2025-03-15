from pysnmp.smi.rfc1902 import ObjectType

from sdp_lib.management_controllers.parsers.parsers_core import Parsers


class MainParser(Parsers):

    def __init__(
            self,
            host_instance,
            content: tuple[ObjectType, ...]
    ):
        super().__init__(content)
        self.host_instance = host_instance

    def parse(self) :

        #DEBUG
        # for oid, val in var_binds:
        #     print(f'oid, val: {str(oid)} val: {val.prettyPrint()}')
        #     print(f'type val: {type(val)}')
        #     print(f'type val pretty : {type(val.prettyPrint())}')

        try:
            for oid, val in self.content:
                oid, val = self.host_instance.processing_oid_from_response(str(oid)), val.prettyPrint()
                field_name, fn = self.host_instance.matches.get(oid)
                self.parsed_content_as_dict[str(field_name)] = fn(val)
        except TypeError:
            return self.parsed_content_as_dict
        print(f'ip: {self.host_instance.ip_v4} | resp: {self.parsed_content_as_dict}')
        self.data_for_response = self.parsed_content_as_dict
        return self.data_for_response