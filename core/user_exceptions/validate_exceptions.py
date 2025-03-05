"""
Модуль содержит классы ошибок для валидации данных json.
"""
import abc

from mypyc.primitives.set_ops import set_update_op

from api_v1.controller_management.schemas import AllowedControllers


class BaseClientException(Exception):
    pass


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

