

class ClientException(Exception):
    def __init__(self, ipv4=None):
        self.ipv4 = ipv4


class BadIpv4(ClientException):

    def __str__(self):
        return f'Некорректный ip-v4 адрес'


class BadControllerType(ClientException):
    def __init__(self, type_controller=None):
        self.type_controller = type_controller
    def __str__(self):
        return f'Некорректный тип контроллера: {self.type_controller!r}'


class ConnectionTimeout(ClientException):

    def __str__(self):
        return f'Превышено время подключения, ip: {self.ipv4!r}'


class NotFoundInDB(ClientException):

    def __str__(self):
        return f'Не найден в базе данных, ip: {self.ipv4!r}'


class HasNotRequiredField(ClientException):

    def __init__(self, field_name=None):
        self.field_name = field_name

    def __str__(self):
        return f'Отсутствует обязательное поле: {self.field_name!r}'


class InvalidLenFieldValue(ClientException):

    def __init__(self, field_name, max_len, current_lenght):
        self.field_name = field_name
        self.max_len = max_len
        self.current_length = current_lenght

    def __str__(self):
        return (f'Максимальная количество символов поля {self.field_name} не должно '
                f'превышать {self.max_len}. Передано: {self.current_length}')