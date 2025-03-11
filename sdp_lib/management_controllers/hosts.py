import abc

from sdp_lib.management_controllers.fields_names import FieldsNames
from sdp_lib.utils_common import check_is_ipv4


class Host:
    """
    Базовый класс хоста.
    """

    ERROR      = 0
    RESPONSE   = 1

    def __init__(self, ip_v4: str, host_id=None):
        self.ip_v4 = ip_v4
        self.host_id = host_id
        self.response: tuple[None | str, dict] | None = None

    def __repr__(self):
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

    @property
    @abc.abstractmethod
    def protocol(self):
        ...

    @property
    def response_as_dict(self):
        """
        Формирует словарь их self.response.
        После запроса, self.response принимает кортеж из 2 элементов:
        i[0] -> Строка с сообщением об ошибке, если в процессе запроса было возбуждено исключение, иначе None
        i[1] -> Словарь с распарсенными данными из ответа.
        :return: Словарь вида:
                 Если self.response[0] -> None(Нет ошибки):
                     "response": {
                          "protocol": "snmp",
                          "ip_address": "10.179.122.113",
                          "error": None,
                          "fixed_time_status": "0",
                          "plan_source": "7",
                          "current_status": "3_light",
                          "current_stage": 1,
                          "current_plan": "2",
                          "num_detectors": "5",
                          "status_soft_flag180_181": "00",
                          "current_mode": "VA"
                     }
                 Если self.response[0] -> "No SNMP response received before timeout"(Есть ошибка):
                     "response": {
                          "protocol": "snmp",
                          "ip_address": "10.45.154.16",
                          "error": "No SNMP response received before timeout"
                     }

        """
        return {
            str(FieldsNames.protocol): self.protocol,
            str(FieldsNames.ipv4_address): self.ip_v4,
            str(FieldsNames.error): self.response[0],
            str(FieldsNames.data): (self.response[1] if isinstance(self.response[1], dict) else {})
        }


