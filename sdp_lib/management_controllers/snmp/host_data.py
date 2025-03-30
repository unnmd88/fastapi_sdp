import dataclasses
import os
import typing
from dataclasses import dataclass

from dotenv import load_dotenv

from sdp_lib.management_controllers.constants import AllowedControllers
from sdp_lib.management_controllers.fields_names import FieldsNames


load_dotenv()


@dataclass(frozen=True)
class HostStaticData:
    type_controller: AllowedControllers
    community_r: str
    community_w: str
    host_protocol: str
    is_scn_dependency: bool


__stcip = (
    os.getenv('communitySTCIP_r'),
    os.getenv('communitySTCIP_r'),
    FieldsNames.protocol_stcip,
    False
)

__ug405 = (
    os.getenv('communityUG405_r'),
    os.getenv('communityUG405_w'),
    FieldsNames.protocol_ug405,
    True
)


def make_instance_props() -> typing.Generator:
    matches = {
        AllowedControllers.SWARCO: __stcip,
        AllowedControllers.POTOK_S: __stcip,
        AllowedControllers.POTOK_P: __ug405,
    }

    return (HostStaticData(controller, *data) for controller, data in matches.items())


swarco_stcip, potok_s, potok_p = make_instance_props()


if __name__ == '__main__':
    print(potok_s)
    print(dataclasses.asdict(potok_s))
    print(potok_s.community_r)

    print(potok_p)
    print(dataclasses.asdict(potok_p))



    # print(ob.host_protocol)