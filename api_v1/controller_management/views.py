import logging
import pprint
import time
from asyncio import TaskGroup

import aiohttp
from fastapi import APIRouter, HTTPException, status, Depends
from pysnmp.entity.engine import SnmpEngine
from sqlalchemy.ext.asyncio import AsyncSession

from api_v1.controller_management.crud.crud import search_hosts_from_db, \
    search_hosts_from_db_for_monitoring_and_management
from . import services
from api_v1.controller_management.sorters import sorters
from .schemas import T1, NumbersOrIpv4, FastRequestMonitoringAndManagement, FastMonitoring, ResponseGetState
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
async def get_hosts(data: NumbersOrIpv4):

    start_time = time.time()
    print(f'da: {data}')
    print(f'da!! : {data.hosts}')
    hosts_from_db = await search_hosts_from_db(data)
    print(f'Время запроса составило: {time.time() - start_time}')
    m = hosts_from_db.response_as_model
    m.time_execution = time.time() - start_time
    # pprint.pprint(f'M: {hosts_from_db.build_data_hosts_as_dict_and_merge_data_from_record_to_body()}')

    return hosts_from_db.response_as_model

    return {f'Время запроса составило: ': time.time() - start_time} | hosts_from_db.response_dict
    print(f'Время запроса составило: {time.time() - start_time}')
    # return hosts_from_db
    return hosts_from_db.get_good_hosts_and_bad_hosts_as_dict()


@router.post('/search-and-get-state-test')
async def get_state_t(data: NumbersOrIpv4):

    states = services.StatesMonitoring(income_data=data, search_in_db=True)
    return await states.compose_request()



    start_time = time.time()
    print(f'da: {data}')
    print(f'da!! : {data.hosts}')
    hosts_from_db = await search_hosts_from_db_for_monitoring_and_management(data)
    print(f'Время запроса составило: {time.time() - start_time}')
    return hosts_from_db.hosts_data_for_monitoring_and_management


@router.post('/search-and-get-state')
async def get_state(data: NumbersOrIpv4) -> ResponseGetState:
    # FIX ME
    # Если в списке hosts будет "192.168.0.1", то возникает ошибка!
    # Проверить и найти в чем проблема

    states = services.StatesMonitoring(income_data=data, search_in_db=True)
    return await states.compose_request()


# @router.post('/get-state')
# async def get_state(data: FastRequestMonitoringAndManagement):
#
#     states = services.StatesMonitoring(income_data=data, search_in_db=False)

@router.post('/get-state')
async def get_state(data: FastMonitoring):

    print(f'data: \n {data}')
    states = services.StatesMonitoring(income_data=data, search_in_db=False)

    return await states.compose_request()



""" Примеры тела запроса """

'''
{
  "hosts": {
    "10.179.16.121": {
      "type_controller": "Peek"
    },
"10.179.67.121": {
      "type_controller": "Поток (P)"
    },
"10.179.8.17": {
      "type_controller": "Swarco"
    },
"10.179.18.41": {
      "type_controller": "Поток (P)"
    },
    "10.179.59.9": {
      "type_controller": "Peek"
    },
    "10.179.59": {
      "type_controller": "Peek"
    },
    "10.179.59.9": {
      "type_controller": "Greek"
    },
    "10.179.59.91": {
      "type_controlhfler": "Greek"
    }
  }
}

'''