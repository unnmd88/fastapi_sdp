from enum import IntEnum


class SnmpResponseStructure(IntEnum):

    ERROR_INDICATION = 0
    ERROR_STATUS     = 1
    ERROR_INDEX      = 2
    VAR_BINDS        = 3


class HostResponseStructure(IntEnum):

    ERRORS        = 0
    DATA_RESPONSE = 1
    RAW_RESPONSE  = 2