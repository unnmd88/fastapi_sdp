import asyncio
import os
from asyncio import TaskGroup

import aiohttp
from dotenv import load_dotenv

from sdp_lib.management_controllers.http.peek.peek_web_monitoring import MultipleData, InputsPage

load_dotenv()


class SetInputs(InputsPage):

    route_set_inp = os.getenv('ROUTE_SET_INPUTS')
    prefix_inputs = os.getenv('INPUT_NAME_FOR_SET_VAL')

    INDEX, NUM, NAME, STATE, TIME, VALUE = range(6)


    async def set_vals(self, session, inps: dict[str, str] = None):
        url = f'{self.base_url}{self.route_set_inp}'
        # payload = {'par_name': f'{self.prefix_inputs}16', 'par_value': '0'}


        # request_inputs = await MultipleData(ip_v4=self.ip_v4).get_and_parse(session, main_page=False)
        await self.get_and_parse(session)
        err, inputs = self.response
        print(self.parser.inputs_from_page)

        if err is not None:
            self.response = err, inputs
            return self

        async with TaskGroup() as tg2:
            res = [
                tg2.create_task(
                    self.post(session=session, url=url, payload=self._get_payload(inp, val)))
                    for inp, val in inps.items()
            ]
        print(f'err: {err}\ninputs: {inputs}')

        return res



        # res = await self.post(
        #     session=session,
        #     url=url,
        #     payload=payload
        # )
        # return res

    def _get_payload(self, inp_name, val):
        inp_index = self.parser.inputs_from_page.get(inp_name)[self.parser.INDEX]
        # print({'par_name': f'{self.prefix_inputs}{inp_index}', 'par_value': val})
        return {'par_name': f'{self.prefix_inputs}{inp_index}', 'par_value': val}





async def main():



    async with aiohttp.ClientSession() as sess:
        obj = SetInputs(ip_v4='10.179.112.241')
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

        r = await asyncio.create_task(obj.set_vals(session=sess, inps=inps))
        print(r)
    return r




if __name__ == '__main__':
    rrr = asyncio.run(main())