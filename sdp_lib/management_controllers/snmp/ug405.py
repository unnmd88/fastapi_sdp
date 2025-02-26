import os

from pysnmp.proto.rfc1902 import Unsigned32

from sdp_lib.management_controllers.responce import FieldsNames
from sdp_lib.management_controllers.controller_modes import NamesMode
from sdp_lib.management_controllers.snmp.snmp_base import SnmpHost
from sdp_lib.management_controllers.snmp.oids import Oids


class PotokP(SnmpHost):

    def __init__(self, ip_v4: str, host_id=None, scn=None):
        super().__init__(ip_v4, host_id)
        self.scn_chars = scn
        self.scn_dec = self.get_scn_as_ascii()

    def set_scn(self, var_binds: list):
        if var_binds:
            self.scn_chars = str(var_binds[0][1])
            self.scn_dec = self.get_scn_as_ascii()

    def get_scn_as_ascii(self):
        if self.scn_chars is not None:
            return self.convert_scn(self.scn_chars)
        return None

    def get_community(self) -> tuple[str, str]:
        return os.getenv('communityUG405_r'), os.getenv('communityUG405_w')

    @staticmethod
    def convert_scn(scn: str) -> str:
        """
        Генерирует SCN
        :param scn -> символы строки, которые необходимо конвертировать в scn
        :return -> возвращет scn
        """
        return f'.1.{str(len(scn))}.{".".join([str(ord(c)) for c in scn])}'

    async def get_scn_snmp(self):
        err, var_b = await self.get(
            oids=[Oids.utcReplySiteID]
        )
        if err is None:
            self.scn_chars = str(var_b[0][1])
            self.scn_dec = self.get_scn_as_ascii()
