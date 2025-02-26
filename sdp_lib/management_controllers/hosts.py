from sdp_lib.utils_common import check_is_ipv4


class Host:
    """
    Базовый класс хоста.
    """

    def __init__(self, ip_v4: str, host_id=None):
        self.ip_v4 = ip_v4
        self.host_id = host_id

    def __repr__(self):
        # return (
        #     f'ip_v4: {self.ip_v4}\n'
        #     f'host_id: {self.host_id}\n'
        # )

        return self.__dict__

    def __str__(self):
        return self.__dict__

    def __setattr__(self, key, value):
        if key == 'ip_v4':
            if check_is_ipv4(value):
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


