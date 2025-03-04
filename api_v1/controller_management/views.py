import pprint
import time
from asyncio import TaskGroup

from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from . import services
from .schemas import T1, GetHostsStaticDataFromDb, FastRequestMonitoringAndManagement
from .sorters import logger, HostSorterMonitoring

from sdp_lib.management_controllers.snmp import stcip


router = APIRouter(tags=['traffic-lights'])


@router.post('/get-hosts-test/{test_val}')
async def get_hosts_test(test_val: str, data: T1):
    logger.debug(f'test_val: {test_val}')
    logger.debug(data)
    logger.debug(data.model_json_schema())
    return data


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

    start_time = time.time()
    logger.debug(data.hosts)
    hosts_from_db = await services.search_hosts_from_db(data)
    pprint.pprint(hosts_from_db)



    print(f'Время запроса составило: {time.time() - start_time}')
    return hosts_from_db.get_good_hosts_and_bad_hosts_as_dict()


@router.post('/search-and-get-state')
async def get_state(data: FastRequestMonitoringAndManagement):
    start_time = time.time()

    logger.debug(data)
    logger.debug(data.hosts)
    hosts_from_db = await services.search_hosts_from_db(data)
    pprint.pprint(hosts_from_db)
    print(f'Время запроса составило: {time.time() - start_time}')
    # TO DO ...
    return hosts_from_db.get_good_hosts_and_bad_hosts_as_dict()


@router.post('/get-state')
async def get_state(data: FastRequestMonitoringAndManagement):
    start_time = time.time()

    data_hosts = HostSorterMonitoring(data)
    print(data_hosts)
    data_hosts.sort()

    states = services.StatesMonitoring(allowed_hosts=data_hosts.good_hosts,
                                       bad_hosts=data_hosts.bad_hosts)
    res = await states.main()

    print(f'res:: {res}')
    # pprint.pprint(data_hosts.good_hosts)
    # print('Bad hosts: ')
    # pprint.pprint(data_hosts.bad_hosts)



    print(f'Время составило: {time.time() - start_time}')
    return data_hosts.get_good_hosts_and_bad_hosts_as_dict()

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


@router.post('/get-state-test')
async def get_state():
    start_time = time.time()
    ipv4_swarco = (
        '10.45.154.16',
        '10.179.18.49',
        '10.179.100.113',
        '10.179.33.41',
        '10.179.100.121',
        '10.179.20.153',
        '10.179.96.233',
        '10.179.52.105',
        '10.179.52.113',
        '10.179.48.1',
        '10.179.24.97',
        '10.179.20.169',
        '10.179.8.25',
        '10.179.40.9',
        '10.179.52.129',
        '10.179.56.73',
        '10.179.24.121',
        '10.179.52.137',
        '10.179.72.65',
        '10.179.68.33',
    )

    objs = [stcip.SwarcoCurrentStatesSTCIP(ip) for ip in ipv4_swarco]

    res = await main(objs)
    print(f'res:::: {res}')

    r = {}
    for task in res:
        r[task.get_name()] = task.result()
    print(f'Время составило: {time.time() - start_time}')
    r['Execution time'] = time.time() - start_time
    return r