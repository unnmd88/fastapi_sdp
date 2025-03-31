import asyncio
import time
import typing
from typing import Callable

from sdp_lib.management_controllers.exceptions import BadControllerType
from sdp_lib.management_controllers.parsers.snmp_parsers.new_parsers_snmp_core import SwarcoStandardParser, \
    PotokPStandardParser, PotokSStandardParser
from sdp_lib.management_controllers.parsers.snmp_parsers.processors import PotokPProcessor
from sdp_lib.management_controllers.parsers.snmp_parsers.stcip_parsers import (
    SwarcoStcipMonitoringParser,
    PotokSMonitoringParser
)
from sdp_lib.management_controllers.snmp import host_data
from sdp_lib.management_controllers.snmp.response_structure import SnmpResponseStructure
from sdp_lib.management_controllers.snmp.smmp_utils import SwarcoConverters
from sdp_lib.management_controllers.snmp.snmp_core import (
    AbstractStcipHosts,
    AbstractUg405Hosts
)


class SwarcoStcip(AbstractStcipHosts):

    host_properties = host_data.swarco_stcip
    states_parser = SwarcoStandardParser
    converter_class = SwarcoConverters


class PotokS(AbstractStcipHosts):

    host_properties = host_data.potok_s
    states_parser = PotokSStandardParser


class PotokP(AbstractUg405Hosts):

    states_parser = PotokPStandardParser
    host_properties = host_data.potok_p

    def get_method_for_scn(self) -> Callable:
        return self.request_sender.snmp_get

    def set_scn_from_response(self) -> None | BadControllerType:
        try:
            self.scn_as_chars = str(self.last_response[SnmpResponseStructure.VAR_BINDS][0][1])
            self.scn_as_ascii_string = self.get_scn_as_ascii_from_scn_as_chars_attr()
        except IndexError:
            raise  BadControllerType()
        return None

    async def get_states(self):
        return await self._make_request_and_build_response(
            *self._get_config_for_curr_state()
        )


async def main():

    # obj = PotokS(ip_v4='10.179.68.177',)
    # obj = SwarcoStcip(ip_v4='10.179.20.129')
    # obj = SwarcoStcip(ip_v4='10.179.68.105')
    # obj = SwarcoStcip(ip_v4='10.179.57.1')
    obj = SwarcoStcip(ip_v4='10.179.61.33', host_id='3205')
    # obj = PotokS(ip_v4='10.179.68.177',)
    # obj = SwarcoStcip(ip_v4='10.179.57.1')

    # obj = PotokP(ip_v4='10.179.56.105')

    r = await obj.set_stage(0)
    print(obj.response_as_dict)
    print(r.response)
    return obj.response

    pass



if __name__ == '__main__':
    start_time = time.time()

    asyncio.run(main())

    print(f'время составло: {time.time() - start_time}')