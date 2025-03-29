from sdp_lib.management_controllers.controller_modes import NamesMode
from sdp_lib.management_controllers.fields_names import FieldsNames
from sdp_lib.management_controllers.parsers.snmp_parsers.parsers_snmp_core import BaseSnmpParser
from sdp_lib.management_controllers.snmp.oids import Oids


class UG405Extensions(BaseSnmpParser):

    UTC_OPERATION_MODE = '3'

    @classmethod
    def convert_val_to_num_stage_get_req(cls, val) -> int | None:
        return cls.convert_hex_to_decimal(val)

    def processing_oid_from_response(self, oid: str) -> str:
        return oid.replace(self.host_instance.scn_as_ascii_string , '')

    def add_depends_data_to_response(self):
        self.parsed_content_as_dict[FieldsNames.curr_mode] = self.get_current_mode()
        self.parsed_content_as_dict[FieldsNames.curr_status_mode] = self.get_current_status_mode()


class ParserPotokP(UG405Extensions):

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
            case ['1', '0', num_det, '1', _] if num_det is not None and num_det.isdigit() and int(num_det) > 0:
                return str(NamesMode.FT)
            case[self.UTC_OPERATION_MODE, *rest]:
                return str(NamesMode.CENTRAL)
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

    # def add_current_mode_to_response_if_has(self):
    #     self.parsed_content_as_dict[FieldsNames.curr_status_mode] = self.get_current_status_mode()
    #     self.parsed_content_as_dict[FieldsNames.curr_mode] = self.get_current_mode()