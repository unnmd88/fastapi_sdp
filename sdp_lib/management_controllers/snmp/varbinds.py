import abc
import asyncio
import pprint
import sys
import time
from functools import cached_property
from typing import TypeVar

from pysnmp.entity.engine import SnmpEngine
from pysnmp.proto import rfc1905
from pysnmp.proto.rfc1902 import Unsigned32, Integer, OctetString, Integer32
from pysnmp.smi.rfc1902 import ObjectType, ObjectIdentity

from sdp_lib.management_controllers.snmp import oids, snmp_requests, host_data
from sdp_lib.management_controllers.snmp.oids import oids_scn_required

from sdp_lib.management_controllers.snmp.oids import Oids


def wrap_oid_by_object_type(oid, val: Unsigned32 | Integer | OctetString = None):
    return ObjectType(ObjectIdentity(oid), val or rfc1905.unSpecified)


def convert_chars_string_to_ascii_string(scn: str) -> str:
        """
        Генерирует SCN
        :param scn -> символы строки, которые необходимо конвертировать в scn
        :return -> возвращет scn
        """
        return f'.1.{str(len(scn))}.{".".join([str(ord(c)) for c in scn])}'


def convert_val_to_num_stage_set_req(max_stage: int) -> dict:

    stg_mask = ['01', '02', '04', '08', '10', '20', '40', '80']
    return {str(k): v for k, v in enumerate((f'{i}{j * "00"}' for j in range(max_stage//8) for i in stg_mask), 1)}


ug405_stage_values = convert_val_to_num_stage_set_req(128)


T_OidsContainer = TypeVar('T_OidsContainer', list[Oids | str], tuple[Oids | str, ...])
T_ObjectTypeContainer = TypeVar('T_ObjectTypeContainer', list[ObjectType], tuple[ObjectType, ...])


class Varbinds(abc.ABC):

    oids_state = T_OidsContainer

    def __init__(self):
        self._varbinds_get_state = self._build_varbinds_for_get_state()

    @abc.abstractmethod
    def _build_varbinds_for_get_state(self):
        ...

    @abc.abstractmethod
    def get_varbinds_current_states(self, *args, **kwargs):
        ...

    @classmethod
    def parse_response(cls, varbinds):
        for oid, val in varbinds:
            print(f'oid: {oid.prettyPrint()} || val: {val.prettyPrint()}')
            print(f'oid as str: {str(oid)} || val: {val.prettyPrint()}')


class VarbindsStcip(Varbinds):

    set_stage_oid = oids.Oids.swarcoUTCTrafftechPhaseCommand

    def __init__(self):
        super().__init__()
        self._varbinds_set_stage = self._build_varbinds_for_set_stage()

    def _build_varbinds_for_get_state(self) -> list[ObjectType]:
        return [wrap_oid_by_object_type(oid) for oid in self.oids_state]

    def get_varbinds_current_states(self) -> list[ObjectType]:
        return self._varbinds_get_state

    def _build_varbinds_for_set_stage(self) -> dict[int, ObjectType]:
        raise NotImplementedError()

    def get_varbinds_set_stage(self, num_stage) -> list[ObjectType]:
        return [self._varbinds_set_stage.get(num_stage)]


class VarbindsSwarco(VarbindsStcip):

    oids_state = oids.oids_state_swarco

    def _build_varbinds_for_set_stage(self) -> dict[int, ObjectType]:
        return {
            num_stage: wrap_oid_by_object_type(Oids.swarcoUTCTrafftechPhaseCommand, Unsigned32(num_stage + 1))
            for num_stage in range(1, 8)
        } | {8: wrap_oid_by_object_type(Oids.swarcoUTCTrafftechPhaseCommand, 1),
             0: wrap_oid_by_object_type(Oids.swarcoUTCTrafftechPhaseCommand, 0)}


class VarbindsPotokS(VarbindsStcip):

    oids_state = oids.oids_state_potok_s

    def _build_varbinds_for_set_stage(self) -> dict[int, ObjectType]:
        return {
            num_stage: wrap_oid_by_object_type(Oids.swarcoUTCTrafftechPhaseCommand, Unsigned32(num_stage + 1))
            for num_stage in range(1, 129)
        } | {0: wrap_oid_by_object_type(Oids.swarcoUTCTrafftechPhaseCommand, 0)}


class VarbindsUg405(Varbinds):

    max_scn = 9999
    num_CO_prefix = 'CO'

    operation_mode1_varbind = wrap_oid_by_object_type(Oids.utcType2OperationMode, Integer32(1))
    operation_mode2_varbind = wrap_oid_by_object_type(Oids.utcType2OperationMode, Integer32(2))
    operation_mode3_varbind = wrap_oid_by_object_type(Oids.utcType2OperationMode, Integer32(3))

    hex_vals128 = {i: OctetString(hexValue=ug405_stage_values.get(str(i))) for i in range(1, 129)}

    integer_vals128 = {i: Integer32(i) for i in range(129)}
    integer32_val1 = Integer32(1)
    integer32_val2 = Integer32(2)
    integer32_val3 = Integer32(3)

    def add_scn_to_oids(
            self,
            scn: str,
            oids: T_OidsContainer,
    ) -> list[Oids | str | ObjectType]:

        return [
            f'{oid}{scn}' if oid in oids.oids_scn_required else oid
            for oid in oids
        ]

    def add_scn_to_oids_and_wrap_by_object_identity(
            self,
            scn: str,
            oids: T_OidsContainer,
    ):
        return [
            ObjectType(ObjectIdentity(f'{oid}{scn}')) if oid in oids_scn_required
            else ObjectType(ObjectIdentity(oid))
            for oid in oids
        ]

    def _build_varbinds_for_get_state(self):
        start_time = time.time()

        result = {}
        for i in range(1, self.max_scn):
            scn = convert_chars_string_to_ascii_string(f'{self.num_CO_prefix}{str(i)}')
            curr_states_object_type = self.add_scn_to_oids_and_wrap_by_object_identity(
                scn, self.oids_state
            )
            result[scn] = curr_states_object_type
        print(f'FinS: {time.time() - start_time}')
        return result

    def get_varbinds_current_states(self, scn_as_ascii: str) -> T_ObjectTypeContainer:
        return self._varbinds_get_state.get(scn_as_ascii)

    def get_varbinds_set_stage(
            self,
            scn_as_ascii: str,
            num_stage: int
    ) -> T_ObjectTypeContainer:
        if 0 < num_stage < 129:
            return (
                self.operation_mode3_varbind,
                wrap_oid_by_object_type(f'{Oids.utcControlTO}{scn_as_ascii}', self.integer32_val1),
                wrap_oid_by_object_type(f'{Oids.utcControlFn}{scn_as_ascii}', self.hex_vals128.get(num_stage)),
                # wrap_oid_by_object_type(f'{Oids.utcControlFn}{scn_as_ascii}', OctetString(hexValue='1'))
            )
        return (self.operation_mode1_varbind, )


class VarbindsPotokP(VarbindsUg405):

    oids_state = oids.oids_state_potok_p

# Singleton instances
potok_ug405_varbinds = VarbindsPotokP()
potok_stcip_varbinds = VarbindsPotokS()
swarco_sctip_varbinds = VarbindsSwarco()


class AbstractVarbindsWrappersByScn:

    _ug405_varbinds: potok_ug405_varbinds

    def __init__(self, scn_as_ascii: str = None):
        self._scn_as_ascii = scn_as_ascii

    @classmethod
    def get_varbinds_current_states_by_scn(
            cls,
            scn_as_ascii: str
    ):
        return cls._ug405_varbinds.get_varbinds_current_states(scn_as_ascii)

    @classmethod
    def get_varbinds_set_stage_by_scn(
            cls,
            scn_as_ascii: str,
            value: int
    ):
        return cls._ug405_varbinds.get_varbinds_set_stage(scn_as_ascii, value)

    def get_varbinds_current_states(self):
        return self._ug405_varbinds.get_varbinds_current_states(self._scn_as_ascii)

    def get_varbinds_set_stage(self, value: int) -> T_ObjectTypeContainer:
        return self._ug405_varbinds.get_varbinds_set_stage(self._scn_as_ascii, value)

    @property
    def ug405_varbinds(self) -> VarbindsUg405:
        return self._ug405_varbinds

    @property
    def scn_as_ascii(self):
        return self._scn_as_ascii

    @scn_as_ascii.setter
    def scn_as_ascii(self, value: str):
        if not isinstance(value, str):
            raise ValueError(f"Уставливое значение 'scn_as_ascii' должно быть типа str")
        if value.count('.') < 2:
            if not isinstance(value, str):
                raise ValueError(f"Проверьте корректность устанавливаемого значения 'scn_as_ascii'.")
        self._scn_as_ascii = value


class WrappersVarbindsByScnPotokP(AbstractVarbindsWrappersByScn):

    _ug405_varbinds = potok_ug405_varbinds




def build_test_obj():
    p = VarbindsPotokP()
    scn155 = convert_chars_string_to_ascii_string('CO155')

    # vb = p.get_varbinds_get_state_by_scn(scn_as_ascii=scn155)
    # print(vb)
    print(f'Volume: {sys.getsizeof(p._varbinds_get_state)}')
    print(f'Volume 2 : {sys.getsizeof(list(p._varbinds_get_state.values()))}')
    print(f'Volume 1 el: {sys.getsizeof(p._varbinds_get_state.get(scn155))}')









async def main():


    r_sender = snmp_requests.SnmpRequests(
        ip='10.179.8.105',
        community_r=host_data.swarco_stcip.community_r,
        community_w=host_data.swarco_stcip.community_w,
        engine=SnmpEngine()
    )

    r_sender = snmp_requests.SnmpRequests(
        # ip='10.179.56.105',
        ip='10.179.69.65',
        community_r=host_data.potok_p.community_r,
        community_w=host_data.potok_p.community_w,
        engine=SnmpEngine()
    )

    r_sender = snmp_requests.SnmpRequests(
        # ip='10.179.56.105',
        ip='10.179.69.65',
        community_r=host_data.potok_p.community_r,
        community_w=host_data.potok_p.community_w,
        engine=SnmpEngine()
    )

    r_sender = snmp_requests.SnmpRequests(
        # ip='10.179.56.105',
        ip='10.179.68.177',
        community_r=host_data.potok_s.community_r,
        community_w=host_data.potok_s.community_w,
        engine=SnmpEngine()
    )

    res = await r_sender.snmp_get(potok_stcip_varbinds.get_varbinds_current_states())

    print(res)

    potok_stcip_varbinds.parse_response(res[3])

if __name__ == '__main__':
    asyncio.run(main())
    # res = {}
    # for i in range(1, 1000)
    #     res[i] = 0
    start_time = time.time()
    # build_test_obj()




