import asyncio
import os

import aiohttp

from sdp_lib.management_controllers.http.peek import routes, web_inputs
from sdp_lib.management_controllers.http.peek.management.management_core import SetData, ActuatorAsValue, ActuatorAsChar
from sdp_lib.management_controllers.http.peek.monitoring.inputs import InputsPage


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
        data = {name: 0 for name in self.web_page_obj.parser.parsed_content_as_dict if name in self.mpp_stages_inputs}
        data[web_inputs.mpp_man] = 1
        return data




async def main():
    async with aiohttp.ClientSession() as sess:
        obj = SetInputs(ip_v4='10.179.112.241', session=sess)
        obj = SetInputs(ip_v4='10.179.107.129', session=sess)
        # obj = SetInputs(ip_v4='10.45.154.19')
        # obj = SetInputs(ip_v4='10.179.20.9')

        return await obj.set_stage(0)


if __name__ == '__main__':

    r = asyncio.run(main())
    print(r.response)

