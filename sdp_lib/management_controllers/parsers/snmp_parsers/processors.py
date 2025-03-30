import abc
from functools import cached_property
from typing import Any

from pysnmp.smi.rfc1902 import ObjectType

from sdp_lib.management_controllers.controller_modes import NamesMode
from sdp_lib.management_controllers.fields_names import FieldsNames
from sdp_lib.management_controllers.parsers.snmp_parsers.mixins import StcipMixin
from sdp_lib.management_controllers.snmp.oids import Oids
from sdp_lib.management_controllers.snmp.response_structure import SnmpResponseStructure
from sdp_lib.management_controllers.snmp.smmp_utils import SwarcoConverters, Ug405Converters


class AbstractProcessor(abc.ABC):

    def __init__(
            self,
            *,
            host_instance,
            var_binds: tuple[ObjectType, ...] = None,
            mode_calculation=True
    ):
        self.host_instance = host_instance
        self.var_binds = var_binds or self.host_instance.last_response[SnmpResponseStructure.VAR_BINDS]
        self.mode_calculation = mode_calculation
        self._processed_response_data = {}

    @property
    def processed_response_data(self):
        return self._processed_response_data

    @property
    @abc.abstractmethod
    def matches(self):
        ...

    @abc.abstractmethod
    def get_current_mode(self):
        ...

    def get_val_as_str(self, val: int | str) -> str:
        return str(val)

    def process_oid(self, oid: str | Oids) -> str | Oids:
        return str(oid)

    def process_oid_val(self, val: Any) -> str | int:
        return val.prettyPrint()

    def process_varbinds(self) -> dict[str, str | None]:
        for oid, val in self.var_binds:
            print(f'oid: {str(oid)}::: val: {str(val)}')
            oid, val = self.process_oid(oid), self.process_oid_val(val)
            field_name, cb_fn = self.matches.get(oid)
            self._processed_response_data[field_name] = cb_fn(val)

        if self.mode_calculation:
            self._processed_response_data[FieldsNames.curr_mode] = self.get_current_mode()
        return self._processed_response_data


class SwarcoProcessor(AbstractProcessor, StcipMixin):

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
            self._processed_response_data.get(FieldsNames.curr_plan),
            self._processed_response_data.get(FieldsNames.plan_source),
            self._processed_response_data.get(FieldsNames.fixed_time_status),
            self._processed_response_data.get(FieldsNames.status_soft_flag180_181, ''),
            int(self._processed_response_data.get(FieldsNames.num_detectors, '0'))

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

    @cached_property
    def matches(self):
        return {
            Oids.swarcoUTCTrafftechFixedTimeStatus: (FieldsNames.fixed_time_status, self.get_val_as_str),
            Oids.swarcoUTCTrafftechPlanSource: (FieldsNames.plan_source, self.get_val_as_str),
            Oids.swarcoUTCStatusEquipment: (FieldsNames.curr_status, self.get_status),
            Oids.swarcoUTCTrafftechPhaseStatus: (FieldsNames.curr_stage, SwarcoConverters.get_num_stage_from_oid_val),
            Oids.swarcoUTCTrafftechPlanCurrent: (FieldsNames.curr_plan, self.get_val_as_str),
            Oids.swarcoUTCDetectorQty: (FieldsNames.num_detectors, self.get_val_as_str),
            Oids.swarcoSoftIOStatus: (FieldsNames.status_soft_flag180_181, self.get_soft_flags_180_181_status),
            Oids.swarcoUTCTrafftechPhaseCommand:
                (Oids.swarcoUTCTrafftechPhaseCommand,
                 lambda val: [val, self.stage_values_get.get(val)])
        }


class PotoPProcessor(AbstractProcessor):

    @cached_property
    def matches(self):
        return {
        Oids.utcType2OperationMode: (FieldsNames.operation_mode, self.get_val_as_str),
        Oids.potokP_utcReplyDarkStatus: (FieldsNames.dark, self.get_val_as_str),
        Oids.utcReplyFR: (FieldsNames.flash, self.get_val_as_str),
        Oids.utcReplyGn: (FieldsNames.curr_stage, Ug405Converters.get_num_stage_from_oid_val),
        Oids.potokP_utcReplyPlanStatus: (FieldsNames.curr_plan, self.get_val_as_str),
        Oids.potokP_utcReplyLocalAdaptiv: (FieldsNames.local_adaptive_status, self.get_val_as_str),
        Oids.utcType2ScootDetectorCount: (FieldsNames.num_detectors, self.get_val_as_str),
        Oids.utcReplyDF: (FieldsNames.has_det_faults, self.get_val_as_str),
        Oids.utcReplyMC: (FieldsNames.is_mode_man, self.get_val_as_str),
    }
