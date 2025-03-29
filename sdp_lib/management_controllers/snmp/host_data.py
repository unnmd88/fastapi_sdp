import dataclasses
import os
import typing
from dataclasses import dataclass

from dotenv import load_dotenv

from sdp_lib.management_controllers.constants import AllowedControllers
from sdp_lib.management_controllers.fields_names import FieldsNames
from sdp_lib.management_controllers.snmp import oids

load_dotenv()


@dataclass
class HostProperties:
    type_controller: AllowedControllers
    community_r: str = None
    community_w: str = None
    host_protocol: str = None
    is_scn_dependency: bool = None
    oids_get_state: tuple = None

    matches = {
        AllowedControllers.SWARCO: (
            os.getenv('communitySTCIP_r'),
            os.getenv('communitySTCIP_w'),
            FieldsNames.protocol_stcip,
            False
        ),
        AllowedControllers.POTOK_S: (
            os.getenv('communitySTCIP_r'),
            os.getenv('communitySTCIP_w'),
            FieldsNames.protocol_stcip,
            False
        ),
        AllowedControllers.POTOK_P: (
            os.getenv('communityUG405_r'),
            os.getenv('communityUG405_w'),
            FieldsNames.protocol_ug405,
            True
        )
    } # Альтернативу if-у в  __post_init__

    def __post_init__(self):
        self.community_r, self.community_w, self.host_protocol, self.is_scn_dependency



        if self.type_controller in (AllowedControllers.SWARCO, AllowedControllers.POTOK_S):
            self.community_r = os.getenv('communitySTCIP_r')
            self.community_w = os.getenv('communitySTCIP_w')
            self.host_protocol = FieldsNames.protocol_stcip
            self.is_scn_dependency = False
        elif self.type_controller in (AllowedControllers.PEEK, AllowedControllers.POTOK_P):
            self.community_r = os.getenv('communityUG405_r')
            self.community_w = os.getenv('communityUG405_w')
            self.host_protocol = FieldsNames.protocol_ug405
            self.is_scn_dependency = True


@dataclass
class HProps:
    type_controller: AllowedControllers
    community_r: str = None
    community_w: str = None
    host_protocol: str = None
    is_scn_dependency: bool = None
    oids_get_state: tuple = None

@dataclass
class StcipHostProperties(HProps):

    def __post_init__(self):
        self.community_r, self.community_w = os.getenv('communitySTCIP_r'), os.getenv('communitySTCIP_w')
        self.host_protocol = FieldsNames.protocol_stcip
        self.is_scn_dependency = False
        if self.type_controller == AllowedControllers.SWARCO:
            self.oids_get_state = oids.oids_state_swarco
        elif self.type_controller == AllowedControllers.POTOK_S:
            self.oids_get_state = oids.oids_state_potok_s
        else:
            raise TypeError







swarco_stcip = HostProperties(AllowedControllers.SWARCO)
potok_s = StcipHostProperties(AllowedControllers.POTOK_S)
potok_p = HostProperties(AllowedControllers.POTOK_P)


# class HostProtocolData(typing.NamedTuple):
#
#     type_controller: AllowedControllers
#     community_r: str
#     community_w: str
#     host_protocol: str
#     is_scn_dependency: bool
#
#
# swarco_stcip = HostProtocolData(
#     type_controller=AllowedControllers.SWARCO,
#     community_r=os.getenv('communitySTCIP_r'),
#     community_w=os.getenv('communitySTCIP_w'),
#     host_protocol=FieldsNames.protocol_stcip,
#     is_scn_dependency = False
# )
#
# potok_p = HostProtocolData(
#     type_controller=AllowedControllers.POTOK_P,
#     community_r=os.getenv('communityUG405_r'),
#     community_w=os.getenv('communityUG405_w'),
#     host_protocol=FieldsNames.protocol_ug405,
#     is_scn_dependency=True
# )
#
# potok_s = HostProtocolData(
#     type_controller=AllowedControllers.POTOK_S,
#     community_r=os.getenv('communitySTCIP_r'),
#     community_w=os.getenv('communitySTCIP_w'),
#     host_protocol=FieldsNames.protocol_stcip,
#     is_scn_dependency=True
# )

if __name__ == '__main__':
    ob = HostProperties(AllowedControllers.SWARCO)
    print(potok_s)
    print(dataclasses.asdict(potok_s))
    print(potok_s.community_r)
    # print(ob.host_protocol)