import asyncio
import time

from sdp_lib.management_controllers.exceptions import BadControllerType
from sdp_lib.management_controllers.parsers.snmp_parsers.new_parsers_snmp_core import SwarcoStandardParser, \
    PotokPStandardParser
from sdp_lib.management_controllers.parsers.snmp_parsers.processors import PotokPProcessor
from sdp_lib.management_controllers.parsers.snmp_parsers.stcip_parsers import (
    SwarcoStcipMonitoringParser,
    PotokSMonitoringParser
)
from sdp_lib.management_controllers.parsers.snmp_parsers.ug405_parsers import ParserPotokP
from sdp_lib.management_controllers.snmp import host_data
from sdp_lib.management_controllers.snmp.response_structure import SnmpResponseStructure
from sdp_lib.management_controllers.snmp.snmp_core import (
    AbstractStcipHosts,
    AbstractUg405Hosts
)


class SwarcoStcip(AbstractStcipHosts):

    host_properties = host_data.swarco_stcip
    # states_parser = SwarcoStcipMonitoringParser
    states_parser = SwarcoStandardParser


class PotokS(AbstractStcipHosts):

    host_properties = host_data.potok_s
    states_parser = PotokSMonitoringParser


class PotokP(AbstractUg405Hosts):

    # states_parser = ParserPotokP
    states_parser = PotokPStandardParser
    host_properties = host_data.potok_p

    def set_scn_from_response(self) -> None | BadControllerType:
        try:
            self.scn_as_chars = str(self.last_response[SnmpResponseStructure.VAR_BINDS][0][1])
            self.scn_as_ascii_string = self.get_scn_as_ascii_from_scn_as_chars_attr()
        except IndexError:
            raise  BadControllerType()
        return None

    async def get_states(self):
        return await self.make_get_request_and_parse_response(self.host_properties.oids_get_state, self.states_parser)

    def _get_config_for_curr_state(self):
        return (
            self.host_properties.oids_get_state,
            self.request_sender.snmp_get,
            self.states_parser,
            True,
            'pretty'
        )


async def main():

    # obj = PotokS(ip_v4='10.179.68.177',)
    # obj = SwarcoStcip(ip_v4='10.179.20.129')
    # obj = SwarcoStcip(ip_v4='10.179.68.105')
    # obj = SwarcoStcip(ip_v4='10.179.57.1')
    # obj = PotokS(ip_v4='10.179.68.177',)
    obj = SwarcoStcip(ip_v4='10.179.57.1')

    obj = PotokP(ip_v4='10.179.56.105')

    r = await obj.get_states()
    print(obj.response_as_dict)
    print(r.response)
    return obj.response

    pass



if __name__ == '__main__':
    start_time = time.time()

    asyncio.run(main())

    print(f'время составло: {time.time() - start_time}')