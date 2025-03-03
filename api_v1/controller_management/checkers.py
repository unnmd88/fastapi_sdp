"""
Модуль с классами проверки валидности данных тела json.
"""

import json
from typing import Any

from api_v1.controller_management.schemas import AllowedDataHostFields, AllowedControllers
from sdp_lib.management_controllers import exceptions as my_exceptions
from sdp_lib.utils_common import check_is_ipv4


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

    def add_message_to_error_field_for_current_host(self, message: str | list | Exception) -> None:
        """
        Добавляет сообщение с текстом ошибки.
        :param message: Строка с текстом сообщения
        :return: None
        """
        self._add_errors_field_for_current_data_host_if_have_not()
        if isinstance(message, str):
            self.properties[str(AllowedDataHostFields.errors)].append(str(message))
        elif isinstance(message, Exception):
            self.properties[str(AllowedDataHostFields.errors)].append(str(message))
        elif isinstance(message, list):
            self.properties[str(AllowedDataHostFields.errors)] += message

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

    def validate_ipv4(self, add_message_to_errors_field_if_not_valid=True) -> bool:
        """
        Проверяет валидность ipv4 self.ip_or_name.
        :param add_message_to_errors_field_if_not_valid: Добавить сообщение в поле errors.
        :return: True если ipv4 валиден, иначе False
        """
        if check_is_ipv4(self.ip_or_name):
            return True
        if add_message_to_errors_field_if_not_valid:
            self.add_message_to_error_field_for_current_host(my_exceptions.BadIpv4())
        return False

    def validate_type_controller(self, add_message_to_errors_field_if_not_valid=True) -> bool:
        """
        Проверяет наличие поля type_controller и валидность типа ДК в данном поле.
        :param add_message_to_errors_field_if_not_valid: Добавить сообщение в поле errors.
        :return: True если type_controller валиден, иначе False
        """
        try:
            AllowedControllers(self.properties[str(AllowedDataHostFields.type_controller)])
            return True
        except ValueError:
             exc = my_exceptions.BadControllerType(self.properties[str(AllowedDataHostFields.type_controller)])
        except KeyError:
            exc = my_exceptions.HasNotRequiredField(str(AllowedDataHostFields.type_controller))

        if add_message_to_errors_field_if_not_valid:
            self.add_message_to_error_field_for_current_host(exc)
        return False

    def get_validate_methods(self):
        """
        Возвращает список с методами валидаций.
        :return:
        """
        return [self.validate_ipv4, self.validate_type_controller]


