import abc
import math
import os

from pysnmp.proto.rfc1902 import Unsigned32, OctetString, Gauge32, Integer
from pysnmp.smi.rfc1902 import ObjectIdentity

from sdp_lib.management_controllers.responce import FieldsNames
from sdp_lib.management_controllers.controller_modes import NamesMode
from sdp_lib.management_controllers.snmp.snmp_base import SnmpHost
from sdp_lib.management_controllers.snmp.oids import Oids


class BaseUG405(SnmpHost):

    scn_required_oids = {
        Oids.utcReplyGn.value, Oids.utcReplyFR.value, Oids.utcReplyDF.value, Oids.utcControlTO.value,
        Oids.utcControlFn.value, Oids.potokP_utcReplyPlanStatus.value, Oids.potokP_utcReplyPlanSource.value,
        Oids.potokP_utcReplyPlanSource.value, Oids.potokP_utcReplyDarkStatus.value,
        Oids.potokP_utcReplyLocalAdaptiv.value, Oids.potokP_utcReplyHardwareErr.value,
        Oids.potokP_utcReplySoftwareErr.value, Oids.potokP_utcReplyElectricalCircuitErr.value,
        Oids.utcReplyMC.value, Oids.utcReplyCF.value, Oids.utcReplyVSn.value
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
        return [f'{oid}{self.scn_as_dec}' for oid in oids if oid in self.scn_required_oids]

    def processing_oid_from_response(self, oid: str) -> str:
        return oid.replace(self.scn_as_dec, '')

    def get_oids_for_get_request(self):
        return self.add_scn_to_oids(self.matches.keys())

class PotokP(BaseUG405):

    @property
    def matches(self):
        return {
        Oids.utcType2OperationMode: (FieldsNames.operation_mode, self.get_val_as_str),
        Oids.potokP_utcReplyDarkStatus: (FieldsNames.dark, self.get_val_as_str),
        Oids.utcReplyFR: (FieldsNames.flash, self.get_val_as_str),
        Oids.utcReplyGn: (FieldsNames.curr_stage, self.convert_val_to_num_stage_get_req),
        Oids.potokP_utcReplyPlanStatus: (FieldsNames.curr_plan, self.get_val_as_str),
        # Oids.swarcoUTCStatusMode: (FieldsNames.curr_status_mode, self.get_status_mode),

        # Oids.swarcoUTCDetectorQty: (FieldsNames.num_detectors, self.get_num_det),
        # Oids.swarcoSoftIOStatus: (FieldsNames.status_soft_flag180_181, self.get_soft_flags_status)
    }

    get_state_oids = {
        Oids.utcType2OperationMode.value,
        Oids.utcReplyCF.value,
        Oids.utcReplyFR.value,
        Oids.potokP_utcReplyDarkStatus.value,
        Oids.utcReplyMC.value,
        Oids.potokP_utcReplyPlanStatus.value,
        Oids.utcReplyGn.value,
        Oids.utcReplyDF.value,
        Oids.potokP_utcReplyLocalAdaptiv.value,
    }

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

    def set_scn_from_response(self, error_indication, var_binds: list) -> bool | None:

        if error_indication is not None or not var_binds:
            return None
        try:
            self.scn_as_chars = str(var_binds[0][1])
            self.scn_as_dec = self.get_scn_as_ascii()
            return True
        except IndexError:
            return None

    async def get_scn_snmp(self):
        if self.scn_as_dec is None:
            err, var_b = await self.get(
                oids=[Oids.utcReplySiteID]
            )
            if self.set_scn_from_response(err, var_b) is None:
                return err, var_b

        return None, []

    async def get_and_parse(self):
        if self.scn_as_dec is None:
            err, var_b = await self.get(
                oids=[Oids.utcReplySiteID]
            )
            if self.set_scn_from_response(err, var_b) is None:
                return err, var_b
        error_indication, var_binds = await self.get(
            oids=self.get_oids_for_get_request()
        )
        if error_indication is not None or not var_binds:
            return error_indication, var_binds
        parsed_response = self.parse_var_binds_from_response(var_binds)
        parsed_response = self.add_extras_for_response(parsed_response)
        print(f'ip: {self.ip_v4} | resp: {parsed_response}')
        return error_indication, parsed_response

    def get_current_mode(self, response_data: dict[str, str], mode=None) -> str | None:
        return 'Tets'

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


