import abc
import asyncio
import os
from asyncio import TaskGroup
from enum import StrEnum
from typing import Self, Type

import aiohttp
from dotenv import load_dotenv

from sdp_lib.management_controllers.exceptions import ConnectionTimeout, BadControllerType, ErrorSetValue
from sdp_lib.management_controllers.http.peek import routes, web_inputs
from sdp_lib.management_controllers.http.peek.peek_core import PeekWeb
from sdp_lib.management_controllers.http.peek.peek_web_monitoring import MultipleData, InputsPage, T


load_dotenv()


class PropertiesNames(StrEnum):
    index = 'index'
    num = 'num'
    name = 'name'
    state = 'state'
    time = 'time'
    value = 'value'


class SetData(PeekWeb):

    web_page_class: Type[T]

    INDEX = 0

    def __init__(self, ip_v4: str, session: aiohttp.ClientSession):
        super().__init__(ip_v4=ip_v4, session=session)
        self.web_page_obj: T = self.web_page_class(self.ip_v4, self.session)
        self.method = self.post

    async def create_tasks_and_send_request_to_set_val(
            self,
            *,
            data_from_web: dict[str, str],
            data_for_set: dict[str, int],
            prefix: str,
            index: int
    ):
        async with TaskGroup() as tg:
            res = [
                tg.create_task(
                    self.http_request_to_host(
                        payload=self.get_payload(inp, val, data_from_web, prefix, index)
                    )
                )
                    for inp, val in data_for_set.items()
            ]
        return res

    def get_payload(
            self,
            inp_name: str,
            val: float,
            data: dict,
            prefix: str,
            index: int | None
    ):
        param_index = '' if index is None else data.get(inp_name)[index]
        return {'par_name': f'{prefix}{param_index}', 'par_value': val}

    async def get_data_from_web_page_and_set_response_if_has_err(self) -> bool:
        await self.web_page_obj.get_and_parse()
        if self.web_page_obj.response[self.ERROR] is not None:
            self.response = self.web_page_obj.response
            return False
        return True

    def check_sending_result_and_set_response_if_has_err(self,sending_result) -> bool:
        if any(res_task.result()[self.RESPONSE] != 200 for res_task in sending_result):
            self.response = ErrorSetValue(), {}
            return False
        return True


class SetInputs(SetData):

    web_page_class = InputsPage

    route = routes.set_inputs
    prefix_inputs = web_inputs.prefix_set_val

    all_mpp_inputs = set(os.getenv('ALL_MPP_INPUTS').split())
    mpp_stages_inputs = set(os.getenv('MPP_STAGES_INPUTS').split())

    prefix_man_stage = web_inputs.prefix_man_stage
    matches_name_inp_to_num_stage = {num: f'{web_inputs.prefix_man_stage}{num}' for num in range(1, 9)}

    NUM, NAME, STATE, TIME, VALUE = range(1, 6)

    async def set_any_vals(self, data_to_set: dict[str, str | int]):
        result = await self.get_data_from_web_page_and_set_response_if_has_err()
        if not result:
            return self

        sending_result = await self.create_tasks_and_send_request_to_set_val(
            data_from_web=self.web_page_obj.parser.data_for_response,
            data_for_set=data_to_set,
            prefix=self.prefix_inputs,
            index=self.INDEX
        )

        if not self.check_sending_result_and_set_response_if_has_err(sending_result):
            return self

        await self.web_page_obj.get_and_parse()
        self.response = self.web_page_obj.response
        return self


    async def set_stage(self, value: int):
        await self.web_page_obj.get_and_parse()
        err, response = self.web_page_obj.response
        if err is not None:
            self.response = err, response
            return self



async def main():

    async with aiohttp.ClientSession() as sess:
        obj = SetInputs(ip_v4='10.179.112.241', session=sess)
        obj = SetInputs(ip_v4='10.179.107.129', session=sess)
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
        r_r = await obj.set_any_vals(data_to_set=inps)

        print(r_r.response)


    return r_r




if __name__ == '__main__':

    rrr = asyncio.run(main())