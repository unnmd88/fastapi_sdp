import abc
import asyncio
import time
from typing import Self, TypeVar, Coroutine, Type
from asyncio import TaskGroup, Task

import aiohttp

from sdp_lib.management_controllers.exceptions import BadControllerType, ConnectionTimeout
from sdp_lib.management_controllers.http.peek.parsers_peek import Parser, MainPageParser, InputsPageParser
from sdp_lib.management_controllers.http.peek.peek_core import PeekWeb


P = TypeVar('P', bound=Parser, covariant=True)


class GetData(PeekWeb):

    main_route: str

    def __repr__(self):
        return f'repr_{self.__class__}'

    async def get_and_parse(
            self,
            session: aiohttp.ClientSession,
    ) -> Self:

        error, content_data = None, {}
        try:
            content = await self.fetch(
                url=f'{self.base_url}{self.main_route}',
                session=session
            )
            self.parser = self.parser_class(content)
            # content_data = parser.parse()
            self.parser.parse()

        except asyncio.TimeoutError:
            error = ConnectionTimeout()
        except (AssertionError, aiohttp.client_exceptions.ClientConnectorCertificateError):
            error = BadControllerType()
        except aiohttp.client_exceptions.ClientConnectorError:
            error = ConnectionTimeout('from connector')
        self.response = error, self.parser.parsed_content_as_dict or {}
        return self

    @property
    @abc.abstractmethod
    def parser_class(self) -> Type[P]:
        ...


class MainPage(GetData):

    main_route = '/hvi?file=m001a.hvi&pos1=0&pos2=-1'

    @property
    def parser_class(self) -> Type[MainPageParser]:
        return MainPageParser


class InputsPage(GetData):
    main_route = '/hvi?file=cell1020.hvi&pos1=0&pos2=-1'

    @property
    def parser_class(self) -> Type[InputsPageParser]:
        return InputsPageParser


T = TypeVar('T', bound=GetData, covariant=True)


class MultipleData(PeekWeb):
    """
    Класс запросов для получения данных различных веб страниц(маршрутов)
    одного контроллера.
    """

    async def get_and_parse(
            self,
            session,
            *,
            main_page=True,
            inputs_page=True
    ):
            tasks = self._get_tasks(session, main_page, inputs_page)
            async with asyncio.TaskGroup() as tg1:
                result = [tg1.create_task(_coro) for _coro in tasks]
            self.response = self.merge_all_responses(result)

            print(f'self.response: {self.response}')
            return self

    def _get_tasks(
            self,
            session: aiohttp.ClientSession,
            main_page: bool,
            inputs_page: bool
    ) -> tuple[Coroutine, ...]:

        match [main_page, inputs_page]:
            case [True, True]:
                return (
                    MainPage(ip_v4=self.ip_v4).get_and_parse(session),
                    InputsPage(ip_v4=self.ip_v4).get_and_parse(session)
                )
            case [True, False]:
                return (MainPage(ip_v4=self.ip_v4).get_and_parse(session), )
            case [False, True]:
                return (InputsPage(ip_v4=self.ip_v4).get_and_parse(session),)
            case _:
                raise ValueError('Не предоставлено данных')

    def merge_all_responses(self, results: list[Task]) -> tuple[None | str, dict]:

        error,response = None, {}
        for r in results:
            curr_err, curr_res = r.result().response
            response |= curr_res
            error = curr_err or error
        return error, response


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
