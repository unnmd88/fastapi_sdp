import os
import typing
from dataclasses import dataclass
import dataclasses
from sdp_lib.management_controllers.snmp.host_data import swarco_stcip, AllowedControllers


class HostProtocolData(typing.NamedTuple):

    type_controller: AllowedControllers
    community_r: str
    community_w: str
    host_protocol: str
    is_scn_dependency: bool





@dataclass
class Stcip(Host):
    community_r = 'daaa'
    community_w = 'aadvaaa'
    host_protocol = 'stcip'

ovc = Stcip(type_controller='xx')



# print(x)
# print(dataclasses.asdict(x))
# print(dataclasses.fields(A))




if __name__ == '__main__':
    print(swarco_stcip._asdict())




