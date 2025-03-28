import asyncio
import os

from pysnmp.entity.engine import SnmpEngine
from pysnmp.proto.rfc1902 import Unsigned32

from sdp_lib.management_controllers.fields_names import FieldsNames
from sdp_lib.management_controllers.controller_modes import NamesMode
from sdp_lib.management_controllers.parsers.snmp_parsers.parsers_snmp import MainParser
from sdp_lib.management_controllers.snmp.snmp_base import SnmpHost
from sdp_lib.management_controllers.snmp.oids import Oids


class BaseSTCIP(SnmpHost):

    status_equipment = {
        '0': 'noInformation',
        '1': str(FieldsNames.three_light),
        '2': str(FieldsNames.power_up),
        '3': str(FieldsNames.dark),
        '4': str(FieldsNames.flash),
        '6': str(FieldsNames.all_red),
    }

    @property
    def host_protocol(self):
        return str(FieldsNames.protocol_stcip)

    def get_community(self) -> tuple[str, str]:
        return os.getenv('communitySTCIP_r'), os.getenv('communitySTCIP_w')

    def get_oids_for_get_request(self):
        return self.matches.keys()

    def processing_oid_from_response(self, oid: str) -> str:
        return oid

    def get_status(self, value: str, ) -> str:
        return self.status_equipment.get(value)

    def add_extras_for_response(self, response_data: dict[str, str]) -> dict[str, str]:
        response_data[str(FieldsNames.curr_mode)] = self.get_current_mode(response_data)
        return response_data


class SwarcoSTCIP(BaseSTCIP):

    plan_source = {
        '1': 'trafficActuatedPlanSelectionCommand',
        '2': 'currentTrafficSituationCentral',
        '3': 'controlBlockOrInput',
        '4': 'manuallyFromWorkstation',
        '5': 'emergencyRoute',
        '6': 'currentTrafficSituation',
        '7': 'calendarClock',
        '8': 'controlBlockInLocal',
        '9': 'forcedByParameterBP40',
        '10': 'startUpPlan',
        '11': 'localPlan',
        '12': 'manualControlPlan',
    }
    stage_values_get = {'2': 1, '3': 2, '4': 3, '5': 4, '6': 5, '7': 6, '8': 7, '1': 8, '0': 0}

    @property
    def matches(self):
        return {
        Oids.swarcoUTCTrafftechFixedTimeStatus: (FieldsNames.fixed_time_status, self.get_val_as_str),
        Oids.swarcoUTCTrafftechPlanSource: (FieldsNames.plan_source, self.get_val_as_str),
        Oids.swarcoUTCStatusEquipment: (FieldsNames.curr_status, self.get_status),
        Oids.swarcoUTCTrafftechPhaseStatus: (FieldsNames.curr_stage, self.convert_val_to_num_stage_get_req),
        Oids.swarcoUTCTrafftechPlanCurrent: (FieldsNames.curr_plan, self.get_val_as_str),
        Oids.swarcoUTCDetectorQty: (FieldsNames.num_detectors, self.get_val_as_str),
        Oids.swarcoSoftIOStatus: (FieldsNames.status_soft_flag180_181, self.get_soft_flags_180_181_status)
    }

    def get_soft_flags_180_181_status(self, octet_string: str) -> str:
        return octet_string[179: 181]

    def get_soft_flags_status(self, octet_string: str, start: int, stop: int, ) -> str:
        return octet_string[start: stop]

    def get_current_mode(self, response_data: dict[str, str], mode=None) -> str | None:

        if response_data.get(FieldsNames.curr_plan) == '16' and response_data.get(FieldsNames.plan_source) == '3':
            mode = str(NamesMode.CENTRAL)
        elif (
            response_data.get(FieldsNames.fixed_time_status) == '1'
            or '1' in response_data.get(FieldsNames.status_soft_flag180_181, '')
            or response_data.get(FieldsNames.num_detectors) == '0'
        ):
            mode = str(NamesMode.FT)
        elif (
            response_data.get(FieldsNames.fixed_time_status) == '0'
            and '1' not in response_data.get(FieldsNames.status_soft_flag180_181, '')
            and int(response_data.get(FieldsNames.num_detectors)) > 0
        ):
            mode = str(NamesMode.VA)
        elif response_data.get(FieldsNames.curr_plan) == '15' and response_data.get(FieldsNames.plan_source) == '3':
            mode = str(NamesMode.MANUAL)
        elif response_data.get(FieldsNames.curr_plan) == '13' and response_data.get(FieldsNames.plan_source) == '3':
            mode = str(NamesMode.SYNC)
        return mode


class PotokS(BaseSTCIP):

    stage_values_get = {str(k) if k < 66 else str(0): v if v < 65 else 0 for k, v in zip(range(2, 67), range(1, 66))}
    stage_values_set = {str(k): str(v) if k > 0 else '0' for k, v in zip(range(65), range(1, 66))}
    modes = {
        '8': str(NamesMode.VA),
        '10': str(NamesMode.MANUAL),
        '11': str(NamesMode.CENTRAL),
        '12': str(NamesMode.FT),
    }

    @property
    def matches(self):
        return {
        Oids.swarcoUTCStatusEquipment: (FieldsNames.curr_status, self.get_status),
        Oids.swarcoUTCTrafftechPhaseStatus: (FieldsNames.curr_stage, self.convert_val_to_num_stage_get_req),
        Oids.swarcoUTCTrafftechPlanCurrent: (FieldsNames.curr_plan, self.get_val_as_str),
        Oids.swarcoUTCStatusMode: (FieldsNames.curr_status_mode, self.get_val_as_str),
        Oids.swarcoUTCDetectorQty: (FieldsNames.num_detectors, self.get_val_as_str),
    }

    def get_current_mode(self, response_data: dict[str, str], mode=None) -> str | None:
        return self.modes.get(response_data.get(FieldsNames.curr_status_mode))


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


    o = SwarcoSTCIPManagement('10.179.116.113', host_id='2095')
    r_ = await o.set_stage('0')
    MainParser.parse_varbinds_base(r_[3])
    # print(o)
    return r_



if __name__ == '__main__':

    # o = SwarcoSTCIPManagement('10.45.154.11')
    r = asyncio.run(main())
    # print(r)