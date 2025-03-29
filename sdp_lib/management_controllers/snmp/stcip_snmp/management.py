import asyncio

from pysnmp.entity.engine import SnmpEngine
from pysnmp.proto.rfc1902 import Unsigned32

from sdp_lib.management_controllers.parsers.snmp_parsers.stcip_parsers import SwarcoStcipMonitoringParser, \
    SwarcoStcipManagementParser, PotokStcipManagementParser
from sdp_lib.management_controllers.snmp.oids import Oids
from sdp_lib.management_controllers.snmp.snmp_base import StcipHost, SnmpHost


class AbstractSetRequest(StcipHost):

    method = SnmpHost.snmp_set
    oids: tuple[Oids, ...]

    def __init__(self, ip_v4: str, value):
        super().__init__(ip_v4)
        self.value = value

    def get_value(self):
        return self.value


class AbstractSetStage(AbstractSetRequest):

    stage_values_set: dict

    def get_oids(self):
        return [
            (Oids.swarcoUTCTrafftechPhaseCommand, self.stage_values_set.get(self.value, Unsigned32(0)))
        ]


class SetStageSwarco(AbstractSetStage):

    parser_class = SwarcoStcipManagementParser

    stage_values_set = {
        stage_num: Unsigned32(stage_num + 1) for stage_num in range(1, 8)
    } | {8: Unsigned32(1), 0: Unsigned32(0)}

    # match_stages = {
    #     stage_val: stage_val - 1 for stage_val in range(2, 8)
    # } | {1: 8}


class SetStagePotokS(AbstractSetStage):

    parser_class = PotokStcipManagementParser

    stage_values_set = {stage_num: Unsigned32(stage_num + 1) for stage_num in range(1, 65)}




async def main():

    obj = SetStagePotokS(ip_v4='10.179.107.177', value=0)
    r = await obj.request_and_parse_response(engine=SnmpEngine())
    print(obj.response_as_dict)
    print(r.response)
    return obj.response

    pass

if __name__ == '__main__':

    # o = SwarcoSTCIPManagement('10.45.154.11')
    r = asyncio.run(main())
    # print(r)


