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

    def __init__(self, ip_v4: str, session: aiohttp.ClientSession):
        super().__init__(ip_v4=ip_v4, session=session)
        self.get_data_from_web_page_obj: T = self.get_web_page_obj()

    @abc.abstractmethod
    def get_web_page_obj(self) -> T:
        ...

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

    async def create_tasks_and_send_request_to_set_val(
            self,
            session: aiohttp.ClientSession,
            data_from_web: dict[str, str],
            data_for_set: dict[str, str],
            prefix: str,
            index: int
    ):
        async with TaskGroup() as tg:
            res = [
                tg.create_task(
                    self.set_and_parse(
                        session=session,
                        url=self.full_url,
                        payload=self.get_payload(inp, val, data_from_web, prefix, index)
                    )
                )
                    for inp, val in data_for_set.items()
            ]
        return res

    def get_payload(
            self,
            inp_name,
            val,
            data,
            prefix,
            index
    ):
        param_index = data.get(inp_name)[index]
        return {'par_name': f'{prefix}{param_index}', 'par_value': val}

class SetInputs(SetData):

    route = routes.set_inputs
    prefix_inputs = os.getenv('INPUT_PREFIX_FOR_SET_VAL')


    all_mpp_inputs = set(os.getenv('ALL_MPP_INPUTS').split())
    mpp_stages_inputs = set(os.getenv('MPP_STAGES_INPUTS').split())

    prefix_man_stage = os.getenv('PREFIX_MAN_STAGE_PEEK')
    matches_name_inp_and_num_stage = {num: f'{prefix_man_stage}{num}' for num in range(1, 9)}


    INDEX, NUM, NAME, STATE, TIME, VALUE = range(6)
    RESULT = 1

    def get_web_page_obj(self) -> T:
        return InputsPage(self.ip_v4, self.session)

    async def get_data_and_set_response(self):
        await self.get_data_from_web_page_obj.get_and_parse(session)
        err, response = self.get_data_from_web_page_obj.response
        if err is not None:
            self.response = err, response

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

        result = await self.create_tasks_and_send_request_to_set_val(
            session=session,
            data_from_web=self.get_data_from_web_page_obj.parser.inputs_from_page,
            data_for_set=inps,
            prefix=self.prefix_inputs,
            index=self.INDEX
        )

        if any(res_task.result().response[self.RESULT] != 200 for res_task in result):
            self.response = ErrorSetValue(), {}
            return self
        await self.get_data_from_web_page_obj.get_and_parse(session)
        self.response = self.get_data_from_web_page_obj.response
        return self

    async def set_stage(self,session, value: int):
        await self.get_data_from_web_page_obj.get_and_parse(session)
        err, response = self.get_data_from_web_page_obj.response
        if err is not None:
            self.response = err, response
            return self



async def main():

    async with aiohttp.ClientSession() as sess:
        obj = SetInputs(ip_v4='10.179.112.241')
        # obj = SetInputs(ip_v4='10.45.154.19')
        # obj = SetInputs(ip_v4='10.179.20.9')
        v = 0
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