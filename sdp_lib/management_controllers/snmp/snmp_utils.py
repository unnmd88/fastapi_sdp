import abc
import math
import os
import typing
from dataclasses import dataclass
import dataclasses

from pysnmp.proto.rfc1902 import Unsigned32
from pysnmp.smi.rfc1902 import ObjectType, ObjectIdentity

from sdp_lib.management_controllers.snmp import oids
from sdp_lib.management_controllers.snmp.host_data import swarco_stcip, AllowedControllers
from sdp_lib.management_controllers.snmp.oids import Oids


class AbstractConverter:

    state_oids: tuple[ObjectType, ...]

    def get_varbinds_for_get_state(self) -> list[ObjectType]:
        raise NotImplementedError()


class AbstractStcipConverters:

    matches_val_from_num_stage_to_oid_vals: dict

    @classmethod
    def get_num_stage_from_oid_val(cls, val: str) -> int | None:
        return cls.matches_val_from_num_stage_to_oid_vals.get(val)


class AbstractUg405PConverters:

    oids_scn_required = oids.oids_scn_required
    state_oids: tuple[Oids | str, ...]
    scn_varbind = ObjectType(ObjectIdentity(oids.Oids.utcReplySiteID))

    @classmethod
    def convert_hex_to_decimal(cls, val: str) -> int | None:
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

    @classmethod
    def get_num_stage_from_oid_val(cls, val: str) -> int | None:
        return cls.convert_hex_to_decimal(val)

    @staticmethod
    def convert_chars_string_to_ascii_string(scn: str) -> str:
        """
        Генерирует SCN
        :param scn -> символы строки, которые необходимо конвертировать в scn
        :return -> возвращет scn
        """
        return f'.1.{str(len(scn))}.{".".join([str(ord(c)) for c in scn])}'

    @classmethod
    def get_scn_as_ascii_from_scn_as_chars(cls, scn_as_chars_string: str) -> str | None:
        return cls.convert_chars_string_to_ascii_string(scn_as_chars_string)

    @classmethod
    def add_scn_to_oids(
            cls,
            oids: tuple[Oids, ...] | list[Oids],
            scn_as_chars_string: str = None,
            scn_as_ascii_string: str = None,
            wrap_oid_by_object_identity: bool = False
    ) -> list[Oids | str | ObjectType]:
        if scn_as_ascii_string:
            scn = scn_as_ascii_string
        elif scn_as_chars_string:
            scn = cls.get_scn_as_ascii_from_scn_as_chars(
                scn_as_chars_string
            )
        else:
            raise ValueError(
                'Необходимо передать в функию один из аргументов:\n'
                'scn_as_chars_string(Например: CO1111) или scn_as_ascii_string(Например: .1.3.22.22.22)'
            )
        if wrap_oid_by_object_identity:
            return [
                ObjectType(ObjectIdentity(f'{oid}{scn}')) if oid in cls.oids_scn_required
                else ObjectType(ObjectIdentity(oid))
                for oid in oids
            ]
        return [
            f'{oid}{scn}' if oid in cls.oids_scn_required else oid
            for oid in oids
        ]

    @classmethod
    def get_varbinds_for_get_state(
            cls,
            *,
            scn_as_ascii_string: str = None,
            scn_as_chars_string: str = None
    ) -> list[ObjectType]:
        print(f'scn_as_ascii_string: {scn_as_ascii_string}')
        print(f'scn_as_chars_string: {scn_as_chars_string}')
        return cls.add_scn_to_oids(
            oids=cls.state_oids,
            scn_as_ascii_string=scn_as_ascii_string,
            scn_as_chars_string=scn_as_chars_string,
            wrap_oid_by_object_identity=True
        )


class SwarcoConverters(AbstractStcipConverters):

    state_oids = oids.oids_state_swarco
    matches_val_from_num_stage_to_oid_vals = {
        '2': 1, '3': 2, '4': 3, '5': 4, '6': 5, '7': 6, '8': 7, '1': 8, '0': 0
    }
    payload_for_set_stage = {
        num_stage: Unsigned32(num_stage + 1) for num_stage in range(1, 8)
    } | {8: Unsigned32(1), 0: Unsigned32(0)}
    varbinds_get_state = [
        ObjectType(ObjectIdentity(oid)) for oid in oids.oids_state_swarco
    ]

    @classmethod
    def get_varbinds_for_set_stage(cls, num_stage: int):
        # *[ObjectType(ObjectIdentity(oid), val) for oid, val in oids]
        return [
            ObjectType(ObjectIdentity(Oids.swarcoUTCTrafftechPhaseCommand), cls.payload_for_set_stage.get(num_stage))
        ]

    @classmethod
    def get_varbinds_for_get_state(cls) -> list[ObjectType]:
        return cls.varbinds_get_state


class PotokSConverters(AbstractStcipConverters):

    matches_val_from_num_stage_to_oid_vals = {
        str(k) if k < 66 else str(0): v if v < 65 else 0 for k, v in zip(range(2, 67), range(1, 66))
    }


class PotokPConverters(AbstractUg405PConverters):

    state_oids = oids.oids_state_potok_p




# print(x)
# print(dataclasses.asdict(x))
# print(dataclasses.fields(A))




if __name__ == '__main__':
    print(swarco_stcip._asdict())




