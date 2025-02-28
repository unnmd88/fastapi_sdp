import aiohttp


class ClientHTTP:
    session = aiohttp.ClientSession()

    def __init__(self):
        self._session = aiohttp.ClientSession()

    @classmethod
    def get_session(cls):
        return cls.session