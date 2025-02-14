import pprint

from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.models import db_helper
from . import crud
from .crud import SearchHosts
from .schemas import RequestMonitoringAndManagement, T1, GetHostsStaticDataFromDb
from .services import logger, HostSorterSearchInDB

router = APIRouter(tags=['traffic-lights'])


@router.post('/get-hosts-test/{test_val}')
async def get_hosts_test(test_val: str, data: T1):
    logger.debug(f'test_val: {test_val}')
    logger.debug(data)
    logger.debug(data.model_json_schema())
    return data



@router.post('/properties')
async def get_hosts(data: GetHostsStaticDataFromDb):

    logger.debug(data.hosts)
    data_hosts = HostSorterSearchInDB(data)
    db = SearchHosts()
    search_entity = data_hosts.get_hosts_data_for_search_db()

    data_hosts.hosts_after_search = await db.get_hosts_where(db.get_stmt_where(search_entity))
    data_hosts.sorting_hosts_after_search_from_db()
    pprint.pprint(data_hosts)

    return data_hosts.get_hosts_and_bad_hosts_as_dict()



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
async def get_state(data: RequestMonitoringAndManagement):
    logger.debug(data)
    logger.debug(data.hosts)
    data_hosts = SortersWithSearchInDbMonitoring(data.hosts)
    db = SearchHosts()

    data_hosts.hosts_after_search_in_db = await db.get_hosts_where(db.get_stmt_where(data_hosts.search_data))
    pprint.pprint(data_hosts)
    # logger.debug()
    return data_hosts.search_data






# @router.post('/get-state')
# async def get_state(data: RequestMonitoringAndManagement):
#
#     logger.debug(data)
#     logger.debug(data.hosts)
#     logger.debug(data.model_fields)
#     logger.debug(data.model_config)
#     logger.debug(data.model_json_schema())
#     return data
#
#     _data = data
#     logger.debug(f'dDATA:: {_data}')
#
#     data_hosts = GetStates(data.model_dump().get('hosts'))
#
#     data_hosts.sorting_income_data()
#
#     if data_hosts.search_in_db_hosts:
#         db = SearchHosts()
#         data_hosts.hosts_after_search_in_db = await db.get_hosts_where(
#             stmt=db.get_stmt_where(hosts=data_hosts.search_in_db_hosts)
#         )
#         data_hosts.sorting_hosts_after_search_from_db()
#
#     print(f'data_hosts >> {data_hosts}')
#     print(f'data_hosts >> {data}')
#
#     return data_hosts.allowed_hosts
#     print(f'data_hosts >> {data_hosts}')