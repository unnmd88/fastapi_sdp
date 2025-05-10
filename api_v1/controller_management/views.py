import logging
import pprint
import time

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from api_v1.controller_management.crud import crud
from core.models.db_helper import db_helper
from core.settings import settings
from core.shared import HTTP_CLIENT_SESSIONS
from api_v1.controller_management import services
from api_v1.controller_management.crud.crud import TrafficLights
from api_v1.controller_management.schemas import (
    BaseSearchTrafficLightsInDb,
    Monitoring,
    ResponseGetState,
    ResponseSearchinDb,
    Management, MonitoringFields,
    # ControllerManagementOptions
)
from api_v1.controller_management.available_services import all_controllers_services, T_CommandOptions


logger = logging.getLogger(__name__)
router = APIRouter()

# @router.post('/get-hosts-test/{test_val}')
# async def get_hosts_test(test_val: str, data: T1):
#     logger.debug(f'test_val: {test_val}')
#     logger.debug(data)
#     logger.debug(data.model_json_schema())
#     return data

# @router.get('/controller-management-options')
# async def get_controller_management_options(
#     session: AsyncSession = Depends(db_helper.session_dependency)
# ) -> list[ControllerManagementOptions]:
#     return await crud.get_controller_management_options(session)


@router.post('/properties', tags=[settings.traffic_lights_tag_static_properties])
async def get_hosts(data: BaseSearchTrafficLightsInDb) -> ResponseSearchinDb:

    start_time = time.time()
    logger.debug(f'data: {data}')
    hosts_from_db = TrafficLights(data)
    await hosts_from_db.search_hosts_and_processing()
    hosts_from_db.get_as_dict()
    return hosts_from_db.get_response_as_pydantic_model()


@router.post('/search-and-get-state', tags=[settings.traffic_lights_tag_monitoring])
async def search_and_get_state(data: BaseSearchTrafficLightsInDb):

    hosts_from_db = TrafficLights(data)
    await hosts_from_db.search_hosts_and_processing()
    # print(f'hosts_from_db host_data: {hosts_from_db.host_data}' )
    # print(f'hosts_from_db src_data: {hosts_from_db.src_data}' )
    # print(f'hosts_from_db hosts_after_search: {hosts_from_db.hosts_after_search}' )
    # print(f'get_response_as_pydantic_model: {hosts_from_db.get_response_as_pydantic_model()}' )

    host_for_req = Monitoring(hosts={**hosts_from_db.get_as_dict()})

    print(f'host_for_req: \n{host_for_req}')

    states = services.StatesMonitoring(
        income_data=host_for_req,
        session=HTTP_CLIENT_SESSIONS[0].session
    )
    return await states.compose_request()


@router.post('/get-state', tags=[settings.traffic_lights_tag_monitoring])
# async def get_state(data: Monitoring) -> ResponseGetState:
async def get_state(data: Monitoring):
    # print(f'data: \n {data}')

    # return data

    states = services.StatesMonitoring(
        income_data=data,
        session=HTTP_CLIENT_SESSIONS[0].session
    )
    return await states.compose_request()


@router.get('/commands-and-options', tags=[settings.traffic_lights_tag_management])
async def commands_options() -> T_CommandOptions:
    return all_controllers_services


@router.post('/set-command', tags=[settings.traffic_lights_tag_management])
async def set_command(data: Management):

    # return data

    result_set_command = services.Management(
        income_data=data,
        session=HTTP_CLIENT_SESSIONS[0].session
    )
    return await result_set_command.compose_request()





# @router.post('/test-ssh', tags=[settings.traffic_lights_tag_management])
# async def test_ssh(commands: dict[str, list[str]]):
#
#     commands = commands.get('commands')
#     print(f'commands: {commands}')
#     print(f'type(commands): {type(commands)}')
#     if not isinstance(SWARCO_SSH_CONNECTIONS.get('10.45.154.18'), SwarcoSSH):
#         obj = SwarcoSSH('10.179.108.177')
#         await obj.create_driver_connection()
#         await obj.create_process()
#         SWARCO_SSH_CONNECTIONS['10.179.108.177'] = obj
#         print(obj.driver.is_closed())
#         print(obj.process.is_closing())
#     else:
#         print(f'SWARCO_SSH_CONNECTIONS: {SWARCO_SSH_CONNECTIONS}')
#         obj = SWARCO_SSH_CONNECTIONS.get('10.179.108.177')
#         print(f'f obj.driver: {obj.driver}')
#         print(f'f obj.process: {obj.process_terminal_stdout}')
#         print(f'f obj.process.is_closing(): {obj.process_terminal_stdout.is_closing()}')
#         # await obj.create_process()
#
#     print(obj.driver.is_closed())
#     print(obj.process.is_closing())
#     # ['lang UK', 'l2', '2727','SIMULATE DISPLAY --poll']
#     # ["lang UK", "l2", "2727","SIMULATE DISPLAY --poll"]
#
#
#     print('>>>>>>>>>>>>>>>>>>>>>>>' * 20)
#     await obj.send_commands2(commands)
#     print(obj.driver.is_closed())
#     print(obj.process.is_closing())
#     # await obj.create_process()
#     await obj.send_commands2(['instat102 ?'])



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


########################
"""

{
  "hosts": {
    "10.179.72.185": {
      "type_controller": "Swarco"
    },
    "10.179.24.73": {
      "type_controller": "Поток (S)"
    },
     "10.179.91.17": {
          "type_controller": "Поток (P)"
        },
     "10.179.66.97": {
          "type_controller": "Peek"
    }
  }
}

"""