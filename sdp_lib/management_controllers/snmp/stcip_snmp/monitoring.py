import asyncio
import os

from pysnmp.entity.engine import SnmpEngine
from pysnmp.proto.rfc1902 import Unsigned32

from sdp_lib.management_controllers.parsers.snmp_parsers.stcip_parsers import (
    SwarcoStcipMonitoringParser,
    PotokSMonitoringParser
)
from sdp_lib.management_controllers.snmp.snmp_base import SnmpHost, StcipHost
from sdp_lib.management_controllers.snmp.oids import Oids


class AbstractGetRequest(StcipHost):

    method = SnmpHost.snmp_get
    oids: tuple[Oids, ...]

    def get_oids(self):
        return self.oids


class CurrentStatesSwarco(AbstractGetRequest):

    parser_class = SwarcoStcipMonitoringParser

    oids = (
        Oids.swarcoUTCTrafftechFixedTimeStatus,
        Oids.swarcoUTCTrafftechPlanSource,
        Oids.swarcoUTCStatusEquipment,
        Oids.swarcoUTCTrafftechPhaseStatus,
        Oids.swarcoUTCTrafftechPlanCurrent,
        Oids.swarcoUTCDetectorQty,
        Oids.swarcoSoftIOStatus
    )


class CurrentStatesPotokS(AbstractGetRequest):

    parser_class = PotokSMonitoringParser

    oids = (
        Oids.swarcoUTCStatusEquipment,
        Oids.swarcoUTCTrafftechPhaseStatus,
        Oids.swarcoUTCTrafftechPlanCurrent,
        Oids.swarcoUTCStatusMode,
        Oids.swarcoUTCDetectorQty,
    )


# class SwarcoSTCIPManagement(SnmpHost):
#
#     # stage_values_set = {'1': 2, '2': 3, '3': 4, '4': 5, '5': 6, '6': 7, '7': 8, '8': 1, 'ЛОКАЛ': 0, '0': 0}
#
#     stage_values_set = {
#         stage_num: Unsigned32(stage_num + 1) for stage_num in range(1, 8)
#     } | {8: Unsigned32(1), 0: Unsigned32(0)}
#
#     def get_community(self) -> tuple[str, str]:
#         return os.getenv('communitySTCIP_r'), os.getenv('communitySTCIP_w')
#
#     async def set_stage(self, val: int):
#
#         oids = [
#             (Oids.swarcoUTCTrafftechPhaseCommand, self.stage_values_set.get(val))
#         ]
#         res = await self.snmp_set(oids=oids, engine=SnmpEngine())
#
#         print(f'res::>> {res}')
#         return res


""" Set commands """


# class SetCommandSwarco(SnmpHost):
#
#     parser_class = SwarcoStcipMonitoringParser
#
#
# class SetAbstract(SnmpHost):
#
#     parser_class = SwarcoStcipMonitoringParser
#
#     def __init__(self, ip_v4: str, value):
#         super().__init__(ip_v4)
#         self.value = self.get_value()
#
#     def get_value(self):
#         return self.value
#
#
# class SetStage(SetAbstract):
#     stage_values_set = {
#         stage_num: Unsigned32(stage_num + 1) for stage_num in range(1, 8)
#     } | {8: Unsigned32(1), 0: Unsigned32(0)}
#
#     def get_oids(self):
#         return [
#         (Oids.swarcoUTCTrafftechPhaseCommand, self.stage_values_set.get(self.value, Unsigned32(0)))
#     ]



async def main():

    # odj = SetStage(ip_v4=, value=1)
    # return val
    # # print(o)
    pass



if __name__ == '__main__':

    # o = SwarcoSTCIPManagement('10.45.154.11')
    r = asyncio.run(main())
    # print(r)