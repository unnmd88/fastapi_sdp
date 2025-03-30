from sdp_lib.management_controllers.parsers.snmp_parsers.stcip_parsers import PotokSMonitoringParser
from sdp_lib.management_controllers.snmp import host_data, oids


class MixinCurrentStatesPotokS:
    host_properties = host_data.potok_s
    oids_get_state = oids.oids_state_potok_s
    states_parser = PotokSMonitoringParser