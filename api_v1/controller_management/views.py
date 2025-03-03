import pprint
import time
from asyncio import TaskGroup

from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from .crud import SearchHosts
from .schemas import RequestMonitoringAndManagement, T1, GetHostsStaticDataFromDb, FastRequestMonitoringAndManagement
from .services import logger, HostSorterSearchInDB, BaseHostSorterNoSearchInDB, HostSorterNoSearchInDBMonitoring

from sdp_lib.management_controllers.snmp import stcip


router = APIRouter(tags=['traffic-lights'])


@router.post('/get-hosts-test/{test_val}')
async def get_hosts_test(test_val: str, data: T1):
    logger.debug(f'test_val: {test_val}')
    logger.debug(data)
    logger.debug(data.model_json_schema())
    return data



@router.post('/properties')
async def get_hosts(data: GetHostsStaticDataFromDb):

    start_time = time.time()
    logger.debug(data.hosts)
    data_hosts = HostSorterSearchInDB(data)
    db = SearchHosts()
    search_entity = data_hosts.get_hosts_data_for_search_db()

    data_hosts.hosts_after_search = await db.get_hosts_where(db.get_stmt_where(search_entity))
    data_hosts.sorting_hosts_after_search_from_db()
    pprint.pprint(data_hosts)

    print(f'Время запроса составило: {time.time() - start_time}')
    return data_hosts.get_good_hosts_and_bad_hosts_as_dict()



# @router.post('/get-hosts')
# async def get_hosts(data: GetHostsStaticDataFromDb):
#     logger.debug(data)
#     logger.debug(data.hosts)
#     data_hosts = GetHostsStaticData(data.hosts)
#     data_hosts.sorting_income_data()
#     print(data_hosts)
#     # return data_hosts.search_in_db_hosts
#     if data_hosts.search_in_db_hosts:
#         db = SearchHosts()
#         data_hosts.hosts_after_search_in_db = await db.get_hosts_where(
#             stmt=db.get_stmt_where(hosts=data_hosts.search_in_db_hosts)
#         )
#         data_hosts.sorting_hosts_after_search_from_db()
#     logger.debug(data_hosts.hosts_after_search_in_db)
#     print(data_hosts)
#
#     return data_hosts.search_in_db_hosts



@router.post('/get-state')
async def get_state(data: FastRequestMonitoringAndManagement):
    logger.debug(data)
    logger.debug(data.hosts)
    # return data
    data_hosts = HostSorterNoSearchInDBMonitoring(data)
    print(data_hosts)
    # print(data_hosts.hosts)
    data_hosts.sorting()
    pprint.pprint(data_hosts.hosts)
    print('Bad hosts: ')
    pprint.pprint(data_hosts.bad_hosts)
    # logger.debug(f' Hosts\n {data_hosts.hosts}')
    return data_hosts.bad_hosts


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