import abc
import typing
from collections.abc import Callable
from functools import cached_property

from mypyc.ir.ops import TypeVar
from pysnmp.smi.rfc1902 import ObjectType

from sdp_lib.management_controllers.controller_modes import NamesMode
from sdp_lib.management_controllers.fields_names import FieldsNames
from sdp_lib.management_controllers.parsers.snmp_parsers.mixins import (
    StcipMixin,
    Ug405Mixin
)
from sdp_lib.management_controllers.snmp.oids import Oids
from sdp_lib.management_controllers.snmp.response_structure import SnmpResponseStructure
from sdp_lib.management_controllers.snmp.snmp_utils import (
    SwarcoConverters,
    PotokPConverters, PotokSConverters, PeekConverters
)


T_Varbinds = tuple[ObjectType, ...]


class ConfigsProcessor(typing.NamedTuple):
    # current_mode: bool = False
    oid_handler: Callable = None
    val_oid_handler: Callable = None


class AbstractVarbindsProcessors(abc.ABC):

    def __init__(self, host_instance):
        self.host_instance = host_instance
        self._processed_response_data = {}

    @property
    def processed_response_data(self):
        return self._processed_response_data

    @property
    @abc.abstractmethod
    def matches(self) -> dict[str | Oids, tuple[FieldsNames, Callable]]:
        ...

    @abc.abstractmethod
    def get_current_mode(self):
        ...

    def get_val_as_str(self, val: int | str) -> str:
        return str(val)

    def get_oid_val_as_pretty_print(self, val) -> str:
        return val.prettyPrint()

    @property
    @abc.abstractmethod
    def extras_methods(self) -> dict[str, Callable]:
        ...

    def get_varbinds(self) -> T_Varbinds:
        return self.host_instance.last_response[SnmpResponseStructure.VAR_BINDS]

    def custom_parse_varbinds(
            self,
            *,
            varbinds,
            oid_handler: Callable = None,
            val_oid_handler: Callable = None,
    ):
        oid_handler = oid_handler or str
        val_oid_handler = val_oid_handler or self.get_oid_val_as_pretty_print
        for oid, val in varbinds:
            oid, val = oid_handler(oid), val_oid_handler(val)
            print(f'oid: {oid}  >>>> val: {val}')
            print(f'oid: {oid}  >>>> type(val): {type(val)}')
            self._processed_response_data[oid] = val

    def process_varbinds(self, varbinds: T_Varbinds = None) -> dict[str, str | None]:
        if self.host_instance.processor_config.oid_handler is None and self.host_instance.processor_config.val_oid_handler is None:
            for oid, val in (varbinds or self.get_varbinds()):
                print(f'oid: {str(oid)}::: val: {str(val)}')
                # oid, val = self.process_oid(oid), self.process_oid_val(val)
                oid, val = self.host_instance.process_oid(oid), self.host_instance.process_oid_val(val)
                field_name, cb_fn = self.matches.get(oid)
                if field_name is None or cb_fn is None:
                    self._processed_response_data[oid] = val.prettyPrint()
                else:
                    self._processed_response_data[field_name] = cb_fn(val)

                for field_name, cb_fn in self.extras_methods.items():
                    self._processed_response_data[field_name] = cb_fn()

        else:
            self.custom_parse_varbinds(
                varbinds=varbinds,
                oid_handler=self.host_instance.processor_config.oid_handler,
                val_oid_handler=self.host_instance.processor_config.val_oid_handler
            )
        return self._processed_response_data


class SwarcoVarbindsProcessors(AbstractVarbindsProcessors, StcipMixin):

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

    @property
    def extras_methods(self) -> dict[str, Callable]:
        return {FieldsNames.curr_mode: self.get_current_mode}

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


class PotokSVarbindsProcessors(AbstractVarbindsProcessors, StcipMixin):

    modes = {
        '8': str(NamesMode.VA),
        '10': str(NamesMode.MANUAL),
        '11': str(NamesMode.CENTRAL),
        '12': str(NamesMode.FT),
    }

    def get_current_mode(self) -> str | None:
        return self.modes.get(
            self._processed_response_data.get(FieldsNames.curr_status_mode)
        )

    @property
    def extras_methods(self) -> dict[str, Callable]:
        return {FieldsNames.curr_mode: self.get_current_mode}

    @cached_property
    def matches(self):
        return {
        Oids.swarcoUTCStatusEquipment: (FieldsNames.curr_status, self.get_status),
        Oids.swarcoUTCTrafftechPhaseStatus: (FieldsNames.curr_stage, PotokSConverters.get_num_stage_from_oid_val),
        Oids.swarcoUTCTrafftechPlanCurrent: (FieldsNames.curr_plan, self.get_val_as_str),
        Oids.swarcoUTCStatusMode: (FieldsNames.curr_status_mode, self.get_val_as_str),
        Oids.swarcoUTCDetectorQty: (FieldsNames.num_detectors, self.get_val_as_str),
    }


class PotokPVarbindsProcessors(AbstractVarbindsProcessors, Ug405Mixin):

    def get_current_mode(self) -> str | None:

        match (
            self._processed_response_data.get(FieldsNames.operation_mode),
            self._processed_response_data.get(FieldsNames.local_adaptive_status),
            self._processed_response_data.get(FieldsNames.num_detectors),
            self._processed_response_data.get(FieldsNames.has_det_faults),
            self._processed_response_data.get(FieldsNames.is_mode_man),
        ):
            case ['1', '1', num_det, '0', _] if num_det is not None and num_det.isdigit() and int(num_det) > 0:
                return str(NamesMode.VA)
            case ['1', '0', '0', _, _]:
                return str(NamesMode.FT)
            case ['1', '0', num_det, '1', _] if num_det is not None and num_det.isdigit() and int(num_det) > 0:
                return str(NamesMode.FT)
            case[self.UTC_OPERATION_MODE, *rest]:
                return str(NamesMode.CENTRAL)
            case[*rest, '1']:
                return str(NamesMode.MANUAL)
        return None

    def get_current_status_mode(self) -> str | None:
        dark, flash = (
            self._processed_response_data.get(FieldsNames.dark),
            self._processed_response_data.get(FieldsNames.flash)
        )
        if dark == '0' and flash == '0':
            return str(FieldsNames.three_light)
        elif flash == '1':
            return str(FieldsNames.flash)
        elif dark == '1':
            return str(FieldsNames.dark)
        return None

    @property
    def extras_methods(self) -> dict[str, Callable]:
        return {
            FieldsNames.curr_status_mode: self.get_current_status_mode,
            FieldsNames.curr_mode: self.get_current_mode
        }

    @cached_property
    def matches(self):
        return {
        Oids.utcType2OperationMode: (FieldsNames.operation_mode, self.get_val_as_str),
        Oids.potokP_utcReplyDarkStatus: (FieldsNames.dark, self.get_val_as_str),
        Oids.utcReplyFR: (FieldsNames.flash, self.get_val_as_str),
        Oids.utcReplyGn: (FieldsNames.curr_stage, PotokPConverters.get_num_stage_from_oid_val),
        Oids.potokP_utcReplyPlanStatus: (FieldsNames.curr_plan, self.get_val_as_str),
        Oids.potokP_utcReplyLocalAdaptiv: (FieldsNames.local_adaptive_status, self.get_val_as_str),
        Oids.utcType2ScootDetectorCount: (FieldsNames.num_detectors, self.get_val_as_str),
        Oids.utcReplyDF: (FieldsNames.has_det_faults, self.get_val_as_str),
        Oids.utcReplyMC: (FieldsNames.is_mode_man, self.get_val_as_str),
    }


class PeekPVarbindsProcessors(AbstractVarbindsProcessors, Ug405Mixin):

    def get_current_mode(self) -> str | None:

        return None

    @property
    def extras_methods(self) -> dict[str, Callable]:
        return {

        }

    @cached_property
    def matches(self):
        return {
        Oids.utcType2OperationMode: (FieldsNames.operation_mode, self.get_val_as_str),
        Oids.potokP_utcReplyDarkStatus: (FieldsNames.dark, self.get_val_as_str),
        Oids.utcReplyFR: (FieldsNames.flash, self.get_val_as_str),
        Oids.utcReplyGn: (FieldsNames.curr_stage, PeekConverters.get_num_stage_from_oid_val),
        Oids.potokP_utcReplyPlanStatus: (FieldsNames.curr_plan, self.get_val_as_str),
        Oids.potokP_utcReplyLocalAdaptiv: (FieldsNames.local_adaptive_status, self.get_val_as_str),
        Oids.utcType2ScootDetectorCount: (FieldsNames.num_detectors, self.get_val_as_str),
        Oids.utcReplyDF: (FieldsNames.has_det_faults, self.get_val_as_str),
        Oids.utcReplyMC: (FieldsNames.is_mode_man, self.get_val_as_str),
    }