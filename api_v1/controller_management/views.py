import logging
import time

from fastapi import APIRouter

from api_v1.controller_management.crud.crud import search_hosts_from_db
from api_v1.controller_management import services
from api_v1.controller_management.schemas import (
    NumbersOrIpv4,
    FastMonitoring,
    ResponseGetState,
    ResponseSearchinDb
)
import logging_config


logger = logging.getLogger(__name__)

router = APIRouter(tags=['traffic-lights'])


# @router.post('/get-hosts-test/{test_val}')
# async def get_hosts_test(test_val: str, data: T1):
#     logger.debug(f'test_val: {test_val}')
#     logger.debug(data)
#     logger.debug(data.model_json_schema())
#     return data


@router.post('/properties')
async def get_hosts(data: NumbersOrIpv4) -> ResponseSearchinDb:

    start_time = time.time()
    logger.debug(f'data: {data}')
    # print(f'da!! : {data.hosts}')
    hosts_from_db = await search_hosts_from_db(data)
    # print(f'Время запроса составило: {time.time() - start_time}')
    m = hosts_from_db.response_as_model
    m.time_execution = time.time() - start_time
    return hosts_from_db.response_as_model


@router.post('/search-and-get-state')
async def search_and_get_state(data: NumbersOrIpv4) -> ResponseGetState:
    states = services.StatesMonitoring(income_data=data, search_in_db=True)
    return await states.compose_request()


@router.post('/get-state')
async def get_state(data: FastMonitoring) -> ResponseGetState:

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