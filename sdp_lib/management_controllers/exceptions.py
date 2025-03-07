


class BadIpv4(Exception):

    def __str__(self):
        return f'Некорректный ip-v4 адрес'


class BadControllerType(Exception):
    message = 'Некорректный тип контроллера'

    def __init__(self, type_controller=None):
        self.type_controller = type_controller
    def __str__(self):
        return self.message if self.type_controller is None else f'{self.message}: {self.type_controller}'


class ConnectionTimeout(Exception):

    def __str__(self):
        return f'Превышено время подключения'


