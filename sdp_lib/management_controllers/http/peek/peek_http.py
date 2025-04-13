import asyncio
from enum import IntEnum, StrEnum
from functools import cached_property
from typing import Callable, Type

import aiohttp
from mypyc.ir.ops import TypeVar

from sdp_lib.management_controllers.exceptions import BadControllerType
from sdp_lib.management_controllers.http.http_core import HttpHosts
from sdp_lib.management_controllers.http.peek import routes, static_data
from sdp_lib.management_controllers.http.peek.static_data import cookies
from sdp_lib.management_controllers.http.peek.varbinds import InputsVarbinds
from sdp_lib.management_controllers.parsers.parsers_peek_http_new import MainPageParser, InputsPageParser, \
    InputsPageParserSet
from sdp_lib.management_controllers.response_structure import HttpResponseStructure


T_Parsers = TypeVar('T_Parsers', MainPageParser, InputsPageParser)


class AvailableDataFromWeb(IntEnum):

    main_page_get     = 1
    inputs_page_get   = 2
    inputs_page_set   = 3



class ActuatorAsChar(StrEnum):
    VF     = '-'
    OFF    = 'ВЫКЛ'
    ON     = 'ВКЛ'


class ActuatorAsValue(StrEnum):
    VF     = '0'
    OFF    = '1'
    ON     = '2'


class PeekWebHosts(HttpHosts):

    @cached_property
    def matches(self) -> dict[AvailableDataFromWeb, tuple[str, Callable, Type[T_Parsers]]]:
        return {
            AvailableDataFromWeb.main_page_get: (routes.main_page, self._request_sender.fetch, MainPageParser),
            AvailableDataFromWeb.inputs_page_get: (routes.get_inputs, self._request_sender.fetch, InputsPageParser),
            AvailableDataFromWeb.inputs_page_set: (routes.set_inputs, self._request_sender.post_request, InputsPageParserSet),
        }

    async def _single_common_request(
            self,
            url,
            method: Callable,
            parser,
            **kwargs
    ):
        self.last_response = await self._request_sender.http_request_to_host(
            url=url,
            method=method,
            **kwargs
        )
        if self.check_http_response_errors_and_add_to_host_data_if_has():
            return self

        parser.parse(self.last_response[HttpResponseStructure.CONTENT])
        print(f'parser.data_for_response: {parser.data_for_response}')
        if not parser.data_for_response:
            self.add_data_to_data_response_attrs(error=BadControllerType())
        else:
            self.add_data_to_data_response_attrs(
                data=parser.data_for_response
            )
        return self

    async def fetch_all_pages(self, *args, **kwargs):
        async with asyncio.TaskGroup() as tg:
            for page in args:
                route, method, parser_class = self.matches.get(page)
                tg.create_task(
                    self._single_common_request(
                        self._base_url + route, method, parser_class(),
                        **kwargs
                    )
                )
        if self.response_errors:
            self.remove_data_from_response()
        return self

    async def get_states(self):
        return await self.fetch_all_pages(AvailableDataFromWeb.main_page_get)

    async def get_inputs(self):
        return await self.fetch_all_pages(AvailableDataFromWeb.inputs_page_get)

    async def post_all_pages(self, page, payload_data: tuple[dict, ...]):
        async with asyncio.TaskGroup() as tg:
            route, method, parser_class = self.matches.get(page)
            for payload in payload_data:
                tg.create_task(
                    self._single_common_request(
                        self._base_url + route, method, parser_class(),
                        cookies=static_data.cookies,
                        data=payload
                    )
                )

        if self.response_errors:
            self.remove_data_from_response()
        return self



    async def set_inputs_to_web(self, *args, **kwargs):

        # Метод, котрый из аргуметов собирает payloads
        await self.get_inputs()
        if self.response_errors:
            return self
        _inputs = self.response_as_dict['data']['inputs']
        # print(f'self.response_as_dict: {self.response_as_dict['data']['inputs']}')
        # print(f'INPMS: {_inputs}')
        # payloads = ({'par_name': f'XIN.R20/12', 'par_value': '1'},
        #             {'par_name': f'XIN.R20/16', 'par_value': '1'}
        #             )

        await self.post_all_pages(AvailableDataFromWeb.inputs_page_set,
                                  payload_data=InputsVarbinds.get_set_stage_varbinds(_inputs, 1))


async def main():
    try:
        sess = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(1))
        obj = PeekWebHosts('10.179.107.129', host_id='2406', session=sess)
        # await obj.get_states()
        # await obj.request_all_types(AvailableDataFromWeb.main_page_get)
        await obj.set_inputs_to_web()
        # await obj.get_states()
    finally:
        await sess.close()

    # print(obj)




if __name__ == '__main__':
    res = asyncio.run(main())