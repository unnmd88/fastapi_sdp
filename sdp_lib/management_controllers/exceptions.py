

class ClientException(Exception):
    def __init__(self, ipv4=None):
        self.ipv4 = ipv4

class BadIpv4(ClientException):

    def __str__(self):
        return f'Некорректный ip-v4 адрес'

class BadControllerType(ClientException):

    def __str__(self):
        return f'Некорректный тип контроллера'


class ConnectionTimeout(ClientException):

    def __str__(self):
        return f'Превышено время подключения, ip: {self.ipv4!r}'