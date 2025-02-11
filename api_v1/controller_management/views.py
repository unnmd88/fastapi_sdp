import pprint

from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.models import db_helper
from . import crud
from .crud import SearchHosts
from .schemas import (
    GetStateResponse, RequestMonitoringAndManagement, T1, GetHostsStaticDataFromDb)
from .services import  logger, BaseSortersWithSearchInDb, SortersWithSearchInDbMonitoring


router = APIRouter(tags=['Intersections'])


@router.post('/get-hosts-test')
async def get_hosts_test(data: T1):
    logger.debug(data)
    logger.debug(data.hosts)
    logger.debug(data.model_fields)
    logger.debug(data.model_config)
    logger.debug(data.model_json_schema())
    return data



@router.post('/get-hosts')
async def get_hosts(data: GetHostsStaticDataFromDb):
    logger.debug(data)
    logger.debug(data.hosts)
    data_hosts = BaseSortersWithSearchInDb(data.hosts)
    db = SearchHosts()

    data_hosts.hosts_after_search_in_db = await db.get_hosts_where(db.get_stmt_where(data_hosts.search_data))
    pprint.pprint(data_hosts)
    logger.debug()
    return data_hosts.search_data



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