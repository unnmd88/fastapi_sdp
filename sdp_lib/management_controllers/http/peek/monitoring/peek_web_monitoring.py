import asyncio
import time
from typing import Self, TypeVar, Coroutine, Type
from asyncio import TaskGroup, Task

import aiohttp

from sdp_lib.management_controllers.exceptions import BadControllerType, ConnectionTimeout
from sdp_lib.management_controllers.http.peek import routes
from sdp_lib.management_controllers.http.peek.parsers_peek import Parser, MainPageParser, InputsPageParser
from sdp_lib.management_controllers.http.peek.peek_core import PeekWeb


P = TypeVar('P', bound=Parser, covariant=True)


class GetData(PeekWeb):

    parser_class: Type[P]

    def __init__(self, ip_v4: str, session: aiohttp.ClientSession):
        super().__init__(ip_v4, session)
        self.method = self.fetch

    @classmethod
    def get_parser_obj(cls, content: str) -> P:
        """
        Возвращает объект класса парсера.
        :param content: Контент веб страницы, который будет
                        передан конструктору класса cls.parser_class.
        :return: Экземпляр класса парсера.
        """
        return cls.parser_class(content)

    def __repr__(self):
        return (
            f'cls.parser_class: {self.parser_class}\n'
            f'self.parser: {self.parser}\n'
            f'self.response: {self.response}\n'
            f'self.method: {self.method.__name__}'
        )

    # async def http_request_to_host(self) -> tuple[Exception | None, str | None]:
    #     """
    #     Совершает http запрос получения контента веб страницы.
    #     :return: Кортеж из 2 объектов:
    #              [0] -> экземпляр производного класса от Exception
    #              при ошибке в получении контента, иначе None.
    #              [1] -> контент веб страницы типа str, если запрос выполнен успешно, иначе None.
    #     """
    #
    #     error = content = None
    #     try:
    #         content = await self.fetch(
    #             url=self.full_url,
    #             session=self.session
    #         )
    #     except asyncio.TimeoutError:
    #         error = ConnectionTimeout()
    #     except (AssertionError, aiohttp.client_exceptions.ClientConnectorCertificateError):
    #         error = BadControllerType()
    #     except aiohttp.client_exceptions.ClientConnectorError:
    #         error = ConnectionTimeout('from connector')
    #     return error, content

    async def get_and_parse(self) -> Self:
        """
        Получает контент, парсит его для вычленения данных.
        :return: Self.
        """
        error, content_data = await self.http_request_to_host()
        if error is None:
            self.parser = self.get_parser_obj(content_data)
            self.parser.parse()
        else:
            self.parser = None

        self.add_data_to_data_response_attrs(error, self.parser.data_for_response)
        return self

    # def set_response_attrs(self, error: Exception | None, parser: P | None) -> None:
    #     """
    #     Присваивает атрибуту self.response данные, на основании
    #     переданных аргументов.
    #     :param error: None или экземпляр производного класса от Exception.
    #     :param parser: instance экземпляра парсера, который хранит в своих атрибутах
    #                    распарсенные данный веб контента. parsed_content_as_dict
    #     :return: None.
    #     """
    #     if error is None and parser is not None:
    #         self.ERROR, self.DATA_RESPONSE = error, self.add
    #     else:
    #         self.ERROR, self.DATA_RESPONSE = error,  {}


class MainPage(GetData):

    route = routes.main_page
    parser_class = MainPageParser


class InputsPage(GetData):

    route = routes.get_inputs
    parser_class = InputsPageParser


T = TypeVar('T', bound=GetData, covariant=True)


class MultipleData(PeekWeb):
    """
    Класс запросов для получения данных различных веб страниц(маршрутов)
    одного контроллера.
    """

    async def get_and_parse(
            self,
            *,
            main_page=True,
            inputs_page=True
    ):
            tasks = self._get_tasks(main_page, inputs_page)
            async with asyncio.TaskGroup() as tg1:
                result = [tg1.create_task(_coro) for _coro in tasks]
            self.add_data_to_data_response_attrs(*self.merge_all_errors_and_responses(result))
            return self

    def _get_tasks(
            self,
            main_page: bool,
            inputs_page: bool
    ) -> list[Coroutine]:
        """
        Собирает список задач(корутин).
        :param main_page: Требуется ли задача с получением контента основной страницы.
        :param inputs_page: Требуется ли задача с получением контента ВВОДОВ.
        :return: Список с задачами(корутинами).
        """
        match [main_page, inputs_page]:
            case [True, True]:
                return [
                    MainPage(self.ip_v4, self.session).get_and_parse(),
                    InputsPage(self.ip_v4, self.session).get_and_parse()
                ]
            case [True, False]:
                return [MainPage(self.ip_v4, self.session).get_and_parse()]
            case [False, True]:
                return [InputsPage(self.ip_v4, self.session).get_and_parse()]
            case _:
                raise ValueError('Не предоставлено данных')

    def merge_all_errors_and_responses(self, results: list[Task]) -> tuple[None | str, dict]:
        """
        Объединяет словари с распарсенными данными контента веб страницы.
        :param results: Список с завершёнными задачами.
        :return:
        """
        error,response = None, {}
        for r in results:
            curr_err, curr_res = r.result().response
            response |= curr_res
            error = curr_err or error
        return error, response # Fix me

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
