"""
Модуль с классами проверки валидности данных тела json.
"""

import json
from typing import Any, TypeVar

from api_v1.controller_management.schemas import AllowedDataHostFields, AllowedControllers
from core.user_exceptions import validate_exceptions
from sdp_lib.utils_common import check_is_ipv4


E = TypeVar('E', bound=validate_exceptions.BaseClientException)


class HostData:
    """
    Класс - обработчик данных хоста.
    """

    def __init__(self, ip_or_name: str, properties: dict):
        self.ip_or_name = ip_or_name
        self.properties = properties
        self.ip_or_name_and_properties_as_dict = self.get_full_host_data_as_dict()

    def __repr__(self):
        return (
            f'self.ip_or_name: {self.ip_or_name}\n'
            f'self.properties: {json.dumps(self.properties, indent=2)}\n'
            f'self.ip_or_name_and_properties_as_dict: {json.dumps(self.ip_or_name_and_properties_as_dict, indent=2)}\n'
        )

    def _add_errors_field_for_current_data_host_if_have_not(self) -> None:
        """
        Добавляет к self.properties свойство в виде dict: {"errors": []}.
        :return: None.
        """
        if self.properties.get(AllowedDataHostFields.errors) is None:
            self.properties |= {str(AllowedDataHostFields.errors): []}

    def add_error_entity_for_current_host(self, exc: E | str) -> None:
        """
        Добавляет сообщение с текстом ошибки.
        :param exc: Экземпляр пользовательского класса ошибки.
        :return: None
        """
        self._add_errors_field_for_current_data_host_if_have_not()
        # if isinstance(exc, validate_exceptions.BaseClientException):
        #     e = exc.get_data_about_exc()
        # elif isinstance(exc, str):
        #     e = exc
        # else:
        #     raise ValueError
        if not isinstance(exc, validate_exceptions.BaseClientException):
            raise ValueError
        self.properties[str(AllowedDataHostFields.errors)].append(exc.get_data_about_exc())

    def get_full_host_data_as_dict(self) -> dict[str, dict[str, Any]]:
        """
        Возвращает словарь вида {self.ip_or_name: self.properties}
        :return:
        """
        return {self.ip_or_name: self.properties}

    def _get_full_host_data_as_dict(self) -> dict[str, Any]:
        return self.properties | {str(AllowedDataHostFields.ipv4): self.ip_or_name}


class MonitoringHostDataChecker(HostData):
    """
    Класс с реализацией проверки данных для запроса,
    принадлежащего к разделу 'Мониторинг'(Режимы дк, поиск в базе и т.д.)
    """

    def validate_ipv4(self) -> bool:
        """
        Проверяет валидность ipv4 self.ip_or_name.
        :param add_message_to_errors_field_if_not_valid: Добавить сообщение в поле errors.
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


