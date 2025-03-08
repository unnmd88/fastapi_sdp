import abc
import asyncio
import time
from asyncio import TaskGroup
from typing import Self

import aiohttp
from watchfiles import awatch

from sdp_lib.management_controllers.exceptions import BadControllerType, ConnectionTimeout
from sdp_lib.management_controllers.http.http_core import HttpHost
from sdp_lib.management_controllers.http.parsers_peek import MainPageParser, InputsPageParser
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
        async with session.get(route, timeout=timeout) as response:
            assert response.status == 200
            return await response.text()


class GetData(PeekWeb):
    main_route: str

    async def get_and_parse(
            self,
            session: aiohttp.ClientSession,
    ) -> Self:

        error, content_data = None, {}
        try:
            content = await self.fetch(
                route=f'{self.base_url}{self.main_route}',
                session=session
            )
            parser = self.parser_class(content)
            # parser.parse()
            # content_data = parser.parsed_content_as_dict
            content_data = parser.parse()

        except asyncio.TimeoutError:
            error = ConnectionTimeout()
        except (AssertionError, aiohttp.client_exceptions.ClientConnectorCertificateError):
            error = BadControllerType()
        except aiohttp.client_exceptions.ClientConnectorError:
            error = ConnectionTimeout('from connector')
        self.response = error, content_data
        return self

    @property
    @abc.abstractmethod
    def parser_class(self):
        ...


class MainPage(GetData):

    main_route = '/hvi?file=m001a.hvi&pos1=0&pos2=-1'

    @property
    def parser_class(self):
        return MainPageParser


class InputsPage(GetData):
    main_route = '/hvi?file=cell1020.hvi&pos1=0&pos2=-1'

    # async def get_and_parse(self, session: aiohttp.ClientSession) -> Self:
    #
    #     error, content_data = None, {}
    #     try:
    #         content = await self.fetch(
    #             route=f'{self.base_url}{self.main_route}',
    #             session=session
    #         )
    #         parser = MainPageParser(content)
    #         parser.parse()
    #         content_data = parser.parsed_content_as_dict
    #     except asyncio.TimeoutError:
    #         error = ConnectionTimeout()
    #     except (AssertionError, aiohttp.client_exceptions.ClientConnectorCertificateError):
    #         error = BadControllerType()
    #     except aiohttp.client_exceptions.ClientConnectorError:
    #         error = ConnectionTimeout('from connector')
    #     self.response = error, content_data
    #     return self

    @property
    def parser_class(self):
        return InputsPageParser


class MultipleData(HttpHost):

    available = (MainPage, InputsPage)

    def __init__(
            self,
            ip_v4: str,
            *,
            main_page=None,
            inputs=None
    ):
        super().__init__(ip_v4)
        self.main_page = MainPage if main_page else None
        self.inputs = InputsPage if inputs else None


    async def get_and_parse(self, session):
        match self.available:
            case [self.main_page, self.inputs]:
                print(f'case 1')
                # main_page = MainPage(ip_v4=self.ip_v4)
                # print(f'r1: {main_page}')
                inputs_page = InputsPage(ip_v4=self.ip_v4)
                # print(f'r1: {inputs_page}')

                r = await inputs_page.get_and_parse(session)
                # r2 = await inputs_page.get_and_parse(session)
                # print(f'r1: {inputs_page}')
                # print(f'r2: {r2}')
                return r


                # async with asyncio.TaskGroup() as tg1:
                #     tasks = [tg1.create_task(main_page.get_and_parse(session)),
                #              tg1.create_task(inputs_page.get_and_parse(session)),
                #              ]
                #     print(tasks)
                #     for t in tasks:
                #         print(f't: {t.result()}')



# u = f'http://10.179.16.121/hvi?file=m001a.hvi&pos1=0&pos2=-1'
# main_route = '/hvi?file=m001a.hvi&pos1=0&pos2=-1'

async def main():

    objs = [MultipleData(ip_v4='10.179.16.121', main_page=True, inputs=True)]
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
        print(_r)
        print(_r.result().response)
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
