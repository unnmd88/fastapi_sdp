from sdp_lib.management_controllers.exceptions import BadControllerType
from sdp_lib.management_controllers.parsers.snmp_parsers.ug405_parsers import ParserPotokP
from sdp_lib.management_controllers.snmp.oids import Oids
from sdp_lib.management_controllers.snmp.snmp_base import UG405Host, SnmpHost


class AbstractGetRequest(UG405Host):

    method = SnmpHost.snmp_get
    oids: tuple[Oids, ...]

    def get_oids(self):
        return self.add_scn_to_oids(self.oids)


class MonitoringPotokP(AbstractGetRequest):

    parser_class = ParserPotokP

    oids = (
        Oids.utcType2OperationMode,
        Oids.potokP_utcReplyDarkStatus,
        Oids.utcReplyFR,
        Oids.utcReplyGn,
        Oids.potokP_utcReplyPlanStatus,
        Oids.potokP_utcReplyLocalAdaptiv,
        Oids.utcType2ScootDetectorCount,
        Oids.utcReplyDF,
        Oids.utcReplyMC,
    )

    def set_scn_from_response(
            self,
            error_indication,
            error_status,
            error_index,
            var_binds
    )-> None:
        print(f'str(var_binds[0][1]): {str(var_binds[0][1])}')

        if any(err for err in (error_indication, error_status, error_index)) or not var_binds:
            raise BadControllerType()

        try:
            self.scn_as_chars = str(var_binds[0][1])
            self.scn_as_dec = self.get_scn_as_ascii()
        except IndexError:
            raise BadControllerType()
