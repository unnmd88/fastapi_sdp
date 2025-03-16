import logging
import pprint
import time
from asyncio import TaskGroup

import aiohttp
from fastapi import APIRouter, HTTPException, status, Depends
from pysnmp.entity.engine import SnmpEngine
from sqlalchemy.ext.asyncio import AsyncSession

from .crud import search_hosts_from_db
from . import services
from api_v1.controller_management.sorters import sorters
from .schemas import T1, GetHostsStaticDataFromDb, FastRequestMonitoringAndManagement
import logging_config


from sdp_lib.management_controllers.snmp import stcip

logger = logging.getLogger(__name__)

router = APIRouter(tags=['traffic-lights'])


# @router.post('/get-hosts-test/{test_val}')
# async def get_hosts_test(test_val: str, data: T1):
#     logger.debug(f'test_val: {test_val}')
#     logger.debug(data)
#     logger.debug(data.model_json_schema())
#     return data


# @router.post('/properties')
# async def get_hosts(data: GetHostsStaticDataFromDb):
#
#     start_time = time.time()
#     logger.debug(data.hosts)
#     data_hosts = HostSorterSearchInDB(data)
#     db = SearchHosts()
#     search_entity = data_hosts.get_hosts_data_for_search_in_db()
#
#     data_hosts.hosts_after_search = await db.get_hosts_where(db.get_stmt_where(search_entity))
#     data_hosts.sorting_hosts_after_search_from_db()
#     pprint.pprint(data_hosts)
#
#     print(f'Время запроса составило: {time.time() - start_time}')
#     return data_hosts.get_good_hosts_and_bad_hosts_as_dict()


@router.post('/properties')
async def get_hosts(data: GetHostsStaticDataFromDb):

    # start_time = time.time()
    hosts_from_db = await search_hosts_from_db(data)
    # print(f'Время запроса составило: {time.time() - start_time}')
    return hosts_from_db.get_good_hosts_and_bad_hosts_as_dict()


@router.post('/search-and-get-state')
async def get_state(data: GetHostsStaticDataFromDb):

    states = services.StatesMonitoring(income_data=data, search_in_db=True)
    return await states.compose_request()


@router.post('/get-state')
async def get_state(data: FastRequestMonitoringAndManagement):

    states = services.StatesMonitoring(data, search_in_db=False)
    return await states.compose_request()




async def main(objs):
    # taks = [o.get_multiple(oids=oids_swarco) for o in objs]
    # res = await asyncio.gather(*taks)
    # async with TaskGroup() as tg:
    #     print('tg1')
    #     # res = [tg.create_task(coro=o.get_multiple(oids=oids_swarco), name=o.ip_v4)  for o in objs]
    #     res = [tg.create_task(coro=o.get_data_for_basic_current_state(), name=o.ip_v4).add_done_callback(tets_callback)  for o in objs]

    async with TaskGroup() as tg:
        print('tg2')
        # res = [tg1.create_task(coro=o.get_multiple(oids=oids_swarco), name=o.ip_v4)  for o in objs]
        res = [tg.create_task(coro=o.get_data_for_basic_current_state(), name=o.ip_v4)  for o in objs]

    return res


