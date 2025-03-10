import asyncio
import os

import aiohttp
from dotenv import load_dotenv

from sdp_lib.management_controllers.exceptions import ConnectionTimeout, BadControllerType
from sdp_lib.management_controllers.http.http_core import HttpHost


load_dotenv()


class PeekWeb(HttpHost):

    cookies = {os.getenv('peek_web_k'): os.getenv('peek_web_v')}

    async def fetch(
            self,
            url: str,
            session: aiohttp.ClientSession,
            timeout: aiohttp.ClientTimeout = aiohttp.ClientTimeout(connect=.6)
    ) -> str:
        async with session.get(url, timeout=timeout) as response:
            assert response.status == 200
            return await response.text()

    async def post(
            self,
            session: aiohttp.ClientSession,
            url: str,
            payload: dict[str, str],
            timeout: aiohttp.ClientTimeout = aiohttp.ClientTimeout(connect=1)
    ) -> int:
        async with session.post(
                url,
                cookies=self.cookies,
                data=payload,
                timeout=timeout
        ) as response:
            assert response.status == 200
            print(f'response.status == {response.status}')

            # raise TimeoutError
            # raise TypeError
            return response.status

            print(f'response.status == {response.status}')
            print(f'response.host == {response.host}')
            print(f'response.ok == {response.ok}')
            print(f'response.ok == {response.history}')
            return await response.text()

