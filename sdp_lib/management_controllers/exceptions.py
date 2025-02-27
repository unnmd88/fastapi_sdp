

class ClientException(Exception):
    def __init__(self, ipv4=None):
        self.ipv4 = ipv4



class BadControllerType(ClientException):

    def __str__(self):
        return f'Некорректный тип контроллера, ip: {self.ipv4!r}'