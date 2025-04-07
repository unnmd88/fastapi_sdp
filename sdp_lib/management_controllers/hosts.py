import abc
from typing import Any

from pysnmp.proto.errind import requestTimedOut

from sdp_lib.management_controllers.fields_names import FieldsNames
from sdp_lib.management_controllers.response import Response
from sdp_lib.utils_common import check_is_ipv4


class Host:
    """
    Базовый класс хоста.
    """

    ERRORS        = 0
    RESPONSE      = 1
    RAW_RESPONSE  = 2

    protocol: str

    def __init__(
            self,
            *,
            ip_v4: str = None,
            host_id: str | int = None
    ):
        self.ip_v4 = ip_v4
        self.host_id = host_id
        self.last_response = None
        self._response = Response(self.protocol)
        # self.ERRORS = []
        # self.DATA_RESPONSE = {}
        # self.RAW_RESPONSE = tuple()
        # self.response: list = [self.ERRORS, self.DATA_RESPONSE, self.RAW_RESPONSE]

    def __repr__(self):
        return self.__dict__

    def __setattr__(self, key, value):
        if key == 'ip_v4':
            if value is None or check_is_ipv4(value):
                self.__dict__[key] = value
            else:
                raise ValueError(f'Значение < self.ipv4 > должно быть валидным ipv4 адресом: {value}')

        elif key == 'scn':
            if value is None or len(value) <= 10:
                self.__dict__[key] = value
            else:
                raise ValueError('Значение < self.scn > не должно превышать 10 символов ')
        else:
            self.__dict__[key] = value

    # @property
    # def ip_v4(self):
    #     return self._ip_v4
    #
    # @ip_v4.setter
    # def ip_v4(self, value):
    #     if check_is_ipv4(value):
    #         self._ip_v4 = value
    #     else:
    #         raise ValueError(f'Значение < self.ipv4 > должно быть валидным ipv4 адресом: {value}')

    @property
    def response(self):
        return self._response

    @property
    def response_errors(self) -> list:
        return self._response.errors

    @property
    def response_data(self) -> dict:
        return self._response.data

    @property
    def response_as_dict(self):
        return self._response.bild_as_dict(self.ip_v4)

    def add_data_to_data_response_attrs(
            self,
            error: Exception | str = None,
            data: dict[str, Any] = None
    ):
        self._response.add_data_to_attrs(error, data)




