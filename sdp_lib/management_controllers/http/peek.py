import asyncio
import time
from asyncio import TaskGroup

import aiohttp

from sdp_lib.management_controllers.http.hosts import HttpHost
from sdp_lib.management_controllers.responce import FieldsNames
from sdp_lib.management_controllers.controller_modes import NamesMode
# from sdp_lib.management_controllers.http.session import ClientHTTP


class PeekWeb(HttpHost):

    async def fetch(
            self,
            route: str,
            session: aiohttp.ClientSession,
            timeout: aiohttp.ClientTimeout = aiohttp.ClientTimeout(connect=.6)
    ):
        async with session.get(route, timeout=timeout) as responce:
            if responce.status != 200:
                raise TypeError
            return await responce.text()


    def parse_current_mode(self, content: str):
        """
        Обрабатывает контент с главной страницы и формирует словарь с данными о состоянии дк
        :param content: словарь с контетом страниц
        :return: словарь для json responce поля basic
        Пример:
        basic_curr_state = EntityJsonResponce.BASIC_STATE.value: {
            "current_plan": "002",
            "current_parameter_plan": "002",
            "current_time": "2024-11-25 01:25:23",
            "current_errors": "SDET,MIMC,UNIT",
            "streams": 4,
            "stream_info": {
                "1": {
                    "current_mode": "FT",
                    "current_stage": "4",
                    "current_state": "УПРАВЛЕНИЕ"
                },
                "2": {
                    "current_mode": "FT",
                    "current_stage": "6",
                    "current_state": "УПРАВЛЕНИЕ"
                },
                "3": {
                    "current_mode": "FT",
                    "current_stage": "8",
                    "current_state": "УПРАВЛЕНИЕ"
                },
                "4": {
                    "current_mode": "FT",
                    "current_stage": "10",
                    "current_state": "УПРАВЛЕНИЕ"
                }
            }
        }
        """

        flag_head, streams_cnt = True, 0
        basic, all_streams_data, curr_stream_data = {}, {}, {}
        curr_plan = curr_plan_param = curr_time = curr_alarms = current_state = current_mode = curr_stage = None
        for line in content:
            if ':SUBTITLE;' in line:
                address = line.split(':SUBTITLE;')[-1]



            if flag_head:
                if ':D;;##T_PLAN##;' in line:
                    curr_plan = line.split(':D;;##T_PLAN##;')[-1].split(maxsplit=1)[0]
                    continue
                elif '##T_TIMINGSET##;' in line:
                    curr_plan_param = line.split('##T_TIMINGSET##;')[-1]
                    continue
                elif ':D;;##T_TIME##;' in line:
                    curr_time = line.split(':D;;##T_TIME##;')[-1]
                    continue
                elif ':D;;##T_ALARMS##;' in line:
                    curr_alarms = line.split(':D;;##T_ALARMS##;')[-1]
                    continue
                elif ':ENDTABLE' in line:
                    flag_head = False
                    basic = {
                        EntityJsonResponce.CURRENT_PLAN.value: curr_plan,
                        EntityJsonResponce.CURRENT_PARAM_PLAN.value: curr_plan_param,
                        EntityJsonResponce.CURRENT_TIME.value: curr_time,
                        EntityJsonResponce.CURRENT_ERRORS.value: curr_alarms,
                    }
                    continue
                continue

            elif '<b>##T_STREAM##' in line:
                streams_cnt += 1
                continue
            elif ':D;;##T_STATE##;' in line:
                current_state = line.split(':D;;##T_STATE##;')[-1]
                continue
            elif '(##T_STAGE##);' in line:
                current_mode, curr_stage = line.split('(##T_STAGE##);')[-1].split()
                curr_stage = curr_stage.replace('(', '').replace(')', '')
                continue
            elif ':ENDTABLE' in line:
                curr_stream_data[streams_cnt] = {
                    EntityJsonResponce.CURRENT_MODE.value: current_mode,
                    EntityJsonResponce.CURRENT_STAGE.value: curr_stage,
                    EntityJsonResponce.CURRENT_STATE.value: current_state,
                }
                all_streams_data |= curr_stream_data
                current_state = current_mode = curr_stage = None
                continue
            elif '<h2>' in line:
                basic['streams'] = streams_cnt
                basic['stream_info'] = all_streams_data
                break

        basic_curr_state = {
            EntityJsonResponce.BASIC_STATE.value: basic
        }

        return content, basic_curr_state


u = f'http://10.179.16.121/hvi?file=m001a.hvi&pos1=0&pos2=-1'
main_route = '/hvi?file=m001a.hvi&pos1=0&pos2=-1'

async def main():
    o = [PeekWeb(ip_v4='10.179.16.81') for _ in range(10)]

    objs = [ PeekWeb(ip_v4='10.179.16.121')]
    session_timeout = aiohttp.ClientTimeout(total=1, connect=0.4)

    async with aiohttp.ClientSession(timeout=session_timeout) as sess:
        try:
            async with TaskGroup() as tg:
                r = [tg.create_task(coro=o.fetch(f'{o.base_url}{main_route}', sess)) for o in objs]
        except:
            pass
    for _r in r:
        pass
        print(_r.result().splitlines())
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
