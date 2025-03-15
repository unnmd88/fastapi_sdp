import math
import os

from pysnmp.entity.engine import SnmpEngine
from pysnmp.proto.rfc1902 import Unsigned32, OctetString, Gauge32, Integer
from pysnmp.smi.rfc1902 import ObjectIdentity

from sdp_lib.management_controllers.exceptions import BadControllerType
from sdp_lib.management_controllers.fields_names import FieldsNames
from sdp_lib.management_controllers.controller_modes import NamesMode
from sdp_lib.management_controllers.snmp.snmp_base import SnmpHost
from sdp_lib.management_controllers.snmp.oids import Oids


class BaseUG405(SnmpHost):

    scn_required_oids = {
        Oids.utcReplyGn, Oids.utcReplyFR, Oids.utcReplyDF, Oids.utcControlTO,
        Oids.utcControlFn, Oids.potokP_utcReplyPlanStatus, Oids.potokP_utcReplyPlanSource,
        Oids.potokP_utcReplyPlanSource, Oids.potokP_utcReplyDarkStatus,
        Oids.potokP_utcReplyLocalAdaptiv, Oids.potokP_utcReplyHardwareErr,
        Oids.potokP_utcReplySoftwareErr, Oids.potokP_utcReplyElectricalCircuitErr,
        Oids.utcReplyMC, Oids.utcReplyCF, Oids.utcReplyVSn, Oids.utcType2ScootDetectorCount
    }

    def __init__(self, ip_v4: str, host_id=None, scn=None):
        super().__init__(ip_v4, host_id)
        self.scn_as_chars = scn
        self.scn_as_dec = self.get_scn_as_ascii()

    def get_community(self) -> tuple[str, str]:
        return os.getenv('communityUG405_r'), os.getenv('communityUG405_w')

    def get_scn_as_ascii(self) -> str | None:
        if self.scn_as_chars is not None:
            return self.convert_scn(self.scn_as_chars)
        return None

    @staticmethod
    def convert_scn(scn: str) -> str:
        """
        Генерирует SCN
        :param scn -> символы строки, которые необходимо конвертировать в scn
        :return -> возвращет scn
        """
        return f'.1.{str(len(scn))}.{".".join([str(ord(c)) for c in scn])}'

    @property
    def host_protocol(self):
        return str(FieldsNames.protocol_ug405)

    def add_scn_to_oids(self, oids):
        return [f'{oid}{self.scn_as_dec}' if oid in self.scn_required_oids else oid for oid in oids]

    def processing_oid_from_response(self, oid: str) -> str:
        return oid.replace(self.scn_as_dec, '')

    def get_oids_for_get_request(self):
        return self.add_scn_to_oids(self.matches.keys())

    async def get_and_parse(self, engine: SnmpEngine = None):

        if self.scn_as_dec is None:
            error_indication, error_status, error_index, var_binds = await self.get(
                oids=[Oids.utcReplySiteID],
                engine=engine
            )
            try:
                self.set_scn_from_response(error_indication, error_status, error_index, var_binds)
            except BadControllerType as e:
                self.add_data_to_data_response_attrs(e)
        if self.ERRORS:
            return self

        return await super().get_and_parse(engine=engine)

    def set_scn_from_response(
            self,
            error_indication,
            error_status,
            error_index,
            var_binds
    ):
        raise NotImplementedError

    def convert_val_to_num_stage_get_req(self, val: str) -> int:
        """
        Конвертирует значение, полученное из oid фазы в номер фазы десятичного представления
        :param val: значение, необходимое отобразить в десятичном виде
        :return: значение(номер) фазы в десятичном виде
        """

        try:
            if val not in (' ', '@'):
                return int(math.log2(int(val, 16))) + 1
            elif val == ' ':
                return 6
            elif val == '@':
                return 7
        except ValueError:
            print(f'Значение val: {val}')


class PotokP(BaseUG405):

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

    def set_scn_from_response(
            self,
            error_indication,
            error_status,
            error_index,
            var_binds
    )-> None:

        if any(err for err in (error_indication, error_status, error_index)) or not var_binds:
            raise BadControllerType()

        try:
            self.scn_as_chars = str(var_binds[0][1])
            self.scn_as_dec = self.get_scn_as_ascii()
        except IndexError:
            raise BadControllerType()

    def get_current_mode(self, response_data: dict[str, str], mode=None) -> str | None:
        operation_mode, local_adaptive_status, num_detectors, has_det_faults, is_mode_man = (
            response_data.get(FieldsNames.operation_mode),
            response_data.get(FieldsNames.local_adaptive_status),
            response_data.get(FieldsNames.num_detectors),
            response_data.get(FieldsNames.has_det_faults),
            response_data.get(FieldsNames.is_mode_man),
        )
        match (operation_mode, local_adaptive_status, num_detectors, has_det_faults, is_mode_man):
            case ['1', '1', num_det, '0', _] if num_det is not None and num_det.isdigit() and int(num_det) > 0:
                return str(NamesMode.VA)
            case ['1', '0', '0', _, _]:
                return str(NamesMode.FT)
            case['3', _, _, _, _]:
                return str(NamesMode.CENTRAL)
            case[_, _, _, _, '1']:
                return str(NamesMode.MANUAL)
        return 'undefined'

    def get_current_status_mode(self, response_data: dict[str, str]) -> str | None:
        dark, flash = response_data.get(FieldsNames.dark), response_data.get(FieldsNames.flash)
        if dark == '0' and flash == '0':
            return str(FieldsNames.three_light)
        elif flash == '1':
            return str(FieldsNames.flash)
        elif dark == '1':
            return str(FieldsNames.dark)
        return None

    def add_extras_for_response(self, response_data: dict[str, str]) -> dict[str, str]:
        response_data[str(FieldsNames.curr_status_mode)] = self.get_current_status_mode(response_data)
        response_data[str(FieldsNames.curr_mode)] = self.get_current_mode(response_data)
        return response_data


