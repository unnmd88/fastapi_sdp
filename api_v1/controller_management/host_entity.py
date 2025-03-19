import abc
from typing import TypeVar, Any

from pydantic import BaseModel

T_PydanticModel = TypeVar("T_PydanticModel", bound=BaseModel, covariant=True)


class BaseDataHosts(abc.ABC):
    def __init__(self, source_data: T_PydanticModel |  dict[str, T_PydanticModel]):
        self.source_data = source_data
        self.hosts_data = self.create_hosts_data()

    def create_hosts_data(self) -> Any:
        raise NotImplementedError()