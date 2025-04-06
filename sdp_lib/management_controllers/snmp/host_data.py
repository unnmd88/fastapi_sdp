import dataclasses
import os
from dataclasses import dataclass

from dotenv import load_dotenv

from sdp_lib.management_controllers.constants import AllowedControllers
from sdp_lib.management_controllers.fields_names import FieldsNames
from sdp_lib.management_controllers.snmp import oids
from sdp_lib.management_controllers.snmp.oids import Oids


load_dotenv()


@dataclass(frozen=True)
class HostStaticData:
    type_controller: AllowedControllers
    community_r: str
    community_w: str
    host_protocol: str
    is_scn_dependency: bool
    oids_get_state: tuple


@dataclass(frozen=True)
class HostStaticDataWithScn(HostStaticData):
    oids_scn_required: set[Oids]


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


def make_instance_props() -> list[HostStaticData]:
    matches = {
        AllowedControllers.SWARCO: (HostStaticData, __stcip),
        AllowedControllers.POTOK_S: (HostStaticData, __stcip),
        AllowedControllers.POTOK_P: (HostStaticDataWithScn, __ug405, oids.oids_scn_required)
    }
    result = []
    for controller, data in matches.items():
        a_class = data[0]
        result.append(a_class(controller, *data[1:]))
    return result


    # return (data[0](controller, *data[1:]) for controller, data in matches.items())


# swarco_stcip, potok_s, potok_p = make_instance_props()

swarco_stcip = HostStaticData(AllowedControllers.SWARCO, *__stcip, oids.oids_state_swarco)
# swarco_stcip = HostStaticData(AllowedControllers.SWARCO, *__stcip, snmp_utils.SwarcoConverters.varbinds_get_state)
potok_s = HostStaticData(AllowedControllers.POTOK_S, *__stcip, oids.oids_state_potok_s)
potok_p = HostStaticDataWithScn(AllowedControllers.POTOK_P, *__ug405, oids.oids_state_potok_p, oids.oids_scn_required)
peek_ug405 = HostStaticDataWithScn(AllowedControllers.PEEK, *__ug405, oids.oids_state_potok_p, oids.oids_scn_required)


# stage_values_set = {
#                        stage_num: Unsigned32(stage_num + 1) for stage_num in range(1, 8)
#                    } | {8: Unsigned32(1), 0: Unsigned32(0)}




if __name__ == '__main__':
    print(potok_s)
    print(dataclasses.asdict(potok_s))
    print(potok_s.community_r)

    print(potok_p)
    print(dataclasses.asdict(potok_p))



    # print(ob.host_protocol)