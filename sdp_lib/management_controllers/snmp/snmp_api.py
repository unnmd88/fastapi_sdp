import asyncio
import time
import typing
from functools import cached_property
from typing import Callable

from pysnmp.entity.engine import SnmpEngine

from sdp_lib.management_controllers.exceptions import BadControllerType
from sdp_lib.management_controllers.parsers.snmp_parsers.new_parsers_snmp_core import StandartVarbindsParsersSwarco, \
    PotokPStandardParser, PeekStandardParser, StandardVarbindsParserPotokS, pretty_processing_ug405
from sdp_lib.management_controllers.parsers.snmp_parsers.processors import PotokPVarbindsProcessors
from sdp_lib.management_controllers.parsers.snmp_parsers.stcip_parsers import (
    SwarcoStcipMonitoringParser,
    PotokSMonitoringParser
)
from sdp_lib.management_controllers.snmp import host_data
from sdp_lib.management_controllers.snmp.oids import Oids
from sdp_lib.management_controllers.snmp.response_checkers import ErrorResponseCheckers
from sdp_lib.management_controllers.snmp.response_structure import SnmpResponseStructure
from sdp_lib.management_controllers.snmp.snmp_utils import SwarcoConverters, PotokSConverters, PotokPConverters, \
    PeekConverters
from sdp_lib.management_controllers.snmp.snmp_core import (
    AbstractStcipHosts,
    AbstractUg405Hosts, T_Oids, ug405_dependency, pretty_processing_config_processor
)
from sdp_lib.management_controllers.snmp.varbinds import swarco_sctip_varbinds, potok_ug405_varbinds, \
    potok_stcip_varbinds


class SwarcoStcip(AbstractStcipHosts):

    host_properties = host_data.swarco_stcip
    parser_class = StandartVarbindsParsersSwarco
    converter_class = SwarcoConverters
    varbinds = swarco_sctip_varbinds


class PotokS(AbstractStcipHosts):

    host_properties = host_data.potok_s
    parser_class = StandardVarbindsParserPotokS
    converter_class = PotokSConverters
    varbinds = potok_stcip_varbinds



class PotokP(AbstractUg405Hosts):

    parser_class = PotokPStandardParser
    host_properties = host_data.potok_p
    converter_class = PotokPConverters
    varbinds = potok_ug405_varbinds

    @property
    def method_for_get_scn(self) -> Callable:
        return self._request_sender.snmp_get

    def _set_scn_from_response(self) -> None | BadControllerType:
        try:
            self.scn_as_chars = str(self.last_response[SnmpResponseStructure.VAR_BINDS][0][1])
            self.scn_as_ascii_string = self._get_scn_as_ascii_from_scn_as_chars_attr()
        except IndexError:
            raise  BadControllerType()
        return None

    @ug405_dependency('potok__ug405')
    async def get_states(self):
        self._parse_method_config = self._get_pretty_processed_config()
        return await self._make_request_and_build_response(
            method=self._request_sender.snmp_get,
            varbinds=self._varbinds_for_request,
        )


class PeekUg405(AbstractUg405Hosts):

    parser_class = PeekStandardParser
    host_properties = host_data.potok_p
    converter_class = PeekConverters


    async def _set_operation_mode(self):
        self.response = await self._request_sender.snmp_get(self.converter_class.get_operation_mode_varbind)
        if ErrorResponseCheckers(self).check_response_errors_and_add_to_host_data_if_has():
            return
        if str(self.response[SnmpResponseStructure.VAR_BINDS][0][1]) == '1':
            await self._request_sender.snmp_set(self.converter_class.set_operation_mode2_varbind)
            if ErrorResponseCheckers(self).check_response_errors_and_add_to_host_data_if_has():
                return
        await self._request_sender.snmp_set(self.converter_class.set_operation_mode3_varbind)
        ErrorResponseCheckers(self).check_response_errors_and_add_to_host_data_if_has()

    async def _make_request_and_build_response(
            self,
            method: Callable,
            oids: T_Oids,
            parser: typing.Any,
    ):
        # if self.scn_as_ascii_string is None:
        #     self.last_response = await self._method_for_get_scn()(varbinds=[self.converter_class.scn_varbind])
        #     if ErrorResponseCheckers(self).check_response_errors_and_add_to_host_data_if_has():
        #         return self
        #     try:
        #         self._set_scn_from_response()
        #     except BadControllerType as e:
        #         self.add_data_to_data_response_attrs(e)

        await self.set_scn_and_add_err_to_data_response_if_has()

        if self.ERRORS:
            return self

        return await super()._make_request_and_build_response(
            method=method,
            varbinds=self.converter_class.add_scn_to_oids(
                oids_without_val=oids,
                scn_as_ascii_string=self.scn_as_ascii_string,
                scn_as_chars_string=self.scn_as_chars,
                wrap_oid_by_object_identity=True
                ),
            parser=parser
        )

        # return await super()._make_request_and_build_response(
        #     method=method,
        #     varbinds=self.converter_class.get_varbinds_for_get_state(
        #         scn_as_ascii_string=self.scn_as_ascii_string,
        #         scn_as_chars_string=self.scn_as_chars
        #         ),
        #     parser=parser
        # )

    def _set_scn_from_response(self) -> None | BadControllerType:
        print(f'1: {str(self.last_response[SnmpResponseStructure.VAR_BINDS][0][1])}')
        try:
            self.scn_as_ascii_string = str(self.last_response[SnmpResponseStructure.VAR_BINDS][0][0]).replace(Oids.utcReplyGn, "")
            self.scn_as_chars = self.get_scn_as_chars_from_scn_as_ascii()
        except IndexError:
            raise  BadControllerType()
        return None


    def _method_for_get_scn(self) -> Callable:
        return self._request_sender.snmp_get_next




async def main():

    obj = PotokS(ip_v4='10.179.68.177',)
    # obj = SwarcoStcip(ip_v4='10.179.20.129')
    # obj = SwarcoStcip(ip_v4='10.179.68.105')
    # obj = SwarcoStcip(ip_v4='10.179.57.1')
    # obj = SwarcoStcip(ip_v4='10.179.61.33', host_id='3205')
    # obj = PotokS(ip_v4='10.179.68.177',)
    obj = SwarcoStcip(ip_v4='10.179.57.1')

    # obj = PotokP(ip_v4='10.179.69.65', host_id='2600')
    obj = PotokP(ip_v4='10.179.56.105', host_id='155')
    # obj = SwarcoStcip(ip_v4='10.179.20.129')

    # obj.ip_v4 = '10.179.20.129'
    # obj.set_engine(SnmpEngine())

    start_time = time.time()

    r = await obj.get_states()
    print(obj.response_as_dict)
    print(r.response)
    print(f'время составло: {time.time() - start_time}')

    return obj.response





if __name__ == '__main__':

    asyncio.run(main())

