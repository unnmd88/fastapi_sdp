from sdp_lib.management_controllers.controller_modes import NamesMode
from sdp_lib.management_controllers.fields_names import FieldsNames
from sdp_lib.management_controllers.parsers.snmp_parsers.parsers_snmp_core import BaseSnmpParser
from sdp_lib.management_controllers.snmp.oids import Oids


class StcipExtensions(BaseSnmpParser):

    status_equipment = {
        '0': 'noInformation',
        '1': str(FieldsNames.three_light),
        '2': str(FieldsNames.power_up),
        '3': str(FieldsNames.dark),
        '4': str(FieldsNames.flash),
        '6': str(FieldsNames.all_red),
    }

    @classmethod
    def get_status(cls, value: str, ) -> str | None:
        return cls.status_equipment.get(value)

    @classmethod
    def convert_val_to_num_stage_get_req(cls, val) -> int | None:
        return cls.stage_values_get.get(val)

    def get_current_mode_and_add_to_extras_dict(self) -> None:
        self.extras_data[FieldsNames.curr_mode] = self.get_current_mode()


class SwarcoStcipMonitoringParser(StcipExtensions):

    stage_values_get = {'2': 1, '3': 2, '4': 3, '5': 4, '6': 5, '7': 6, '8': 7, '1': 8, '0': 0}

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

    CENTRAL_PLAN              = '16'
    MANUAL_PLAN               = '15'
    SYNC_PLAN                 = '13'
    CONTROL_BLOCK_SOURCE      = '3'
    CALENDAR_CLOCK_SOURCE     = '7'
    TRAFFIC_SITUATION_SOURCE  = '6'
    FT_STATUS_TRUE            = '1'
    FT_STATUS_FALSE           = '0'

    def get_soft_flags_180_181_status(self, octet_string: str) -> str:
        return octet_string[179: 181]

    def get_current_mode(self) -> str | None:

        match (
            self.parsed_content_as_dict.get(FieldsNames.curr_plan),
            self.parsed_content_as_dict.get(FieldsNames.plan_source),
            self.parsed_content_as_dict.get(FieldsNames.fixed_time_status),
            self.parsed_content_as_dict.get(FieldsNames.status_soft_flag180_181, ''),
            int(self.parsed_content_as_dict.get(FieldsNames.num_detectors, '0'))

        ):
            case [self.CENTRAL_PLAN, self.CONTROL_BLOCK_SOURCE, *rest]:
                return str(NamesMode.CENTRAL)
            case [_, _, self.FT_STATUS_FALSE, '00', num_det] if num_det > 0:
                return str(NamesMode.VA)
            case [_, self.CALENDAR_CLOCK_SOURCE, fixed_status, flag180_181, num_det] if (
                '1' in flag180_181 or num_det == 0 or fixed_status == self.FT_STATUS_TRUE
            ):
                return str(NamesMode.FT)
            case[self.MANUAL_PLAN, self.CONTROL_BLOCK_SOURCE, *rest]:
                return str(NamesMode.MANUAL)
            case[self.SYNC_PLAN, source_plan, *rest] if source_plan in (
                self.CONTROL_BLOCK_SOURCE, self.TRAFFIC_SITUATION_SOURCE
            ):
                return str(NamesMode.SYNC)
        return None

    @property
    def matches(self):
        return {
            Oids.swarcoUTCTrafftechFixedTimeStatus: (FieldsNames.fixed_time_status, self.get_val_as_str),
            Oids.swarcoUTCTrafftechPlanSource: (FieldsNames.plan_source, self.get_val_as_str),
            Oids.swarcoUTCStatusEquipment: (FieldsNames.curr_status, self.get_status),
            Oids.swarcoUTCTrafftechPhaseStatus: (FieldsNames.curr_stage, self.convert_val_to_num_stage_get_req),
            Oids.swarcoUTCTrafftechPlanCurrent: (FieldsNames.curr_plan, self.get_val_as_str),
            Oids.swarcoUTCDetectorQty: (FieldsNames.num_detectors, self.get_val_as_str),
            Oids.swarcoSoftIOStatus: (FieldsNames.status_soft_flag180_181, self.get_soft_flags_180_181_status),
            Oids.swarcoUTCTrafftechPhaseCommand:
                (f'{FieldsNames.set_stage}[{Oids.swarcoUTCTrafftechPhaseCommand}]',
                 lambda val: val)
        }

    def add_depends_data_to_response(self):
        self.parsed_content_as_dict[FieldsNames.curr_mode] = self.get_current_mode()

class PotokSMonitoringParser(StcipExtensions):

    stage_values_get = {str(k) if k < 66 else str(0): v if v < 65 else 0 for k, v in zip(range(2, 67), range(1, 66))}

    modes = {
        '8': str(NamesMode.VA),
        '10': str(NamesMode.MANUAL),
        '11': str(NamesMode.CENTRAL),
        '12': str(NamesMode.FT),
    }

    def get_current_mode(self) -> str | None:
        return self.modes.get(
            self.parsed_content_as_dict.get(FieldsNames.curr_status_mode)
        )

    @property
    def matches(self):
        return {
        Oids.swarcoUTCStatusEquipment: (FieldsNames.curr_status, self.get_status),
        Oids.swarcoUTCTrafftechPhaseStatus: (FieldsNames.curr_stage, self.convert_val_to_num_stage_get_req),
        Oids.swarcoUTCTrafftechPlanCurrent: (FieldsNames.curr_plan, self.get_val_as_str),
        Oids.swarcoUTCStatusMode: (FieldsNames.curr_status_mode, self.get_val_as_str),
        Oids.swarcoUTCDetectorQty: (FieldsNames.num_detectors, self.get_val_as_str),
    }