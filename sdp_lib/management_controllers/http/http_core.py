import abc

import aiohttp

from sdp_lib.management_controllers.fields_names import FieldsNames
from sdp_lib.management_controllers.hosts import Host


class HttpHost(Host):

    route: str

    def __init__(
            self,
            *,
            ip_v4: str = None,
            session: aiohttp.ClientSession = None
    ):
        super().__init__(ip_v4=ip_v4)
        self._base_url = f'http://{self.ip_v4}'
        self._session = session
        # self.full_url = f'{self.base_url}{self.main_route}'
        self.method = None
        self.parser = None

    def set_session(self, session: aiohttp.ClientSession):
        if isinstance(session, aiohttp.ClientSession):
            self._session = session

    def set_base_url(self):
        if isinstance(self.ip_v4, str):
            self._base_url = f'http://{self.ip_v4}'

    @property
    def base_url(self):
        return self._base_url

    @property
    def full_url(self) -> str:
        if isinstance(self._base_url, str) and isinstance(self.route, str):
            return f'{self._base_url}{self.route}'

    @property
    def protocol(self):
        return str(FieldsNames.protocol_http)


