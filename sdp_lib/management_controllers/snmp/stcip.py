import asyncio
import os

from pysnmp.entity.engine import SnmpEngine
from pysnmp.proto.rfc1902 import Unsigned32

from sdp_lib.management_controllers.fields_names import FieldsNames
from sdp_lib.management_controllers.parsers.snmp_parsers.stcip_parsers import (
    SwarcoStcipParser,
    PotokSParser
)
from sdp_lib.management_controllers.snmp.snmp_base import SnmpHost
from sdp_lib.management_controllers.snmp.oids import Oids


class BaseSTCIP(SnmpHost):

    host_protocol = FieldsNames.protocol_stcip

    def get_community(self) -> tuple[str, str]:
        return os.getenv('communitySTCIP_r'), os.getenv('communitySTCIP_w')


class CurrentStatesSwarco(BaseSTCIP):

    parser_class = SwarcoStcipParser

    oids_state = (
        Oids.swarcoUTCTrafftechFixedTimeStatus,
        Oids.swarcoUTCTrafftechPlanSource,
        Oids.swarcoUTCStatusEquipment,
        Oids.swarcoUTCTrafftechPhaseStatus,
        Oids.swarcoUTCTrafftechPlanCurrent,
        Oids.swarcoUTCDetectorQty,
        Oids.swarcoSoftIOStatus
    )


class CurrentStatesPotokS(BaseSTCIP):

    parser_class = PotokSParser

    oids_state = (
        Oids.swarcoUTCStatusEquipment,
        Oids.swarcoUTCTrafftechPhaseStatus,
        Oids.swarcoUTCTrafftechPlanCurrent,
        Oids.swarcoUTCStatusMode,
        Oids.swarcoUTCDetectorQty,
    )


class SwarcoSTCIPManagement(SnmpHost):

    stage_values_set = {'1': 2, '2': 3, '3': 4, '4': 5, '5': 6, '6': 7, '7': 8, '8': 1, 'ЛОКАЛ': 0, '0': 0}

    def get_community(self) -> tuple[str, str]:
        return os.getenv('communitySTCIP_r'), os.getenv('communitySTCIP_w')

    async def set_stage(self, val: str):
        v = Unsigned32(self.stage_values_set.get(val))
        oids = [
            (Oids.swarcoUTCTrafftechPhaseCommand, Unsigned32(v))
        ]
        res = await self.set(oids=oids, engine=SnmpEngine())

        print(f'res::>> {res}')
        return res


async def main():


    o = CurrentStatesSwarco('10.179.58.233')
    r = await o.get_and_parse(SnmpEngine())
    print(f'r: {r.response_as_dict}')
    return r
    # print(o)




if __name__ == '__main__':

    # o = SwarcoSTCIPManagement('10.45.154.11')
    r = asyncio.run(main())
    # print(r)