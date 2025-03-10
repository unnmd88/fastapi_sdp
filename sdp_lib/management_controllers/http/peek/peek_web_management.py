import abc
import asyncio
import os
from asyncio import TaskGroup
from typing import Self, Type

import aiohttp
from dotenv import load_dotenv

from sdp_lib.management_controllers.exceptions import ConnectionTimeout, BadControllerType, ErrorSetValue
from sdp_lib.management_controllers.http.peek import routes
from sdp_lib.management_controllers.http.peek.peek_core import PeekWeb
from sdp_lib.management_controllers.http.peek.peek_web_monitoring import MultipleData, InputsPage, T


load_dotenv()


class SetData(PeekWeb):

    # main_route: str

    def __init__(self, ip_v4: str):
        super().__init__(ip_v4=ip_v4)
        self.get_data_from_web_page_obj: T = self.get_web_page_obj()

    async def set_and_parse(
            self,
            url,
            session,
            payload
    ) -> Self:

        error, req_status = None, None
        try:
            req_status = await self.post(
                url=url,
                session=session,
                payload=payload
            )
        except asyncio.TimeoutError:
            error = ConnectionTimeout()
        except (AssertionError, aiohttp.client_exceptions.ClientConnectorCertificateError):
            error = BadControllerType()
        except aiohttp.client_exceptions.ClientConnectorError:
            error = ConnectionTimeout('from connector')
        self.response = error, req_status
        return self

    @abc.abstractmethod
    def get_web_page_obj(self) -> T:
        ...


class SetInputs(SetData):

    route = routes.set_inputs
    prefix_inputs = os.getenv('INPUT_PREFIX_FOR_SET_VAL')

    INDEX, NUM, NAME, STATE, TIME, VALUE = range(6)
    RESULT = 1

    def get_web_page_obj(self) -> T:
        return InputsPage(self.ip_v4)

    async def set_any_vals(
            self,
            session,
            inps: dict[str, str | int]
    ):
        await self.get_data_from_web_page_obj.get_and_parse(session)
        err, response = self.get_data_from_web_page_obj.response
        if err is not None:
            self.response = err, response
            return self
        async with TaskGroup() as tg2:
            res = [
                tg2.create_task(
                    self.set_and_parse(session=session, url=self.full_url, payload=self._get_payload(inp, val)))
                    for inp, val in inps.items()
            ]
        if any(res_task.result().response[self.RESULT] != 200 for res_task in res):
            self.response = ErrorSetValue(), {}
            return self
        await self.get_data_from_web_page_obj.get_and_parse(session)
        self.response = self.get_data_from_web_page_obj.response
        return self

    def _get_payload(self, inp_name, val, inp_index=None):
        if inp_index is None:
            inp_index = self.get_data_from_web_page_obj.parser.inputs_from_page.get(inp_name)[self.INDEX]
        return {'par_name': f'{self.prefix_inputs}{inp_index}', 'par_value': val}


async def main():



    async with aiohttp.ClientSession() as sess:
        obj = SetInputs(ip_v4='10.179.112.241')
        # obj = SetInputs(ip_v4='10.45.154.19')
        # obj = SetInputs(ip_v4='10.179.20.9')
        v = 1
        inps = {
            'MPP_PH1': v,
            'MPP_PH2': v,
            'MPP_PH3': v,
            'MPP_PH4': v,
            'MPP_PH5': v,
            'MPP_PH6': v,
            'MPP_PH7': v,
            'MPP_PH8': v,

        }
        # r_r = asyncio.create_task(obj.set_vals(session=sess, inps=inps))
        # r_r = await obj.set_vals(session=sess, inps=inps)
        r_r = await obj.set_any_vals(session=sess, inps=inps)

        print(r_r.response)


    return r_r




if __name__ == '__main__':
    rrr = asyncio.run(main())