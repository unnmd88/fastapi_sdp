import dotenv
import os
import typing
from enum import StrEnum

from dotenv import load_dotenv

from sdp_lib.management_controllers.fields_names import FieldsNames


load_dotenv()


class AllowedControllers(StrEnum):

    SWARCO = 'Swarco'
    POTOK_P = 'Поток (P)'
    POTOK_S = 'Поток (S)'
    PEEK = 'Peek'


class HostProtocolData(typing.NamedTuple):

    type_controller: AllowedControllers
    community_r: str
    community_w: str
    host_protocol: str
    is_scn_dependency: bool


swarco_stcip = HostProtocolData(
    type_controller=AllowedControllers.SWARCO,
    community_r=os.getenv('communitySTCIP_r'),
    community_w=os.getenv('communitySTCIP_w'),
    host_protocol=FieldsNames.protocol_stcip,
    is_scn_dependency = False
)

potok_p = HostProtocolData(
    type_controller=AllowedControllers.POTOK_P,
    community_r=os.getenv('communityUG405_r'),
    community_w=os.getenv('communityUG405_w'),
    host_protocol=FieldsNames.protocol_ug405,
    is_scn_dependency=True
)

if __name__ == '__main__':
    print(potok_p)
    print(swarco_stcip)