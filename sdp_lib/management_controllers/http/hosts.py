from sdp_lib.management_controllers.fields_names import FieldsNames
from sdp_lib.management_controllers.hosts import Host


class HttpHost(Host):
    def __init__(self, ip_v4: str):
        super().__init__(ip_v4)
        self.base_url = f'http://{self.ip_v4}'

    @property
    def host_protocol(self):
        return str(FieldsNames.protocol_http)