"""
Модуль содержит классы ошибок для валидации данных json.
"""
import abc
from enum import StrEnum

from core.constants import AllowedControllers
from sdp_lib.management_controllers import exceptions as sdp_lib_exc


class ErrMessages(StrEnum):

    bad_ip = 'Некорректный ip-v4 адрес'
    bad_controller = 'Недопустимый тип контроллера'
    bad_num_stage = 'Некорректный номер фазы'
    bad_command = 'Невалидная команда'
    bad_source = 'Невалидный источник'

    @classmethod
    def get_bad_ip_pretty(cls, ip):
        return f'{cls.bad_ip}: {ip}'

    @classmethod
    def get_bad_controller_pretty(cls, controller_type) -> str:
        return f'{cls.bad_controller}: {controller_type}'

    @classmethod
    def bad_command_pretty(cls, allowed_commands) -> str:
        return f'{cls.bad_command}. Доступные команды: {list(allowed_commands)}'

    @classmethod
    def bad_value_pretty(cls, min_val, max_val, command_name='') -> str:
        command_name_pattern = f' < {command_name} >' if command_name else command_name
        return (
            f'Некорректное значение команды{command_name_pattern}. '
            f'Допустимый диапазон: '
            f'[{min_val}...{max_val}]'
        )

    @classmethod
    def bad_source_pretty(cls, sources) -> str:
        return f'Невалидный источник команды. Допустимые: {sources}'


class BaseClientException(Exception):
    pass


class BadIpv4(BaseClientException):

    def __init__(self, src_ip=None):
        self.src_ip = src_ip

    def __str__(self):
        return f'Некорректный ip-v4 адрес' if self.src_ip is None else f'Некорректный ip-v4 адрес: {self.src_ip}'


class ClientException(BaseClientException):
    type_exc: str
    _field_name = 'field_name'
    _ctx = 'ctx'
    _msg = 'msg'
    _type = 'type'
    _input = 'input'

    def __init__(self, field_name, ctx=None, input_val=None):
        self.field_name = field_name
        self.ctx = ctx
        self.input_val = input_val

    @property
    @abc.abstractmethod
    def message(self) -> str:
        """ Сообщение об ошибке. """
        pass

    def __str__(self):
        return self.message

    def get_data_about_exc(self, **kwargs) -> dict[str, str]:
        """ Возвращает объект ошибки с данными в виде словаря """
        pattern = {
            self._field_name: self.field_name,
            self._ctx: self.ctx,
            self._msg: self.message,
            self._type: self.type_exc,
            self._input: self.input_val
        }
        return pattern | kwargs


class RequiredField(ClientException):
    type_exc = 'required field'

    @property
    def message(self):
        return f'Поле {self.field_name} является обязательным'


class InvalidValue(ClientException):
    type_exc = 'invalid value'

    @property
    def message(self):
        return f'Невалидное значение: {self.input_val}'

    def get_allowed_controller_types(self):
        return f'Допустимые типы контроллеров: {", ".join([str(c) for c in AllowedControllers])}'


class NotFoundInDB(ClientException):
    type_exc = 'not found in database'


    @property
    def message(self) -> str:
        """ Сообщение об ошибке. """
        return f'Не найден в базе данных, ip/name: {self.input_val!r}'

    def get_data_about_exc(self, **kwargs) -> dict[str, str]:
        data = super().get_data_about_exc()
        data.pop(self._input)
        return data


BadControllerType = sdp_lib_exc.BadControllerType