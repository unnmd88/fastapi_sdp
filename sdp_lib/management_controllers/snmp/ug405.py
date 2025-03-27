import os

from pysnmp.entity.engine import SnmpEngine
from pysnmp.proto.rfc1902 import Unsigned32, OctetString, Gauge32, Integer
from pysnmp.smi.rfc1902 import ObjectIdentity

from sdp_lib.management_controllers.exceptions import BadControllerType
from sdp_lib.management_controllers.fields_names import FieldsNames
from sdp_lib.management_controllers.controller_modes import NamesMode
from sdp_lib.management_controllers.parsers.snmp_parsers.ug405_parsers import ParserPotokP
from sdp_lib.management_controllers.snmp.snmp_base import SnmpHost
from sdp_lib.management_controllers.snmp.oids import Oids


# class BaseUG405(SnmpHost):
#
#     scn_required_oids = {
#         Oids.utcReplyGn, Oids.utcReplyFR, Oids.utcReplyDF, Oids.utcControlTO,
#         Oids.utcControlFn, Oids.potokP_utcReplyPlanStatus, Oids.potokP_utcReplyPlanSource,
#         Oids.potokP_utcReplyPlanSource, Oids.potokP_utcReplyDarkStatus,
#         Oids.potokP_utcReplyLocalAdaptiv, Oids.potokP_utcReplyHardwareErr,
#         Oids.potokP_utcReplySoftwareErr, Oids.potokP_utcReplyElectricalCircuitErr,
#         Oids.utcReplyMC, Oids.utcReplyCF, Oids.utcReplyVSn, Oids.utcType2ScootDetectorCount
#     }
#
#     def __init__(self, ip_v4: str, host_id=None, scn=None):
#         super().__init__(ip_v4, host_id)
#         self.scn_as_chars = scn
#         self.scn_as_dec = self.get_scn_as_ascii()
#
#     def get_community(self) -> tuple[str, str]:
#         return os.getenv('communityUG405_r'), os.getenv('communityUG405_w')
#
#     def get_scn_as_ascii(self) -> str | None:
#         if self.scn_as_chars is not None:
#             return self.convert_scn(self.scn_as_chars)
#         return None
#
#     @staticmethod
#     def convert_scn(scn: str) -> str:
#         """
#         Генерирует SCN
#         :param scn -> символы строки, которые необходимо конвертировать в scn
#         :return -> возвращет scn
#         """
#         return f'.1.{str(len(scn))}.{".".join([str(ord(c)) for c in scn])}'
#
#     @property
#     def host_protocol(self):
#         return str(FieldsNames.protocol_ug405)
#
#     def add_scn_to_oids(self, oids):
#         return [f'{oid}{self.scn_as_dec}' if oid in self.scn_required_oids else oid for oid in oids]
#
#     def get_oids_for_get_state(self):
#         return self.add_scn_to_oids(self.matches.keys())
#
#     async def get_and_parse(self, engine: SnmpEngine = None):
#
#         if self.scn_as_dec is None:
#             error_indication, error_status, error_index, var_binds = await self.get(
#                 oids=[Oids.utcReplySiteID],
#                 engine=engine
#             )
#             try:
#                 self.set_scn_from_response(error_indication, error_status, error_index, var_binds)
#             except BadControllerType as e:
#                 self.add_data_to_data_response_attrs(e)
#         if self.ERRORS:
#             return self
#
#         return await super().get_and_parse(engine=engine)
#
#     def set_scn_from_response(
#             self,
#             error_indication,
#             error_status,
#             error_index,
#             var_binds
#     ):
#         raise NotImplementedError()


class BaseUG405(SnmpHost):

    host_protocol = FieldsNames.protocol_ug405

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

    @staticmethod
    def add_CO_to_scn(scn: str) -> str | None:
        if not isinstance(scn, str) or not scn.isdigit():
            return None
        return f'CO{scn}'


    def add_scn_to_oids(self, oids):
        return [f'{oid}{self.scn_as_dec}' if oid in self.scn_required_oids else oid for oid in oids]

    async def get_basic_states_and_parse(self, engine: SnmpEngine = None):
        print(f'scn_as_chars!!!>> {self.scn_as_chars}')
        print(f'scn_as_dec!!!>> {self.scn_as_dec}')
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


        return await super().get_basic_states_and_parse(engine=engine)

    def set_scn_from_response(
            self,
            error_indication,
            error_status,
            error_index,
            var_binds
    ):
        raise NotImplementedError()


class MonitoringPotokP(BaseUG405):

    parser_class = ParserPotokP

    oids_state = (
        Oids.utcType2OperationMode,
        Oids.potokP_utcReplyDarkStatus,
        Oids.utcReplyFR,
        Oids.utcReplyGn,
        Oids.potokP_utcReplyPlanStatus,
        Oids.potokP_utcReplyLocalAdaptiv,
        Oids.utcType2ScootDetectorCount,
        Oids.utcReplyDF,
        Oids.utcReplyMC,
    )

    def get_oids_for_get_state(self):
        print('+scn ', self.add_scn_to_oids(self.oids_state))
        print('scn ', self.scn_as_chars)
        print('scn ', self.scn_as_dec)
        return self.add_scn_to_oids(self.oids_state)

    def set_scn_from_response(
            self,
            error_indication,
            error_status,
            error_index,
            var_binds
    )-> None:
        print(f'str(var_binds[0][1]): {str(var_binds[0][1])}')

        if any(err for err in (error_indication, error_status, error_index)) or not var_binds:
            raise BadControllerType()

        try:
            self.scn_as_chars = str(var_binds[0][1])
            self.scn_as_dec = self.get_scn_as_ascii()
        except IndexError:
            raise BadControllerType()


# class PotokP(BaseUG405):
#
#     def set_scn_from_response(
#             self,
#             error_indication,
#             error_status,
#             error_index,
#             var_binds
#     )-> None:
#
#         if any(err for err in (error_indication, error_status, error_index)) or not var_binds:
#             raise BadControllerType()
#
#         try:
#             self.scn_as_chars = str(var_binds[0][1])
#             self.scn_as_dec = self.get_scn_as_ascii()
#         except IndexError:
#             raise BadControllerType()
#
#     def get_current_mode(self, response_data: dict[str, str], mode=None) -> str | None:
#         operation_mode, local_adaptive_status, num_detectors, has_det_faults, is_mode_man = (
#             response_data.get(FieldsNames.operation_mode),
#             response_data.get(FieldsNames.local_adaptive_status),
#             response_data.get(FieldsNames.num_detectors),
#             response_data.get(FieldsNames.has_det_faults),
#             response_data.get(FieldsNames.is_mode_man),
#         )
#         match (operation_mode, local_adaptive_status, num_detectors, has_det_faults, is_mode_man):
#             case ['1', '1', num_det, '0', _] if num_det is not None and num_det.isdigit() and int(num_det) > 0:
#                 return str(NamesMode.VA)
#             case ['1', '0', '0', _, _]:
#                 return str(NamesMode.FT)
#             case['3', _, _, _, _]:
#                 return str(NamesMode.CENTRAL)
#             case[_, _, _, _, '1']:
#                 return str(NamesMode.MANUAL)
#         return 'undefined'
#
#     def get_current_status_mode(self, response_data: dict[str, str]) -> str | None:
#         dark, flash = response_data.get(FieldsNames.dark), response_data.get(FieldsNames.flash)
#         if dark == '0' and flash == '0':
#             return str(FieldsNames.three_light)
#         elif flash == '1':
#             return str(FieldsNames.flash)
#         elif dark == '1':
#             return str(FieldsNames.dark)
#         return None
#
#     def add_extras_for_response(self, response_data: dict[str, str]) -> dict[str, str]:
#         response_data[str(FieldsNames.curr_status_mode)] = self.get_current_status_mode(response_data)
#         response_data[str(FieldsNames.curr_mode)] = self.get_current_mode(response_data)
#         return response_data


