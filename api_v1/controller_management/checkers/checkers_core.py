import json
from typing import Any, TypeVar

from pydantic import BaseModel

from api_v1.controller_management.schemas import AllowedDataHostFields, SearchinDbHostBodyMonitoringAndManagementProxy, \
    SearchinDbHostBodyMonitoring
from core.user_exceptions import validate_exceptions


E = TypeVar('E', bound=validate_exceptions.BaseClientException)
T_PydanticModel = TypeVar("T_PydanticModel",
                          SearchinDbHostBodyMonitoringAndManagementProxy,
                          SearchinDbHostBodyMonitoring
                          )


class HostData:
    """
    Класс - обработчик данных хоста.
    """

    def __init__(self, ip_or_name: str, properties: T_PydanticModel):
        self.ip_or_name = ip_or_name
        self.properties = properties
        # self.ip_or_name_and_properties_as_dict = self.get_full_host_data_as_dict()

    def __repr__(self):
        return (
            f'self.ip_or_name: {self.ip_or_name}\n'
            f'self.properties: {json.dumps(self.properties, indent=2)}\n'
            f'self.ip_or_name_and_properties_as_dict: {json.dumps(self.ip_or_name_and_properties_as_dict, indent=2)}\n'
        )

    # def _add_errors_field_for_current_data_host_if_have_not(self) -> None:
    #     """
    #     Добавляет к self.properties свойство в виде dict: {"errors": []}.
    #     :return: None.
    #     """
    #     try:
    #         if self.properties.get(AllowedDataHostFields.errors) is None:
    #             self.properties |= {str(AllowedDataHostFields.errors): []}
    #     except AttributeError:
    #         if self.properties.errors is None:
    #             self.properties.errors = []

    # def add_error_entity_for_current_host(self, exc: E | str | list) -> None:
    #     """
    #     Добавляет сообщение с текстом ошибки.
    #     :param exc: Экземпляр пользовательского класса ошибки.
    #     :return: None
    #     """
    #     self._add_errors_field_for_current_data_host_if_have_not()
    #     if isinstance(exc, validate_exceptions.BaseClientException):
    #         e = exc.get_data_about_exc()
    #         self.properties[str(AllowedDataHostFields.errors)].append(e)
    #     elif isinstance(exc, (str, list)):
    #         try:
    #             self.properties[str(AllowedDataHostFields.errors)] += exc
    #         except TypeError:
    #             self.properties.errors += exc
    #         # self.properties[str(AllowedDataHostFields.errors)].append(exc)
    #
    #     else:
    #         raise ValueError
    #     # if not isinstance(exc, validate_exceptions.BaseClientException):
    #     #     raise ValueError
    #     # self.properties[str(AllowedDataHostFields.errors)].append(exc.get_data_about_exc())
    #     # self.properties[str(AllowedDataHostFields.errors)].append(e)

    def add_error_entity_for_current_host(self, exc: E | str | list) -> None:
        """
        Добавляет сообщение с текстом ошибки.
        :param exc: Экземпляр пользовательского класса ошибки.
        :return: None
        """
        if isinstance(exc, validate_exceptions.BaseClientException):
            e = exc.get_data_about_exc()
            self.properties[str(AllowedDataHostFields.errors)].append(e)
        elif isinstance(exc, (str, list)):
            try:
                self.properties[str(AllowedDataHostFields.errors)] += exc
            except TypeError:
                self.properties.errors += exc
            # self.properties[str(AllowedDataHostFields.errors)].append(exc)

        else:
            raise ValueError
        # if not isinstance(exc, validate_exceptions.BaseClientException):
        #     raise ValueError
        # self.properties[str(AllowedDataHostFields.errors)].append(exc.get_data_about_exc())
        # self.properties[str(AllowedDataHostFields.errors)].append(e)

    @property
    def full_host_data_as_dict(self):
        return {self.ip_or_name: self.properties}

    # def get_full_host_data_as_dict(self) -> dict[str, dict[str, Any]]:
    #     """
    #     Возвращает словарь вида {self.ip_or_name: self.properties}
    #     :return:
    #     """
    #     return {self.ip_or_name: self.properties}
    #
    # def _get_full_host_data_as_dict(self) -> dict[str, Any]:
    #     return self.properties | {str(AllowedDataHostFields.ipv4): self.ip_or_name}