import json
from typing import TypeVar

from api_v1.controller_management.schemas import (
    AllowedDataHostFields,
    SearchinDbHostBodyForMonitoringAndManagementProxy,
    SearchinDbHostBodyForMonitoring
)

from core.user_exceptions import validate_exceptions


E = TypeVar('E', bound=validate_exceptions.BaseClientException)
T_PydanticModel = TypeVar("T_PydanticModel",
                          SearchinDbHostBodyForMonitoringAndManagementProxy,
                          SearchinDbHostBodyForMonitoring
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
            # f'self.ip_or_name_and_properties_as_dict: {json.dumps(self.ip_or_name_and_properties_as_dict, indent=2)}\n'
        )

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

