import aiohttp


class AsyncClientHTTP:
    def __init__(self, base_url=None, *, timeout: float = 1, **kwargs):
        self._session = aiohttp.ClientSession(
            base_url=base_url,
            timeout=aiohttp.ClientTimeout(timeout),
            **kwargs
        )

    @property
    def timeout(self):
        return self._session.timeout

    @property
    def session(self):
        return self._session

    def close(self):
        self._session.close()

