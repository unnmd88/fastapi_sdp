from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.models import db_helper
from . import crud
from .schemas import (
    GetStateResponse, GetHostsFromDb, RequestMonitoringAndManagement, T1)
from .services import GetStates, BaseSearch, SearchHosts, logger, GetHosts

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
async def get_hosts(data: GetHostsFromDb):
    logger.debug(data)
    logger.debug(data.hosts)
    logger.debug(data.model_fields)
    logger.debug(data.model_config)
    logger.debug(data.model_json_schema())
    return data
    data_hosts = GetHosts(data.model_dump().get('hosts'))
    data_hosts.sorting_income_data()
    if data_hosts.search_in_db_hosts:
        db = SearchHosts()
        data_hosts.hosts_after_search_in_db = await db.get_hosts_where(
            stmt=db.get_stmt_where(hosts=data_hosts.search_in_db_hosts)
        )
        data_hosts.sorting_hosts_after_get_grom_db()
    logger.debug(data_hosts)
    # print(data_hosts)

    return data_hosts.create_responce()



@router.post('/get-state')
async def get_state(data: RequestMonitoringAndManagement):

    logger.debug(data)
    logger.debug(data.hosts)
    logger.debug(data.model_fields)
    logger.debug(data.model_config)
    logger.debug(data.model_json_schema())
    return data

    _data = data
    logger.debug(f'dDATA:: {_data}')

    data_hosts = GetStates(data.model_dump().get('hosts'))

    data_hosts.sorting_income_data()

    if data_hosts.search_in_db_hosts:
        db = SearchHosts()
        data_hosts.hosts_after_search_in_db = await db.get_hosts_where(
            stmt=db.get_stmt_where(hosts=data_hosts.search_in_db_hosts)
        )
        data_hosts.sorting_hosts_after_get_grom_db()

    print(f'data_hosts >> {data_hosts}')
    print(f'data_hosts >> {data}')

    return data_hosts.allowed_hosts
    print(f'data_hosts >> {data_hosts}')