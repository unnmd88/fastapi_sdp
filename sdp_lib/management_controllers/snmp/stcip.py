import os

from pysnmp.hlapi.v3arch.asyncio import *

from sdp_lib.management_controllers.responce import FieldsNames
from sdp_lib.management_controllers.controller_modes import NamesMode
from sdp_lib.management_controllers.snmp.snmp_base import SnmpAllProtocols
from sdp_lib.management_controllers.snmp.oids import Oids


class BaseSTCIP(SnmpAllProtocols):

    def get_community(self) -> tuple[str, str]:
        return os.getenv('communitySTCIP_r'), os.getenv('communitySTCIP_w')

    async def get_multiple(self, oids: list[str | Oids]):
        print('я в функции get_multiple')
        res = await self.get_request(oids=oids)
        print('я в функции get_multiple перед return')
        return res


class BaseSwarcoSTCIP(BaseSTCIP):

    status_equipment = {
        '0': 'noInformation',
        '1': str(FieldsNames.three_light),
        '2': str(FieldsNames.power_up),
        '3': str(FieldsNames.dark),
        '4': str(FieldsNames.flash),
        '6': str(FieldsNames.all_red),
    }
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
    stage_values_set = {'1': 2, '2': 3, '3': 4, '4': 5, '5': 6, '6': 7, '7': 8, '8': 1, 'ЛОКАЛ': 0, '0': 0}

    @property
    def matches(self):
        return {
        Oids.swarcoUTCTrafftechFixedTimeStatus: (FieldsNames.fixed_time_status, self.get_fixed_time_status),
        Oids.swarcoUTCTrafftechPlanSource: (FieldsNames.plan_source, self.get_plan_source),
        Oids.swarcoUTCStatusEquipment: (FieldsNames.curr_status, self.get_status),
        Oids.swarcoUTCTrafftechPhaseStatus: (FieldsNames.curr_stage, self.convert_val_to_num_stage_get_req),
        Oids.swarcoUTCTrafftechPlanCurrent: (FieldsNames.curr_plan, self.get_plan),
        Oids.swarcoUTCDetectorQty: (FieldsNames.num_detectors, self.get_num_det),
        Oids.swarcoSoftIOStatus: (FieldsNames.status_soft_flag180_181, self.get_soft_flags_status)
    }

    def get_plan_source(self, value: str) -> str:
        return value

    def get_status(self, value: str, ) -> str:
        return self.status_equipment.get(value)

    def get_fixed_time_status(self, value: str) -> str:
        return value

    def get_num_det(self, value: str) -> str:
        return value

    def get_soft_flags_status(self, octet_string: str, start: int = 179, stop: int = 181, ) -> str:
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

    def parse_response(
            self,
            response: [tuple[ObjectIdentity, OctetString | Gauge32 | Integer | Unsigned32]]
    ) -> dict[str, str]:
        resp = {}
        for oid, val in response:
            oid, val = str(oid), str(val)
            field_name, fn = self.matches.get(oid)
            resp[str(field_name)] = fn(val)
        print(f'ip: {self.ip_v4} | resp: {resp}')
        return resp

    # async def get_stage(self):
    #     error_indication, var_binds = await self.get_request(
    #         oids=[Oids.swarcoUTCTrafftechPhaseStatus]
    #     )
    #     return error_indication, self.parse_response(var_binds)

    async def get_stage(self):
        return await self.get_request_and_parse_response(
            oids=[Oids.swarcoUTCTrafftechPhaseStatus]
        )


class SwarcoCurrentStatesSTCIP(BaseSwarcoSTCIP):

    def parse_response(
            self,
            response: [tuple[ObjectIdentity, OctetString | Gauge32 | Integer | Unsigned32]]
    ) -> dict[str, str]:
        resp = super().parse_response(response=response)
        resp[str(FieldsNames.curr_mode)] = self.get_current_mode(resp)
        print(f'ip: {self.ip_v4} | resp: {resp}')
        return resp

    async def get_data_for_basic_current_state(self):

        return await self.get_request_and_parse_response(
            oids=self.matches.keys()
        )


        #
        # error_indication, var_binds = await self.get_request(
        #     oids=self.matches.keys()
        # )
        # return error_indication, self.parse_response(var_binds)