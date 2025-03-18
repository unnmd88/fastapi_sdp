import abc
from typing import TypeVar, Any

from pydantic import BaseModel

T_PydanticModel = TypeVar("T_PydanticModel", bound=BaseModel, covariant=True)


class BaseHost:
    def __init__(
            self,
            source_data: T_PydanticModel | dict[str, Any],
    ):
        self.source_data = source_data
        self.hosts_data = self.create_hosts_data(self.source_data.hosts)

    @abc.abstractmethod
    def create_hosts_data(self, hosts) -> dict:
        ...