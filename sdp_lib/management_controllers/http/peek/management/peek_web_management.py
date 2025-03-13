import asyncio
import os
from asyncio import TaskGroup
from enum import StrEnum
from typing import Type

import aiohttp
from dotenv import load_dotenv

from sdp_lib.management_controllers.exceptions import ErrorSetValue
from sdp_lib.management_controllers.fields_names import FieldsNames
from sdp_lib.management_controllers.http.peek import routes, web_inputs
from sdp_lib.management_controllers.http.peek.peek_core import PeekWeb
# from sdp_lib.management_controllers.http.peek.monitoring.peek_web_monitoring import InputsPage, T
from sdp_lib.management_controllers.http.peek.monitoring.multiple import T
from sdp_lib.management_controllers.http.peek.monitoring.inputs import InputsPage


load_dotenv()


class PropertiesNames(StrEnum):
    index   = 'index'
    num     = 'num'
    name    = 'name'
    state   = 'state'
    time    = 'time'
    value   = 'value'


class ActuatorAsChar(StrEnum):
    VF     = '-'
    OFF    = 'ВЫКЛ'
    ON     = 'ВКЛ'


class ActuatorAsValue(StrEnum):
    VF     = '0'
    OFF    = '1'
    ON     = '2'


class SetData(PeekWeb):

    web_page_class: Type[T]

    prefix_par_name: str

    INDEX = 0

    def __init__(self, ip_v4: str, session: aiohttp.ClientSession):
        super().__init__(ip_v4=ip_v4, session=session)
        self.web_page_obj: T = self.web_page_class(self.ip_v4, self.session)
        self.method = self.post
        self.data_for_set_to_web = None

    async def set_any_vals(
            self,
            data_to_set: dict[str, str | int],
            start_by_getting_data_from_web_page=False
    ):
        if start_by_getting_data_from_web_page:
            result = await self.get_data_from_web_page_and_set_response_if_has_err()
            if not result:
                return self

        sending_result = await self.create_tasks_and_send_request_to_set_val(
            data_from_web=self.web_page_obj.parser.parsed_content_as_dict,
            data_for_set=data_to_set,
            prefix=self.prefix_par_name,
            index=self.INDEX
        )

        if not self.check_sending_result_and_set_response_if_has_err(sending_result):
            return self

        await self.web_page_obj.get_and_parse()
        # self.response = self.web_page_obj.response
        self.add_data_to_data_response_attrs(*self.web_page_obj.response)
        self.add_data_to_data_response_attrs(data={str(FieldsNames.sent_data): self.data_for_set_to_web})
        print(f'self.data_for_set_to_web: {self.data_for_set_to_web}')

        print(f'self.response: {self.response}')
        return self

    async def get_data_from_web_page_and_set_response_if_has_err(self) -> bool:
        await self.web_page_obj.get_and_parse()
        print(f'self.web_page_obj.ERRORS: {self.web_page_obj.ERRORS}')
        if self.web_page_obj.ERRORS:
            self.add_data_to_data_response_attrs(*self.web_page_obj.response)
            return False
        return True

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

    def check_sending_result_and_set_response_if_has_err(self,sending_result) -> bool:
        if any(res_task.result()[self.RESPONSE] != 200 for res_task in sending_result):
            self.response = ErrorSetValue(), {}
            return False
        return True


class SetInputs(SetData):

    web_page_class = InputsPage
    route = routes.set_inputs
    prefix_par_name = web_inputs.prefix_set_val

    all_mpp_inputs = set(os.getenv('ALL_MPP_INPUTS').split())
    mpp_stages_inputs = set(web_inputs.mpp_stages_inputs.split())

    NUM        = 1
    NAME       = 2
    STATE      = 3
    TIME       = 4
    ACTUATOR   = 5


    async def set_stage(self, stage_value: int):
        result = await self.get_data_from_web_page_and_set_response_if_has_err()
        if not result:
            return self

        self.data_for_set_to_web = self.make_values_to_set_stage(stage_value)
        print(self.data_for_set_to_web)
        print(len(self.data_for_set_to_web))
        return await self.set_any_vals(self.data_for_set_to_web)

    def make_values_to_set_stage(self, stage_value: int) -> dict[str, int]:
        """

        Пример name и props:
        name          -> 'MPP_PH2'
        props         -> ('9', '10', 'MPP_PH2', '1', '1', '-')
        {name: props} ->  {'MPP_PH2': ('9', '10', 'MPP_PH2', '1', '1', '-')}
        :param stage_value:
        :return:
        """
        if stage_value == 0:
            return self.make_values_to_reset_man()

        data = {}
        for name, props in self.web_page_obj.parser.parsed_content_as_dict.items():
            if name in self.mpp_stages_inputs and int(name[-1]) != stage_value:
                data[name] = int(ActuatorAsValue.OFF)

        mpp_man: web_inputs.input_properties = self.web_page_obj.parser.parsed_content_as_dict[web_inputs.mpp_man]
        mpp_stage: web_inputs.input_properties = (
            self.web_page_obj.parser.parsed_content_as_dict[f'{web_inputs.prefix_mpp_stage}{str(stage_value)}']
        )
        if mpp_man[self.STATE] == '0' or mpp_man[self.ACTUATOR] != ActuatorAsChar.ON:
            data[web_inputs.mpp_man] = int(ActuatorAsValue.ON)
        if mpp_stage[self.STATE] == '0' or mpp_stage[self.ACTUATOR] != ActuatorAsChar.ON:
            data[f'{web_inputs.prefix_mpp_stage}{str(stage_value)}'] = int(ActuatorAsValue.ON)

        print(f'part2 data: {data}')
        return data

    def make_values_to_reset_man(self) -> dict[str, int]:
        return {name: 0 for name in self.web_page_obj.parser.parsed_content_as_dict if name in self.all_mpp_inputs}




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
        # r_r = await obj.set_any_vals(data_to_set=inps, start_by_getting_data_from_web_page=True)
        r_r = await obj.set_stage(0)

        print(r_r.response)


    return r_r




if __name__ == '__main__':

    rrr = asyncio.run(main())