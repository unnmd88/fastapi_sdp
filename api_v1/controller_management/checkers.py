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

    type_err_required_field = 'required_field'
    type_err_invalid_value = 'invalid_value'

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

    # def add_message_to_error_field_for_current_host(
    #         self,
    #         message: str | list | Exception,
    #         field_name: str,
    #         type_err: str = None
    # ) -> None:
    #     """
    #     Добавляет сообщение с текстом ошибки.
    #     :param message: Строка с текстом сообщения
    #     :return: None
    #     """
    #
    #     pattern = {
    #         "detail": [
    #             {
    #                 'field_name': field_name,
    #                 'msg': message,
    #                 'type': type_err
    #             }
    #         ]
    #     }
    #
    #     self._add_errors_field_for_current_data_host_if_have_not()
    #     if isinstance(message, str):
    #         self.properties[str(AllowedDataHostFields.errors)].append(str(message))
    #     elif isinstance(message, Exception):
    #         self.properties[str(AllowedDataHostFields.errors)].append(str(message))
    #     elif isinstance(message, list):
    #         self.properties[str(AllowedDataHostFields.errors)] += message

    def add_message_to_error_field_for_current_host(
            self,
            message: str | Exception,
            field_name: str,
            type_err: str
    ) -> None:
        """
        Добавляет сообщение с текстом ошибки.
        :param message: Строка с текстом сообщения
        :return: None
        """

        self._add_errors_field_for_current_data_host_if_have_not()
        if isinstance(message, Exception):
            message = str(message)
        if not isinstance(message, str):
            raise ValueError('Ошибка должна быть строкой или наследником класса < Exception >')
        pattern = {
            'field_name': field_name,
            'msg': message,
            'type': type_err
        }
        self.properties[str(AllowedDataHostFields.errors)].append(pattern)

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
            self.add_message_to_error_field_for_current_host(
                message=my_exceptions.BadIpv4(),
                field_name=str(AllowedDataHostFields.ipv4),
                type_err=self.type_err_invalid_value
            )
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
            type_err = self.type_err_invalid_value
        except KeyError:
            exc = my_exceptions.HasNotRequiredField(str(AllowedDataHostFields.type_controller))
            type_err = self.type_err_required_field

        if add_message_to_errors_field_if_not_valid:
            self.add_message_to_error_field_for_current_host(
                message=exc,
                field_name=str(AllowedDataHostFields.type_controller),
                type_err=type_err
            )
        return False

    def get_validate_methods(self):
        """
        Возвращает список с методами валидаций.
        :return:
        """
        return [self.validate_ipv4, self.validate_type_controller]


