import logging
import time

from fastapi import APIRouter


from core.settings import settings
from api_v1.controller_management import services
from api_v1.controller_management.crud.crud import HostPropertiesProcessors
from api_v1.controller_management.schemas import (
    NumbersOrIpv4,
    FastMonitoring,
    ResponseGetState,
    ResponseSearchinDb, FastManagement
)
import logging_config


logger = logging.getLogger(__name__)


router = APIRouter()



# @router.post('/get-hosts-test/{test_val}')
# async def get_hosts_test(test_val: str, data: T1):
#     logger.debug(f'test_val: {test_val}')
#     logger.debug(data)
#     logger.debug(data.model_json_schema())
#     return data



@router.post('/properties', tags=[settings.traffic_lights_tag_static_properties])
async def get_hosts(data: NumbersOrIpv4) -> ResponseSearchinDb:

    start_time = time.time()
    logger.debug(f'data: {data}')
    hosts_from_db = HostPropertiesProcessors(data)
    await hosts_from_db.search_hosts_and_processing()
    return hosts_from_db.response_as_model


@router.post('/search-and-get-state', tags=[settings.traffic_lights_tag_monitoring])
async def search_and_get_state(data: NumbersOrIpv4) -> ResponseGetState:
    states = services.StatesMonitoring(income_data=data, search_in_db=True)
    return await states.compose_request()


@router.post('/get-state', tags=[settings.traffic_lights_tag_monitoring])
async def get_state(data: FastMonitoring) -> ResponseGetState:
    # print(f'data: \n {data}')
    states = services.StatesMonitoring(income_data=data, search_in_db=False)
    return await states.compose_request()


@router.post('/set-command', tags=[settings.traffic_lights_tag_management])
async def set_command(data: FastManagement):

    result_set_command = services.Management(income_data=data, search_in_db=False)
    return await result_set_command.compose_request()

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