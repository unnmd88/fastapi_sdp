from pysnmp.smi.rfc1902 import ObjectType

from sdp_lib.management_controllers.parsers.parsers_core import Parsers


class MainParser(Parsers):

    def __init__(
            self,
            instance,
            content: tuple[ObjectType, ...]
    ):
        super().__init__(content)
        self.instance = instance

    def parse(self) :

        try:
            for oid, val in self.content:
                oid, val = self.instance.processing_oid_from_response(str(oid)), val.prettyPrint()
                field_name, fn = self.instance.matches.get(oid)
                self.parsed_content_as_dict[str(field_name)] = fn(val)
        except TypeError:
            return self.parsed_content_as_dict
        print(f'ip: {self.instance.ip_v4} | resp: {self.parsed_content_as_dict}')
        self.data_for_response = self.parsed_content_as_dict
        return self.data_for_response