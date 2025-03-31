import math
import os
import typing
from dataclasses import dataclass
import dataclasses
from sdp_lib.management_controllers.snmp.host_data import swarco_stcip, AllowedControllers


class AbstractStcipConverters:

    matches_val_from_num_stage_to_oid_vals: dict

    @classmethod
    def get_num_stage_from_oid_val(cls, val: str) -> int | None:
        return cls.matches_val_from_num_stage_to_oid_vals.get(val)


class SwarcoConverters(AbstractStcipConverters):

    matches_val_from_num_stage_to_oid_vals = {
        '2': 1, '3': 2, '4': 3, '5': 4, '6': 5, '7': 6, '8': 7, '1': 8, '0': 0
    }


class PotokSConverters(AbstractStcipConverters):
    matches_val_from_num_stage_to_oid_vals = {
        str(k) if k < 66 else str(0): v if v < 65 else 0 for k, v in zip(range(2, 67), range(1, 66))
    }


class Ug405Converters:

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




# print(x)
# print(dataclasses.asdict(x))
# print(dataclasses.fields(A))




if __name__ == '__main__':
    print(swarco_stcip._asdict())




