import asyncio

from pysnmp.entity.engine import SnmpEngine
from pysnmp.proto.rfc1902 import Unsigned32

from sdp_lib.management_controllers.parsers.snmp_parsers.stcip_parsers import SwarcoStcipMonitoringParser
from sdp_lib.management_controllers.snmp.oids import Oids
from sdp_lib.management_controllers.snmp.snmp_base import StcipHost, SnmpHost


class AbstractGetRequest(StcipHost):

    method = SnmpHost.snmp_set
    oids: tuple[Oids, ...]

    def __init__(self, ip_v4: str, value):
        super().__init__(ip_v4)
        self.value = value

    def get_value(self):
        return self.value

    def get_oids(self):
        return self.oids





class SetStage(AbstractGetRequest):

    parser_class = SwarcoStcipMonitoringParser

    stage_values_set = {
        stage_num: Unsigned32(stage_num + 1) for stage_num in range(1, 8)
    } | {8: Unsigned32(1), 0: Unsigned32(0)}

    match_stages = {
        stage_val: stage_val - 1 for stage_val in range(2, 8)
    } | {1: 8}

    def get_oids(self):
        return [
            (Oids.swarcoUTCTrafftechPhaseCommand, self.stage_values_set.get(self.value, Unsigned32(0)))
        ]
        return self.stage_values_set.get(self.value, Unsigned32(0))

    # def get_command_data(self, val):
    #     return f'value: {val}'


async def main():

    obj = SetStage(ip_v4='10.179.65.17', value=0)
    r = await obj.request_and_parse_response(engine=SnmpEngine())
    print(obj.response_as_dict)
    print(r.response)
    return obj.response

    pass

if __name__ == '__main__':

    # o = SwarcoSTCIPManagement('10.45.154.11')
    r = asyncio.run(main())
    # print(r)


