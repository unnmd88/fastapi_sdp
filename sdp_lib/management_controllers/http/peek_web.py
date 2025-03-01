import asyncio
import time
from asyncio import TaskGroup
from typing import Self

import aiohttp
from dulwich.porcelain import fetch

from sdp_lib.management_controllers.exceptions import BadControllerType, ConnectionTimeout
from sdp_lib.management_controllers.http.hosts import HttpHost
from sdp_lib.management_controllers.http.parsers_peek import MainPageParser
from sdp_lib.management_controllers.fields_names import FieldsNames
from sdp_lib.management_controllers.controller_modes import NamesMode
# from sdp_lib.management_controllers.http.session import ClientHTTP


class PeekWeb(HttpHost):

    async def fetch(
            self,
            route: str,
            session: aiohttp.ClientSession,
            timeout: aiohttp.ClientTimeout = aiohttp.ClientTimeout(connect=.6)
    ) -> str:
        async with session.get(route, timeout=timeout) as responce:
            assert responce.status == 200
            return await responce.text()


class MainPage(PeekWeb):

    main_route = '/hvi?file=m001a.hvi&pos1=0&pos2=-1'

    async def get_and_parse(self, session: aiohttp.ClientSession) -> Self:

        error, content_data = None, {}
        try:
            content = await self.fetch(
                route=f'{self.base_url}{self.main_route}',
                session=session
            )
            parser = MainPageParser(content)
            parser.parse()
            content_data = parser.parsed_content_as_dict
        except asyncio.TimeoutError:
            error = ConnectionTimeout()
        except (AssertionError, aiohttp.client_exceptions.ClientConnectorCertificateError):
            error = BadControllerType()
        except aiohttp.client_exceptions.ClientConnectorError:
            error = ConnectionTimeout('from connector')
        self.response = error, content_data
        return self

u = f'http://10.179.16.121/hvi?file=m001a.hvi&pos1=0&pos2=-1'
main_route = '/hvi?file=m001a.hvi&pos1=0&pos2=-1'

async def main():
    # o = [PeekWeb(ip_v4='10.179.16.81') for _ in range(10)]

    objs = [MainPage(ip_v4='10.179.16.121')]
    session_timeout = aiohttp.ClientTimeout(total=1, connect=0.4)

    async with aiohttp.ClientSession(timeout=session_timeout) as sess:
        try:
            async with TaskGroup() as tg:
                # r = [tg.create_task(coro=o.fetch(f'{o.base_url}{main_route}', sess)) for o in objs]
                r = [tg.create_task(coro=o.get_and_parse(sess)) for o in objs]
        except:
            pass
    for _r in r:
        pass
        # print(_r.result().splitlines())
        print(repr(_r.result()))
        print(_r.result())
        # print(f'{_r.exception()!r}')
        print(f'{_r.cancelled()!r}')
    return r


if __name__ == '__main__':

    start_time = time.time()
    res = asyncio.run(
        main()
    )
    print(f'res:: {res}')

    print(f'Время выполнения составило >> {time.time() - start_time}')
