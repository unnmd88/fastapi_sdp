from typing import TypeVar

from pysnmp.smi.rfc1902 import ObjectType

from sdp_lib.management_controllers.snmp.oids import Oids


T_Oids = TypeVar('T_Oids', tuple[Oids | str, ...], list[Oids | str])
T_Varbinds = TypeVar('T_Varbinds', tuple[ObjectType, ...], list[ObjectType])
T_Parsers = TypeVar('T_Parsers')

