from sdp_lib.management_controllers.controller_modes import NamesMode
from sdp_lib.management_controllers.fields_names import FieldsNames
from sdp_lib.management_controllers.parsers.snmp_parsers.parsers_snmp_core import BaseSnmpParser
from sdp_lib.management_controllers.snmp.oids import Oids


class BaseUG405(BaseSnmpParser):

    UTC_OPERATION_MODE = '3'

    def processing_oid_from_response(self, oid: str) -> str:
        return oid.replace(self.host_instance.scn_as_dec , '')

    @classmethod
    def convert_val_to_num_stage_get_req(cls, val) -> int | None:
        return cls.convert_hex_to_decimal(val)


class ParserPotokP(BaseUG405):

    @property
    def matches(self):
        return {
        Oids.utcType2OperationMode: (FieldsNames.operation_mode, self.get_val_as_str),
        Oids.potokP_utcReplyDarkStatus: (FieldsNames.dark, self.get_val_as_str),
        Oids.utcReplyFR: (FieldsNames.flash, self.get_val_as_str),
        Oids.utcReplyGn: (FieldsNames.curr_stage, self.convert_val_to_num_stage_get_req),
        Oids.potokP_utcReplyPlanStatus: (FieldsNames.curr_plan, self.get_val_as_str),
        Oids.potokP_utcReplyLocalAdaptiv: (FieldsNames.local_adaptive_status, self.get_val_as_str),
        Oids.utcType2ScootDetectorCount: (FieldsNames.num_detectors, self.get_val_as_str),
        Oids.utcReplyDF: (FieldsNames.has_det_faults, self.get_val_as_str),
        Oids.utcReplyMC: (FieldsNames.is_mode_man, self.get_val_as_str),
    }

    def get_current_mode(self) -> str | None:
        # operation_mode, local_adaptive_status, num_detectors, has_det_faults, is_mode_man = (
        #     self.parsed_content_as_dict .get(FieldsNames.operation_mode),
        #     self.parsed_content_as_dict.get(FieldsNames.local_adaptive_status),
        #     self.parsed_content_as_dict.get(FieldsNames.num_detectors),
        #     self.parsed_content_as_dict.get(FieldsNames.has_det_faults),
        #     self.parsed_content_as_dict.get(FieldsNames.is_mode_man),
        # )
        match (
            self.parsed_content_as_dict.get(FieldsNames.operation_mode),
            self.parsed_content_as_dict.get(FieldsNames.local_adaptive_status),
            self.parsed_content_as_dict.get(FieldsNames.num_detectors),
            self.parsed_content_as_dict.get(FieldsNames.has_det_faults),
            self.parsed_content_as_dict.get(FieldsNames.is_mode_man),
        ):
            case ['1', '1', num_det, '0', _] if num_det is not None and num_det.isdigit() and int(num_det) > 0:
                return str(NamesMode.VA)
            case ['1', '0', '0', _, _]:
                return str(NamesMode.FT)
            # case[self.UTC_OPERATION_MODE, _, _, _, _]:
            case[self.UTC_OPERATION_MODE,*rest]:
                return str(NamesMode.CENTRAL)
            # case[_, _, _, _, '1']:
            case[*rest, '1']:
                return str(NamesMode.MANUAL)
        return None

    def get_current_status_mode(self) -> str | None:
        dark, flash = (
            self.parsed_content_as_dict.get(FieldsNames.dark),
            self.parsed_content_as_dict.get(FieldsNames.flash)
        )
        if dark == '0' and flash == '0':
            return str(FieldsNames.three_light)
        elif flash == '1':
            return str(FieldsNames.flash)
        elif dark == '1':
            return str(FieldsNames.dark)
        return None

    def add_current_mode_to_response(self):
        self.parsed_content_as_dict[FieldsNames.curr_status_mode] = self.get_current_status_mode()
        self.parsed_content_as_dict[FieldsNames.curr_mode] = self.get_current_mode()