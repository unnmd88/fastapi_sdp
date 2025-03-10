import abc

from sdp_lib.management_controllers.fields_names import FieldsNames
from sdp_lib.management_controllers.hosts import Host


class HttpHost(Host):

    route: str

    def __init__(self, ip_v4: str):
        super().__init__(ip_v4)
        self.base_url = f'http://{self.ip_v4}'
        # self.full_url = f'{self.base_url}{self.main_route}'
        self.parser = None

    @property
    def full_url(self) -> str:
        return f'{self.base_url}{self.route}'

    @property
    def protocol(self):
        return str(FieldsNames.protocol_http)


