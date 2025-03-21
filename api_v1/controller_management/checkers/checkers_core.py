import json
from typing import TypeVar

from pydantic import ValidationError

from api_v1.controller_management.schemas import (
    AllowedDataHostFields,
    T_PydanticModel
)
from core.user_exceptions import validate_exceptions


# E = TypeVar('E', bound=ValidationError, covariant=True)


class HostData:
    """
    Класс - обработчик данных хоста.
    """

    def __init__(self, ip_or_name: str, properties: T_PydanticModel):
        self.ip_or_name = ip_or_name
        self.properties = properties

    def __repr__(self):
        return (
            f'self.ip_or_name: {self.ip_or_name}\n'
            f'self.properties: {json.dumps(self.properties, indent=2)}\n'
            # f'self.ip_or_name_and_properties_as_dict: {json.dumps(self.ip_or_name_and_properties_as_dict, indent=2)}\n'
        )

    def add_error_entity_for_current_host(self, exc: str | list) -> None:
        """
        Добавляет сообщение с текстом ошибки.
        :param exc: Экземпляр пользовательского класса ошибки.
        :return: None
        """
        self.properties.errors += exc

    @property
    def full_host_data_as_dict(self):
        return {self.ip_or_name: self.properties}

