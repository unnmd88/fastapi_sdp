"""
Модуль с классами проверки валидности данных тела json.
"""

from api_v1.controller_management.checkers.checkers_core import HostData
from api_v1.controller_management.schemas import AllowedDataHostFields, AllowedControllers
from core.user_exceptions import validate_exceptions
from sdp_lib.utils_common import check_is_ipv4


class MonitoringHostDataChecker(HostData):
    """
    Класс с реализацией проверки данных для запроса,
    принадлежащего к разделу 'Мониторинг'(Режимы дк, поиск в базе и т.д.)
    """

    def validate_ipv4(self) -> bool:
        """
        Проверяет валидность ipv4 self.ip_or_name.
        :return: True если ipv4 валиден, иначе False
        """
        if check_is_ipv4(self.ip_or_name):
            return True
        exc = validate_exceptions.InvalidValue(
            field_name=str(AllowedDataHostFields.ipv4),
            input_val=self.ip_or_name
        )
        self.add_error_entity_for_current_host(exc)
        return False

    def validate_type_controller(self) -> bool:
        """
        Проверяет наличие поля type_controller и валидность типа ДК в данном поле.
        :return: True если type_controller валиден, иначе False
        """
        type_controller = str(AllowedDataHostFields.type_controller)
        try:
            AllowedControllers(self.properties[type_controller])
            return True
        except ValueError:
            exc = validate_exceptions.InvalidValue(
                field_name=type_controller,
                input_val=self.properties[type_controller]
            )
            exc.ctx = exc.get_allowed_controller_types()
        except KeyError:
            exc = validate_exceptions.RequiredField(field_name=str(AllowedDataHostFields.type_controller))
        self.add_error_entity_for_current_host(exc)
        return False

    def get_validate_methods(self):
        """
        Возвращает список с методами валидаций.
        :return:
        """
        return [self.validate_ipv4, self.validate_type_controller]


