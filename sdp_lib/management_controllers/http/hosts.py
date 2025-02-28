from sdp_lib.management_controllers.hosts import Host


class HttpHost(Host):
    def __init__(self, ip_v4: str):
        super().__init__(ip_v4)
        self.base_url = f'http://{self.ip_v4}'